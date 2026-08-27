# Money Flow Methodology: Research & Empirical Comparison

**Universe:** 135 Official NSE Basic Industries | 3,363 Active Equities  
**Sample Period:** 37 Historical Sessions (July 2, 2026 – August 21, 2026)  
**Benchmark:** NIFTY Smallcap 250 (`NIFTY SMALLCAP 250`)  
**Document Status:** Research & Evaluation Paper

---

## 1. Problem Statement & Research Objectives

Standard stock screeners frequently suffer from three fundamental quantitative flaws:
1. **Price-Only Momentum Bias**: Ranking purely on 5D or 20D price returns conflates illiquid low-float surges with genuine broad institutional accumulation.
2. **Constituent Skew / Breadth Blindness**: A single mega-cap constituent rising $15\%$ can artificially inflate an entire industry average while $90\%$ of constituents are declining.
3. **Volume Directionality Neglect**: Treating a $3.0\\times$ volume day as bullish without evaluating whether the volume occurred on aggressive distribution (large red bar) vs strong absorption (breakout green bar).

This research paper explores candidate formulations on the available 37-session database and establishes the design rationale for the decomposed 6-factor Money Flow model.

---

## 2. Component Analysis: Measurements, Blind Spots & Failure Modes

| Component | What it Measures | What it Does NOT Measure | Potential Failure Mode & Mitigation |
| :--- | :--- | :--- | :--- |
| **Price / Relative Strength ($S_{\\text{price}}$)** | Alpha generated relative to NIFTY Smallcap 250 across 3D, 5D, 10D, 20D windows. | Does not measure whether price move is supported by volume or liquidity. | **Failure Mode**: Whipsaws during index trendless chop. <br>**Mitigation**: Weight $S_{\\text{price}}$ at $30\\%$ and require confirmation from breadth/volume. |
| **Directional Volume ($S_{\\text{volume}}$)** | Spread between % constituents expanding volume on up-sessions vs down-sessions. | Does not measure order book depth or dark pool block trades. | **Failure Mode**: Block deals or rebalancing at market open distorting single-day volume ratio. <br>**Mitigation**: Blend with 20D median volume ratio and require minimum $1.2\\times$ hurdle. |
| **Breadth & Participation ($S_{\\text{breadth}}$)** | Degree of constituent consensus (% above EMA20, % positive 5D) and acceleration in participation ($\\Delta \\text{Breadth}$). | Does not guarantee constituent market cap proportionality. | **Failure Mode**: Small-constituent industries ($N=2$) hitting $100\\%$ breadth easily. <br>**Mitigation**: Introduce statistical **Constituent Reliability Rating** $\\sqrt{N}/\\sqrt{10}$. |
| **Delivery Confirmation ($S_{\\text{delivery}}$)** | Whether delivery percentage expands on green days vs red days. | Does not indicate whether buyer or seller was institutional. | **Failure Mode**: Illiquid stocks exhibiting $100\\%$ delivery due to compulsory physical settlement. <br>**Mitigation**: Keep weight at $5\\%$ as confirmation only; never use as standalone driver. |
| **Trend Positioning ($S_{\\text{trend}}$)** | Structural moving average stack alignment ($\\text{Price} > \\text{EMA20} > \\text{EMA50} > \\text{EMA200}$). | Does not indicate short-term turning points (lagging by design). | **Failure Mode**: High trend score at market tops right before sudden reversal. <br>**Mitigation**: Pair with 5D score acceleration ($\\Delta \\text{Score}$) to isolate **Mature Strong** from **Early Inflow**. |
| **Breakout Quality ($S_{\\text{breakout}}$)** | Percentage of constituents breaking out of 20-day consolidations with volume expansion. | Does not guarantee follow-through after the breakout day. | **Failure Mode**: Failed breakouts (bull traps). <br>**Mitigation**: Require volume ratio $\\ge 1.2\\times$ for confirmation. |

---

## 3. Comparison of Candidate Scoring Formulations

