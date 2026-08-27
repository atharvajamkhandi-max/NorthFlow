# Custom Trading Industry & Segment Classification Layer

This file (`data/custom_industry_mapping.csv`) is the **transparent and editable source of truth** for Layer 2 Custom Trading Classifications.

## Architecture

1. **Layer 1: Official NSE Classification (Untouched)**:
   - Stored in the `stocks` table (`industry`, `basic_industry`).
   - Sourced directly from official NSE index and industry masters.

2. **Layer 2: Custom Trading Intelligence Layer**:
   - Stored in the `custom_industry_classification` table.
   - Provides granular segment breakdowns (e.g. `Luxury / Premium`, `Midscale`, `Industrial EMS`, `Power Cables`).

## CSV Column Specifications

- `symbol` (Required): Valid NSE trading symbol. Must exist in active stock universe.
- `custom_industry` (Required): Custom trading industry name (e.g. `Hotels`, `EMS`, `Wires & Cables`).
- `custom_segment` (Optional): Specific sub-industry or market segment (e.g. `Luxury / Premium`, `Midscale`).
- `notes` (Optional): Transparent explanation or primary product/revenue rationale.

## Validation Rules

- Duplicate symbols in the CSV are flagged and rejected.
- Symbols not present in the official stock universe are rejected.
- Empty or whitespace-only `custom_industry` values are rejected.
