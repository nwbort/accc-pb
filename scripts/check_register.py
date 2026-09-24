#!/usr/bin/env python3
"""Check the ACCC acquisitions register (public benefit phase filter) for items.

Prints the items found as JSON to stdout and writes `count` and `items`
to $GITHUB_OUTPUT when running in GitHub Actions. Exits non-zero if the
page can't be fetched or doesn't look like the register, so we never
treat a block page as "no items" (or as "items found").
"""
import json
import os
import re
import sys
import urllib.request
from html import unescape
from urllib.parse import unquote, urljoin

URL = (
    "https://www.accc.gov.au/public-registers/acquisitions-and-mergers-registers/"
    "acquisitions-register?f%5B0%5D=stage%3Apublic_benefit_phase"
)
ITEM_PATH = "/public-registers/acquisitions-and-mergers-registers/acquisitions-register/"
EMPTY_TEXT = "Couldn't find any matches"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-AU,en;q=0.9",
}


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse(html):
    items = {}
    pattern = re.compile(
        r'<a\b[^>]*href="(?P<href>[^"]*' + re.escape(ITEM_PATH) + r'[^"?#]+)"[^>]*>(?P<text>.*?)</a>',
        re.S | re.I,
    )
    for m in pattern.finditer(html):
        href = urljoin(URL, unescape(m.group("href")))
        title = re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", m.group("text")))).strip()
        if href not in items or (title and not items[href]):
            items[href] = title
    return [
        {"title": t or unquote(h.rstrip("/").rsplit("/", 1)[-1]), "url": h}
        for h, t in items.items()
    ]


def main():
    html = fetch(URL)
    normalised = html.replace("&#039;", "'").replace("&rsquo;", "'").replace("’", "'")
    items = parse(html)
    empty = EMPTY_TEXT in normalised

    if not items and not empty:
        print("Page didn't contain items or the empty-results message; refusing to guess.", file=sys.stderr)
        print(html[:2000], file=sys.stderr)
        return 1
    if empty:
        items = []

    print(json.dumps(items, indent=2))
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as f:
            f.write(f"count={len(items)}\n")
            f.write("items<<__EOF__\n")
            for it in items:
                f.write(f"- {it['title']}: {it['url']}\n")
            f.write("__EOF__\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
