"""抓取白名单源，提取标题+正文，存 corpus/raw 和 corpus/processed/articles.jsonl。"""
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

GENERIC_TITLE_MARKS = ("科普栏目", "中国科学院心理研究所--", "首页")


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
    # 去掉 CAS 网页的面包屑与工具栏噪声
    text = re.sub(r"您的位置[:：][^\n]*", "", text)
    text = re.sub(r"字体大小\s*[:：]\s*小\s*中\s*大", "", text)
    text = re.sub(r"^\s*(打印|关闭)\s*$", "", text, flags=re.M)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _title(html: str, url: str, text: str) -> str:
    md = trafilatura.extract_metadata(html)
    if md and getattr(md, "title", None):
        t = md.title.strip()
        if t and not any(m in t for m in GENERIC_TITLE_MARKS):
            return t
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    if m:
        t = m.group(1).strip()
        if t and not any(mark in t for mark in GENERIC_TITLE_MARKS):
            return t
    # 兜底：从正文里取「关闭」之后、换行/「作者」之前的一小段当标题
    seg = re.sub(r".*?关闭\s*", "", text[:400], count=1, flags=re.S)
    seg = re.split(r"\n|作者\s*[:：]", seg)[0].strip()
    if 2 <= len(seg) <= 40:
        return seg
    return text[:30].strip()


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
                print(f"SKIP  {source:9s}  (正文过短/未提取到)  {url}")
                continue
            text = _clean(raw_text)
            title = _title(html, url, text)

            dom = urlparse(url).netloc.replace(".", "_")
            slug = re.sub(r"[^0-9a-zA-Z]+", "_", urlparse(url).path)[:80]
            (RAW / dom).mkdir(parents=True, exist_ok=True)
            (RAW / dom / f"{slug}.html").write_text(html, encoding="utf-8")

            records.append({"source": source, "url": url, "title": title, "text": text})
            print(f"OK    {source:9s} {len(text):6d} chars  {title[:55]}")
        except Exception as exc:  # noqa: BLE001
            print(f"ERR   {source:9s} {repr(exc)[:100]}  {url}")
        time.sleep(0.4)

    (PROCESSED / "articles.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records), encoding="utf-8"
    )
    print(f"\nDONE  {len(records)} 篇 → corpus/processed/articles.jsonl")
    return 0


if __name__ == "__main__":
    sys.exit(main())