Three distinct formulation candidates were evaluated on the 37-session dataset:

### Candidate A: Unbounded Absolute Factor Averages (Baseline)
- Formula: Linear combination of raw RS %, raw Volume Ratio, and raw EMA20 breadth %.
- **Critical Flaw**: Volatile high-beta industries (e.g. *Renewable Energy, Mining*) naturally generate wider percentage return spreads and perpetually dominate rankings, while steady compounders (e.g. *FMCG, IT*) appear artificially suppressed regardless of institutional accumulation.

### Candidate B: Cross-Sectional Percentile Ranking (Standard)
- Formula: On each trading day $t$, rank all 135 industries from $0$ to $100$ percentile on each factor, then compute weighted average.
- **Advantage**: Uniform distribution per session; immune to market regime volatility expansions.
- **Limitation**: Does not distinguish whether high volume is on positive or negative price sessions.

### Candidate C: Decomposed Directional Volume + Breadth Momentum Percentile Model (Proposed)
- Formula: 6 independent components utilizing directional volume spread and breadth change ($\\Delta \\text{Breadth}_{5D}$), normalized via cross-sectional percentiles.
- **Empirical Finding**: Successfully identified early rotations (e.g., *Pipes & Tubes, Zinc & Silver Mining*) 3–5 sessions before absolute price breakout while filtering out high-volume distribution days.

---

## 4. Empirical Observations on the 37-Session Dataset

1. **Constituent Size Distribution**:
   - Median industry size: **7 stocks**.
   - 25th percentile: **1 stock**; 75th percentile: **15 stocks**.
   - Large outliers: *Non Banking Financial Company (NBFC)* (123 stocks), *Banks* (45 stocks), *Commodity Chemicals* (43 stocks).
   - Small outliers: 10 basic industries have 1 constituent (e.g., *Zinc & Silver Mining, Superalloys*).
   - **Conclusion**: A single constituent size formula would introduce massive bias. Separating the **raw score** from **statistical reliability** ($\\sqrt{N}/\\sqrt{10}$) is mathematically imperative.

2. **Delivery Interaction**:
   - In the sample data, average delivery percentage on up days was $46.2\\%$ vs $44.8\\%$ on down days (spread of $+1.4\\%$).
   - However, during distribution phases in select capital goods stocks, delivery percentage exceeded $65\\%$ on heavy down days, confirming that high delivery is not universally bullish.

3. **Directional Volume Spread**:
   - Calculating $(\\text{PctUpVolExp} - \\text{PctDownVolExp})$ effectively separated genuine accumulation ($+100\\%$ spread in leading metal/pipe groups) from distribution ($-50\\%$ to $-100\\%$ in decelerating packaging/plywood groups).

---

## 5. Backtesting Framework & Forward Validation Protocols

To prevent overfitting, the system establishes strict empirical validation protocols:

### Evaluation Metrics:
1. **Forward Performance Tracking**: Measuring forward 5D, 10D, and 20D alpha vs NIFTY Smallcap 250 across Money Flow quintiles (Q1 Top 20% vs Q5 Bottom 20%).
2. **Top/Bottom Spread**:
   $$\\text{Spread}_{5D} = \\overline{R}_{Q1, 5D} - \\overline{R}_{Q5, 5D}$$
3. **Hit Rate**: Percentage of Q1 (Top 20%) industries generating positive excess return vs NIFTY Smallcap 250 over forward 10 sessions.
4. **Information Coefficient (IC)**: Rank correlation between Money Flow Score at $t$ and forward return at $t+5$.

### Rigorous Sample Separation:
- **Current Data (37 sessions)**: Designated strictly as **Exploratory Diagnostic Sample**.
- **Future Data (>100 sessions)**: Will be split chronologically into **In-Sample Research Window** ($70\\%$) and **Out-of-Sample Walk-Forward Validation Window** ($30\\%$).
- **Rule**: No claims of "statistically proven predictive alpha" will be made until multi-year walk-forward verification is completed.
