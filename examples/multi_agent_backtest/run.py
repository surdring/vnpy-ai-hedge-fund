"""
Fallback multi-agent backtest smoke example.
"""

from vnpy_ai.data_adapter import DataAdapter
from vnpy_ai.workflow.runner import WorkflowRunner


def main() -> None:
    runner = WorkflowRunner(DataAdapter())
    result = runner.run(["AAPL.NASDAQ"], start_date="2024-03-01", end_date="2024-03-08")
    print(result.model_dump())


if __name__ == "__main__":
    main()

