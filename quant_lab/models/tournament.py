"""
Automated 10-Architecture Model Search Tournament for Quant Lab.
"""
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.linear_model import Ridge, Lasso, ElasticNet, HuberRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

def run_model_search_tournament(train_X: pd.DataFrame, train_y: pd.Series, 
                                test_X: pd.DataFrame, test_y: pd.Series, 
                                test_dates: pd.Series, max_train_samples: int = 40000) -> pd.DataFrame:
    """
    Evaluates candidate architectures out-of-sample:
    1. Ridge L2
    2. LASSO L1
    3. ElasticNet
    4. Huber M-Estimator
    5. Random Forest
    6. Gradient Boosting
    7. Equal-Weighted Linear Ensemble
    8. Robust Hybrid Ensemble
    """
    # Sample training set if too large for speed
    if len(train_X) > max_train_samples:
        sample_idx = np.random.choice(train_X.index, size=max_train_samples, replace=False)
        tr_X = train_X.loc[sample_idx]
        tr_y = train_y.loc[sample_idx]
    else:
        tr_X = train_X
        tr_y = train_y

    models = {
        "Ridge_L2": Ridge(alpha=10.0),
        "LASSO_L1": Lasso(alpha=0.1),
        "ElasticNet": ElasticNet(alpha=0.1, l1_ratio=0.5),
        "Huber_M_Estimator": HuberRegressor(max_iter=300),
        "Random_Forest": RandomForestRegressor(n_estimators=30, max_depth=5, random_state=42, n_jobs=-1),
        "Gradient_Boosting": GradientBoostingRegressor(n_estimators=30, max_depth=3, random_state=42)
    }
    
    results = []
    preds = {}
    
    # Train and predict
    for name, m in models.items():
        m.fit(tr_X, tr_y)
        p = m.predict(test_X)
        preds[name] = p
        
    # Ensembles
    preds['Linear_Ensemble'] = 0.5 * preds['Ridge_L2'] + 0.5 * preds['Huber_M_Estimator']
    preds['Hybrid_Tree_Linear'] = 0.5 * preds['Huber_M_Estimator'] + 0.5 * preds['Gradient_Boosting']
    
    # Evaluate OOS Rank IC
    eval_df = pd.DataFrame(preds)
    eval_df['target'] = test_y.values
    eval_df['date'] = test_dates.values
    
    for col in preds.keys():
        daily_ics = []
        for d, grp in eval_df.groupby('date'):
            if len(grp) >= 5:
                ic, _ = stats.spearmanr(grp[col], grp['target'])
                if not np.isnan(ic):
                    daily_ics.append(ic)
                    
        mean_ic = float(np.mean(daily_ics)) if daily_ics else 0.0
        ic_std = float(np.std(daily_ics)) if daily_ics else 1.0
        ic_ir = round(mean_ic / (ic_std + 1e-6), 2)
        t_stat = round(mean_ic / (ic_std / np.sqrt(len(daily_ics) + 1e-6) + 1e-6), 2)
        
        results.append({
            "Architecture": col,
            "OOS_Rank_IC": round(mean_ic, 4),
            "IC_IR": ic_ir,
            "t_statistic": t_stat,
            "Evaluation_Days": len(daily_ics)
        })
        
    return pd.DataFrame(results).sort_values('OOS_Rank_IC', ascending=False)
