"""Extract preserved H1/H2/H5 Markdown tables without changing their precision."""

from pathlib import Path
import csv
import hashlib
import json

OUT = Path(__file__).resolve().parent.parent
ROOT = OUT.parents[1]
records = []
for name in ["h1_results", "h2_results", "h5_results"]:
    source = ROOT / "docs" / (name + ".md")
    tables, current = [], []
    for line in source.read_text().splitlines() + [""]:
        if line.startswith("|"):
            current.append([cell.strip() for cell in line.strip("|").split("|")])
        elif current:
            tables.append(current)
            current = []
    for number, table in enumerate(tables, 1):
        header, *rows = table
        rows = [row for row in rows if not all(set(cell) <= set("-: ") for cell in row)]
        if any(len(row) != len(header) for row in rows):
            raise ValueError("Malformed table in " + str(source))
        target = OUT / "tables" / f"{name}-{number}.csv"
        with target.open("w", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(header)
            writer.writerows(rows)
        records.append(
            {
                "table": target.name,
                "rows": len(rows),
                "source": str(source.relative_to(ROOT)),
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            }
        )
(OUT / "audits/supplementary-table-index.json").write_text(
    json.dumps(records, indent=2) + "\n"
)
