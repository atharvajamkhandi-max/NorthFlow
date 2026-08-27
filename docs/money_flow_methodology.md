# Money Flow Methodology: Technical Specification

**Version:** 2.0  
**Target Universe:** 135 Official NSE Basic Industries (3,363 Active Equities)  
**Benchmark:** NIFTY Smallcap 250 (`NIFTY SMALLCAP 250`)  
**Document Status:** Architecture Design & Formal Specification (Pre-Implementation)

---

## 1. System Objective & Core Philosophy

The primary objective of the Money Flow Intelligence System is to:
> **Identify granular industries where market participation, relative price strength, volume/turnover behaviour, and delivery participation collectively indicate strengthening or weakening demand.**

### Key Design Principles:
1. **Inferred vs Observed Capital Flow**: The system does **not** claim direct observation of institutional bank balances or trade books. The term **Money Flow Score** represents a disciplined composite quantitative inference derived from observable price, volume, breadth, trend, and delivery metrics.
2. **Decomposable Component Layering**: No opaque single-number "black boxes". The Money Flow Score is explicitly decomposed into 6 independent, transparent component scores (each normalized $0–100$).
3. **Cross-Sectional Normalization**: Metrics are percentile-ranked across the 135-industry cross-section per session to eliminate market-wide drift and scale differences.
4. **Early Inflow Detection**: Differentiating mature leaders from early emerging groups with accelerating participation.
5. **Signal Confirmation & Conflict Transparency**: The system explicitly detects and flags divergence (e.g., Price rising while Breadth contracts or Volume expands on down days).

---

## 2. Architecture Overview

```text
                                  INDUSTRY CONSTITUENTS (N Stocks)
                                                 │
            ┌─────────────────┬──────────────────┼─────────────────┬──────────────────┐
            ↓                 ↓                  ↓                 ↓                  ↓
       [ PRICE / RS ]    [ VOL / TURNOVER ]  [ BREADTH ]      [ DELIVERY ]       [ TREND ]
            │                 │                  │                 │                  │
            ├─────────────────┴──────────────────┼─────────────────┴──────────────────┘
            │                                    ↓
            │                          [ BREAKOUT QUALITY ]
            │                                    │
            └────────────────────────────────────┼────────────────────────────────────┐
                                                 ↓
                                    6 INDEPENDENT COMPONENT SCORES (0–100)
                                    ├── S_price       (Price / Relative Strength)
                                    ├── S_volume      (Directional Volume & Turnover)
                                    ├── S_breadth     (Breadth & Breadth Momentum)
                                    ├── S_delivery    (Delivery Confirmation)
                                    ├── S_trend       (Trend Positioning Stack)
                                    └── S_breakout    (Breakout & High Proximity)
                                                 │
                                                 ↓
                                    CROSS-SECTIONAL PERCENTILE RANKING
                                                 │
                                                 ↓
                                     COMPOSITE MONEY FLOW SCORE (0–100)
                                                 │
                        ┌────────────────────────┴────────────────────────┐
                        ↓                                                 ↓
              FLOW CONFIRMATION STATE                             FLOW REGIME STATE
              ├── HIGH CONFIRMATION                               ├── EARLY INFLOW (EMERGING)
              ├── MODERATE CONFIRMATION                           ├── ACCELERATING
              ├── LOW CONFIRMATION                                ├── STRONG LEADERS
              └── CONFLICTING (DIVERGENCE)                        ├── MATURE STRONG
                                                                  ├── COOLING
                                                                  ├── DISTRIBUTION
                                                                  └── WEAK LAGGARDS
                                                 │
                                                 ↓
                                    INDEPENDENT STOCK LEADERSHIP
                                    (Top Stock Picks per Industry)
```

---

## 3. The 6 Independent Analytical Component Scores

Each component is computed cross-sectionally for every industry $i \in \{1, \dots, 135\}$ on trading date $t$, producing a normalized score $S_k \in [0, 100]$.

