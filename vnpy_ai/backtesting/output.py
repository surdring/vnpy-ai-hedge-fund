import csv
import json


class Output:
    @staticmethod
    def to_csv(data: list[dict], filepath: str):
        if not data:
            return
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

    @staticmethod
    def to_json(data: dict, filepath: str):
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    @staticmethod
    def to_html_report(metrics: dict, filepath: str):
        html = f"<html><body><h1>Backtest Report</h1><pre>{json.dumps(metrics, indent=2)}</pre></body></html>"
        with open(filepath, 'w') as f:
            f.write(html)
