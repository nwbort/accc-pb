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
from html import unescape
from urllib.parse import unquote, urljoin

from curl_cffi import requests

URL = (
    "https://www.accc.gov.au/public-registers/acquisitions-and-mergers-registers/"
    "acquisitions-register?f%5B0%5D=stage%3Apublic_benefit_phase"
)
ITEM_PATH = "/public-registers/acquisitions-and-mergers-registers/acquisitions-register/"
EMPTY_TEXT = "Couldn't find any matches"

# The ACCC's WAF fingerprints the TLS handshake, not just the User-Agent, so a
# plain urllib request is blocked whatever UA it sends. curl_cffi impersonates
# Chrome's handshake and headers, as mergers.fyi's scraper does.
def fetch(url):
    resp = requests.get(url, impersonate="chrome", timeout=60)
    resp.raise_for_status()
    return resp.text


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