### 3.1. Component 1: Price & Relative Strength ($S_{\\text{price}}$)
Measures pure price performance relative to the confirmed benchmark (**NIFTY Smallcap 250**).

* **Inputs**:
  - Industry Average Relative Strength vs NIFTY Smallcap 250:
    $$\\text{RS}_{3D} = \\overline{R}_{\\text{ind}, 3D} - R_{\\text{bench}, 3D}$$
    $$\\text{RS}_{5D} = \\overline{R}_{\\text{ind}, 5D} - R_{\\text{bench}, 5D}$$
    $$\\text{RS}_{10D} = \\overline{R}_{\\text{ind}, 10D} - R_{\\text{bench}, 10D}$$
    $$\\text{RS}_{20D} = \\overline{R}_{\\text{ind}, 20D} - R_{\\text{bench}, 20D}$$
* **Raw Composite Formula**:
  $$\\text{Raw}_{\\text{price}} = 0.35 \\cdot \\text{RS}_{5D} + 0.30 \\cdot \\text{RS}_{20D} + 0.20 \\cdot \\text{RS}_{10D} + 0.15 \\cdot \\text{RS}_{3D}$$
* **Normalization**:
  $$S_{\\text{price}} = \\text{PercentileRank}_{i \in [1, 135]}(\\text{Raw}_{\\text{price}}) \times 100$$

---

### 3.2. Component 2: Directional Volume & Turnover ($S_{\\text{volume}}$)
Differentiates healthy buying volume expansion from heavy selling distribution.

* **Definitions**:
  - $\\text{VolRatio}_{j} = \\frac{\\text{Volume}_{j, t}}{\\text{SMA20}(\\text{Volume}_{j})}$
  - An expanding up-stock satisfies: $R_{j, 1D} > 0 \;\\land\; \\text{VolRatio}_j \ge 1.2$
  - An expanding down-stock satisfies: $R_{j, 1D} < 0 \;\\land\; \\text{VolRatio}_j \ge 1.2$
* **Industry Aggregations**:
  - $\\text{PctUpVolExp} = \\frac{1}{N} \\sum_{j=1}^N \\mathbf{1}_{\\{R_{j, 1D} > 0 \,\\land\, \\text{VolRatio}_j \ge 1.2\\}}$
  - $\\text{PctDownVolExp} = \\frac{1}{N} \\sum_{j=1}^N \\mathbf{1}_{\\{R_{j, 1D} < 0 \,\\land\, \\text{VolRatio}_j \ge 1.2\\}}$
  - $\\text{DirectionalVolSpread} = (\\text{PctUpVolExp} - \\text{PctDownVolExp}) \times 100$
  - $\\text{MedianVolRatio} = \\text{Median}_{j \in \\text{ind}}(\\text{VolRatio}_j)$
* **Raw Composite Formula**:
  $$\\text{Raw}_{\\text{volume}} = 0.60 \\cdot \\text{DirectionalVolSpread} + 0.40 \\cdot \\min(3.0, \\text{MedianVolRatio}) \times 33.3$$
* **Normalization**:
  $$S_{\\text{volume}} = \\text{PercentileRank}_{i \in [1, 135]}(\\text{Raw}_{\\text{volume}}) \times 100$$

---

### 3.3. Component 3: Breadth & Breadth Momentum ($S_{\\text{breadth}}$)
Evaluates widespread constituent participation and whether participation is expanding or contracting.

* **Static Participation**:
  - $\\text{EMA20}_{\\text{breadth}} = \\frac{1}{N} \\sum_{j=1}^N \\mathbf{1}_{\\{\\text{Price}_j > \\text{EMA20}_j\\}} \times 100$
  - $\\text{EMA50}_{\\text{breadth}} = \\frac{1}{N} \\sum_{j=1}^N \\mathbf{1}_{\\{\\text{Price}_j > \\text{EMA50}_j\\}} \times 100$
  - $\\text{Pos5D}_{\\text{breadth}} = \\frac{1}{N} \\sum_{j=1}^N \\mathbf{1}_{\\{R_{j, 5D} > 0\\}} \times 100$
