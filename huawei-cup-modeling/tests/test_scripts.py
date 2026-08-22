from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
INIT_SCRIPT = SKILL_ROOT / "scripts" / "init_competition_workspace.py"
PREFLIGHT_SCRIPT = SKILL_ROOT / "scripts" / "preflight_submission.py"

def assemble_pdf(objects: tuple[bytes, ...]) -> bytes:
    content = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, body in enumerate(objects, start=1):
        offsets.append(len(content))
        content.extend(f"{number} 0 obj\n".encode("ascii"))
        content.extend(body)
        content.extend(b"\nendobj\n")
    xref_offset = len(content)
    content.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    content.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        content.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    content.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return bytes(content)


def build_minimal_pdf() -> bytes:
    return assemble_pdf(
        (
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 72 72] "
        b"/Resources << >> /Contents 4 0 R >>",
        b"<< /Length 0 >>\nstream\n\nendstream",
        )
    )


def build_text_pdf(text: str) -> bytes:
    stream = f"BT /F1 12 Tf 8 36 Td ({text}) Tj ET".encode("ascii")
    return assemble_pdf(
        (
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 72] "
            b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
            f"<< /Length {len(stream)} >>\nstream\n".encode("ascii")
            + stream
            + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        )
    )


MINIMAL_PDF = build_minimal_pdf()


