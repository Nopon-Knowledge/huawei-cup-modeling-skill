#!/usr/bin/env python3
"""Read-only preflight checks and hash manifest for a competition submission."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


def positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("value must be an integer") from exc
    if number <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return number


def fixed_hex(value: str, length: int, label: str) -> str:
    normalized = value.lower()
    if len(normalized) != length or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise argparse.ArgumentTypeError(
            f"{label} must contain exactly {length} hexadecimal characters"
        )
    return normalized


def md5_value(value: str) -> str:
    return fixed_hex(value, 32, "MD5")


def sha256_value(value: str) -> str:
    return fixed_hex(value, 64, "SHA-256")


def nonempty_text(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise argparse.ArgumentTypeError("value must contain non-whitespace text")
    return normalized


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check a final PDF without modifying it and compute MD5/SHA-256."
    )
    parser.add_argument("paper", type=Path, help="Final PDF file")
    parser.add_argument(
        "--expected-name",
        help="Exact paper filename required by the current official rules",
    )
    parser.add_argument(
        "--expected-md5",
        type=md5_value,
        help="Previously recorded MD5 to verify a locked paper",
    )
    parser.add_argument(
        "--expected-sha256",
        type=sha256_value,
        help="Previously recorded SHA-256 to verify a locked paper",
    )
    parser.add_argument(
        "--max-paper-bytes",
        type=positive_int,
        help="Paper byte limit from the rules or a documented conservative conversion",
    )
    parser.add_argument("--attachment", type=Path, action="append", default=[])
    parser.add_argument(
        "--max-attachment-bytes",
        type=positive_int,
        help="Per-attachment byte limit from rules or a documented conversion",
    )
    parser.add_argument(
        "--identity",
        action="append",
        type=nonempty_text,
        default=[],
        help="Identity term to scan; repeat as needed",
    )
    parser.add_argument(
        "--identity-start-page",
        type=positive_int,
        help="First PDF page included in identity scanning; set from current rules",
    )
    parser.add_argument("--manifest", type=Path, help="Write a JSON hash manifest")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return a non-zero exit code when any warning remains",
    )
    parser.add_argument("--json", action="store_true", help="Print the full report as JSON")
    return parser.parse_args()


def digest_file(path: Path) -> tuple[str, str, int, int]:
    before = path.stat()
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            md5.update(chunk)
            sha256.update(chunk)
    after = path.stat()
    if before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
        raise RuntimeError("file changed while hashing")
    return md5.hexdigest(), sha256.hexdigest(), after.st_size, after.st_mtime_ns


def add_finding(findings: list[dict[str, str]], level: str, message: str) -> None:
    findings.append({"level": level, "message": message})


def display_name(path: Path, fallback: str) -> str:
    return path.expanduser().name or fallback


def safe_error_detail(error: BaseException) -> str:
    if isinstance(error, OSError):
        return error.strerror or type(error).__name__
    return str(error)


def redact_path(text: str, path: Path) -> str:
    return text.replace(str(path), path.name)


def extract_from_page(pdf: Path, start_page: int) -> tuple[str | None, str | None]:
    executable = shutil.which("pdftotext")
    if not executable:
        return None, "pdftotext is unavailable; identity text scan was skipped"
    try:
        result = subprocess.run(
            [executable, "-f", str(start_page), str(pdf), "-"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
        )
    except subprocess.TimeoutExpired:
        return None, "pdftotext timed out; identity text scan was skipped"
    except OSError as exc:
        return None, f"pdftotext could not run; identity text scan was skipped: {exc}"
    if result.returncode != 0:
        detail = result.stderr.strip() or f"exit code {result.returncode}"
        detail = redact_path(detail, pdf)
        return None, f"pdftotext failed; identity text scan was skipped: {detail}"
    return result.stdout, None


def validate_pdf_structure(pdf: Path) -> tuple[str, str]:
    executable = shutil.which("pdfinfo")
    if not executable:
        return (
            "WARN",
            "pdfinfo is unavailable; PDF structure validation was skipped",
        )
    try:
        result = subprocess.run(
            [executable, str(pdf)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
        )
    except subprocess.TimeoutExpired:
        return "WARN", "pdfinfo timed out; PDF structure validation was skipped"
    except OSError as exc:
        return "WARN", f"pdfinfo could not run; PDF structure validation was skipped: {exc}"
    if result.returncode != 0:
        detail = result.stderr.strip() or f"exit code {result.returncode}"
        detail = redact_path(detail, pdf)
        return "FAIL", f"pdfinfo could not parse the PDF structure: {detail}"
    return "PASS", "PDF structure was parsed successfully by pdfinfo"


def raw_path_is_symlink(path: Path) -> bool:
    try:
        return path.expanduser().is_symlink()
    except OSError:
        return False


def check_regular_file(
    raw_path: Path, resolved: Path, label: str, findings: list[dict[str, str]]
) -> bool:
    shown = display_name(raw_path, label)
    if raw_path_is_symlink(raw_path):
        add_finding(findings, "FAIL", f"{label} is a symbolic link: {shown}")
        return False
    if not resolved.exists():
        add_finding(findings, "FAIL", f"{label} does not exist: {shown}")
        return False
    if not resolved.is_file():
        add_finding(findings, "FAIL", f"{label} is not a regular file: {shown}")
        return False
    if resolved.stat().st_size == 0:
        add_finding(findings, "FAIL", f"{label} is empty: {shown}")
        return False
    return True


def status_from_findings(findings: list[dict[str, str]], strict: bool) -> str:
    levels = {item["level"] for item in findings}
    if "FAIL" in levels:
        return "FAIL"
    if "WARN" in levels:
        return "FAIL_STRICT" if strict else "PASS_WITH_WARNINGS"
    return "PASS"


def finish(args: argparse.Namespace, report: dict[str, Any]) -> int:
    findings = report["findings"]
    report["status"] = status_from_findings(findings, args.strict)

    if args.manifest:
        raw_manifest = args.manifest.expanduser()
        manifest = raw_manifest.resolve()
        protected = {args.paper.expanduser().resolve()}
        protected.update(path.expanduser().resolve() for path in args.attachment)
        shown_manifest = display_name(raw_manifest, "manifest")
        if raw_manifest.is_symlink():
            add_finding(findings, "FAIL", f"manifest is a symbolic link: {shown_manifest}")
            report["status"] = "FAIL"
        elif manifest in protected:
            add_finding(
                findings,
                "FAIL",
                f"refusing to overwrite an input file with the manifest: {shown_manifest}",
            )
            report["status"] = "FAIL"
        elif manifest.exists():
            add_finding(
                findings,
                "FAIL",
                f"manifest exists; not overwritten: {shown_manifest}",
            )
            report["status"] = "FAIL"
        else:
            created_manifest = False
            try:
                manifest.parent.mkdir(parents=True, exist_ok=True)
                with manifest.open("x", encoding="utf-8") as handle:
                    created_manifest = True
                    handle.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
            except OSError as exc:
                if created_manifest and manifest.exists():
                    try:
                        manifest.unlink()
                    except OSError:
                        pass
                add_finding(
                    findings,
                    "FAIL",
                    f"cannot write manifest: {safe_error_detail(exc)}",
                )
                report["status"] = "FAIL"

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"{report['status']}: {report['paper']}")
        for item in findings:
            print(f"[{item['level']}] {item['message']}")
        if args.manifest and report["status"] != "FAIL":
            print(f"manifest: {display_name(args.manifest, 'manifest')}")
    return 1 if report["status"].startswith("FAIL") else 0


def main() -> int:
    args = parse_args()
    raw_paper = args.paper
    paper = raw_paper.expanduser().resolve()
    findings: list[dict[str, str]] = []
    report: dict[str, Any] = {
        "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "paper": display_name(raw_paper, "paper"),
        "configured_checks": {
            "expected_name": args.expected_name,
            "max_paper_bytes": args.max_paper_bytes,
            "max_attachment_bytes": args.max_attachment_bytes,
            "identity_start_page": args.identity_start_page,
            "identity_term_count": len(args.identity),
        },
        "manual_review_required": [
            "current official template and annual rules",
            "visual page rendering, fonts, formulas, figures, and pagination",
            "identity information not extractable as text",
            "citations, AI disclosure, and attachment contents",
        ],
        "findings": findings,
    }

    if not check_regular_file(raw_paper, paper, "paper", findings):
        return finish(args, report)

    if paper.suffix.lower() != ".pdf":
        add_finding(findings, "FAIL", "paper extension is not .pdf")
    with paper.open("rb") as handle:
        signature = handle.read(5)
        if paper.stat().st_size > 4096:
            handle.seek(-4096, 2)
        else:
            handle.seek(0)
        tail = handle.read()
    if signature != b"%PDF-":
        add_finding(findings, "FAIL", "file does not start with a PDF signature")
    if b"%%EOF" not in tail:
        add_finding(findings, "WARN", "PDF end marker was not found near the end of the file")
    structure_level, structure_message = validate_pdf_structure(paper)
    add_finding(findings, structure_level, structure_message)

    try:
        paper_md5, paper_sha256, paper_size, paper_mtime = digest_file(paper)
    except (OSError, RuntimeError) as exc:
        add_finding(
            findings,
            "FAIL",
            f"cannot hash paper: {safe_error_detail(exc)}",
        )
        return finish(args, report)

    report["paper_hashes"] = {"md5": paper_md5, "sha256": paper_sha256}
    report["paper_size_bytes"] = paper_size
    report["paper_mtime_ns"] = paper_mtime
    add_finding(findings, "PASS", f"paper MD5 {paper_md5}")

    if args.expected_md5 is not None:
        if paper_md5 != args.expected_md5:
            add_finding(
                findings,
                "FAIL",
                f"paper MD5 {paper_md5} does not match recorded MD5 {args.expected_md5}",
            )
        else:
            add_finding(findings, "PASS", "paper MD5 matches the recorded locked value")

    if args.expected_sha256 is not None:
        if paper_sha256 != args.expected_sha256:
            add_finding(findings, "FAIL", "paper SHA-256 does not match the recorded value")
        else:
            add_finding(findings, "PASS", "paper SHA-256 matches the recorded value")

    if args.max_paper_bytes is not None:
        if paper_size > args.max_paper_bytes:
            add_finding(
                findings,
                "FAIL",
                f"paper is {paper_size} bytes, above {args.max_paper_bytes} bytes",
            )
        else:
            add_finding(findings, "PASS", "paper is within the supplied byte limit")

    if args.expected_name is not None:
        if paper.name != args.expected_name:
            add_finding(
                findings,
                "FAIL",
                f"filename is {paper.name!r}; expected {args.expected_name!r}",
            )
        else:
            add_finding(findings, "PASS", "paper filename matches the supplied annual rule")
    else:
        add_finding(findings, "INFO", "filename rule was not supplied; check not run")

    attachments: list[dict[str, Any]] = []
    seen_inputs = {paper}
    for raw_attachment in args.attachment:
        attachment = raw_attachment.expanduser().resolve()
        item: dict[str, Any] = {
            "name": display_name(raw_attachment, "attachment")
        }
        attachments.append(item)
        if attachment in seen_inputs:
            add_finding(
                findings,
                "FAIL",
                f"duplicate input file: {display_name(raw_attachment, 'attachment')}",
            )
            continue
        seen_inputs.add(attachment)
        if not check_regular_file(
            raw_attachment, attachment, "attachment", findings
        ):
            continue
        try:
            digest_md5, digest_sha256, size, mtime = digest_file(attachment)
        except (OSError, RuntimeError) as exc:
            add_finding(
                findings,
                "FAIL",
                f"cannot hash attachment {attachment.name}: {safe_error_detail(exc)}",
            )
            continue
        item.update(
            {
                "md5": digest_md5,
                "sha256": digest_sha256,
                "size_bytes": size,
                "mtime_ns": mtime,
            }
        )
        if args.max_attachment_bytes is not None and size > args.max_attachment_bytes:
            add_finding(
                findings,
                "FAIL",
                f"attachment {attachment.name} is {size} bytes, above "
                f"{args.max_attachment_bytes} bytes",
            )
    report["attachments"] = attachments

    if args.identity:
        if args.identity_start_page is None:
            add_finding(
                findings,
                "FAIL",
                "identity terms were supplied without --identity-start-page from current rules",
            )
        else:
            text, warning = extract_from_page(paper, args.identity_start_page)
            if warning:
                add_finding(findings, "WARN", warning)
            elif text is not None:
                found_indexes = [
                    index
                    for index, term in enumerate(args.identity, start=1)
                    if term in text
                ]
                if found_indexes:
                    add_finding(
                        findings,
                        "FAIL",
                        f"identity terms found from page {args.identity_start_page} onward: "
                        + ", ".join(f"#{index}" for index in found_indexes),
                    )
                else:
                    add_finding(
                        findings,
                        "PASS",
                        f"no supplied identity terms found from page "
                        f"{args.identity_start_page} onward",
                    )
    else:
        if args.identity_start_page is not None:
            add_finding(
                findings,
                "WARN",
                "--identity-start-page was supplied without any --identity terms",
            )
        else:
            add_finding(findings, "INFO", "identity text scan was not configured")

    add_finding(
        findings,
        "INFO",
        "mechanical checks do not replace current official rules or manual page review",
    )
    return finish(args, report)


if __name__ == "__main__":
    raise SystemExit(main())
