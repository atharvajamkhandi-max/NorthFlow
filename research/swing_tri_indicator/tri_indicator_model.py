"""
Tri-Indicator Swing Strategy Research Engine.
Based on "The Only Swing Strategy You Need: 3 Indicators, 1 High-Probability Trade"
(EMA 3/15 Ribbon + ZigZag Market Structure / BOS + MACD Histogram Expansion).
Designed strictly for quantitative research, backtesting, and model learning.
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any

BASE = Path(r"C:\Users\athar\.gemini\antigravity\scratch\industry-money-flow")
DB_PATH = BASE / "data" / "market_flow.db"

def calculate_zigzag_pivots(highs: np.ndarray, lows: np.ndarray, deviation_pct: float = 3.0) -> List[Dict[str, Any]]:
    """
    Computes ZigZag swing pivots (Higher Highs, Higher Lows, BOS).
    """
    n = len(highs)
    if n < 10:
        return []
        
    pivots = []
    trend = 0  # 1: Up, -1: Down
    last_pivot_idx = 0
    last_pivot_price = (highs[0] + lows[0]) / 2.0
    
    for i in range(1, n):
        h = highs[i]
        l = lows[i]
        
        if trend == 0:
            if h >= last_pivot_price * (1 + deviation_pct / 100.0):
                trend = 1
                last_pivot_idx = i
                last_pivot_price = h
                pivots.append({'idx': i, 'type': 'HIGH', 'price': h})
            elif l <= last_pivot_price * (1 - deviation_pct / 100.0):
                trend = -1
                last_pivot_idx = i
                last_pivot_price = l
                pivots.append({'idx': i, 'type': 'LOW', 'price': l})
        elif trend == 1:
            if h > last_pivot_price:
                last_pivot_idx = i
                last_pivot_price = h
                if pivots:
                    pivots[-1] = {'idx': i, 'type': 'HIGH', 'price': h}
            elif l <= last_pivot_price * (1 - deviation_pct / 100.0):
                trend = -1
                last_pivot_idx = i
                last_pivot_price = l
                pivots.append({'idx': i, 'type': 'LOW', 'price': l})
        elif trend == -1:
            if l < last_pivot_price:
                last_pivot_idx = i
                last_pivot_price = l
                if pivots:
                    pivots[-1] = {'idx': i, 'type': 'LOW', 'price': l}
            elif h >= last_pivot_price * (1 + deviation_pct / 100.0):
                trend = 1
                last_pivot_idx = i
                last_pivot_price = h
                pivots.append({'idx': i, 'type': 'HIGH', 'price': h})
                
    return pivots


def backtest_tri_indicator_strategy(min_history_bars: int = 35) -> Dict[str, Any]:
    """
    Backtests the 3-Indicator Strategy across all equities in the historical database.
    """
    conn = sqlite3.connect(str(DB_PATH))
    
    df_all_prices = pd.read_sql("""
        SELECT symbol, date, open, high, low, close, volume
        FROM daily_prices
        ORDER BY symbol, date ASC
    """, conn)
    
    completed_trades = []
    
    for sym, df_sym in df_all_prices.groupby('symbol'):
        if len(df_sym) < min_history_bars:
            continue
            
        df_sym = df_sym.reset_index(drop=True)
        closes = df_sym['close'].values
        highs = df_sym['high'].values
        lows = df_sym['low'].values
        dates = df_sym['date'].values
        
        # Indicator 1: Fast EMA 3 and Base EMA 15
        s_close = pd.Series(closes)
        ema_3 = s_close.ewm(span=3, adjust=False).mean().values
        ema_15 = s_close.ewm(span=15, adjust=False).mean().values
        
        # Indicator 2: MACD (12, 26, 9) Histogram
        ema_12 = s_close.ewm(span=12, adjust=False).mean()
        ema_26 = s_close.ewm(span=26, adjust=False).mean()
        macd_line = (ema_12 - ema_26).values
        signal_line = pd.Series(macd_line).ewm(span=9, adjust=False).mean().values
        macd_hist = macd_line - signal_line
        
        # Indicator 3: ZigZag Market Structure
        pivots = calculate_zigzag_pivots(highs, lows, deviation_pct=3.0)
        if len(pivots) < 4:
            continue
            
        in_trade = False
        entry_idx = 0
        entry_price = 0.0
        stop_loss = 0.0
        target_1 = 0.0
        target_2 = 0.0
        
        for i in range(15, len(df_sym) - 2):
            if in_trade:
                curr_h = highs[i]
                curr_l = lows[i]
                curr_c = closes[i]
                
                if curr_h >= target_2:
                    pnl = ((target_2 - entry_price) / entry_price) * 100.0
                    completed_trades.append({
                        'symbol': sym,
                        'entry_date': dates[entry_idx],
                        'exit_date': dates[i],
                        'entry_price': entry_price,
                        'exit_price': target_2,
                        'pnl_pct': pnl,
                        'result': 'WIN_T2',
                        'bars_held': i - entry_idx
                    })
                    in_trade = False
                elif curr_h >= target_1 and curr_c < target_1:
                    pnl = ((target_1 - entry_price) / entry_price) * 100.0
                    completed_trades.append({
                        'symbol': sym,
                        'entry_date': dates[entry_idx],
                        'exit_date': dates[i],
                        'entry_price': entry_price,
                        'exit_price': target_1,
                        'pnl_pct': pnl,
                        'result': 'WIN_T1',
                        'bars_held': i - entry_idx
                    })
                    in_trade = False
                elif curr_l <= stop_loss:
                    pnl = ((stop_loss - entry_price) / entry_price) * 100.0
                    completed_trades.append({
                        'symbol': sym,
                        'entry_date': dates[entry_idx],
                        'exit_date': dates[i],
                        'entry_price': entry_price,
                        'exit_price': stop_loss,
                        'pnl_pct': pnl,
                        'result': 'LOSS_SL',
                        'bars_held': i - entry_idx
                    })
                    in_trade = False
                elif (i - entry_idx) >= 12:  # 12-day max swing duration
                    pnl = ((curr_c - entry_price) / entry_price) * 100.0
                    completed_trades.append({
                        'symbol': sym,
                        'entry_date': dates[entry_idx],
                        'exit_date': dates[i],
                        'entry_price': entry_price,
                        'exit_price': curr_c,
                        'pnl_pct': pnl,
                        'result': 'TIME_EXIT',
                        'bars_held': i - entry_idx
                    })
                    in_trade = False
                continue

            trend_bullish = (ema_3[i] > ema_15[i]) and (closes[i] > ema_15[i])
            momentum_bullish = (macd_hist[i] > 0) and (macd_hist[i] > macd_hist[i-1])
            
            past_lows = [p for p in pivots if p['idx'] < i and p['type'] == 'LOW']
            past_highs = [p for p in pivots if p['idx'] < i and p['type'] == 'HIGH']
            
            if past_lows and past_highs and trend_bullish and momentum_bullish:
                recent_hl = past_lows[-1]['price']
                recent_sh = past_highs[-1]['price']
                
                if closes[i] > recent_hl and closes[i] <= recent_sh * 1.01:
                    entry_price = float(closes[i])
                    stop_loss = float(recent_hl * 0.992)
                    target_1 = float(recent_sh)
                    target_2 = float(entry_price + ((target_1 - entry_price) * 1.618))
                    
                    risk = entry_price - stop_loss
                    reward = target_1 - entry_price
                    
                    if risk > 0 and reward > 0 and (reward / risk) >= 1.6 and (risk / entry_price) <= 0.05:
                        in_trade = True
                        entry_idx = i

    if not completed_trades:
        return {'total_trades': 0}
        
    df_res = pd.DataFrame(completed_trades)
    wins = df_res[df_res['pnl_pct'] > 0]
    losses = df_res[df_res['pnl_pct'] <= 0]
    
    win_rate = (len(wins) / len(df_res)) * 100.0
    avg_gain = wins['pnl_pct'].mean() if not wins.empty else 0.0
    avg_loss = abs(losses['pnl_pct'].mean()) if not losses.empty else 0.0
    profit_factor = (wins['pnl_pct'].sum() / abs(losses['pnl_pct'].sum())) if not losses.empty and losses['pnl_pct'].sum() != 0 else 0.0
    avg_trade_pnl = df_res['pnl_pct'].mean()
    
    return {
        'total_trades': len(df_res),
        'win_rate_pct': win_rate,
        'profit_factor': profit_factor,
        'avg_win_pct': avg_gain,
        'avg_loss_pct': avg_loss,
        'avg_trade_pnl_pct': avg_trade_pnl,
        'target_2_runners': len(df_res[df_res['result'] == 'WIN_T2']),
        'target_1_hits': len(df_res[df_res['result'] == 'WIN_T1']),
        'stop_losses': len(df_res[df_res['result'] == 'LOSS_SL']),
        'time_exits': len(df_res[df_res['result'] == 'TIME_EXIT']),
        'sample_trades': df_res.head(10).to_dict('records')
    }

if __name__ == "__main__":
    print("Executing Tri-Indicator Quantitative Backtest across historical price series...")
    res = backtest_tri_indicator_strategy()
    print("\n============================================================")
    print("  TRI-INDICATOR SWING STRATEGY QUANTITATIVE AUDIT")
    print("============================================================")
    print(f"  • Total Executed Setups: {res['total_trades']:,}")
    print(f"  • Strategy Win Rate:     {res['win_rate_pct']:.2f}%")
    print(f"  • Profit Factor:         {res['profit_factor']:.2f}")
    print(f"  • Avg Win Gain:          +{res['avg_win_pct']:.2f}%")
    print(f"  • Avg Loss Risk:         -{res['avg_loss_pct']:.2f}%")
    print(f"  • Net Trade Expectancy:  +{res['avg_trade_pnl_pct']:.2f}%")
    print(f"  • Target 1 Hits:         {res['target_1_hits']} ({res['target_1_hits']/res['total_trades']*100:.1f}%)")
    print(f"  • Target 2 Runners:      {res['target_2_runners']} ({res['target_2_runners']/res['total_trades']*100:.1f}%)")
    print(f"  • Stop-Loss Exits:       {res['stop_losses']} ({res['stop_losses']/res['total_trades']*100:.1f}%)")