def run_script(script: Path, *arguments: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *(str(argument) for argument in arguments)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


class InitWorkspaceTests(unittest.TestCase):
    def test_creates_expected_workspace_without_overwriting(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "team"
            result = run_script(INIT_SCRIPT, target, "--year", 2027)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((target / "PROJECT.md").is_file())
            self.assertTrue((target / "problem/rules/RULES.md").is_file())
            self.assertTrue((target / "logs/result-ledger.csv").is_file())
            self.assertIn("届次年份：2027", (target / "PROJECT.md").read_text())
            self.assertTrue((target / "PRIVATE_DATA.md").is_file())
            ignore_text = (target / ".gitignore").read_text(encoding="utf-8")
            self.assertIn("paper/", ignore_text)
            self.assertIn("logs/", ignore_text)

            project_before = (target / "PROJECT.md").read_bytes()
            merged = run_script(INIT_SCRIPT, target, "--merge", "--year", 2030)
            self.assertEqual(merged.returncode, 0, merged.stderr)
            self.assertEqual((target / "PROJECT.md").read_bytes(), project_before)

    def test_nonempty_target_requires_merge(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "team"
            target.mkdir()
            sentinel = target / "member-notes.txt"
            sentinel.write_text("keep", encoding="utf-8")

            result = run_script(INIT_SCRIPT, target)

            self.assertEqual(result.returncode, 2)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")
            self.assertFalse((target / "PROJECT.md").exists())

    def test_layout_conflict_is_detected_before_any_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "team"
            conflict = target / "logs/ai-use-log.csv"
            conflict.mkdir(parents=True)

            result = run_script(INIT_SCRIPT, target, "--merge")

            self.assertEqual(result.returncode, 2)
            self.assertIn("expected file", result.stderr)
            self.assertFalse((target / "PROJECT.md").exists())
            self.assertFalse((target / "problem").exists())
            self.assertFalse((target / "data").exists())

    def test_symlinked_parent_directory_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "team"
            outside = root / "outside"
            target.mkdir()
            outside.mkdir()
            (target / "problem").symlink_to(outside, target_is_directory=True)

            result = run_script(INIT_SCRIPT, target, "--merge")

            self.assertEqual(result.returncode, 2)
            self.assertIn("symbolic link", result.stderr)
            self.assertFalse((outside / "rules").exists())
            self.assertFalse((target / "PROJECT.md").exists())

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root bypasses modes")
    def test_io_failure_rolls_back_every_new_item(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "team"
            logs = target / "logs"
            logs.mkdir(parents=True)
            logs.chmod(0o555)
            try:
                result = run_script(INIT_SCRIPT, target, "--merge")
            finally:
                logs.chmod(0o755)

            self.assertEqual(result.returncode, 2)
            self.assertIn("rolled back new items", result.stderr)
            self.assertFalse((target / "PROJECT.md").exists())
            self.assertFalse((target / "problem").exists())
            self.assertFalse((target / "data").exists())
            self.assertEqual([path.name for path in target.iterdir()], ["logs"])


class PreflightTests(unittest.TestCase):
    def make_pdf(self, directory: Path, name: str = "paper.pdf") -> Path:
        paper = directory / name
        paper.write_bytes(MINIMAL_PDF)
        return paper

    def test_minimal_pdf_passes_and_writes_new_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paper = self.make_pdf(root)
            manifest = root / "hash-report.json"

            result = run_script(
                PREFLIGHT_SCRIPT,
                paper,
                "--expected-name",
                paper.name,
                "--manifest",
                manifest,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads(manifest.read_text(encoding="utf-8"))
            expected_status = "PASS" if shutil.which("pdfinfo") else "PASS_WITH_WARNINGS"
            self.assertEqual(report["status"], expected_status)
            self.assertEqual(report["paper"], paper.name)
            self.assertNotIn(str(root), manifest.read_text(encoding="utf-8"))
            self.assertEqual(report["paper_hashes"]["md5"], hashlib.md5(MINIMAL_PDF).hexdigest())

    def test_filename_and_exact_byte_limit_are_parameterized(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paper = self.make_pdf(root, "A123.pdf")
            exact = paper.stat().st_size

            passing = run_script(
                PREFLIGHT_SCRIPT,
                paper,
                "--expected-name",
                "A123.pdf",
                "--max-paper-bytes",
                exact,
            )
            too_small = run_script(
                PREFLIGHT_SCRIPT,
                paper,
                "--expected-name",
                "different.pdf",
                "--max-paper-bytes",
                exact - 1,
            )

            self.assertEqual(passing.returncode, 0, passing.stdout + passing.stderr)
            self.assertEqual(too_small.returncode, 1)
            self.assertIn("above", too_small.stdout)
            self.assertIn("expected 'different.pdf'", too_small.stdout)

    def test_attachment_limit_is_an_exact_byte_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paper = self.make_pdf(root)
            attachment = root / "result.bin"
            attachment.write_bytes(b"12345")

            passing = run_script(
                PREFLIGHT_SCRIPT,
                paper,
                "--attachment",
                attachment,
                "--max-attachment-bytes",
                5,
            )
            failing = run_script(
                PREFLIGHT_SCRIPT,
                paper,
                "--attachment",
                attachment,
                "--max-attachment-bytes",
                4,
            )

            self.assertEqual(passing.returncode, 0, passing.stdout + passing.stderr)
            self.assertEqual(failing.returncode, 1)
            self.assertIn("above 4 bytes", failing.stdout)

    def test_manifest_records_attachment_name_without_absolute_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paper = self.make_pdf(root)
            attachment = root / "result.bin"
            attachment.write_bytes(b"12345")
            manifest = root / "report.json"

            result = run_script(
                PREFLIGHT_SCRIPT,
                paper,
                "--attachment",
                attachment,
                "--manifest",
                manifest,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report_text = manifest.read_text(encoding="utf-8")
            report = json.loads(report_text)
            self.assertEqual(report["attachments"][0]["name"], attachment.name)
            self.assertNotIn(str(root), report_text)

    def test_invalid_numeric_limit_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            paper = self.make_pdf(Path(temporary))
            result = run_script(PREFLIGHT_SCRIPT, paper, "--max-paper-bytes", "nan")

            self.assertEqual(result.returncode, 2)
            self.assertIn("must be an integer", result.stderr)

    def test_identity_terms_require_rule_derived_start_page(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            paper = self.make_pdf(Path(temporary))
            result = run_script(PREFLIGHT_SCRIPT, paper, "--identity", "某大学")

            self.assertEqual(result.returncode, 1)
            self.assertIn("without --identity-start-page", result.stdout)

    def test_empty_identity_term_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            paper = self.make_pdf(Path(temporary))
            for value in ("", "   "):
                with self.subTest(value=repr(value)):
                    result = run_script(
                        PREFLIGHT_SCRIPT,
                        paper,
                        "--identity",
                        value,
                        "--identity-start-page",
                        1,
                    )
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("non-whitespace text", result.stderr)

    @unittest.skipUnless(
        shutil.which("pdfinfo") and shutil.which("pdftotext"),
        "Poppler is needed for identity redaction",
    )
    def test_identity_finding_records_index_not_private_term(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            private_term = "SECRET_IDENTITY"
            paper = root / "paper.pdf"
            paper.write_bytes(build_text_pdf(private_term))
            manifest = root / "report.json"

            result = run_script(
                PREFLIGHT_SCRIPT,
                paper,
                "--identity",
                private_term,
                "--identity-start-page",
                1,
                "--manifest",
                manifest,
            )

            self.assertEqual(result.returncode, 1)
            report_text = manifest.read_text(encoding="utf-8")
            self.assertNotIn(private_term, report_text)
            self.assertNotIn(private_term, result.stdout)
            self.assertIn("#1", report_text)

    def test_strict_mode_fails_when_warning_remains(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            paper = self.make_pdf(Path(temporary))

            result = run_script(
                PREFLIGHT_SCRIPT,
                paper,
                "--identity-start-page",
                1,
                "--strict",
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("FAIL_STRICT", result.stdout)
            self.assertIn("without any --identity terms", result.stdout)

    @unittest.skipUnless(shutil.which("pdfinfo"), "pdfinfo is needed for this check")
    def test_fake_pdf_signature_and_eof_do_not_pass_structure_check(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            paper = Path(temporary) / "fake.pdf"
            paper.write_bytes(b"%PDF-1.4\nnot a real PDF\n%%EOF\n")

            result = run_script(PREFLIGHT_SCRIPT, paper)

            self.assertEqual(result.returncode, 1)
            self.assertIn("could not parse the PDF structure", result.stdout)

    def test_recorded_md5_is_verified(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            paper = self.make_pdf(Path(temporary))
            recorded = hashlib.md5(MINIMAL_PDF).hexdigest()

            passing = run_script(PREFLIGHT_SCRIPT, paper, "--expected-md5", recorded)
            failing = run_script(PREFLIGHT_SCRIPT, paper, "--expected-md5", "0" * 32)

            self.assertEqual(passing.returncode, 0, passing.stdout + passing.stderr)
            self.assertEqual(failing.returncode, 1)
            self.assertIn("does not match recorded MD5", failing.stdout)

    def test_existing_manifest_is_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paper = self.make_pdf(root)
            manifest = root / "hash-report.json"
            manifest.write_bytes(b"keep this report")

            result = run_script(PREFLIGHT_SCRIPT, paper, "--manifest", manifest)

            self.assertEqual(result.returncode, 1)
            self.assertEqual(manifest.read_bytes(), b"keep this report")
            self.assertIn("not overwritten", result.stdout)

    def test_manifest_hard_link_cannot_overwrite_input_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paper = self.make_pdf(root)
            manifest = root / "hash-report.json"
            os.link(paper, manifest)
            paper_before = paper.read_bytes()
            inode_before = paper.stat().st_ino

            result = run_script(PREFLIGHT_SCRIPT, paper, "--manifest", manifest)

            self.assertEqual(result.returncode, 1)
            self.assertEqual(paper.read_bytes(), paper_before)
            self.assertEqual(manifest.read_bytes(), paper_before)
            self.assertEqual(paper.stat().st_ino, inode_before)
            self.assertEqual(manifest.stat().st_ino, inode_before)

    def test_symbolic_link_input_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paper = self.make_pdf(root)
            linked = root / "linked.pdf"
            linked.symlink_to(paper)

            result = run_script(PREFLIGHT_SCRIPT, linked)

            self.assertEqual(result.returncode, 1)
            self.assertIn("symbolic link", result.stdout)


if __name__ == "__main__":
    unittest.main()
