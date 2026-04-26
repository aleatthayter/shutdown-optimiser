from pathlib import Path
from typing import List

import pandas as pd
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel


SHUTDOWN_HOURS = 48


class WorkOrderTask(BaseModel):
    sequence: int
    work_order_id: str
    original_description: str
    improved_description: str
    area: str
    priority: int
    duration_hours: float
    crew_type: str
    access_required: str
    planned_start_hour: float
    planned_end_hour: float
    grouping_rationale: str
    at_risk: bool


class ShutdownSummary(BaseModel):
    total_planned_hours: float
    shutdown_window_hours: int
    overrun_risk: bool
    overrun_risk_notes: str
    tasks_at_risk: List[str]


class OptimisedPlan(BaseModel):
    optimised_plan: List[WorkOrderTask]
    summary: ShutdownSummary


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
6. Flag any task where the planned end time exceeds {SHUTDOWN_HOURS} hours as at_risk."""


def optimise_shutdown(work_orders: pd.DataFrame) -> OptimisedPlan:
    llm = ChatAnthropic(model="claude-sonnet-4-6", max_tokens=8096)
    structured_llm = llm.with_structured_output(OptimisedPlan)
    return structured_llm.invoke(build_prompt(work_orders))


def export_to_excel(result: OptimisedPlan, output_path: str):
    columns = [
        "sequence", "work_order_id", "area", "priority", "crew_type",
        "access_required", "improved_description", "original_description",
        "duration_hours", "planned_start_hour", "planned_end_hour",
        "grouping_rationale", "at_risk",
    ]
    df_plan = pd.DataFrame([task.model_dump() for task in result.optimised_plan])[columns]
    df_summary = pd.DataFrame([result.summary.model_dump()])

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

    if result.summary.overrun_risk:
        print(f"WARNING: Overrun risk — {result.summary.overrun_risk_notes}")
    else:
        print("No overrun risk detected.")


if __name__ == "__main__":
    main()
