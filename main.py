import json
import re
from pathlib import Path

import anthropic
import pandas as pd


SHUTDOWN_HOURS = 48


def load_work_orders(filepath: str) -> pd.DataFrame:
    return pd.read_csv(filepath)


def build_prompt(work_orders: pd.DataFrame) -> str:
    wo_json = work_orders.to_json(orient="records", indent=2)
    return f"""You are a shutdown planning expert for mining operations.

You have been given {len(work_orders)} work orders from SAP for a {SHUTDOWN_HOURS}-hour planned shutdown.

Work Orders:
{wo_json}

Your task:
1. Group work orders that share the same physical area and access requirements (scaffolding, isolations) to minimise setup and teardown time.
2. Within each group, sequence by priority (1 = highest, 4 = lowest).
3. Order groups so the most critical work happens first.
4. Rewrite each terse SAP description into a clear, specific, actionable instruction for a field worker.
5. Assign a planned start time (hours from shutdown start, T+0) based on logical sequencing.
6. Flag any task where the planned end time exceeds {SHUTDOWN_HOURS} hours as at_risk.

Return ONLY valid JSON with two keys:
- "optimised_plan": array of objects, each with:
    sequence, work_order_id, original_description, improved_description,
    area, priority, duration_hours, crew_type, access_required,
    planned_start_hour, planned_end_hour, grouping_rationale, at_risk
- "summary": object with:
    total_planned_hours, shutdown_window_hours, overrun_risk (bool),
    overrun_risk_notes, tasks_at_risk (list of work_order_id strings)"""


def optimise_shutdown(work_orders: pd.DataFrame) -> dict:
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8096,
        messages=[{"role": "user", "content": build_prompt(work_orders)}],
    )
    text = message.content[0].text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return json.loads(text)


def export_to_excel(result: dict, output_path: str):
    columns = [
        "sequence", "work_order_id", "area", "priority", "crew_type",
        "access_required", "improved_description", "original_description",
        "duration_hours", "planned_start_hour", "planned_end_hour",
        "grouping_rationale", "at_risk",
    ]
    df_plan = pd.DataFrame(result["optimised_plan"])[columns]
    df_summary = pd.DataFrame([result["summary"]])

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df_plan.to_excel(writer, sheet_name="Optimised Plan", index=False)
        df_summary.to_excel(writer, sheet_name="Summary", index=False)


def main():
    work_orders = load_work_orders("data/work_orders.csv")
    print(f"Processing {len(work_orders)} work orders for {SHUTDOWN_HOURS}-hour shutdown...")

    result = optimise_shutdown(work_orders)

    Path("output").mkdir(exist_ok=True)
    output_path = "output/shutdown_plan.xlsx"
    export_to_excel(result, output_path)
    print(f"Plan written to {output_path}")

    summary = result["summary"]
    if summary["overrun_risk"]:
        print(f"WARNING: Overrun risk — {summary['overrun_risk_notes']}")
    else:
        print("No overrun risk detected.")


if __name__ == "__main__":
    main()
