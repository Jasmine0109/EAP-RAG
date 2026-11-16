"""Crawl whitelisted sources, extract title + body, save to corpus/raw and corpus/processed/articles.jsonl.

Usage: python pipeline/crawl.py
Depends on: trafilatura (HTML -> text)
"""
from __future__ import annotations

import json
import re
import ssl
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

import certifi
import trafilatura

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "corpus" / "raw"
PROCESSED = ROOT / "corpus" / "processed"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
}


def fetch(url: str) -> str:
    ctx = ssl.create_default_context(cafile=certifi.where())
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
        data = r.read()
    for enc in ("utf-8", "gb18030"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", "ignore")


def _clean(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _title(html: str, url: str, text: str) -> str:
    md = trafilatura.extract_metadata(html)
    if md and getattr(md, "title", None):
        return md.title.strip()
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    if m and m.group(1).strip():
        return m.group(1).strip()
    return text[:30].strip() or urlparse(url).path.split("/")[-1]


def main() -> int:
    seeds = json.loads((ROOT / "corpus" / "seeds.json").read_text(encoding="utf-8"))
    RAW.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    records = []

    for item in seeds:
        source, url = item["source"], item["url"]
        try:
            html = fetch(url)
            raw_text = trafilatura.extract(html, url=url, include_comments=False, include_tables=False)
            if not raw_text or len(raw_text.strip()) < 200:
                print(f"SKIP  {source:12s}  (too short / no body)  {url}")
                continue
            text = _clean(raw_text)
            title = _title(html, url, text)

            dom = urlparse(url).netloc.replace(".", "_")
            slug = re.sub(r"[^0-9a-zA-Z]+", "_", urlparse(url).path)[:80]
            (RAW / dom).mkdir(parents=True, exist_ok=True)
            (RAW / dom / f"{slug}.html").write_text(html, encoding="utf-8")

            records.append({"source": source, "url": url, "title": title, "text": text})
            print(f"OK    {source:12s} {len(text):6d} chars  {title[:55]}")
        except Exception as exc:  # noqa: BLE001
            print(f"ERR   {source:12s} {repr(exc)[:100]}  {url}")
        time.sleep(0.4)

    (PROCESSED / "articles.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records), encoding="utf-8"
    )
    print(f"\nDONE  {len(records)} articles -> corpus/processed/articles.jsonl")
    return 0


if __name__ == "__main__":
    sys.exit(main())
