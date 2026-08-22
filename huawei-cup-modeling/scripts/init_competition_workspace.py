#!/usr/bin/env python3
"""Create a non-destructive workspace for a modeling competition team."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path
import sys


DIRECTORIES = (
    "problem",
    "problem/rules",
    "data",
    "data/raw",
    "data/processed",
    "src",
    "experiments",
    "outputs",
    "outputs/figures",
    "outputs/tables",
    "paper",
    "references",
    "submission",
    "logs",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a reproducible competition workspace without overwriting files."
    )
    parser.add_argument("target", type=Path, help="Directory to create")
    parser.add_argument("--title", default="华为杯数学建模竞赛项目")
    parser.add_argument("--contest", default="中国研究生数学建模竞赛")
    parser.add_argument(
        "--year",
        type=int,
        default=datetime.now().year,
        help="Competition year; defaults to the current calendar year",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Add missing items to an existing directory; never overwrite files",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show planned changes without writing"
    )
    return parser.parse_args()


def project_markdown(title: str, contest: str, year: int) -> str:
    created = datetime.now().astimezone().isoformat(timespec="seconds")
    return f"""# {title}

- 赛事：{contest}
- 届次年份：{year}
- 创建时间：{created}
- 当届规则快照：`problem/rules/`
- 当前阶段：赛前准备

## 复现入口

记录从原始数据生成核心表格、图和论文结果的命令。

## 当前决策

记录下一次阶段门、负责人和内部截止时间。
"""


TEXT_FILES = {
    ".gitignore": """# Competition materials are private by default.
# Review and de-identify files before publishing anything from this workspace.
problem/
data/
src/
experiments/
outputs/
paper/
references/
submission/
logs/
""",
    "PRIVATE_DATA.md": """# 竞赛材料隐私提示

本工作区默认包含赛题、数据、代码、论文、身份信息、AI 使用记录和提交哈希。
不要在正式比赛期间把这些目录同步到公开仓库、公共问答、在线查重或公开文件服务。

根目录 `.gitignore` 默认忽略全部竞赛材料目录，但忽略规则不是访问控制。
使用受控存储，按当届规则处理材料；赛后公开前逐项检查授权、匿名、赛事纪律和第三方版权。
预检清单仍包含文件名、大小、修改时间和哈希，不应在比赛期间公开。
""",
    "problem/rules/RULES.md": """# 当届规则登记

只登记官方文件。每项包含标题、发布日期、下载时间、来源链接、文件哈希和核验人。
尚未确认的年度规则必须标记为待确认，不用往届规则填充。
""",
    "logs/decision-log.md": """# 决策记录

每项记录日期、决策、候选方案、证据、风险、回退方案和负责人。
""",
    "submission/preflight.md": """# 提交前人工清单

