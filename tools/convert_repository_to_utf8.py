"""Convert repository text files to UTF-8 without BOM.

The script first scans all supported text files. If any file cannot be decoded
as UTF-8, GB18030, or GBK, it stops without modifying files.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

TEXT_EXTENSIONS = {
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
    ".json",
    ".md",
    ".html",
    ".css",
    ".js",
}

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "models",
    "datasets",
    "finetuned_models",
    "vector_store",
    "cache",
}

CODECS = ("utf-8", "gb18030", "gbk")


@dataclass(frozen=True)
class FileEncoding:
    path: str
    encoding: str | None
    size: int
    error: str | None = None
    converted: bool = False


def iter_text_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS:
            files.append(path)
    return sorted(files)


def detect_encoding(data: bytes) -> tuple[str | None, str | None]:
    last_error = None
    for codec in CODECS:
        try:
            data.decode(codec)
            return codec, None
        except UnicodeDecodeError as exc:
            last_error = str(exc)
    return None, last_error


def scan(root: Path) -> tuple[list[FileEncoding], list[FileEncoding]]:
    detected: list[FileEncoding] = []
    failures: list[FileEncoding] = []
    for path in iter_text_files(root):
        data = path.read_bytes()
        encoding, error = detect_encoding(data)
        item = FileEncoding(
            path=path.relative_to(root).as_posix(),
            encoding=encoding,
            size=len(data),
            error=error,
        )
        detected.append(item)
        if encoding is None:
            failures.append(item)
    return detected, failures


def write_report(root: Path, detected: list[FileEncoding], report_path: Path) -> None:
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "files": [asdict(item) for item in detected],
        "non_utf8": [asdict(item) for item in detected if item.encoding != "utf-8"],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def convert(root: Path, detected: list[FileEncoding]) -> list[FileEncoding]:
    converted: list[FileEncoding] = []
    for item in detected:
        if item.encoding == "utf-8":
            continue
        path = root / item.path
        data = path.read_bytes()
        text = data.decode(item.encoding or "")
        path.write_text(text, encoding="utf-8", newline="\n")
        converted.append(
            FileEncoding(
                path=item.path,
                encoding=item.encoding,
                size=item.size,
                converted=True,
            )
        )
    return converted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Repository root to scan")
    parser.add_argument("--apply", action="store_true", help="Write UTF-8 files")
    parser.add_argument(
        "--report",
        default="tools/encoding_conversion_report.json",
        help="Report path relative to root",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report_path = root / args.report

    detected, failures = scan(root)
    write_report(root, detected, report_path)

    if failures:
        print("Encoding scan failed; no files were modified.")
        for item in failures:
            print(f"UNDECODABLE {item.path}: {item.error}")
        return 2

    non_utf8 = [item for item in detected if item.encoding != "utf-8"]
    print(f"Scanned {len(detected)} text files.")
    print(f"Report: {report_path}")
    if non_utf8:
        for item in non_utf8:
            print(f"NON_UTF8 {item.path}: {item.encoding}")
    else:
        print("All files are already UTF-8.")

    if args.apply:
        converted = convert(root, detected)
        print(f"Converted {len(converted)} files to UTF-8 without BOM.")
    else:
        print("Dry run only. Re-run with --apply to convert.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
