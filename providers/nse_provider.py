"""
NSE Data Provider Layer.
Encapsulates all interaction with nselib and direct NSE data endpoints.
Normalizes schemas, types, dates, series, delivery data, and handles market holidays and network errors.
"""

import logging
import datetime
from typing import Optional, List, Dict, Any, Union
import pandas as pd
import numpy as np

import nselib
from nselib import capital_market

from config.settings import VALID_SERIES, BENCHMARK_INDEX

logger = logging.getLogger(__name__)


class NSEProvider:
    """
    Unified Data Provider wrapping nselib for Indian Stock Market data.
    """

    def __init__(self):
        self._holiday_cache = None

    @staticmethod
    def _format_to_dmy(date_val: Union[str, datetime.date, datetime.datetime]) -> str:
        """Converts date to DD-MM-YYYY required by nselib."""
        if isinstance(date_val, (datetime.date, datetime.datetime)):
            return date_val.strftime("%d-%m-%Y")
        if isinstance(date_val, str):
            # Parse possible formats
            for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d-%b-%Y", "%Y/%m/%d", "%d/%m/%Y"):
                try:
                    dt = datetime.datetime.strptime(date_val, fmt)
                    return dt.strftime("%d-%m-%Y")
                except ValueError:
                    continue
        raise ValueError(f"Cannot parse date format: {date_val}")

    @staticmethod
    def _format_to_iso(date_val: Union[str, datetime.date, datetime.datetime]) -> str:
        """Converts date to ISO format YYYY-MM-DD."""
        if isinstance(date_val, (datetime.date, datetime.datetime)):
            return date_val.strftime("%Y-%m-%d")
        if isinstance(date_val, str):
            for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d-%b-%Y", "%d/%m/%Y", "%Y/%m/%d"):
                try:
                    dt = datetime.datetime.strptime(date_val, fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
        raise ValueError(f"Cannot parse date to ISO: {date_val}")

    def get_trading_holidays(self) -> List[str]:
        """
        Retrieves list of NSE trading holidays in YYYY-MM-DD format.
        """
        if self._holiday_cache is not None:
            return self._holiday_cache

        holidays = []
        try:
            df_hol = nselib.trading_holiday_calendar()
            if df_hol is not None and not df_hol.empty:
                # Filter specifically for Equities segment if Product column exists
                if 'Product' in df_hol.columns:
                    df_hol = df_hol[df_hol['Product'].astype(str).str.strip().str.lower() == 'equities']

                # Find date column
                date_col = None
                for col in df_hol.columns:
                    if 'date' in col.lower() or 'tradingdate' in col.lower():
                        date_col = col
                        break
                if date_col:
                    for val in df_hol[date_col].dropna():
                        try:
                            iso_d = self._format_to_iso(str(val).strip())
                            holidays.append(iso_d)
                        except Exception:
                            pass
        except Exception as e:
            logger.warning(f"Could not load trading holidays from nselib: {e}")

        self._holiday_cache = list(set(holidays))
        return self._holiday_cache

    def get_trading_days(self, start_date: Union[str, datetime.date], end_date: Union[str, datetime.date]) -> List[str]:
        """
        Generates list of expected trading dates (YYYY-MM-DD) excluding weekends and known NSE holidays.
        """
        iso_start = self._format_to_iso(start_date)
        iso_end = self._format_to_iso(end_date)
        
        start_dt = datetime.datetime.strptime(iso_start, "%Y-%m-%d").date()
        end_dt = datetime.datetime.strptime(iso_end, "%Y-%m-%d").date()
        
        if start_dt > end_dt:
            return []

        holidays = set(self.get_trading_holidays())
        trading_days = []
        curr = start_dt
        while curr <= end_dt:
            # 0=Monday, 4=Friday, 5=Saturday, 6=Sunday
            if curr.weekday() < 5:
                curr_str = curr.strftime("%Y-%m-%d")
                if curr_str not in holidays:
                    trading_days.append(curr_str)
            curr += datetime.timedelta(days=1)

        return trading_days

    def _fetch_bhavcopy_direct_cdn(self, trade_date) -> pd.DataFrame:
        """
        Fetches bhavcopy directly from NSE archives CDN — no session cookies needed.
        Works from any IP including GitHub Actions cloud runners.
        URL: https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_{DDMMYYYY}.csv
        """
        import requests
        from io import StringIO

        if isinstance(trade_date, datetime.date):
            ddmmyyyy = trade_date.strftime('%d%m%Y')
            iso_date = trade_date.strftime('%Y-%m-%d')
        else:
            # Parse from ISO or DMY
            for fmt in ('%Y-%m-%d', '%d-%m-%Y'):
                try:
                    dt = datetime.datetime.strptime(str(trade_date), fmt)
                    ddmmyyyy = dt.strftime('%d%m%Y')
                    iso_date = dt.strftime('%Y-%m-%d')
                    break
                except ValueError:
                    continue
            else:
                return pd.DataFrame()

        url = f'https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_{ddmmyyyy}.csv'
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/130.0.0.0 Safari/537.36'
            ),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.nseindia.com/',
        }

        logger.info(f"CDN fetch: {url}")
        try:
            r = requests.get(url, headers=headers, timeout=30)
            if r.status_code == 200 and len(r.content) > 1000:
                content = r.content.decode('utf-8', errors='ignore')
                df_raw = pd.read_csv(StringIO(content))
                # Normalize column names (strip spaces)
                df_raw.columns = [c.strip() for c in df_raw.columns]
                logger.info(f"CDN fetch succeeded: {len(df_raw)} rows")
                return df_raw, iso_date
            else:
                logger.warning(f"CDN fetch returned status {r.status_code} for {ddmmyyyy}")
                return None, iso_date
        except Exception as e:
            logger.warning(f"CDN fetch failed: {e}")
            return None, iso_date

    def get_daily_equity_data(self, trade_date) -> pd.DataFrame:
        """
        Fetches daily market data (OHLC, volume, turnover, delivery) for all NSE stocks for a given date.

        Strategy:
        1. Try direct NSE Archives CDN (no session required — works from cloud IPs)
        2. Fall back to nselib.bhav_copy_with_delivery (requires IP not blocked by NSE)
        3. Fall back to nselib.bhav_copy_equities

        Returns DataFrame with standard schema:
        ['date', 'symbol', 'series', 'open', 'high', 'low', 'close', 'previous_close',
         'volume', 'turnover', 'delivery_quantity', 'delivery_percentage']
        """
        dmy_date = self._format_to_dmy(trade_date)
        iso_date = self._format_to_iso(trade_date)

        logger.info(f"Fetching bhavcopy for trade date: {dmy_date} ({iso_date})")

        # ── Strategy 1: Direct CDN (works from any IP) ──────────────────────
        df_raw, iso_date = self._fetch_bhavcopy_direct_cdn(trade_date)
        if df_raw is not None and not df_raw.empty:
            return self._parse_delivery_bhavcopy(df_raw, iso_date)

        # ── Strategy 2: nselib with delivery (requires non-blocked IP) ───────
        logger.warning("CDN fetch failed — trying nselib bhav_copy_with_delivery...")
        try:
            df_raw = capital_market.bhav_copy_with_delivery(dmy_date)
            if df_raw is not None and not df_raw.empty:
                df_raw.columns = [str(c).strip() for c in df_raw.columns]
                return self._parse_delivery_bhavcopy(df_raw, iso_date)
        except Exception as e:
            logger.warning(f"bhav_copy_with_delivery failed: {e}")

        # ── Strategy 3: nselib standard bhavcopy fallback ────────────────────
        logger.warning("Trying nselib bhav_copy_equities fallback...")
        try:
            df_raw = capital_market.bhav_copy_equities(dmy_date)
            if df_raw is not None and not df_raw.empty:
                df_raw.columns = [str(c).strip() for c in df_raw.columns]
                if 'TckrSymb' in df_raw.columns:
                    return self._parse_old_bhavcopy(df_raw, iso_date)
                return self._parse_standard_bhavcopy(df_raw, iso_date)
        except Exception as e:
            logger.error(f"All bhavcopy fetch strategies failed for {dmy_date}: {e}")

        logger.error(f"No market data available for {dmy_date}")
        return pd.DataFrame()


    def _parse_delivery_bhavcopy(self, df: pd.DataFrame, iso_date: str) -> pd.DataFrame:
        """Parses output from bhav_copy_with_delivery."""
        # Columns: ['SYMBOL', 'SERIES', 'DATE1', 'PREV_CLOSE', 'OPEN_PRICE', 'HIGH_PRICE', 'LOW_PRICE', 'LAST_PRICE', 'CLOSE_PRICE', 'AVG_PRICE', 'TTL_TRD_QNTY', 'TURNOVER_LACS', 'NO_OF_TRADES', 'DELIV_QTY', 'DELIV_PER']
        df['symbol'] = df['SYMBOL'].astype(str).str.strip().str.upper()
        df['series'] = df['SERIES'].astype(str).str.strip().str.upper()
        
        # Filter series
        if VALID_SERIES:
            df = df[df['series'].isin(VALID_SERIES)].copy()

        df['date'] = iso_date
        
        # Numeric conversions
        for col_raw, col_target in [
            ('OPEN_PRICE', 'open'),
            ('HIGH_PRICE', 'high'),
            ('LOW_PRICE', 'low'),
            ('CLOSE_PRICE', 'close'),
            ('PREV_CLOSE', 'previous_close'),
            ('TURNOVER_LACS', 'turnover'),
            ('TTL_TRD_QNTY', 'volume'),
            ('DELIV_QTY', 'delivery_quantity'),
            ('DELIV_PER', 'delivery_percentage')
        ]:
            if col_raw in df.columns:
                # Replace '-' or whitespace with NaN
                s = df[col_raw].astype(str).str.strip().replace({'-': np.nan, '': np.nan, 'None': np.nan})
                df[col_target] = pd.to_numeric(s, errors='coerce')
            else:
                df[col_target] = np.nan

        # If turnover is in Lacs, convert to exact rupees: turnover_lacs * 100,000
        if 'turnover' in df.columns:
            df['turnover'] = df['turnover'] * 100000.0

        # Validate prices: close > 0, high >= low
        df = df[df['close'] > 0].copy()
        
        # Drop duplicates on symbol if any
        df = df.drop_duplicates(subset=['symbol'], keep='first')

        final_cols = [
            'date', 'symbol', 'series', 'open', 'high', 'low', 'close',
            'previous_close', 'volume', 'turnover', 'delivery_quantity', 'delivery_percentage'
        ]
        return df[final_cols].reset_index(drop=True)

    def _parse_old_bhavcopy(self, df: pd.DataFrame, iso_date: str) -> pd.DataFrame:
        """Parses output from bhav_copy_equities with TckrSymb format."""
        df['symbol'] = df['TckrSymb'].astype(str).str.strip().str.upper()
        df['series'] = df.get('SctySrs', pd.Series('EQ', index=df.index)).astype(str).str.strip().str.upper()
        
        if VALID_SERIES:
            df = df[df['series'].isin(VALID_SERIES)].copy()

        df['date'] = iso_date
        
        for col_raw, col_target in [
            ('OpnPric', 'open'),
            ('HghPric', 'high'),
            ('LwPric', 'low'),
            ('ClsPric', 'close'),
            ('PrvsClsgPric', 'previous_close'),
            ('TtlTradgVol', 'volume'),
            ('TtlTrfVal', 'turnover')
        ]:
            if col_raw in df.columns:
                s = df[col_raw].astype(str).str.strip().replace({'-': np.nan, '': np.nan})
                df[col_target] = pd.to_numeric(s, errors='coerce')
            else:
                df[col_target] = np.nan

        df['delivery_quantity'] = np.nan
        df['delivery_percentage'] = np.nan

        df = df[df['close'] > 0].copy()
        df = df.drop_duplicates(subset=['symbol'], keep='first')

        final_cols = [
            'date', 'symbol', 'series', 'open', 'high', 'low', 'close',
            'previous_close', 'volume', 'turnover', 'delivery_quantity', 'delivery_percentage'
        ]
        return df[final_cols].reset_index(drop=True)

    def _parse_standard_bhavcopy(self, df: pd.DataFrame, iso_date: str) -> pd.DataFrame:
        """Parses standard bhavcopy format."""
        df['symbol'] = df['SYMBOL'].astype(str).str.strip().str.upper()
        df['series'] = df.get('SERIES', pd.Series('EQ', index=df.index)).astype(str).str.strip().str.upper()
        
        if VALID_SERIES:
            df = df[df['series'].isin(VALID_SERIES)].copy()

        df['date'] = iso_date
        
        for col_raw, col_target in [
            ('OPEN', 'open'),
            ('HIGH', 'high'),
            ('LOW', 'low'),
            ('CLOSE', 'close'),
            ('PREVCLOSE', 'previous_close'),
            ('TOTTRDQTY', 'volume'),
            ('TOTTRDVAL', 'turnover')
        ]:
            if col_raw in df.columns:
                s = df[col_raw].astype(str).str.strip().replace({'-': np.nan, '': np.nan})
                df[col_target] = pd.to_numeric(s, errors='coerce')
            else:
                df[col_target] = np.nan

        df['delivery_quantity'] = np.nan
        df['delivery_percentage'] = np.nan

        df = df[df['close'] > 0].copy()
        df = df.drop_duplicates(subset=['symbol'], keep='first')

        final_cols = [
            'date', 'symbol', 'series', 'open', 'high', 'low', 'close',
            'previous_close', 'volume', 'turnover', 'delivery_quantity', 'delivery_percentage'
        ]
        return df[final_cols].reset_index(drop=True)

    def get_index_data(self, index_name: str = BENCHMARK_INDEX,
                       from_date: Optional[Union[str, datetime.date]] = None,
                       to_date: Optional[Union[str, datetime.date]] = None,
                       period: Optional[str] = None) -> pd.DataFrame:
        """
        Fetches historical index benchmark data (e.g. NIFTY 50).
        
        Returns DataFrame with schema:
        ['date', 'index_name', 'open', 'high', 'low', 'close', 'volume', 'turnover']
        """
        dmy_from = self._format_to_dmy(from_date) if from_date else None
        dmy_to = self._format_to_dmy(to_date) if to_date else None
        
        try:
            df_raw = capital_market.index_data(index=index_name, from_date=dmy_from, to_date=dmy_to, period=period)
        except Exception as e:
            logger.error(f"Failed to fetch index data for {index_name}: {e}")
            return pd.DataFrame()

        if df_raw is None or df_raw.empty:
            return pd.DataFrame()

        df = df_raw.copy()
        df.columns = [str(c).strip() for c in df.columns]

        # Convert date
        # Column TIMESTAMP format e.g. '14-AUG-2024' or '14-08-2024'
        if 'TIMESTAMP' in df.columns:
            df['date'] = df['TIMESTAMP'].apply(lambda x: self._format_to_iso(str(x).strip()))
        elif 'HistoricalDate' in df.columns:
            df['date'] = df['HistoricalDate'].apply(lambda x: self._format_to_iso(str(x).strip()))
        else:
            df['date'] = datetime.date.today().strftime("%Y-%m-%d")

        df['index_name'] = index_name
        
        for col_raw, col_target in [
            ('OPEN_INDEX_VAL', 'open'),
            ('HIGH_INDEX_VAL', 'high'),
            ('LOW_INDEX_VAL', 'low'),
            ('CLOSE_INDEX_VAL', 'close'),
            ('TRADED_QTY', 'volume'),
            ('TURN_OVER', 'turnover')
        ]:
            if col_raw in df.columns:
                s = df[col_raw].astype(str).str.replace(',', '').str.strip().replace({'-': np.nan, '': np.nan})
                df[col_target] = pd.to_numeric(s, errors='coerce')
            else:
                df[col_target] = np.nan

        df = df[df['close'] > 0].copy()
        df = df.sort_values('date').drop_duplicates(subset=['date'], keep='last').reset_index(drop=True)

        cols = ['date', 'index_name', 'open', 'high', 'low', 'close', 'volume', 'turnover']
        return df[cols]

    def get_security_universe(self) -> pd.DataFrame:
        """
        Fetches the complete listed equity master from NSE.
        Returns DataFrame with ['symbol', 'company_name', 'series', 'isin']
        """
        try:
            df_raw = capital_market.equity_list()
        except Exception as e:
            logger.error(f"Failed to fetch equity list: {e}")
            return pd.DataFrame()

        if df_raw is None or df_raw.empty:
            return pd.DataFrame()

        df = df_raw.copy()
        df.columns = [str(c).strip() for c in df.columns]

        # Standardize columns
        df['symbol'] = df['SYMBOL'].astype(str).str.strip().str.upper()
        
        name_col = next((c for c in ['NAME OF COMPANY', 'NAME_OF_COMPANY', 'COMPANY NAME', 'Company Name'] if c in df.columns), None)
        df['company_name'] = df[name_col].astype(str).str.strip() if name_col else df['symbol']

        series_col = next((c for c in ['SERIES', 'Series', ' Srs'] if c in df.columns), None)
        df['series'] = df[series_col].astype(str).str.strip().str.upper() if series_col else 'EQ'

        isin_col = next((c for c in ['ISIN NUMBER', 'ISIN', 'ISIN_NUMBER', 'ISIN Code'] if c in df.columns), None)
        df['isin'] = df[isin_col].astype(str).str.strip().str.upper() if isin_col else ''

        if VALID_SERIES:
            df = df[df['series'].isin(VALID_SERIES)].copy()

        df = df.drop_duplicates(subset=['symbol'], keep='first').reset_index(drop=True)
        return df[['symbol', 'company_name', 'series', 'isin']]
