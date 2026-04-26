# Shutdown Optimiser

An AI agent that takes SAP work orders for a planned mining shutdown and produces an optimised, sequenced work package ready for Primavera P6 scheduling.

## The Problem

A typical fixed-duration shutdown carries 60 or more SAP work orders, each with different priorities, crew types, and access requirements. Figuring out what gets done, in what order, and whether it all fits inside the available window is a complex planning problem — currently done manually by engineers working through spreadsheets for weeks before each event.

## How It Works

1. **Groups** work orders by shared access requirements (scaffolding, isolation, confined space) so setup and teardown costs are shared across tasks rather than repeated per order
2. **Sequences** by priority within each group so critical work is completed before the window closes
3. **Rewrites** terse SAP descriptions into clear, actionable field instructions using Claude
4. **Flags** overrun risk with planned start and end times against the shutdown window
5. **Outputs** a structured Excel plan compatible with Primavera P6

## Tech Stack

Python · Claude (Anthropic) · LangChain · Pydantic · openpyxl

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

## Input Format

Place a CSV at `data/work_orders.csv` with columns:

| Column | Description |
|--------|-------------|
| `work_order_id` | SAP work order number |
| `description` | SAP work order description |
| `priority` | 1 (highest) to 4 (lowest) |
| `area` | Physical location on site |
| `duration_hours` | Estimated hours to complete |
| `crew_type` | Mechanical, Electrical, Structural, Instrumentation |
| `access_required` | None, Scaffolding, Isolation, Confined Space |

---

*Proof of concept. Production use would require integration with live SAP exports and P6 scheduling APIs.*
