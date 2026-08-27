"""
Industry Classification and Stock Universe Synchronization Pipeline.
Applies the 4-tier resolution hierarchy:
1. User overrides (data/industry_overrides.csv) with action support (ADD, MOVE, SET, REMOVE)
2. Official / current NSE index classifications
3. Cached verified classification seed (data/seed_classifications.json)
4. UNKNOWN

Maintains and updates the 'stocks' master table in SQLite.
"""

import json
import logging
import io
import requests
import pandas as pd
import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from config.settings import INDUSTRY_OVERRIDES_PATH, SEED_CLASSIFICATIONS_PATH
from providers.nse_provider import NSEProvider
from database.db import Database

logger = logging.getLogger(__name__)


class ClassificationUpdater:
    """
    Manages stock universe discovery and granular industry classification resolution.
    """

    def __init__(self, db: Optional[Database] = None, provider: Optional[NSEProvider] = None):
        self.db = db or Database()
        self.provider = provider or NSEProvider()

    def load_user_overrides(self) -> Dict[str, Dict[str, str]]:
        """
        Loads manual user overrides from CSV.
        Supports columns: symbol, industry, basic_industry, [action]
        Actions supported: ADD, MOVE, SET (assigns industry), REMOVE (sets to UNKNOWN).
        """
        if not INDUSTRY_OVERRIDES_PATH.exists():
            return {}
        
        overrides = {}
        try:
            df = pd.read_csv(INDUSTRY_OVERRIDES_PATH)
            df.columns = [str(c).strip().lower() for c in df.columns]
            if 'symbol' in df.columns:
                for _, row in df.iterrows():
                    sym = str(row['symbol']).strip().upper()
                    if not sym or sym == 'NAN':
                        continue
                    action = str(row.get('action', 'SET')).strip().upper()
                    
                    if action == 'REMOVE':
                        overrides[sym] = {
                            "industry": "UNKNOWN",
                            "basic_industry": "UNKNOWN",
                            "action": "REMOVE"
                        }
                    else:
                        ind = str(row.get('industry', 'UNKNOWN')).strip()
                        basic_ind = str(row.get('basic_industry', ind)).strip()
                        overrides[sym] = {
                            "industry": ind if ind else "UNKNOWN",
                            "basic_industry": basic_ind if basic_ind else "UNKNOWN",
                            "action": action
                        }
        except Exception as e:
            logger.error(f"Error loading industry overrides from {INDUSTRY_OVERRIDES_PATH}: {e}")
        
        return overrides

    def load_seed_classifications(self) -> Dict[str, Dict[str, str]]:
        """Loads verified classification seed dictionary."""
        if not SEED_CLASSIFICATIONS_PATH.exists():
            return {}
        try:
            with open(SEED_CLASSIFICATIONS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading seed classifications from {SEED_CLASSIFICATIONS_PATH}: {e}")
            return {}

    def fetch_nse_index_classifications(self) -> Dict[str, Dict[str, str]]:
        """
        Fetches broad sector/industry classification from Nifty Total Market index CSV.
        """
        url = "https://archives.nseindia.com/content/indices/ind_niftytotalmarket_list.csv"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        mapping = {}
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200 and len(r.content) > 100:
                df = pd.read_csv(io.StringIO(r.text))
                for _, row in df.iterrows():
                    sym = str(row.get('Symbol', '')).strip().upper()
                    ind = str(row.get('Industry', 'UNKNOWN')).strip()
                    if sym:
                        mapping[sym] = {
                            "industry": ind,
                            "basic_industry": ind
                        }
        except Exception as e:
            logger.warning(f"Could not fetch live Nifty Total Market CSV: {e}")
        return mapping

    def sync_universe_and_classifications(self) -> int:
        """
        Main execution method:
        1. Fetches complete listed equity universe from NSE.
        2. Resolves classifications using 4-tier hierarchy.
        3. Updates SQLite 'stocks' table.
        """
        logger.info("Starting stock universe and classification synchronization...")
        self.db.initialize_schema()

        # Step 1: Fetch security universe
        df_universe = self.provider.get_security_universe()
        if df_universe.empty:
            logger.warning("Could not fetch equity universe from provider. Retaining existing DB stocks if present.")
            df_universe = self.db.get_active_stocks()
            if df_universe.empty:
                logger.error("No stocks available to process.")
                return 0

        # Step 2: Load sources
        overrides_map = self.load_user_overrides()
        if isinstance(overrides_map, pd.DataFrame):
            od = {}
            for _, r in overrides_map.iterrows():
                s = str(r.get('symbol', '')).strip().upper()
                if s:
                    od[s] = {
                        'industry': str(r.get('industry', 'UNKNOWN')).strip(),
                        'basic_industry': str(r.get('basic_industry', 'UNKNOWN')).strip(),
                        'action': str(r.get('action', 'SET')).strip().upper()
                    }
            overrides_map = od

        seed_map = self.load_seed_classifications()
        if isinstance(seed_map, pd.DataFrame):
            sd = {}
            for _, r in seed_map.iterrows():
                s = str(r.get('symbol', '')).strip().upper()
                if s:
                    sd[s] = {
                        'industry': str(r.get('industry', 'UNKNOWN')).strip(),
                        'basic_industry': str(r.get('basic_industry', 'UNKNOWN')).strip()
                    }
            seed_map = sd

        nse_index_map = self.fetch_nse_index_classifications()
        if isinstance(nse_index_map, pd.DataFrame):
            nd = {}
            for _, r in nse_index_map.iterrows():
                s = str(r.get('symbol', '')).strip().upper()
                if s:
                    nd[s] = {
                        'industry': str(r.get('industry', 'UNKNOWN')).strip(),
                        'basic_industry': str(r.get('basic_industry', 'UNKNOWN')).strip()
                    }
            nse_index_map = nd

        # Step 3: Resolve hierarchy
        now_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        records = []
        for _, row in df_universe.iterrows():
            sym = str(row['symbol']).strip().upper()
            comp_name = str(row.get('company_name', sym)).strip()
            isin = str(row.get('isin', '')).strip().upper()
            series = str(row.get('series', 'EQ')).strip().upper()

            # Priority 1: User Overrides (highest priority)
            if sym in overrides_map:
                ind = overrides_map[sym].get('industry', 'UNKNOWN')
                basic_ind = overrides_map[sym].get('basic_industry', 'UNKNOWN')
            # Priority 2: Seed Classifications
            elif sym in seed_map:
                ind = seed_map[sym].get('industry', 'UNKNOWN')
                basic_ind = seed_map[sym].get('basic_industry', 'UNKNOWN')
            # Priority 3: NSE Official Index Mapping
            elif sym in nse_index_map:
                ind = nse_index_map[sym].get('industry', 'UNKNOWN')
                basic_ind = nse_index_map[sym].get('basic_industry', 'UNKNOWN')
            # Priority 4: UNKNOWN
            else:
                ind = 'UNKNOWN'
                basic_ind = 'UNKNOWN'

            records.append({
                'symbol': sym,
                'company_name': comp_name,
                'isin': isin,
                'series': series,
                'industry': ind,
                'basic_industry': basic_ind,
                'active': 1,
                'last_updated': now_ts
            })

        df_final = pd.DataFrame(records)
        rowcount = self.db.insert_or_replace_df("stocks", df_final)
        
        self.db.log_pipeline_event(
            stage="CLASSIFICATION_SYNC",
            status="SUCCESS",
            records_processed=rowcount,
            message=f"Synced {rowcount} stocks. Overrides: {len(overrides_map)}, Seed: {len(seed_map)}, Index: {len(nse_index_map)}"
        )
        logger.info(f"Successfully synced {rowcount} stocks into SQLite database.")
        return rowcount

    def apply_overrides(self, overrides) -> int:
        """
        Applies a list or DataFrame of override dictionaries (ADD, MOVE, SET, REMOVE) directly to the database.
        """
        if isinstance(overrides, pd.DataFrame):
            overrides = overrides.to_dict('records')
        
        now_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updated_count = 0
        with self.db.get_connection() as conn:
            for item in overrides:
                sym = str(item.get('symbol', '')).strip().upper()
                if not sym:
                    continue
                action = str(item.get('action', 'SET')).strip().upper()
                ind = str(item.get('industry', 'UNKNOWN')).strip()
                basic_ind = str(item.get('basic_industry', ind)).strip()
                
                if action == 'REMOVE':
                    conn.execute("UPDATE stocks SET basic_industry = 'UNKNOWN', last_updated = ? WHERE symbol = ?;", [now_ts, sym])
                elif action in ('MOVE', 'SET'):
                    conn.execute("UPDATE stocks SET industry = ?, basic_industry = ?, last_updated = ? WHERE symbol = ?;", [ind, basic_ind, now_ts, sym])
                elif action == 'ADD':
                    comp = str(item.get('company_name', sym)).strip()
                    conn.execute(
                        "INSERT OR REPLACE INTO stocks (symbol, company_name, series, industry, basic_industry, active, last_updated) VALUES (?, ?, 'EQ', ?, ?, 1, ?);",
                        [sym, comp, ind, basic_ind, now_ts]
                    )
                updated_count += 1
        return updated_count

