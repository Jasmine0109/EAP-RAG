"""命令行入口：python -m rag <命令>，安装后也可直接 `rag`。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .config import load
from .pipeline import Rag
from .store import DimMismatch


def _print_hits(hits) -> None:
    for i, hit in enumerate(hits, 1):
        where = f"{hit.chunk.source} § {hit.chunk.heading}" if hit.chunk.heading else hit.chunk.source
        print(f"[{i}] {hit.score:.3f}  {where}")
        print(f"    {hit.chunk.text[:160].replace(chr(10), ' ')}…")


def cmd_ingest(args: argparse.Namespace) -> int:
    rag = Rag()
    try:
        stats = rag.ingest(args.paths, reset=args.reset)
    finally:
        rag.close()
    print(f"入库完成：{stats.documents} 篇文档，{stats.chunks} 个块，跳过 {stats.skipped} 个。")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    rag = Rag()
    try:
        hits = rag.retrieve(args.query, k=args.k)
    finally:
        rag.close()
    _print_hits(hits)
    return 0


def cmd_ask(args: argparse.Namespace) -> int:
    rag = Rag()
    try:
        answer = rag.ask(args.query, k=args.k, offline=args.offline or None)
    finally:
        rag.close()
    if answer.mode == "llm":
        print(answer.text)
        print("\n--- 引用 ---")
        _print_hits(answer.hits)
    else:
        print(answer.text)
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    rag = Rag()
    try:
        stats = rag.store.stats()
    finally:
        rag.close()
    print(f"路径：{rag.config.index_path}")
    print(f"文档 {stats['documents']} 篇 / 块 {stats['chunks']} 个 / 维度 {stats['dim']}")
    return 0


def cmd_reset(args: argparse.Namespace) -> int:
    if not args.yes:
        print("这会清空整个索引。加上 --yes 确认。")
        return 1
    rag = Rag()
    try:
        rag.store.reset()
    finally:
        rag.close()
    print("索引已清空。")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rag", description="本地 RAG 知识库骨架")
    parser.add_argument("--version", action="version", version=f"rag {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("ingest", help="把文档或目录建进索引")
    p.add_argument("paths", nargs="+", help="文件或目录，可多个")
    p.add_argument("--reset", action="store_true", help="先清空索引")
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("search", help="只检索，不调用 LLM")
    p.add_argument("query")
    p.add_argument("-k", type=int, default=None, help="返回片段数")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("ask", help="检索 + 生成回答")
    p.add_argument("query")
    p.add_argument("-k", type=int, default=None, help="返回片段数")
    p.add_argument("--offline", action="store_true", help="不调用 LLM")
    p.set_defaults(func=cmd_ask)

    p = sub.add_parser("stats", help="查看索引规模")
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("reset", help="清空索引")
    p.add_argument("--yes", action="store_true")
    p.set_defaults(func=cmd_reset)

    return parser


def main(argv: list[str] | None = None) -> int:
    load()  # 提前校验环境变量（配置非法时立刻报错）
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except FileNotFoundError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:  # 空索引等可预期错误
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    except DimMismatch as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
