#!/usr/bin/env python3
"""controlmap: a small cross-framework security control mapping tool.

Commands:
  search <text>            Full-text search across themes, descriptions and control IDs
  show <ID>                Show one mapping row (e.g. CM-004)
  lookup <framework> <id>  Find themes that reference a framework control (e.g. lookup nist_800_53_r5 AC-2)
  coverage <framework>...  Report which themes map to the given frameworks and which don't
  html [-o FILE]           Generate a self-contained, searchable HTML page
  export [-o FILE]         Write the mapping as JSON

Data lives in controls.csv. Multiple IDs in a cell are separated by semicolons.
"""
import argparse
import csv
import html
import json
import sys
from pathlib import Path

DATA_FILE = Path(__file__).with_name("controls.csv")

# NIST CSF 2.0 is the anchor: each row's id IS a CSF subcategory (e.g. PR.AA-03).
# The frameworks below are the ones each row is compared against.
ANCHOR_KEY = "nist_csf_2"
ANCHOR_LABEL = "NIST CSF 2.0"

FRAMEWORKS = {
    "soc2_tsc": "SOC 2 TSC",
    "glba": "GLBA Safeguards (16 CFR 314.4)",
    "ffiec": "FFIEC IT Handbook",
    "iso_27001_2022": "ISO/IEC 27001:2022",
}
LABELS = {ANCHOR_KEY: ANCHOR_LABEL, **FRAMEWORKS}
FUNCTION_ORDER = ["Govern", "Identify", "Protect", "Detect", "Respond", "Recover"]


def load(path=DATA_FILE):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        for key in FRAMEWORKS:
            raw = (row.get(key) or "").strip()
            row[key] = [p.strip() for p in raw.split(";") if p.strip()]
    return rows


def fmt_ids(ids):
    return ", ".join(ids) if ids else "-"


def print_row(row):
    print(f"{row['id']}  {row['theme']}  [{row['domain']} / {row['category']}]")
    print(f"  {row['description']}")
    for key, label in FRAMEWORKS.items():
        print(f"  {label:<32} {fmt_ids(row[key])}")
    if row.get("notes"):
        print(f"  Note: {row['notes']}")
    print()


def cmd_search(rows, args):
    q = " ".join(args.text).lower()
    hits = []
    for r in rows:
        hay = " ".join(
            [r["id"], r["theme"], r["domain"], r["description"], r.get("notes", "")]
            + [i for k in FRAMEWORKS for i in r[k]]
        ).lower()
        if q in hay:
            hits.append(r)
    if not hits:
        print(f"No matches for '{q}'.")
        return 1
    for r in hits:
        print_row(r)
    print(f"{len(hits)} match(es).")
    return 0


def cmd_show(rows, args):
    for r in rows:
        if r["id"].lower() == args.id.lower():
            print_row(r)
            return 0
    print(f"No row with ID {args.id}.")
    return 1


def cmd_lookup(rows, args):
    if args.framework not in LABELS:
        print("Unknown framework. Choose from: " + ", ".join(LABELS))
        return 2
    target = args.control_id.lower()

    def matches(r):
        if args.framework == ANCHOR_KEY:
            # CSF anchor: PR.AA-03 matches exactly, PR.AA matches the whole category
            return r["id"].lower().startswith(target)
        return any(
            i.lower() == target or i.lower().startswith(target + "(") or i.lower().startswith(target + ".")
            for i in r[args.framework]
        )

    hits = [r for r in rows if matches(r)]
    if not hits:
        print(f"{args.control_id} is not referenced in {LABELS[args.framework]} in this dataset.")
        return 1
    print(f"{LABELS[args.framework]} {args.control_id} appears in:\n")
    for r in hits:
        print_row(r)
    return 0


def cmd_coverage(rows, args):
    fws = args.frameworks or list(FRAMEWORKS)
    for fw in fws:
        if fw not in FRAMEWORKS:
            print(f"Unknown framework: {fw}")
            return 2
    for fw in fws:
        covered = [r for r in rows if r[fw]]
        missing = [r for r in rows if not r[fw]]
        pct = 100 * len(covered) / len(rows)
        print(f"{FRAMEWORKS[fw]}: {len(covered)}/{len(rows)} themes mapped ({pct:.0f}%)")
        for r in missing:
            print(f"    no mapping: {r['id']} {r['theme']}")
    return 0


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Control Mapping</title>
<style>
  :root {{ --bg:#fff; --fg:#1b1f24; --muted:#5b6570; --line:#d8dde3; --accent:#1f5fbf; --chip:#eef3fb; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg:#14181d; --fg:#e6e9ed; --muted:#9aa5b1; --line:#2a313a; --accent:#7fb0ff; --chip:#1e2733; }}
  }}
  body {{ margin:0; background:var(--bg); color:var(--fg); font:15px/1.5 system-ui,sans-serif; }}
  header, main {{ max-width:1200px; margin:0 auto; padding:16px; }}
  h1 {{ margin:8px 0 4px; font-size:24px; }}
  p.sub {{ margin:0 0 16px; color:var(--muted); }}
  .controls {{ display:flex; flex-wrap:wrap; gap:8px; margin-bottom:12px; }}
  input, select {{ padding:8px 10px; border:1px solid var(--line); border-radius:6px; background:var(--bg); color:var(--fg); font:inherit; }}
  input[type=search] {{ flex:1 1 260px; }}
  .count {{ color:var(--muted); margin:4px 0 12px; }}
  table {{ width:100%; border-collapse:collapse; }}
  th, td {{ text-align:left; vertical-align:top; padding:10px 8px; border-bottom:1px solid var(--line); }}
  th {{ position:sticky; top:0; background:var(--bg); font-size:13px; color:var(--muted); }}
  td.theme strong {{ display:block; }}
  td.theme span {{ color:var(--muted); font-size:13px; }}
  .chip {{ display:inline-block; background:var(--chip); border-radius:4px; padding:1px 6px; margin:1px 2px 1px 0; font-size:13px; white-space:nowrap; }}
  .note {{ color:var(--muted); font-size:13px; margin-top:4px; }}
  .wrap {{ overflow-x:auto; }}
  footer {{ color:var(--muted); font-size:13px; padding:16px; max-width:1200px; margin:0 auto; }}