* **Breadth Momentum (Improvement)**:
  - $\\Delta \\text{Breadth}_{3D} = \\text{EMA20}_{\\text{breadth}}(t) - \\text{EMA20}_{\\text{breadth}}(t-3)$
  - $\\Delta \\text{Breadth}_{5D} = \\text{EMA20}_{\\text{breadth}}(t) - \\text{EMA20}_{\\text{breadth}}(t-5)$
* **Raw Composite Formula**:
  $$\\text{Raw}_{\\text{breadth}} = 0.35 \\cdot \\text{EMA20}_{\\text{breadth}} + 0.25 \\cdot \\text{Pos5D}_{\\text{breadth}} + 0.15 \\cdot \\text{EMA50}_{\\text{breadth}} + 0.15 \\cdot \\Delta \\text{Breadth}_{5D} + 0.10 \\cdot \\Delta \\text{Breadth}_{3D}$$
* **Normalization**:
  $$S_{\\text{breadth}} = \\text{PercentileRank}_{i \in [1, 135]}(\\text{Raw}_{\\text{breadth}}) \times 100$$

---

### 3.4. Component 4: Delivery Confirmation ($S_{\\text{delivery}}$)
Treats delivery percentage as confirmation rather than a standalone directional signal.

* **Definitions**:
  - $\\text{UpDelivery} = \\text{Mean}(\\text{DeliveryPct}_j \mid R_{j, 1D} > 0)$
  - $\\text{DownDelivery} = \\text{Mean}(\\text{DeliveryPct}_j \mid R_{j, 1D} < 0)$
  - $\\text{DeliverySpread} = \\text{UpDelivery} - \\text{DownDelivery}$ (positive indicates higher delivery on green sessions).
  - $\\text{MeanDelivery} = \\text{Mean}(\\text{DeliveryPct}_j)$
* **Raw Composite Formula**:
  $$\\text{Raw}_{\\text{delivery}} = 0.50 \\cdot \\text{DeliverySpread} + 0.50 \\cdot \\text{MeanDelivery}$$
* **Normalization**:
  $$S_{\\text{delivery}} = \\text{PercentileRank}_{i \in [1, 135]}(\\text{Raw}_{\\text{delivery}}) \times 100$$
* *Missing Data Rule*: If delivery data is unavailable for an industry or session, $S_{\\text{delivery}}$ defaults to the cross-sectional median ($50.0$).

---

### 3.5. Component 5: Trend Positioning ($S_{\\text{trend}}$)
Measures structural moving average alignment across constituents.

* **Definitions**:
  - $\\text{TrendStackPct} = \\frac{1}{N} \\sum_{j=1}^N \\mathbf{1}_{\\{\\text{Price}_j > \\text{EMA20}_j > \\text{EMA50}_j > \\text{EMA200}_j\\}} \times 100$
  - $\\text{AboveEMA200Pct} = \\frac{1}{N} \\sum_{j=1}^N \\mathbf{1}_{\\{\\text{Price}_j > \\text{EMA200}_j\\}} \times 100$
* **Raw Composite Formula**:
  $$\\text{Raw}_{\\text{trend}} = 0.60 \\cdot \\text{TrendStackPct} + 0.40 \\cdot \\text{AboveEMA200Pct}$$
* **Normalization**:
  $$S_{\\text{trend}} = \\text{PercentileRank}_{i \in [1, 135]}(\\text{Raw}_{\\text{trend}}) \times 100$$

---

### 3.6. Component 6: Breakout & High Proximity ($S_{\\text{breakout}}$)
Measures expansion out of 20-day consolidations and proximity to recent highs.

