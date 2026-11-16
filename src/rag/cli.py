"""Command-line entry point: `python -m rag <command>` or `rag` after install."""

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
    print(f"ingested: {stats.documents} documents, {stats.chunks} chunks, {stats.skipped} skipped.")
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
        print("\n--- citations ---")
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
    print(f"path: {rag.config.index_path}")
    print(f"{stats['documents']} documents / {stats['chunks']} chunks / dim {stats['dim']}")
    return 0


def cmd_reset(args: argparse.Namespace) -> int:
    if not args.yes:
        print("This clears the whole index. Pass --yes to confirm.")
        return 1
    rag = Rag()
    try:
        rag.store.reset()
    finally:
        rag.close()
    print("index cleared.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rag", description="Local RAG knowledge base skeleton")
    parser.add_argument("--version", action="version", version=f"rag {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("ingest", help="ingest files or directories")
    p.add_argument("paths", nargs="+", help="files or directories, one or more")
    p.add_argument("--reset", action="store_true", help="clear the index first")
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("search", help="retrieve only, no LLM")
    p.add_argument("query")
    p.add_argument("-k", type=int, default=None, help="number of hits")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("ask", help="retrieve + generate an answer")
    p.add_argument("query")
    p.add_argument("-k", type=int, default=None, help="number of hits")
    p.add_argument("--offline", action="store_true", help="do not call the LLM")
    p.set_defaults(func=cmd_ask)

    p = sub.add_parser("stats", help="show index size")
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("reset", help="clear the index")
    p.add_argument("--yes", action="store_true")
    p.set_defaults(func=cmd_reset)

    return parser


def main(argv: list[str] | None = None) -> int:
    load()  # validate env vars early
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except DimMismatch as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
