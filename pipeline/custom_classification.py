"""
Custom Industry & Segment Classification Resolver.
Validates and synchronizes Layer 2 custom trading classifications from data/custom_industry_mapping.csv
into SQLite custom_industry_classification table without modifying official NSE classifications.
"""

import logging
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

from database.db import Database
from config.settings import CUSTOM_INDUSTRY_MAPPING_PATH

logger = logging.getLogger(__name__)


class CustomClassificationResolver:
    """
    Validates and synchronizes custom trading industry and segment mappings.
    """

    def __init__(self, db: Optional[Database] = None, csv_path: Optional[Path] = None):
        self.db = db or Database()
        self.csv_path = Path(csv_path) if csv_path else CUSTOM_INDUSTRY_MAPPING_PATH

    def sync_custom_classifications(self) -> Dict[str, Any]:
        """
        Reads data/custom_industry_mapping.csv, validates rows against stocks universe,
        detects duplicates and invalid symbols, and updates custom_industry_classification table.
        Returns a structured validation report.
        """
        logger.info(f"Synchronizing custom classifications from {self.csv_path}...")
        self.db.initialize_schema()

        if not self.csv_path.exists():
            logger.warning(f"Custom mapping CSV not found at {self.csv_path}")
            return {
                "status": "NOT_FOUND",
                "rows_read": 0,
                "valid_count": 0,
                "invalid_symbols": [],
                "duplicate_symbols": [],
                "malformed_rows": 0,
                "updated_records": 0,
                "message": f"Mapping file {self.csv_path} does not exist."
            }

        try:
            df = pd.read_csv(self.csv_path)
        except Exception as e:
            logger.error(f"Failed to parse CSV file {self.csv_path}: {e}")
            return {
                "status": "PARSE_ERROR",
                "rows_read": 0,
                "valid_count": 0,
                "invalid_symbols": [],
                "duplicate_symbols": [],
                "malformed_rows": 0,
                "updated_records": 0,
                "message": f"CSV parse error: {str(e)}"
            }

        # Normalize column names
        df.columns = [str(c).strip().lower() for c in df.columns]
        rows_read = len(df)

        if 'symbol' not in df.columns or 'custom_industry' not in df.columns:
            msg = "CSV must contain at least 'symbol' and 'custom_industry' columns."
            logger.error(msg)
            return {
                "status": "INVALID_COLUMNS",
                "rows_read": rows_read,
                "valid_count": 0,
                "invalid_symbols": [],
                "duplicate_symbols": [],
                "malformed_rows": rows_read,
                "updated_records": 0,
                "message": msg
            }

        # Load known active universe symbols from stocks table
        with self.db.get_connection() as conn:
            valid_universe_symbols = set(
                r[0] for r in conn.execute("SELECT symbol FROM stocks;").fetchall()
            )

        seen_symbols = set()
        duplicate_symbols = []
        invalid_symbols = []
        valid_records = []
        malformed_count = 0
        now_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for idx, row in df.iterrows():
            sym_raw = row.get('symbol')
            ind_raw = row.get('custom_industry')
            seg_raw = row.get('custom_segment')
            notes_raw = row.get('notes', '')

            # Check for missing symbol or industry
            if pd.isna(sym_raw) or not str(sym_raw).strip() or pd.isna(ind_raw) or not str(ind_raw).strip():
                malformed_count += 1
                continue

            sym = str(sym_raw).strip().upper()
            ind = str(ind_raw).strip()
            seg = str(seg_raw).strip() if pd.notna(seg_raw) and str(seg_raw).strip() else None
            notes = str(notes_raw).strip() if pd.notna(notes_raw) else ''

            # Duplicate Check in CSV
            if sym in seen_symbols:
                duplicate_symbols.append(sym)
                continue
            seen_symbols.add(sym)

            # Universe Existence Check
            if valid_universe_symbols and sym not in valid_universe_symbols:
                invalid_symbols.append(sym)
                continue

            valid_records.append({
                'symbol': sym,
                'custom_industry': ind,
                'custom_segment': seg,
                'classification_source': 'MANUAL_MAP',
                'confidence': 1.0,
                'notes': notes,
                'updated_at': now_ts
            })

        # Persist valid records into custom_industry_classification table
        updated_records = 0
        if valid_records:
            df_valid = pd.DataFrame(valid_records)
            updated_records = self.db.insert_or_replace_df("custom_industry_classification", df_valid)

        report = {
            "status": "SUCCESS",
            "rows_read": rows_read,
            "valid_count": len(valid_records),
            "invalid_symbols": invalid_symbols,
            "duplicate_symbols": duplicate_symbols,
            "malformed_rows": malformed_count,
            "updated_records": updated_records,
            "message": f"Successfully synced {updated_records} custom classification records."
        }

        self.db.log_pipeline_event(
            stage="CUSTOM_CLASSIFICATION_SYNC",
            status="SUCCESS",
            records_processed=updated_records,
            message=f"Rows: {rows_read}, Valid: {len(valid_records)}, Invalid: {len(invalid_symbols)}, Duplicates: {len(duplicate_symbols)}"
        )
        logger.info(f"Custom Classification Sync Report: {report}")
        return report