- [ ] 已下载并核对当届开赛公告、模板和 AI 规定
- [ ] 全部子问题有直接答案
- [ ] 关键结果已由第二人复现或复核
- [ ] 摘要、正文、图表和附件数字一致
- [ ] 引用、程序来源和 AI 使用已按当届规则披露
- [ ] 已逐页检查匿名信息、字体、公式、图像和分页
- [ ] 题号、队号、文件名、附件和大小符合当届公告
- [ ] 两人共同核对最终 PDF 与 MD5
- [ ] 提交 MD5 后未再修改或重导出 PDF
- [ ] 已确认系统提交成功并保存记录
""",
}


CSV_FILES = {
    "logs/source-log.csv": [
        "source_id",
        "type",
        "author_or_owner",
        "title",
        "url_or_path",
        "version_or_date",
        "accessed_at",
        "sha256",
        "used_for",
        "verified_by",
    ],
    "logs/ai-use-log.csv": [
        "timestamp",
        "tool",
        "model_or_version",
        "provider",
        "purpose",
        "input_summary",
        "output_used",
        "human_processing_and_validation",
        "related_artifact",
    ],
    "logs/result-ledger.csv": [
        "claim_id",
        "question_part",
        "claim",
        "metric_and_unit",
        "source_script",
        "source_output",
        "run_id",
        "validation",
        "reviewer",
        "status",
    ],
    "logs/data-manifest.csv": [
        "data_id",
        "path",
        "source",
        "version_or_downloaded_at",
        "sha256",
        "license_or_permission",
        "processing_script",
        "verified_by",
    ],
    "logs/experiment-ledger.csv": [
        "run_id",
        "timestamp",
        "question_part",
        "hypothesis",
        "code_version",
        "data_version",
        "command",
        "random_seed",
        "parameters",
        "output_path",
        "metric",
        "status",
        "reviewer",
    ],
}


def directory_is_nonempty(path: Path) -> bool:
    return path.exists() and any(path.iterdir())


def validate_layout(
    target: Path, directories: tuple[str, ...], files: tuple[str, ...]
) -> list[str]:
    errors: list[str] = []
    for relative in directories:
        path = target / relative
        if path.is_symlink():
            errors.append(f"expected directory is a symbolic link: {path}")
        elif path.exists() and not path.is_dir():
            errors.append(f"expected directory but found another type: {path}")
    for relative in files:
        path = target / relative
        if path.is_symlink():
            errors.append(f"expected file is a symbolic link: {path}")
        elif path.exists() and not path.is_file():
            errors.append(f"expected file but found another type: {path}")
    return errors


def write_new_text(
    path: Path, content: str, dry_run: bool, created_paths: list[Path]
) -> str:
    if path.exists():
        return "kept"
    if not dry_run:
        with path.open("x", encoding="utf-8") as handle:
            created_paths.append(path)
            handle.write(content)
    return "created"


def write_new_csv(
    path: Path, header: list[str], dry_run: bool, created_paths: list[Path]
) -> str:
    if path.exists():
        return "kept"
    if not dry_run:
        with path.open("x", encoding="utf-8", newline="") as handle:
            created_paths.append(path)
            csv.writer(handle).writerow(header)
    return "created"


def missing_directory_chain(path: Path) -> list[Path]:
    missing: list[Path] = []
    current = path
    while not current.exists() and current != current.parent:
        missing.append(current)
        current = current.parent
    return list(reversed(missing))


def rollback_created(files: list[Path], directories: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in reversed(files):
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            errors.append(f"could not remove created file {path}: {exc}")
    for path in reversed(directories):
        try:
            path.rmdir()
        except FileNotFoundError:
            continue
        except OSError as exc:
            errors.append(f"could not remove created directory {path}: {exc}")
    return errors


def main() -> int:
    args = parse_args()
    raw_target = args.target.expanduser()
    if raw_target.is_symlink():
        print(f"ERROR: target is a symbolic link: {raw_target}", file=sys.stderr)
        return 2
    target = raw_target.resolve()

    if target == Path(target.anchor):
        print(f"ERROR: refusing to initialize a filesystem root: {target}", file=sys.stderr)
        return 2
    if target.exists() and not target.is_dir():
        print(f"ERROR: target exists and is not a directory: {target}", file=sys.stderr)
        return 2
    if directory_is_nonempty(target) and not args.merge:
        print("ERROR: target is non-empty; use --merge to add only missing items", file=sys.stderr)
        return 2

    text_files = dict(TEXT_FILES)
    text_files["PROJECT.md"] = project_markdown(args.title, args.contest, args.year)
    planned_files = tuple(text_files) + tuple(CSV_FILES)
    layout_errors = validate_layout(target, DIRECTORIES, planned_files)
    if layout_errors:
        for error in layout_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2

    created_dirs: list[str] = []
    existing_dirs: list[str] = []
    created_directory_paths: list[Path] = []
    created_file_paths: list[Path] = []
    created_files: list[str] = []
    kept_files: list[str] = []
    try:
        if not args.dry_run:
            for path in missing_directory_chain(target):
                path.mkdir()
                created_directory_paths.append(path)

        for relative in DIRECTORIES:
            path = target / relative
            if path.exists():
                if not path.is_dir():
                    raise OSError(f"expected directory but found another type: {path}")
                existing_dirs.append(relative)
            else:
                created_dirs.append(relative)
                if not args.dry_run:
                    path.mkdir()
                    created_directory_paths.append(path)

        for relative, content in text_files.items():
            status = write_new_text(
                target / relative, content, args.dry_run, created_file_paths
            )
            (created_files if status == "created" else kept_files).append(relative)
        for relative, header in CSV_FILES.items():
            status = write_new_csv(
                target / relative, header, args.dry_run, created_file_paths
            )
            (created_files if status == "created" else kept_files).append(relative)
    except OSError as exc:
        cleanup_errors = rollback_created(
            created_file_paths, created_directory_paths
        )
        print(f"ERROR: initialization failed; rolled back new items: {exc}", file=sys.stderr)
        for error in cleanup_errors:
            print(f"ERROR: rollback incomplete: {error}", file=sys.stderr)
        return 2

    prefix = "DRY RUN" if args.dry_run else "DONE"
    print(f"{prefix}: {target}")
    print(f"directories created={len(created_dirs)} existing={len(existing_dirs)}")
    print(f"files created={len(created_files)} kept={len(kept_files)}")
    for relative in created_files:
        print(f"  create {relative}")
    for relative in kept_files:
        print(f"  keep   {relative}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
