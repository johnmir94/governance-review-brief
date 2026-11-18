# Governance Review Brief

Convert a CSV of AI systems into a prioritized Markdown review queue. The brief identifies overdue and upcoming reviews, missing owners, missing evidence references, and unscheduled reviews.

## Run locally

Use Python 3.10 or later. Clone this repository or download and extract the ZIP, then run this command from the project folder. No packages, web server, or API key are required.

```sh
python report.py examples/inventory.csv --as-of 2027-03-01
```

The example finds **three systems needing attention** out of four, including **one overdue review**. That overdue system is high risk. The critical system is due today and appears first.

## How it works

Each inventory row has a unique `system_id`, a `system_name`, and a `risk_tier` of `critical`, `high`, `medium`, or `low`. The other columns, `owner`, `review_due`, and `evidence_ref`, can be blank and generate follow-up flags when missing. Dates use `YYYY-MM-DD`.

A review before the report date is overdue. Reviews on that date or within the inclusive `--window` are due. The default window is 30 calendar days. Flagged systems sort by risk tier, then by the earliest scheduled review within a tier. Unscheduled reviews sort after scheduled ones within the same tier. The app uses the risk tiers supplied in the input.

## Output and errors

Reports go to standard output by default. Add `--output brief.md` to save a new file. The command refuses to overwrite an existing report. Invalid CSVs and dates produce a diagnostic on standard error and exit with code 2. The explicit report date makes repeated runs reproducible.

## Project files

- [`report.py`](report.py) contains the CLI, input validation, and report rendering.
- [`examples/`](examples/) contains fictional CSV fixtures.

Use `python report.py --help` for the CLI options. Run the example above to check the report counts against the expected outcome.

## Project context

The workflow translates AI inventory, ownership, review, and evidence concepts into a brief a governance buyer could use. It reflects the technical-to-commercial translation involved in product marketing for the Holistic AI platform. This is an independent portfolio project using fictional data without employer materials or customer records.
