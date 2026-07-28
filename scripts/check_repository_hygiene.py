#!/usr/bin/env python3
"""Fail when versioned repository areas lose traceability.

Run this command in CI and locally before committing:
    python scripts/check_repository_hygiene.py
"""

from __future__ import annotations

import re
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
CONTROLLED_DIRECTORIES = ("src", "tests", "docs", "scripts", "config")
DOCUMENT_ID = re.compile(r"(?:DOC|IT|ADR)\s*-\s*\d{3}(?:\s*-\s*\d{3})?", re.IGNORECASE)
IGNORED_SOURCE_DIRECTORY = re.compile(
    r"^(?:/?|\*\*/)(?:src|tests|docs|scripts|config)/?\*?$", re.I
)
PROVISIONAL_IDENTIFIER = re.compile(r"\bIT-\d{3}-\d{2}X\b", re.IGNORECASE)
ROOT_UNTRACKED_ALLOWLIST: frozenset[str] = frozenset()
TEXTUAL_EXTENSIONS = {
    ".cfg",
    ".ini",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}


def git(*args: str) -> str:
    return subprocess.check_output(
        [
            "git",
            "-c",
            f"safe.directory={ROOT.as_posix()}",
            "-c",
            "core.quotepath=false",
            "-C",
            str(ROOT),
            *args,
        ],
        text=True,
        encoding="utf-8",
    )


def repository_files() -> set[str]:
    return {line for line in git("ls-files").splitlines() if line}


def untracked_files() -> set[str]:
    return {
        line[3:].replace("\\", "/")
        for line in git("status", "--porcelain", "--untracked-files=all").splitlines()
        if line.startswith("?? ")
    }


def document_text(path: Path) -> str:
    if path.suffix.lower() != ".docx":
        return path.read_text(encoding="utf-8", errors="ignore")
    try:
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("word/document.xml")
        return " ".join(ElementTree.fromstring(xml).itertext())
    except (KeyError, OSError, zipfile.BadZipFile, ElementTree.ParseError) as error:
        raise ValueError(f"cannot read {path.relative_to(ROOT)}: {error}") from error


def check_gitignore(errors: list[str]) -> None:
    for raw_line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines():
        rule = raw_line.strip().lstrip("!").replace("\\", "/")
        if (
            rule
            and not rule.startswith("#")
            and IGNORED_SOURCE_DIRECTORY.fullmatch(rule)
        ):
            errors.append(
                f".gitignore must not ignore a controlled directory: {raw_line}"
            )


def check_controlled_files(errors: list[str]) -> None:
    tracked = repository_files()
    untracked = untracked_files()
    for directory in CONTROLLED_DIRECTORIES:
        base = ROOT / directory
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(ROOT).as_posix()
            parts = Path(relative).parts
            generated = (
                "__pycache__" in parts
                or relative.endswith((".pyc", ".pyo", ".pyd"))
                or relative == "src/pyvenv.cfg"
                or relative.startswith(("src/bin/", "src/lib/", "src/lib64/"))
                or ".egg-info/" in relative
            )
            if generated:
                continue
            if relative not in tracked:
                state = "untracked" if relative in untracked else "not indexed"
                errors.append(f"{state} controlled file: {relative}")


def check_untracked_root_files(errors: list[str]) -> None:
    for relative in sorted(untracked_files()):
        if "/" not in relative and relative not in ROOT_UNTRACKED_ALLOWLIST:
            errors.append(f"untracked root file: {relative}")


def check_document_references(errors: list[str]) -> None:
    documents = [
        path
        for path in (ROOT / "docs").rglob("*")
        if path.is_file() and path.suffix.lower() in {".docx", ".md", ".txt"}
    ]
    available = {
        code.upper().replace(" ", "")
        for path in documents
        for code in DOCUMENT_ID.findall(path.name)
    }
    for path in documents:
        try:
            references = {
                re.sub(r"\s+", "", reference).upper()
                for reference in DOCUMENT_ID.findall(document_text(path))
            }
        except ValueError as error:
            errors.append(str(error))
            continue
        for reference in sorted(references - available):
            # A short IT identifier denotes its task family; an implementation
            # record such as IT-021-001 is a valid physical target.
            if re.fullmatch(r"IT-\d{3}", reference) and any(
                code.startswith(f"{reference}-") for code in available
            ):
                continue
            errors.append(
                f"broken document reference in {path.relative_to(ROOT)}: {reference}"
            )


def check_provisional_identifiers(errors: list[str]) -> None:
    for directory in CONTROLLED_DIRECTORIES:
        base = ROOT / directory
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXTUAL_EXTENSIONS | {
                ".docx"
            }:
                continue
            try:
                content = document_text(path)
            except ValueError as error:
                errors.append(str(error))
                continue
            for identifier in sorted(set(PROVISIONAL_IDENTIFIER.findall(content))):
                relative = path.relative_to(ROOT)
                errors.append(f"provisional identifier in {relative}: {identifier}")


def main() -> int:
    errors: list[str] = []
    check_gitignore(errors)
    check_controlled_files(errors)
    check_untracked_root_files(errors)
    check_document_references(errors)
    check_provisional_identifiers(errors)
    if errors:
        print("Repository hygiene check failed:", file=sys.stderr)
        print(*[f"- {error}" for error in errors], sep="\n", file=sys.stderr)
        return 1
    print("Repository hygiene check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