* **Definitions**:
  - $\\text{BreakoutPct} = \\frac{1}{N} \\sum_{j=1}^N \\mathbf{1}_{\\{\\text{Breakout20D}_j = 1\\}} \times 100$
  - $\\text{ConfirmedBreakoutPct} = \\frac{1}{N} \\sum_{j=1}^N \\mathbf{1}_{\\{\\text{Breakout20D}_j = 1 \,\\land\, \\text{VolRatio}_j \ge 1.2\\}} \times 100$
  - $\\text{NearHighPct} = \\frac{1}{N} \\sum_{j=1}^N \\mathbf{1}_{\\{\\text{Price}_j \ge 0.95 \\cdot \\text{High20D}_j\\}} \times 100$
* **Raw Composite Formula**:
  $$\\text{Raw}_{\\text{breakout}} = 0.50 \\cdot \\text{ConfirmedBreakoutPct} + 0.30 \\cdot \\text{NearHighPct} + 0.20 \\cdot \\text{BreakoutPct}$$
* **Normalization**:
  $$S_{\\text{breakout}} = \\text{PercentileRank}_{i \in [1, 135]}(\\text{Raw}_{\\text{breakout}}) \times 100$$

---

## 4. Composite Money Flow Score Formulation

The final composite score is calculated as a weighted combination of the 6 independent components:

$$\\text{Money Flow Score} = w_p S_{\\text{price}} + w_v S_{\\text{volume}} + w_b S_{\\text{breadth}} + w_d S_{\\text{delivery}} + w_t S_{\\text{trend}} + w_{bk} S_{\\text{breakout}}$$

### Recommended Factor Weights:
| Component Layer | Weight ($w_k$) | Primary Analytical Purpose |
| :--- | :---: | :--- |
| **Price / Relative Strength ($S_{\\text{price}}$)** | **$30\%$** | Outperformance relative to NIFTY Smallcap 250 across multiple time horizons. |
| **Breadth & Participation ($S_{\\text{breadth}}$)** | **$25\%$** | Broad-based constituent strength vs isolated single-stock rallies. |
| **Volume & Turnover Flow ($S_{\\text{volume}}$)** | **$20\%$** | Volume expansion on up days vs selling pressure on down days. |
| **Trend Positioning ($S_{\\text{trend}}$)** | **$10\%$** | Structural alignment ($\\text{Price} > \\text{EMA20} > \\text{EMA50} > \\text{EMA200}$). |
| **Breakout Quality ($S_{\\text{breakout}}$)** | **$10\%$** | Volume-confirmed 20-day base breakouts. |
| **Delivery Confirmation ($S_{\\text{delivery}}$)** | **$5\%$** | Delivery accumulation confirmation. |
| **Total** | **$100\%$** | |

---

## 5. Statistical Reliability & Small-Industry Handling

Industries in the NSE universe range from 1 constituent (e.g. *Superalloys, Zinc & Silver Mining*) to $>40$ constituents (e.g. *Banks, Commodity Chemicals*).

### Two-Tier Rule:
1. **Raw Score**: Computed identically across all 135 industries regardless of size.
2. **Constituent Reliability Metric**: A statistical confidence rating ($0.0–1.0$) displayed alongside the score:
   $$\\text{Reliability} = \\min\\left(1.0, \\frac{\\sqrt{N}}{\\sqrt{10}}\\right)$$
   - $N \ge 10$ stocks: Reliability = **$100\%$** (High sample confidence)
   - $N = 5$ stocks: Reliability = **$71\%$** (Moderate sample confidence)
   - $N = 2$ stocks: Reliability = **$45\%$** (Lower sample confidence)
   - $N = 1$ stock: Reliability = **$32\%$** (Single-stock proxy)
3. **Low Sample Flag**: Industries with $N < 3$ stocks are tagged with `[LOW SAMPLE: N=X]` in screeners to prevent users from mistaking a single stock move for an entire industry trend.

---

## 6. Flow Confirmation Model (Signal Quality)

Detects internal consensus vs divergence across factors:

