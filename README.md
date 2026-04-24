# Shutdown Optimiser

An AI agent that takes SAP work orders for a planned mining shutdown and produces an optimised, sequenced work package ready for scheduling in Primavera P6.

## What it does

- Ingests work orders from SAP (priority, area, duration, crew type, access requirements)
- Groups tasks that share scaffolding or isolation requirements to minimise setup and teardown time
- Sequences by priority within each group so critical work is completed first
- Rewrites terse SAP descriptions into clear, actionable field instructions
- Flags overrun risk against the shutdown window
- Outputs an optimised plan to Excel

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here
```

## Usage

```bash
python main.py
```

Output is written to `output/shutdown_plan.xlsx` with two sheets: **Optimised Plan** and **Summary**.

## Input format

Place a CSV at `data/work_orders.csv` with columns:

| Column | Description |
|--------|-------------|
| work_order_id | SAP work order number |
| description | SAP work order description |
| priority | 1 (highest) to 4 (lowest) |
| area | Physical location on site |
| duration_hours | Estimated hours to complete |
| crew_type | Mechanical, Electrical, Structural, Instrumentation |
| access_required | None, Scaffolding, Isolation, Confined Space |