</style>
</head>
<body>
<header>
  <h1>NIST CSF 2.0 Control Mapping</h1>
  <p class="sub">Each row is a CSF 2.0 subcategory mapped to SOC 2, GLBA, FFIEC and ISO 27001. Search by CSF ID or any other control ID (for example PR.AA-03, A.8.5, CC6.1, 314.4(c)(5)).</p>
  <div class="controls">
    <input id="q" type="search" placeholder="Search themes, descriptions, or control IDs" aria-label="Search">
    <select id="domain" aria-label="Filter by domain"><option value="">All CSF functions</option>{domain_options}</select>
  </div>
  <div class="count" id="count"></div>
</header>
<main>
  <div class="wrap">
  <table>
    <thead><tr><th>Control theme</th>{fw_headers}</tr></thead>
    <tbody id="rows"></tbody>
  </table>
  </div>
</main>
<footer>Mappings are conceptual and approximate. Verify against official sources before relying on this for an audit or exam.</footer>
<script>
const FRAMEWORKS = {frameworks_json};
const DATA = {data_json};
const rowsEl = document.getElementById('rows');
const qEl = document.getElementById('q');
const domEl = document.getElementById('domain');
const countEl = document.getElementById('count');

function el(tag, cls, text) {{
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}}

function render() {{
  const q = qEl.value.trim().toLowerCase();
  const dom = domEl.value;
  rowsEl.replaceChildren();
  let n = 0;
  for (const r of DATA) {{
    if (dom && r.domain !== dom) continue;
    const hay = [r.id, r.theme, r.domain, r.description, r.notes || '',
      ...Object.keys(FRAMEWORKS).flatMap(k => r[k])].join(' ').toLowerCase();
    if (q && !hay.includes(q)) continue;
    n++;
    const tr = el('tr');
    const t = el('td', 'theme');
    t.append(el('strong', '', r.id + '  ' + r.theme), el('span', '', r.domain + ' / ' + r.category), el('span', '', ' - ' + r.description));
    if (r.notes) t.append(el('div', 'note', r.notes));
    tr.append(t);
    for (const k of Object.keys(FRAMEWORKS)) {{
      const td = el('td');
      if (r[k].length === 0) td.textContent = '-';
      for (const id of r[k]) td.append(el('span', 'chip', id));
      tr.append(td);
    }}
    rowsEl.append(tr);
  }}
  countEl.textContent = n + ' of ' + DATA.length + ' themes shown';
}}
qEl.addEventListener('input', render);
domEl.addEventListener('change', render);
render();
</script>
</body>
</html>
"""


def cmd_html(rows, args):
    present = {str(r["domain"]) for r in rows}
    domains = [d for d in FUNCTION_ORDER if d in present] + sorted(present - set(FUNCTION_ORDER))
    domain_options = "".join(
        f'<option value="{html.escape(d)}">{html.escape(d)}</option>' for d in domains
    )
    fw_headers = "".join(f"<th>{html.escape(v)}</th>" for v in FRAMEWORKS.values())
    # Escape "</" so data can never close the script tag
    data_json = json.dumps(rows).replace("</", "<\\/")
    page = PAGE.format(
        domain_options=domain_options,
        fw_headers=fw_headers,
        frameworks_json=json.dumps(FRAMEWORKS),
        data_json=data_json,
    )
    out = Path(args.output)
    out.write_text(page, encoding="utf-8")
    print(f"Wrote {out}")
    return 0


def cmd_export(rows, args):
    out = Path(args.output)
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    return 0


def build_parser():
    p = argparse.ArgumentParser(description="Cross-framework security control mapping tool")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="full-text search")
    s.add_argument("text", nargs="+")
    s.set_defaults(fn=cmd_search)

    s = sub.add_parser("show", help="show one row by ID")
    s.add_argument("id")
    s.set_defaults(fn=cmd_show)

    s = sub.add_parser("lookup", help="find themes that reference a framework control")
    s.add_argument("framework", help="one of: " + ", ".join(LABELS))
    s.add_argument("control_id")
    s.set_defaults(fn=cmd_lookup)

    s = sub.add_parser("coverage", help="report mapping coverage per framework")
    s.add_argument("frameworks", nargs="*")
    s.set_defaults(fn=cmd_coverage)

    s = sub.add_parser("html", help="generate a searchable HTML page")
    s.add_argument("-o", "--output", default="index.html")
    s.set_defaults(fn=cmd_html)

    s = sub.add_parser("export", help="export mapping as JSON")
    s.add_argument("-o", "--output", default="controls.json")
    s.set_defaults(fn=cmd_export)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    rows = load()
    return args.fn(rows, args)


if __name__ == "__main__":
    sys.exit(main())