| Confirmation Classification | Quantitative Condition | Interpretation |
| :--- | :--- | :--- |
| **HIGH CONFIRMATION** | $S_{\\text{price}} \ge 60 \;\\land\; S_{\\text{volume}} \ge 60 \;\\land\; S_{\\text{breadth}} \ge 60$ | Unified buying across price, volume, and constituent breadth. |
| **MODERATE CONFIRMATION** | Consensus across 4 of the 6 component layers ($S_k \ge 50$). | Solid demand with minor factor divergence. |
| **CONFLICTING / DIVERGENCE** | $(S_{\\text{price}} \ge 70 \;\\land\; S_{\\text{breadth}} \le 40) \;\\lor\; (\\text{DirectionalVolSpread} < -20)$ | Danger signal: Price rising on narrow breadth or heavy down-volume. |
| **LOW CONFIRMATION** | High score driven solely by 1 isolated factor while others lag. | Weak underlying institutional consensus. |

---

## 7. Discrete Flow States (Industry Rotation Regimes)

Rather than treating a high score as "inflow", industries are categorized into discrete dynamic flow states:

```text
               5D Acceleration (Δ Score)
                          ▲
                          │
       EARLY INFLOW       │       ACCELERATING / STRONG
    (Score: 40-65, Δ > 8) │       (Score: >65, Δ > 0)
                          │
  ────────────────────────┼────────────────────────► Current Money Flow Score
                          │
     LAGGARDS / WEAK      │       COOLING / MATURE
    (Score: <40, Δ ≤ 0)   │       (Score: >65, Δ < -5)
                          │
                          ▼
```

1. **`EARLY INFLOW (EMERGING)`**:
   - $\\text{Score} \in [40, 70] \;\\land\; \\Delta \\text{Score}_{5D} \ge +8.0 \;\\land\; \\Delta \\text{Breadth}_{5D} > +10\\%$
   - *Key Value*: Identifies newly emerging groups before they become overbought leaders.
2. **`ACCELERATING`**:
   - $\\text{Score} \ge 60 \;\\land\; \\Delta \\text{Score}_{5D} \ge +4.0 \;\\land\; S_{\\text{volume}} \ge 55$
3. **`STRONG LEADERS`**:
   - $\\text{Score} \ge 75 \;\\land\; \\Delta \\text{Score}_{5D} \ge 0 \;\\land\; S_{\\text{breadth}} \ge 65$
4. **`MATURE STRONG`**:
   - $\\text{Score} \ge 75 \;\\land\; \\Delta \\text{Score}_{5D} \in [-5.0, 0.0)$ (High score but momentum plateauing).
5. **`COOLING`**:
   - $\\text{Score} \ge 55 \;\\land\; \\Delta \\text{Score}_{5D} \le -5.0 \;\\land\; \\Delta \\text{Breadth}_{5D} < 0$
6. **`DISTRIBUTION / OUTFLOW`**:
   - $S_{\\text{price}} \le 40 \;\\land\; S_{\\text{volume}} \le 40 \;\\land\; \\text{DirectionalVolSpread} \le -15$
7. **`WEAK LAGGARDS`**:
   - $\\text{Score} < 40 \;\\land\; \\Delta \\text{Score}_{5D} \le 0$
8. **`NEUTRAL`**:
   - All other balanced/consolidation industries.

---

## 8. Constituent Stock Leadership Model

Within any industry, stock leadership is computed independently so that stock ranking does not distort industry flow:

$$\\text{Stock Leadership Score} = 0.25 \\cdot \\text{NearHigh} + 0.25 \\cdot \\text{RS}_{20D} + 0.15 \\cdot \\text{TrendStack} + 0.15 \\cdot \\text{RS}_{5D} + 0.10 \\cdot \\text{VolExpansion} + 0.10 \\cdot \\text{Breakout}$$

---

## 9. Look-Ahead Bias & Execution Safeguards

1. **Strict Lagging**: All metrics at date $T$ use only data $t \le T$.
2. **No Leakage**: Moving averages, returns, and percentile ranks are calculated cross-sectionally per session date.
3. **Historical Backfill Resumability**: Every calculation is deterministic and reproducible.
