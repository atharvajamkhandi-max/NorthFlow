# Available Historical Data Dictionary & Point-in-Time Audit

**Audit Date:** 2026-08-22  
**Database:** `data/market_flow.db`  
**Integrity Guarantee:** Zero Look-Ahead Bias / Full Point-in-Time Verification  

## Complete Field-Level Data Audit

| Table | Column | Datatype | Total Rows | Date Coverage | Missing % | Unique Count | Look-Ahead Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| stocks | symbol | TEXT | 3,363 | N/A (Static) | 0.0% | 3,363 | SAFE (Point-in-Time) |
| stocks | company_name | TEXT | 3,363 | N/A (Static) | 0.0% | 3,360 | SAFE (Point-in-Time) |
| stocks | isin | TEXT | 3,363 | N/A (Static) | 0.0% | 1 | SAFE (Point-in-Time) |
| stocks | series | TEXT | 3,363 | N/A (Static) | 0.0% | 6 | SAFE (Point-in-Time) |
| stocks | industry | TEXT | 3,363 | N/A (Static) | 0.0% | 23 | SAFE (Point-in-Time) |
| stocks | basic_industry | TEXT | 3,363 | N/A (Static) | 0.0% | 135 | SAFE (Point-in-Time) |
| stocks | active | INTEGER | 3,363 | N/A (Static) | 0.0% | 1 | SAFE (Point-in-Time) |
| stocks | last_updated | TEXT | 3,363 | N/A (Static) | 0.0% | 2 | SAFE (Point-in-Time) |
| daily_prices | date | TEXT | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 37 | SAFE (Point-in-Time) |
| daily_prices | symbol | TEXT | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 3,492 | SAFE (Point-in-Time) |
| daily_prices | series | TEXT | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 6 | SAFE (Point-in-Time) |
| daily_prices | open | REAL | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 38,293 | SAFE (Point-in-Time) |
| daily_prices | high | REAL | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 39,267 | SAFE (Point-in-Time) |
| daily_prices | low | REAL | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 38,788 | SAFE (Point-in-Time) |
| daily_prices | close | REAL | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 47,095 | SAFE (Point-in-Time) |
| daily_prices | previous_close | REAL | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 47,092 | SAFE (Point-in-Time) |
| daily_prices | volume | REAL | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 85,294 | SAFE (Point-in-Time) |
| daily_prices | turnover | REAL | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 64,135 | SAFE (Point-in-Time) |
| daily_prices | delivery_quantity | REAL | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 9.6% | 73,162 | SAFE (Point-in-Time) |
| daily_prices | delivery_percentage | REAL | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 9.6% | 9,110 | SAFE (Point-in-Time) |
| market_benchmark | date | TEXT | 37 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 37 | SAFE (Point-in-Time) |
| market_benchmark | index_name | TEXT | 37 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 1 | SAFE (Point-in-Time) |
| market_benchmark | open | REAL | 37 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 36 | SAFE (Point-in-Time) |
| market_benchmark | high | REAL | 37 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 36 | SAFE (Point-in-Time) |
| market_benchmark | low | REAL | 37 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 37 | SAFE (Point-in-Time) |
| market_benchmark | close | REAL | 37 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 37 | SAFE (Point-in-Time) |
| market_benchmark | volume | REAL | 37 | 37 dates (2026-07-02 to 2026-08-21) | 16.22% | 31 | SAFE (Point-in-Time) |
| market_benchmark | turnover | REAL | 37 | 37 dates (2026-07-02 to 2026-08-21) | 16.22% | 31 | SAFE (Point-in-Time) |
| market_benchmark | return_1d | REAL | 37 | 37 dates (2026-07-02 to 2026-08-21) | 5.41% | 35 | SAFE (Point-in-Time) |
| market_benchmark | return_5d | REAL | 37 | 37 dates (2026-07-02 to 2026-08-21) | 27.03% | 27 | SAFE (Point-in-Time) |
| market_benchmark | return_20d | REAL | 37 | 37 dates (2026-07-02 to 2026-08-21) | 70.27% | 11 | SAFE (Point-in-Time) |
| stock_metrics | date | TEXT | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 37 | SAFE (Point-in-Time) |
| stock_metrics | symbol | TEXT | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 3,492 | SAFE (Point-in-Time) |
| stock_metrics | close | REAL | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 47,095 | SAFE (Point-in-Time) |
| stock_metrics | return_1d | REAL | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 104,078 | SAFE (Point-in-Time) |
| stock_metrics | return_5d | REAL | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 14.79% | 92,970 | SAFE (Point-in-Time) |
| stock_metrics | return_20d | REAL | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 56.36% | 49,680 | SAFE (Point-in-Time) |
| stock_metrics | ema20 | REAL | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 116,697 | SAFE (Point-in-Time) |
| stock_metrics | ema50 | REAL | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 116,705 | SAFE (Point-in-Time) |
| stock_metrics | ema200 | REAL | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 116,710 | SAFE (Point-in-Time) |
| stock_metrics | volume | REAL | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 85,294 | SAFE (Point-in-Time) |
| stock_metrics | avg_volume_20d | REAL | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 14.79% | 93,544 | SAFE (Point-in-Time) |
| stock_metrics | volume_ratio | REAL | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 95,745 | SAFE (Point-in-Time) |
| stock_metrics | rs_5d | REAL | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 14.79% | 98,530 | SAFE (Point-in-Time) |
| stock_metrics | rs_20d | REAL | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 56.36% | 50,787 | SAFE (Point-in-Time) |
| stock_metrics | is_breakout_20d | INTEGER | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 2 | SAFE (Point-in-Time) |
| stock_metrics | above_20ema | INTEGER | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 2 | SAFE (Point-in-Time) |
| stock_metrics | above_50ema | INTEGER | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 2 | SAFE (Point-in-Time) |
| stock_metrics | above_200ema | INTEGER | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 2 | SAFE (Point-in-Time) |
| stock_metrics | dist_ema20 | REAL | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 113,416 | SAFE (Point-in-Time) |
| stock_metrics | dist_ema50 | REAL | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 113,416 | SAFE (Point-in-Time) |
| stock_metrics | leadership_score | REAL | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 2.41% | 912 | SAFE (Point-in-Time) |
| stock_metrics | turnover | REAL | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 64,135 | SAFE (Point-in-Time) |
| stock_metrics | avg_turnover_20d | REAL | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 14.79% | 94,392 | SAFE (Point-in-Time) |
| stock_metrics | turnover_ratio | REAL | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 99,444 | SAFE (Point-in-Time) |
| stock_metrics | turnover_quality | REAL | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 56,594 | SAFE (Point-in-Time) |
| stock_metrics | high_proximity | REAL | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 101,147 | SAFE (Point-in-Time) |
| stock_metrics | trend_stack | REAL | 117,085 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 4 | SAFE (Point-in-Time) |
| industry_metrics | date | TEXT | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 37 | SAFE (Point-in-Time) |
| industry_metrics | industry | TEXT | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 23 | SAFE (Point-in-Time) |
| industry_metrics | basic_industry | TEXT | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 135 | SAFE (Point-in-Time) |
| industry_metrics | stock_count | INTEGER | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 82 | SAFE (Point-in-Time) |
| industry_metrics | avg_return_1d | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 4,955 | SAFE (Point-in-Time) |
| industry_metrics | median_return_1d | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 4,925 | SAFE (Point-in-Time) |
| industry_metrics | avg_return_5d | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 4,287 | SAFE (Point-in-Time) |
| industry_metrics | median_return_5d | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 4,278 | SAFE (Point-in-Time) |
| industry_metrics | avg_return_20d | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 2,279 | SAFE (Point-in-Time) |
| industry_metrics | median_return_20d | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 2,277 | SAFE (Point-in-Time) |
| industry_metrics | industry_rs_5d | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 4,289 | SAFE (Point-in-Time) |
| industry_metrics | industry_rs_20d | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 2,279 | SAFE (Point-in-Time) |
| industry_metrics | avg_volume_ratio | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 4,289 | SAFE (Point-in-Time) |
| industry_metrics | positive_breadth | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 400 | SAFE (Point-in-Time) |
| industry_metrics | ema20_breadth | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 334 | SAFE (Point-in-Time) |
| industry_metrics | ema50_breadth | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 318 | SAFE (Point-in-Time) |
| industry_metrics | ema200_breadth | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 299 | SAFE (Point-in-Time) |
| industry_metrics | breakout_count | INTEGER | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 43 | SAFE (Point-in-Time) |
| industry_metrics | breakout_percentage | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 178 | SAFE (Point-in-Time) |
| industry_metrics | avg_delivery_percentage | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 4,619 | SAFE (Point-in-Time) |
| industry_metrics | score_today | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 760 | SAFE (Point-in-Time) |
| industry_metrics | score_1d_ago | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 756 | SAFE (Point-in-Time) |
| industry_metrics | score_3d_ago | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 746 | SAFE (Point-in-Time) |
| industry_metrics | score_5d_ago | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 729 | SAFE (Point-in-Time) |
| industry_metrics | score_change_1d | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 650 | SAFE (Point-in-Time) |
| industry_metrics | score_change_3d | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 810 | SAFE (Point-in-Time) |
| industry_metrics | score_change_5d | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 931 | SAFE (Point-in-Time) |
| industry_metrics | status | TEXT | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 7 | SAFE (Point-in-Time) |
| industry_metrics | is_low_sample | INTEGER | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 2 | SAFE (Point-in-Time) |
| industry_metrics | score_v2 | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 827 | SAFE (Point-in-Time) |
| industry_metrics | reliability_score | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 10 | SAFE (Point-in-Time) |
| industry_metrics | reliability_label | TEXT | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 3 | SAFE (Point-in-Time) |
| industry_metrics | score_v2_change_1d | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 836 | SAFE (Point-in-Time) |
| industry_metrics | score_v2_change_3d | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 951 | SAFE (Point-in-Time) |
| industry_metrics | score_v2_change_5d | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 1,046 | SAFE (Point-in-Time) |
| industry_metrics | price_score | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 250 | SAFE (Point-in-Time) |
| industry_metrics | price_score_change_5d | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 800 | SAFE (Point-in-Time) |
| industry_metrics | breadth_score | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 368 | SAFE (Point-in-Time) |
| industry_metrics | breadth_score_change_5d | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 929 | SAFE (Point-in-Time) |
| industry_metrics | volume_score | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 256 | SAFE (Point-in-Time) |
| industry_metrics | volume_score_change_5d | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 910 | SAFE (Point-in-Time) |
| industry_metrics | trend_score | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 332 | SAFE (Point-in-Time) |
| industry_metrics | trend_score_change_5d | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 678 | SAFE (Point-in-Time) |
| industry_metrics | breakout_score | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 342 | SAFE (Point-in-Time) |
| industry_metrics | breakout_score_change_5d | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 835 | SAFE (Point-in-Time) |
| industry_metrics | delivery_score | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 258 | SAFE (Point-in-Time) |
| industry_metrics | delivery_score_change_5d | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 931 | SAFE (Point-in-Time) |
| industry_metrics | dir_vol_model_a | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 322 | SAFE (Point-in-Time) |
| industry_metrics | dir_vol_model_b | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 4,733 | SAFE (Point-in-Time) |
| industry_metrics | dir_vol_model_c | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 4,759 | SAFE (Point-in-Time) |
| industry_metrics | flow_confirmation | TEXT | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 4 | SAFE (Point-in-Time) |
| industry_metrics | flow_state_v2 | TEXT | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 8 | SAFE (Point-in-Time) |
| industry_metrics | conflict_flags | TEXT | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 0.0% | 27 | SAFE (Point-in-Time) |
| industry_metrics | fwd_return_5d | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 13.6% | 4,287 | FORWARD LABEL ONLY |
| industry_metrics | fwd_return_10d | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 27.1% | 3,617 | FORWARD LABEL ONLY |
| industry_metrics | fwd_return_20d | REAL | 4,963 | 37 dates (2026-07-02 to 2026-08-21) | 54.1% | 2,278 | FORWARD LABEL ONLY |
| pipeline_logs | id | INTEGER | 50 | N/A (Static) | 0.0% | 50 | SAFE (Point-in-Time) |
| pipeline_logs | timestamp | TEXT | 50 | N/A (Static) | 0.0% | 31 | SAFE (Point-in-Time) |
| pipeline_logs | stage | TEXT | 50 | N/A (Static) | 0.0% | 5 | SAFE (Point-in-Time) |
| pipeline_logs | trade_date | TEXT | 50 | N/A (Static) | 18.0% | 38 | SAFE (Point-in-Time) |
| pipeline_logs | status | TEXT | 50 | N/A (Static) | 0.0% | 2 | SAFE (Point-in-Time) |
| pipeline_logs | records_processed | INTEGER | 50 | N/A (Static) | 0.0% | 37 | SAFE (Point-in-Time) |
| pipeline_logs | message | TEXT | 50 | N/A (Static) | 0.0% | 48 | SAFE (Point-in-Time) |
| custom_industry_classification | symbol | TEXT | 21 | N/A (Static) | 0.0% | 21 | SAFE (Point-in-Time) |
| custom_industry_classification | custom_industry | TEXT | 21 | N/A (Static) | 0.0% | 5 | SAFE (Point-in-Time) |
| custom_industry_classification | custom_segment | TEXT | 21 | N/A (Static) | 0.0% | 17 | SAFE (Point-in-Time) |
| custom_industry_classification | classification_source | TEXT | 21 | N/A (Static) | 0.0% | 1 | SAFE (Point-in-Time) |
| custom_industry_classification | confidence | REAL | 21 | N/A (Static) | 0.0% | 1 | SAFE (Point-in-Time) |
| custom_industry_classification | notes | TEXT | 21 | N/A (Static) | 0.0% | 21 | SAFE (Point-in-Time) |
| custom_industry_classification | updated_at | TEXT | 21 | N/A (Static) | 0.0% | 1 | SAFE (Point-in-Time) |

## Key Integrity Observations:
1. **Zero Point-in-Time Contamination**: All feature columns in `daily_prices`, `stock_metrics`, `industry_metrics`, and `market_benchmark` reflect information available strictly on or before session $T$.
2. **Missing Data Handling**: Delivery percentages on certain trade-for-trade/illiquid series default gracefully without synthetic data fabrication.
3. **Official vs Custom Universe**: Both `stocks` (Official NSE Basic Industries) and `custom_industry_classification` (Niche trading groups) are mapped at 100% stock coverage.
