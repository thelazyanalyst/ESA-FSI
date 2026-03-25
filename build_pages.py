#!/usr/bin/env python3
"""Generate styled HTML sub-pages from markdown research files."""

import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))

BANK_META = {
    "anz":      {"name": "ANZ Bank",              "flag": "🇦🇺", "ticker": "ASX: ANZ", "accent": "#0076a8", "accent_bg": "#e8f4fa", "accent_mid": "#cce7f3"},
    "cba":      {"name": "Commonwealth Bank",     "flag": "🇦🇺", "ticker": "ASX: CBA", "accent": "#b87200", "accent_bg": "#fef6e8", "accent_mid": "#fde5b0"},
    "nab":      {"name": "NAB",                   "flag": "🇦🇺", "ticker": "ASX: NAB", "accent": "#c0271d", "accent_bg": "#faecea", "accent_mid": "#f4c8c5"},
    "westpac":  {"name": "Westpac",               "flag": "🇦🇺", "ticker": "ASX: WBC", "accent": "#a81030", "accent_bg": "#f9eaed", "accent_mid": "#f0c0cb"},
    "kiwibank": {"name": "Kiwibank",              "flag": "🇳🇿", "ticker": "NZX: KWB", "accent": "#1a8c50", "accent_bg": "#e8f7ee", "accent_mid": "#b8e8cc"},
}

FILE_LABELS = {
    "business-lines":    ("Business Lines & Processes", "📄"),
    "financial-summary": ("Financial Summary",          "📊"),
    "sources":           ("Sources & References",       "🔗"),
    "press-releases":    ("Press Releases",             "📰"),
    "sabsa-contextual":  ("SABSA Contextual",           "🏛"),
}


def md_to_html(md: str) -> str:
    """Convert markdown to HTML — handles headers, tables, lists, bold, hr, links."""
    lines = md.split("\n")
    html_parts = []
    i = 0
    in_list = False
    in_table = False
    table_buf = []

    def flush_list():
        nonlocal in_list
        if in_list:
            html_parts.append("</ul>")
            in_list = False

    def flush_table():
        nonlocal in_table, table_buf
        if in_table and table_buf:
            html_parts.append('<div class="table-wrap"><table>')
            header_done = False
            for row in table_buf:
                if re.match(r"^\|[-| :]+\|$", row.strip()):
                    html_parts.append("</thead><tbody>")
                    header_done = True
                    continue
                cells = [c.strip() for c in row.strip().strip("|").split("|")]
                tag = "th" if not header_done else "td"
                html_parts.append("<tr>" + "".join(f"<{tag}>{inline(c)}</{tag}>" for c in cells) + "</tr>")
                if not header_done:
                    html_parts.append("<thead>")
                    header_done = True
            html_parts.append("</tbody></table></div>")
            table_buf = []
            in_table = False

    def inline(text: str) -> str:
        # Bold **text**
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        # Italic *text*
        text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
        # Inline code `code`
        text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
        # Links [text](url)
        text = re.sub(r"\[([^\]]+)\]\((https?://[^\)]+)\)", r'<a href="\2" target="_blank">\1</a>', text)
        # Bare URLs
        text = re.sub(r"(?<![\"'])(https?://\S+)", r'<a href="\1" target="_blank">\1</a>', text)
        return text

    while i < len(lines):
        line = lines[i]

        # Horizontal rule
        if re.match(r"^---+$", line.strip()):
            flush_list()
            flush_table()
            html_parts.append("<hr>")
            i += 1
            continue

        # Table row
        if line.strip().startswith("|"):
            flush_list()
            in_table = True
            table_buf.append(line)
            i += 1
            continue
        else:
            flush_table()

        # Heading 1
        if line.startswith("# "):
            flush_list()
            html_parts.append(f"<h1>{inline(line[2:])}</h1>")
            i += 1
            continue

        # Heading 2
        if line.startswith("## "):
            flush_list()
            html_parts.append(f"<h2>{inline(line[3:])}</h2>")
            i += 1
            continue

        # Heading 3
        if line.startswith("### "):
            flush_list()
            html_parts.append(f"<h3>{inline(line[4:])}</h3>")
            i += 1
            continue

        # Heading 4
        if line.startswith("#### "):
            flush_list()
            html_parts.append(f"<h4>{inline(line[5:])}</h4>")
            i += 1
            continue

        # List item
        if line.startswith("- ") or line.startswith("* "):
            if not in_list:
                html_parts.append('<ul>')
                in_list = True
            html_parts.append(f"<li>{inline(line[2:])}</li>")
            i += 1
            continue

        # Numbered list
        if re.match(r"^\d+\. ", line):
            if not in_list:
                html_parts.append('<ul class="ol">')
                in_list = True
            text = re.sub(r"^\d+\. ", "", line)
            html_parts.append(f"<li>{inline(text)}</li>")
            i += 1
            continue

        # Empty line
        if line.strip() == "":
            flush_list()
            i += 1
            continue

        # Normal paragraph
        flush_list()
        html_parts.append(f"<p>{inline(line)}</p>")
        i += 1

    flush_list()
    flush_table()
    return "\n".join(html_parts)


TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{page_title} · ESA-FSI</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Figtree:wght@300;400;500;600;700&family=DM+Serif+Display:ital@0;1&family=JetBrains+Mono:wght@400;500&display=swap');

  :root {{
    --bg: #edf0f5;
    --bg-card: #ffffff;
    --bg-section: #f5f7fa;
    --border: #dde3ec;
    --border-dark: #c8d1de;
    --text: #0f1e33;
    --text-sub: #445570;
    --text-muted: #8496ae;
    --accent: {accent};
    --accent-bg: {accent_bg};
    --accent-mid: {accent_mid};
    --font-ui: 'Figtree', sans-serif;
    --font-display: 'DM Serif Display', serif;
    --font-mono: 'JetBrains Mono', monospace;
    --radius: 6px;
    --shadow: 0 1px 3px rgba(0,0,0,0.07), 0 4px 12px rgba(0,0,0,0.05);
  }}

  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: var(--font-ui); font-size: 15px; line-height: 1.7; }}

  /* TOP BAR */
  .topbar {{
    background: var(--text);
    color: rgba(255,255,255,0.55);
    font-family: var(--font-mono);
    font-size: 10px;
    letter-spacing: 0.1em;
    padding: 8px 48px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
  }}
  .topbar a {{ color: rgba(255,255,255,0.7); text-decoration: none; transition: color 0.15s; }}
  .topbar a:hover {{ color: #fff; }}
  .topbar .hi {{ color: rgba(255,255,255,0.9); }}

  .wrap {{ max-width: 960px; margin: 0 auto; padding: 0 40px 80px; }}

  /* BREADCRUMB */
  .breadcrumb {{
    padding: 20px 0 0;
    font-family: var(--font-mono);
    font-size: 10px;
    letter-spacing: 0.12em;
    color: var(--text-muted);
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .breadcrumb a {{ color: var(--text-muted); text-decoration: none; transition: color 0.15s; }}
  .breadcrumb a:hover {{ color: var(--accent); }}
  .breadcrumb .sep {{ opacity: 0.4; }}
  .breadcrumb .current {{ color: var(--accent); }}

  /* PAGE HEADER */
  .page-header {{
    padding: 28px 0 32px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 40px;
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 24px;
  }}
  .page-header-left h1 {{
    font-family: var(--font-display);
    font-size: clamp(22px, 3vw, 32px);
    font-weight: 400;
    line-height: 1.2;
    color: var(--text);
    margin-bottom: 6px;
  }}
  .page-header-left .sub {{
    font-size: 13px;
    color: var(--text-muted);
    font-family: var(--font-mono);
    letter-spacing: 0.06em;
  }}
  .bank-badge {{
    display: flex;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
  }}
  .bank-pill {{
    font-family: var(--font-mono);
    font-size: 11px;
    letter-spacing: 0.06em;
    padding: 6px 14px;
    border-radius: 20px;
    background: var(--accent-bg);
    color: var(--accent);
    border: 1px solid var(--accent-mid);
    font-weight: 500;
  }}
  .bank-flag-big {{ font-size: 28px; }}

  /* ACCENT STRIPE */
  .accent-stripe {{
    height: 3px;
    background: var(--accent);
    margin-bottom: 40px;
    border-radius: 2px;
  }}

  /* CONTENT */
  .content {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    padding: 40px 48px;
  }}

  .content h1 {{
    font-family: var(--font-display);
    font-size: 26px;
    font-weight: 400;
    color: var(--text);
    margin: 0 0 6px;
    line-height: 1.2;
  }}

  .content h2 {{
    font-family: var(--font-ui);
    font-size: 17px;
    font-weight: 600;
    color: var(--accent);
    margin: 40px 0 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--accent-mid);
    letter-spacing: -0.01em;
  }}

  .content h2:first-of-type {{ margin-top: 28px; }}

  .content h3 {{
    font-size: 14px;
    font-weight: 600;
    color: var(--text);
    margin: 24px 0 8px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-family: var(--font-mono);
  }}

  .content h4 {{
    font-size: 13px;
    font-weight: 600;
    color: var(--text-sub);
    margin: 16px 0 6px;
  }}

  .content p {{
    color: var(--text-sub);
    margin: 10px 0;
    line-height: 1.75;
  }}

  .content strong {{ color: var(--text); font-weight: 600; }}
  .content em {{ font-style: italic; color: var(--text-sub); }}
  .content code {{
    font-family: var(--font-mono);
    font-size: 12px;
    background: var(--bg-section);
    border: 1px solid var(--border);
    padding: 1px 6px;
    border-radius: 3px;
    color: var(--accent);
  }}

  .content ul {{ margin: 8px 0 16px 20px; }}
  .content ul.ol {{ list-style: decimal; }}
  .content ul li {{ color: var(--text-sub); margin-bottom: 5px; line-height: 1.65; }}

  .content a {{ color: var(--accent); text-decoration: none; border-bottom: 1px solid var(--accent-mid); transition: border-color 0.15s; }}
  .content a:hover {{ border-bottom-color: var(--accent); }}

  .content hr {{ border: none; border-top: 1px solid var(--border); margin: 32px 0; }}

  /* TABLES */
  .table-wrap {{ overflow-x: auto; margin: 16px 0 24px; border-radius: 5px; border: 1px solid var(--border); }}
  .content table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  .content thead {{ background: var(--accent-bg); }}
  .content th {{
    font-family: var(--font-mono);
    font-size: 9px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--accent);
    padding: 10px 14px;
    text-align: left;
    font-weight: 500;
    border-bottom: 1px solid var(--accent-mid);
  }}
  .content td {{
    padding: 9px 14px;
    border-bottom: 1px solid var(--border);
    color: var(--text-sub);
    vertical-align: top;
    line-height: 1.5;
  }}
  .content tr:last-child td {{ border-bottom: none; }}
  .content tbody tr:hover td {{ background: var(--bg-section); }}

  /* METADATA BAR */
  .meta-bar {{
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    margin: 14px 0 28px;
  }}
  .meta-chip {{
    font-family: var(--font-mono);
    font-size: 9px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 4px 10px;
    border-radius: 3px;
    background: var(--bg-section);
    color: var(--text-muted);
    border: 1px solid var(--border);
  }}

  /* PAGE NAV (top) */
  .page-nav {{
    margin-bottom: 28px;
    padding-bottom: 20px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    flex-wrap: wrap;
  }}
  .back-link {{
    font-family: var(--font-mono);
    font-size: 11px;
    letter-spacing: 0.08em;
    color: var(--text-muted);
    text-decoration: none;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: color 0.15s;
  }}
  .back-link:hover {{ color: var(--accent); }}

  .sibling-nav {{ display: flex; gap: 8px; flex-wrap: wrap; }}
  .sib-link {{
    font-family: var(--font-mono);
    font-size: 10px;
    letter-spacing: 0.06em;
    padding: 5px 12px;
    border-radius: 4px;
    border: 1px solid var(--border);
    color: var(--text-muted);
    text-decoration: none;
    transition: all 0.15s;
    background: var(--bg-card);
  }}
  .sib-link:hover {{ border-color: var(--accent); color: var(--accent); background: var(--accent-bg); }}
  .sib-link.active {{ border-color: var(--accent); color: var(--accent); background: var(--accent-bg); pointer-events: none; }}

  @media (max-width: 700px) {{
    .wrap {{ padding: 0 16px 60px; }}
    .content {{ padding: 24px 20px; }}
    .topbar {{ padding: 8px 16px; }}
    .page-header {{ flex-direction: column; align-items: flex-start; }}
  }}
</style>
</head>
<body>

<div class="topbar">
  <span class="hi">ESA-FSI</span>
  <div style="display:flex;gap:20px;">
    <a href="../index.html">← Index</a>
    <span>Phase 1 Research · March 2026</span>
    <a href="https://github.com/thelazyanalyst/ESA-FSI" target="_blank">GitHub</a>
  </div>
</div>

<div class="wrap">

  <div class="breadcrumb">
    <a href="../index.html">Index</a>
    <span class="sep">/</span>
    <span>{bank_name}</span>
    <span class="sep">/</span>
    <span class="current">{file_label}</span>
  </div>

  <div class="page-header">
    <div class="page-header-left">
      <h1>{page_icon} {page_title}</h1>
      <div class="sub">{bank_name} · {ticker} · Research date: March 2026</div>
    </div>
    <div class="bank-badge">
      <span class="bank-flag-big">{flag}</span>
      <span class="bank-pill">{ticker}</span>
    </div>
  </div>

  <div class="accent-stripe"></div>

  <div class="page-nav">
    <a href="../index.html" class="back-link">← Back to index</a>
    <div class="sibling-nav">
{sibling_links}
    </div>
  </div>

  <div class="content">
{content_html}
  </div>

</div>
</body>
</html>
"""


def sibling_links_html(bank: str, current_file: str, meta: dict) -> str:
    if bank == "kiwibank":
        files = ["business-lines", "financial-summary", "press-releases", "sources", "sabsa-contextual"]
    else:
        files = ["business-lines", "financial-summary", "sources", "sabsa-contextual"]
    parts = []
    for f in files:
        label, icon = FILE_LABELS[f]
        active = " active" if f == current_file else ""
        parts.append(f'      <a href="{f}.html" class="sib-link{active}">{icon} {label}</a>')
    return "\n".join(parts)


def build_page(bank: str, file_key: str):
    md_path = os.path.join(BASE, bank, f"{file_key}.md")
    html_path = os.path.join(BASE, bank, f"{file_key}.html")

    if not os.path.exists(md_path):
        print(f"  SKIP (not found): {md_path}")
        return

    with open(md_path, encoding="utf-8") as f:
        md_content = f.read()

    meta = BANK_META[bank]
    label, icon = FILE_LABELS[file_key]
    content_html = md_to_html(md_content)

    html = TEMPLATE.format(
        page_title=f"{meta['name']} — {label}",
        page_icon=icon,
        bank_name=meta["name"],
        ticker=meta["ticker"],
        flag=meta["flag"],
        file_label=label,
        accent=meta["accent"],
        accent_bg=meta["accent_bg"],
        accent_mid=meta["accent_mid"],
        content_html=content_html,
        sibling_links=sibling_links_html(bank, file_key, meta),
    )

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  OK  {bank}/{file_key}.html")


def main():
    print("Building HTML sub-pages...")
    for bank in ["anz", "cba", "nab", "westpac", "kiwibank"]:
        files = ["business-lines", "financial-summary", "sources"]
        if bank == "kiwibank":
            files.append("press-releases")
        for file_key in files:
            build_page(bank, file_key)
    print("Done.")


if __name__ == "__main__":
    main()
