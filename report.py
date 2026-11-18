"""Generate a Markdown briefing report from fictional or user-supplied CSV data."""

import argparse
import csv
from datetime import date
from pathlib import Path


def read_csv(path, required):
    """Yield validated rows with their CSV line numbers."""
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        headers = reader.fieldnames or []
        missing = set(required).difference(headers)
        if missing:
            raise ValueError(f"{path}: missing columns: {', '.join(sorted(missing))}")
        if len(headers) != len(set(headers)):
            raise ValueError(f"{path}: duplicate column names")
        for record in reader:
            line = reader.line_num
            if None in record or any(value is None for value in record.values()):
                raise ValueError(f"{path}:{line}: wrong number of fields")
            yield line, {key: value.strip() for key, value in record.items()}


def parse_date(value, label):
    try:
        if len(value) != 10:
            raise ValueError
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{label}: expected YYYY-MM-DD") from None


def unique_id(value, seen, label):
    if not value or value in seen:
        raise ValueError(f"{label}: ID must be nonempty and unique")
    seen.add(value)


def table_row(*cells):
    escaped = []
    for cell in cells:
        value = str(cell).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        escaped.append(value.replace("\\", "&#92;").replace("|", "&#124;").replace("\r", " ").replace("\n", " "))
    return "| " + " | ".join(escaped) + " |"


LEVELS = {"critical": 0, "high": 1, "medium": 2, "low": 3}
FIELDS = ("system_id", "system_name", "owner", "risk_tier", "review_due", "evidence_ref")


def add_arguments(parser):
    parser.add_argument("inventory", type=Path, help="AI system inventory CSV")
    parser.add_argument("--window", type=int, default=30, help="Upcoming review window in days")


def build_report(args, as_of):
    if args.window < 0:
        raise ValueError("--window must be nonnegative")

    seen = set()
    flagged = []
    total = 0
    overdue = 0
    for line, row in read_csv(args.inventory, FIELDS):
        label = f"{args.inventory}:{line}"
        unique_id(row["system_id"], seen, label)
        if not row["system_name"] or row["risk_tier"] not in LEVELS:
            raise ValueError(f"{label}: system_name and a valid risk_tier are required")

        total += 1
        issues = []
        due = parse_date(row["review_due"], label + " review_due") if row["review_due"] else None
        days = (due - as_of).days if due else None
        if days is None:
            issues.append("No review date")
        elif days < 0:
            overdue += 1
            issues.append(f"Overdue by {-days} days")
        elif days == 0:
            issues.append("Due today")
        elif days <= args.window:
            issues.append(f"Due in {days} days")
        if not row["owner"]:
            issues.append("No owner")
        if not row["evidence_ref"]:
            issues.append("No evidence reference")
        if issues:
            flagged.append((row, due, issues))

    flagged.sort(key=lambda item: (LEVELS[item[0]["risk_tier"]], item[1] or date.max, item[0]["system_id"]))
    output = [
        "# AI governance review brief", "",
        f"As of {as_of.isoformat()} · Upcoming window: {args.window} days", "",
        f"- Systems scanned: {total}",
        f"- Systems needing attention: {len(flagged)}",
        f"- Overdue reviews: {overdue}", "",
        "| ID | System | Risk tier | Owner | Review due | Evidence reference | Follow-up |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row, due, issues in flagged:
        output.append(table_row(row["system_id"], row["system_name"], row["risk_tier"],
                                row["owner"] or "Unassigned", due or "Unscheduled",
                                row["evidence_ref"] or "Missing", ", ".join(issues)))
    if not flagged:
        output.extend(["", "No systems met the follow-up rules."])
    return "\n".join(output) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_arguments(parser)
    parser.add_argument("--as-of", required=True, metavar="YYYY-MM-DD", help="Report date")
    parser.add_argument("--output", type=Path, help="Write Markdown to a new file instead of stdout")
    args = parser.parse_args()
    try:
        report = build_report(args, parse_date(args.as_of, "--as-of"))
        if args.output:
            with args.output.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(report)
        else:
            print(report, end="")
    except (ValueError, OSError, csv.Error) as error:
        parser.exit(2, f"error: {error}\n")


if __name__ == "__main__":
    main()
