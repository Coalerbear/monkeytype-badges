# scripts/fetch_monkeytype.py
#!/usr/bin/env python3
"""
Simple script to fetch MonkeyType runs for a user and generate an SVG badge.

Usage:
  python scripts/fetch_monkeytype.py --username Luke3512 --output assets/monkeytype-badge.svg
"""

import argparse
import sys
from html import escape
import os

import requests

# This endpoint returns recent runs for a user; if MonkeyType changes, this may need updating.
MONKEYTYPE_SCOREBOARD_URL = "https://monkeytype.com/api/scoreboard?user={username}"

BADGE_TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="20" viewBox="0 0 {width} 20" role="img" aria-label="MonkeyType: {label}">
  <title>MonkeyType: {label}</title>
  <linearGradient id="g" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <rect rx="3" width="{width}" height="20" fill="#555"/>
  <rect rx="3" x="{left_width}" width="{right_width}" height="20" fill="#2aa198"/>
  <rect rx="3" width="{width}" height="20" fill="url(#g)"/>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="{left_center}" y="14" fill="#fff">MonkeyType</text>
    <text x="{right_center}" y="14" fill="#fff">{value_text}</text>
  </g>
</svg>
"""

def safe_int(v, default=0):
    try:
        return int(round(float(v)))
    except Exception:
        return default

def fetch_stats(username):
    url = MONKEYTYPE_SCOREBOARD_URL.format(username=username)
    try:
        res = requests.get(url, timeout=15, headers={"User-Agent": "github-action/monkeytype-badge"})
    except Exception as e:
        print("Request failed:", e, file=sys.stderr)
        return None

    if res.status_code != 200:
        print(f"Unexpected status {res.status_code} from {url}", file=sys.stderr)
        return None

    try:
        data = res.json()
    except Exception as e:
        print("Failed to decode JSON:", e, file=sys.stderr)
        return None

    if not isinstance(data, list) or len(data) == 0:
        return None

    wpms = []
    accs = []
    for item in data:
        if isinstance(item, dict):
            if 'wpm' in item:
                try:
                    wpms.append(float(item.get('wpm', 0)))
                except Exception:
                    pass
            if 'acc' in item:
                try:
                    accs.append(float(item.get('acc', 0)))
                except Exception:
                    pass

    best_wpm = safe_int(max(wpms) if wpms else 0)
    avg_acc = round((sum(accs) / len(accs)) if accs else 0, 1)
    return {"best_wpm": best_wpm, "avg_acc": avg_acc}

def render_badge(value_text):
    left_width = 72
    right_width = max(60, 7 * len(value_text) + 20)
    width = left_width + right_width
    left_center = left_width / 2
    right_center = left_width + right_width / 2
    return BADGE_TEMPLATE.format(
        width=width,
        left_width=left_width,
        right_width=right_width,
        left_center=left_center,
        right_center=right_center,
        label=escape(value_text),
        value_text=escape(value_text),
    )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True)
    parser.add_argument("--output", default="assets/monkeytype-badge.svg")
    args = parser.parse_args()

    stats = fetch_stats(args.username)
    if not stats:
        value_text = "no data"
    else:
        value_text = f"{stats['best_wpm']} WPM · {stats['avg_acc']}%"

    svg = render_badge(value_text)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote badge to {args.output}")

if __name__ == "__main__":
    main()
