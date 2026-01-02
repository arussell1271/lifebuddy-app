#!/usr/bin/env python3
"""Normalize relative ../ links in markdown files to workspace-relative paths.

Usage:
  python scripts/normalize_doc_links.py .github/copilot-instructions.md

The script will:
 - Find markdown links with parent-relative paths like "(../foo/bar.md)".
 - If the file exists at the resolved path, leave it.
 - If not, check if the target exists at the repository root (by name) and replace the link with the workspace-relative path (e.g. "(foo/bar.md)" or "(lifebuddy-app.yml)").
 - Write the updated file in-place and print replacements.
"""



import re
import sys
from pathlib import Path


MD_LINK_RE = re.compile(r"\((\.{1,2}/[^)\s]+)\)")
INLINE_RE = re.compile(r"(?P<prefix>`?)(?P<path>\.{1,2}/[\w\-./]+)(?P<suffix>`?)")


def normalize_file(md_path: Path, repo_root: Path) -> int:
    text = md_path.read_text(encoding="utf-8")
    changed = 0

    def repl(m):
        nonlocal changed
        orig = m.group(1)
        # Resolve orig relative to the markdown file
        resolved = (md_path.parent / orig).resolve()
        # If the resolved file exists, prefer the workspace-relative path (no leading ../)
        if resolved.exists():
            try:
                new_rel = resolved.relative_to(repo_root).as_posix()
                if new_rel != orig:
                    changed += 1
                    print(f"Normalize: {orig} -> {new_rel}")
                    return f"({new_rel})"
                return f"({orig})"
            except Exception:
                return f"({orig})"

        # Try collapsing leading '..' segments (join and normalize)
        try_alt = Path('/'.join(Path(orig).parts[1:]))
        alt_candidate = repo_root / try_alt
        if alt_candidate.exists():
            new_rel = alt_candidate.relative_to(repo_root).as_posix()
            changed += 1
            print(f"Replace (collapse): {orig} -> {new_rel}")
            return f"({new_rel})"

        # Nothing found; keep original
        return f"({orig})"

    new_text = MD_LINK_RE.sub(repl, text)

    # Also handle inline ../path occurrences (e.g. `../lifebuddy-app.yml` or ../app/main.py)
    def inline_repl(m):
        nonlocal changed
        orig = m.group('path')
        prefix = m.group('prefix') or ''
        suffix = m.group('suffix') or ''
        resolved = (md_path.parent / orig).resolve()
        if resolved.exists():
            try:
                new_rel = resolved.relative_to(repo_root).as_posix()
                if new_rel != orig:
                    changed += 1
                    print(f"Normalize inline: {orig} -> {new_rel}")
                    return f"{prefix}{new_rel}{suffix}"
                return f"{prefix}{orig}{suffix}"
            except Exception:
                return f"{prefix}{orig}{suffix}"

        candidate = repo_root / Path(orig).name
        if candidate.exists():
            new_rel = candidate.relative_to(repo_root).as_posix()
            changed += 1
            print(f"Replace inline: {orig} -> {new_rel}")
            return f"{prefix}{new_rel}{suffix}"

        try_alt = Path('/'.join(Path(orig).parts[1:]))
        alt_candidate = repo_root / try_alt
        if alt_candidate.exists():
            new_rel = alt_candidate.relative_to(repo_root).as_posix()
            changed += 1
            print(f"Replace inline (collapse): {orig} -> {new_rel}")
            return f"{prefix}{new_rel}{suffix}"

        return f"{prefix}{orig}{suffix}"

    new_text = INLINE_RE.sub(inline_repl, new_text)
    if changed:
        md_path.write_text(new_text, encoding="utf-8")
    return changed


import argparse


def iter_markdown_files(paths):
    for p in paths:
        p = Path(p)
        if p.is_dir():
            for f in p.rglob("*.md"):
                yield f
        elif p.is_file() and p.suffix.lower() == ".md":
            yield p


def main():
    parser = argparse.ArgumentParser(description="Normalize ../ links in markdown files to workspace-relative paths.")
    parser.add_argument("paths", nargs="+", help="Files or directories to normalize")
    parser.add_argument("--repo-root", default=".", help="Repository root path (defaults to CWD)")
    parser.add_argument("--check", action="store_true", help="Check mode: don't write files, exit 1 if replacements would be made")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    total_changes = 0
    affected = []

    for md in iter_markdown_files(args.paths):
        print(f"Scanning: {md}")
        # run normalize on each file but in check mode avoid writing
        before = md.read_text(encoding="utf-8")
        changes = normalize_file(md.resolve(), repo_root)
        if changes:
            total_changes += changes
            affected.append(str(md))
            if args.check:
                print(f"[CHECK] {md} would be modified ({changes} replacements)")

    if args.check:
        if total_changes > 0:
            print(f"Check failed: {total_changes} replacements would be made in {len(affected)} files")
            sys.exit(1)
        else:
            print("Check passed: no replacements needed")
            sys.exit(0)

    print(f"Done. Total replacements made: {total_changes}")


if __name__ == "__main__":
    main()
