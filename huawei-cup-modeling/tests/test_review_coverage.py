from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "measure_review_coverage.py"
SPEC = importlib.util.spec_from_file_location("review_coverage", SCRIPT)
COVERAGE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(COVERAGE)


def annotation(raw: bytes, **changes: object) -> dict:
    value = {
        "text_sha256": hashlib.sha256(raw).hexdigest(),
        "scope": "full_paper",
        "reviewed_spans": [[0, len(raw.decode("utf-8"))]],
        "confirmed_issue_spans": [],
    }
    value.update(changes)
    return value


class ReviewCoverageTests(unittest.TestCase):
    def test_overlaps_are_deduplicated_and_pending_is_separate(self) -> None:
        raw = "甲乙 丙丁\n戊己。".encode()
        report = COVERAGE.measure(raw, annotation(
            raw, confirmed_issue_spans=[[0, 4], [1, 5]], pending_issue_spans=[[3, 8]],
        ))
        self.assertEqual(report["counts"]["eligible"], 7)
        self.assertEqual(report["counts"]["confirmed_issue"], 4)
        self.assertEqual(report["counts"]["pending_issue"], 2)
        self.assertEqual(report["confirmed_issue_pct_of_full_text"], 57.1)
        self.assertEqual(report["pending_issue_pct_of_reviewed"], 28.6)
        self.assertIsNone(report["ai_generated_probability"])

    def test_exclusions_change_the_denominator_without_counting_whitespace(self) -> None:
        raw = "封面\n正文。".encode()
        report = COVERAGE.measure(raw, annotation(
            raw, excluded_spans=[[0, 3]], confirmed_issue_spans=[[3, 5]],
        ))
        self.assertEqual(report["counts"]["eligible"], 3)
        self.assertEqual(report["counts"]["excluded_non_whitespace"], 2)
        self.assertEqual(report["confirmed_issue_pct_of_full_text"], 66.7)

    def test_partial_review_does_not_produce_full_text_percentage(self) -> None:
        raw = b"abcdefgh"
        report = COVERAGE.measure(raw, annotation(
            raw, reviewed_spans=[[0, 4]], confirmed_issue_spans=[[0, 2]],
        ))
        self.assertEqual(report["review_coverage_pct"], 50.0)
        self.assertEqual(report["confirmed_issue_pct_of_reviewed"], 50.0)
        self.assertFalse(report["full_text_review_complete"])
        self.assertIsNone(report["confirmed_issue_pct_of_full_text"])

    def test_fully_reviewed_excerpt_is_not_a_full_paper(self) -> None:
        raw = b"abcdef"
        report = COVERAGE.measure(raw, annotation(raw, scope="excerpt"))
        self.assertEqual(report["review_coverage_pct"], 100.0)
        self.assertFalse(report["full_text_review_complete"])
        self.assertIsNone(report["confirmed_issue_pct_of_full_text"])

    def test_empty_review_has_unknown_issue_percentage(self) -> None:
        raw = b"abcdef"
        report = COVERAGE.measure(raw, annotation(raw, reviewed_spans=[]))
        self.assertEqual(report["review_coverage_pct"], 0.0)
        self.assertIsNone(report["confirmed_issue_pct_of_reviewed"])

    def test_unicode_offsets_and_crlf_are_preserved(self) -> None:
        raw = "甲🙂\r\n乙".encode()
        report = COVERAGE.measure(raw, annotation(raw, confirmed_issue_spans=[[4, 5]]))
        self.assertEqual(report["counts"]["eligible"], 3)
        self.assertEqual(report["counts"]["confirmed_issue"], 1)
        self.assertEqual(report["confirmed_issue_pct_of_full_text"], 33.3)

    def test_stale_hash_invalid_ranges_and_schema_are_rejected(self) -> None:
        raw = b"abcdef"
        invalid = [
            annotation(raw, text_sha256="0" * 64),
            annotation(raw, scope="unknown"),
            annotation(raw, reviewed_spans=[[0, 7]]),
            annotation(raw, confirmed_issue_spans=[[2, 2]]),
            annotation(raw, confirmed_issue_spans=[[-1, 2]]),
            annotation(raw, confirmed_issue_spans=[[True, 2]]),
            annotation(raw, pending_issue_spans=[[1.0, 2]]),
            annotation(raw, excluded_spans="0:2"),
            annotation(raw, excluded_spans=[[0, 6]]),
            annotation(raw, reviewed_spans=[[0, 2]], confirmed_issue_spans=[[2, 3]]),
            annotation(raw, reviewed_spans=[], pending_issue_spans=[[1, 2]]),
            annotation(raw, misspelled_field=[]),
            {},
            [],
        ]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                COVERAGE.measure(raw, value)

    def test_cli_returns_json_without_mutating_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            text = Path(directory) / "paper.txt"
            spans = Path(directory) / "annotations.json"
            raw = "模型 A 的误差较低。".encode()
            text.write_bytes(raw)
            annotations = json.dumps(annotation(raw), ensure_ascii=False).encode()
            spans.write_bytes(annotations)
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(text), str(spans)],
                capture_output=True, text=True, encoding="utf-8", check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["confirmed_issue_pct_of_full_text"], 0.0)
            self.assertEqual(text.read_bytes(), raw)
            self.assertEqual(spans.read_bytes(), annotations)
            self.assertEqual(len(list(Path(directory).iterdir())), 2)


if __name__ == "__main__":
    unittest.main()
