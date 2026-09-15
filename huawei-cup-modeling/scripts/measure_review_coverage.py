#!/usr/bin/env python3
"""Measure supplied review annotations; does not classify text authorship."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


SPAN_FIELDS = (
    "reviewed_spans",
    "excluded_spans",
    "confirmed_issue_spans",
    "pending_issue_spans",
)


def span_mask(spans: Any, size: int, field: str) -> bytearray:
    if not isinstance(spans, list):
        raise ValueError(f"{field} must be an array of [start, end] ranges")
    mask = bytearray(size)
    for index, span in enumerate(spans):
        if (
            not isinstance(span, list)
            or len(span) != 2
            or any(type(value) is not int for value in span)
        ):
            raise ValueError(f"{field}[{index}] must contain two integer offsets")
        start, end = span
        if not 0 <= start < end <= size:
            raise ValueError(f"{field}[{index}] is outside the text or empty")
        mask[start:end] = b"\x01" * (end - start)
    return mask


def measure(raw_text: bytes, annotations: Any) -> dict[str, Any]:
    if not isinstance(annotations, dict):
        raise ValueError("annotations must be a JSON object")
    allowed = {"text_sha256", "scope", *SPAN_FIELDS}
    if set(annotations) - allowed:
        raise ValueError("annotations contain unsupported fields")
    required = {"text_sha256", "scope", "reviewed_spans", "confirmed_issue_spans"}
    if not required <= set(annotations):
        raise ValueError("text_sha256, scope, reviewed_spans and confirmed_issue_spans are required")
    digest = hashlib.sha256(raw_text).hexdigest()
    if annotations["text_sha256"] != digest:
        raise ValueError("text_sha256 does not match; rebuild annotations for this text version")
    scope = annotations["scope"]
    if scope not in ("full_paper", "excerpt"):
        raise ValueError("scope must be full_paper or excerpt")
    # Keep the exact decoded text, including CRLF: offsets are Python string indices.
    text = raw_text.decode("utf-8")
    masks = {
        field: span_mask(annotations.get(field, []), len(text), field)
        for field in SPAN_FIELDS
    }
    counts = {
        "eligible": 0,
        "reviewed": 0,
        "confirmed_issue": 0,
        "pending_issue": 0,
        "excluded_non_whitespace": 0,
    }
    for i, character in enumerate(text):
        if character.isspace():
            continue
        if masks["excluded_spans"][i]:
            counts["excluded_non_whitespace"] += 1
            continue
        counts["eligible"] += 1
        reviewed = bool(masks["reviewed_spans"][i])
        confirmed = bool(masks["confirmed_issue_spans"][i])
        pending = bool(masks["pending_issue_spans"][i])
        if (confirmed or pending) and not reviewed:
            raise ValueError("issue annotations include eligible text outside reviewed_spans")
        counts["reviewed"] += reviewed
        counts["confirmed_issue"] += confirmed
        # Confirmed evidence takes precedence; overlapping pending spans are not added twice.
        counts["pending_issue"] += pending and not confirmed
    if not counts["eligible"]:
        raise ValueError("no eligible non-whitespace characters remain")
    counts["unreviewed"] = counts["eligible"] - counts["reviewed"]
    full_review = scope == "full_paper" and counts["unreviewed"] == 0

    def percent(numerator: int, denominator: int) -> float | None:
        return round(100 * numerator / denominator, 1) if denominator else None

    return {
        "method": "annotation_coverage_v1",
        "text_sha256": digest,
        "scope": scope,
        "counts": counts,
        "review_coverage_pct": percent(counts["reviewed"], counts["eligible"]),
        "confirmed_issue_pct_of_reviewed": percent(counts["confirmed_issue"], counts["reviewed"]),
        "pending_issue_pct_of_reviewed": percent(counts["pending_issue"], counts["reviewed"]),
        "confirmed_issue_pct_of_full_text": (
            percent(counts["confirmed_issue"], counts["eligible"]) if full_review else None
        ),
        "full_text_review_complete": full_review,
        "ai_generated_probability": None,
        "note": "Counts supplied annotations only; does not verify their meaning, authorship or compliance.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", type=Path, help="Frozen UTF-8 text; no newline normalization")
    parser.add_argument("annotations", type=Path, help="JSON ranges tied to the text SHA-256")
    args = parser.parse_args()
    try:
        report = measure(args.text.read_bytes(), json.loads(args.annotations.read_text(encoding="utf-8")))
    except OSError as error:
        parser.error(error.strerror or "could not read an input file")
    except UnicodeError:
        parser.error("inputs must be valid UTF-8")
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
