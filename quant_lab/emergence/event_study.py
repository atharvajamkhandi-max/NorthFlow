"""
Pre-Move Event Study Fingerprinting (T-60 to T+60).
"""
import pandas as pd
import numpy as np

def run_emergence_event_study(industry_df: pd.DataFrame, 
                              emergence_events: list, 
                              windows: list = [-60, -40, -20, -10, -5, -3, -1, 0, 1, 3, 5, 10, 20, 40, 60]) -> pd.DataFrame:
    """
    Computes the statistical trajectory of features around major emergence events.
    """
    event_logs = []
    
    for event in emergence_events:
        ind = event['industry']
        event_date = pd.to_datetime(event['date'])
        
        ind_data = industry_df[industry_df['industry'] == ind].sort_values('date').reset_index(drop=True)
        if ind_data.empty:
            continue
            
        dates = ind_data['date'].values
        matching_indices = np.where(ind_data['date'] == event_date)[0]
        if len(matching_indices) == 0:
            continue
            
        t0_idx = matching_indices[0]
        
        for w in windows:
            curr_idx = t0_idx + w
            if 0 <= curr_idx < len(ind_data):
                row = ind_data.iloc[curr_idx]
                event_logs.append({
                    "Industry": ind,
                    "Event_Date": event_date.strftime('%Y-%m-%d'),
                    "T_Offset": w,
                    "Breadth_50": row.get('industry_breadth_50', 50.0),
                    "Return_20D": row.get('industry_return_20d', 0.0),
                    "Dispersion": row.get('industry_dispersion', 1.0)
                })
                
    df_event = pd.DataFrame(event_logs)
    if not df_event.empty:
        summary = df_event.groupby('T_Offset').agg(
            Avg_Breadth_50=('Breadth_50', 'mean'),
            Avg_Return_20D=('Return_20D', 'mean'),
            Avg_Dispersion=('Dispersion', 'mean')
        ).reset_index()
        return summary
    return pd.DataFrame()
