"""Integration benchmark: measure size reduction on real PyPI wheels.

Run with: uv run pytest -m benchmark -v
Skipped by default in normal test runs.
"""

from __future__ import annotations

import dataclasses
import os
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass, fields
from pathlib import Path

import pytest

from wheel_optimizer.config import OptimizerConfig
from wheel_optimizer.pipeline import OptimizerPipeline

BENCHMARK_WHEELS: list[dict[str, str]] = [
    {"spec": "attrs>=25", "import_name": "attr"},
    {"spec": "rich>=14", "import_name": "rich"},
    {"spec": "beautifulsoup4>=4.13", "import_name": "bs4"},
    {"spec": "markupsafe>=3", "import_name": "markupsafe"},
    {"spec": "charset-normalizer>=3.4", "import_name": "charset_normalizer"},
    {"spec": "certifi>=2025", "import_name": "certifi"},
    {"spec": "jinja2>=3.1", "import_name": "jinja2"},
    {"spec": "packaging>=25", "import_name": "packaging"},
    {"spec": "pygments>=2.19", "import_name": "pygments"},
    {"spec": "idna>=3.10", "import_name": "idna"},
    {"spec": "numpy>=2.2", "import_name": "numpy"},
    {"spec": "pandas>=2.2", "import_name": "pandas"},
    {"spec": "scipy>=1.15", "import_name": "scipy"},
    {"spec": "python-dateutil>=2.9", "import_name": "dateutil"},
    {"spec": "pytz>=2025.1", "import_name": "pytz"},
    {"spec": "six>=1.17", "import_name": "six"},
    {"spec": "tzdata>=2025.1", "import_name": "tzdata"},
]

_OPTIMIZER_FIELDS = [
    f.name
    for f in fields(OptimizerConfig)
    if f.name not in ("disable_all", "compile_pyc")
]


@dataclass
class WheelResult:
    name: str
    original_bytes: int
    combined_bytes: int
    per_optimizer: dict[str, int]
    import_ok: bool

    @property
    def saved_bytes(self) -> int:
        return self.original_bytes - self.combined_bytes

    @property
    def saved_pct(self) -> float:
        if self.original_bytes == 0:
            return 0.0
        return (self.saved_bytes / self.original_bytes) * 100


def _dir_size(path: Path) -> int:
    total = 0
    for f in path.rglob("*"):
        if f.is_file():
            total += f.stat().st_size
    return total


def _format_bytes(n: int) -> str:
    if n >= 1024 * 1024:
        return f"{n / (1024 * 1024):.1f} MB"
    if n >= 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n} B"


def _download_wheel(spec: str, dest: Path) -> Path:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "download",
            "--no-deps",
            "--only-binary",
            ":all:",
            "--dest",
            str(dest),
            spec,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(f"pip download {spec} failed:\n{result.stderr}")
    wheels = list(dest.glob("*.whl"))
    assert len(wheels) == 1, f"Expected 1 wheel for {spec}, got {len(wheels)}"
    return wheels[0]


def _unpack_wheel(whl: Path, dest: Path) -> Path:
    with zipfile.ZipFile(whl) as zf:
        zf.extractall(dest)
    return dest


def _try_import(
    wheel_dir: Path, import_name: str, extra_paths: list[Path] | None = None
) -> bool:
    paths = [str(wheel_dir)]
    if extra_paths:
        paths.extend(str(p) for p in extra_paths if p != wheel_dir)

    code = f"import sys; sys.path[:0] = {paths!r}; import {import_name}"
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(f"Import {import_name} failed: {result.stderr.strip()}")
    return result.returncode == 0


def _run_single_optimizer(source_dir: Path, work_dir: Path, opt_name: str) -> int:
    if work_dir.exists():
        shutil.rmtree(work_dir)
    shutil.copytree(source_dir, work_dir)

    config = OptimizerConfig(**{opt_name: True})
    OptimizerPipeline(config).run(work_dir)
    return _dir_size(work_dir)


def _generate_markdown(results: list[WheelResult]) -> str:
    opt_names = _OPTIMIZER_FIELDS

    header = "| Wheel | Original | All Combined | Saved | % |"
    for name in opt_names:
        header += f" {name} |"
    header += " Import |"

    sep = "|-------|----------|--------------|-------|---|"
    for _ in opt_names:
        sep += "---|"
    sep += "--------|"

    lines = ["## Wheel Optimizer Benchmark Results", "", header, sep]

    total_original = 0
    total_combined = 0
    total_per_opt = {n: 0 for n in opt_names}  # noqa: C420

    for r in results:
        total_original += r.original_bytes
        total_combined += r.combined_bytes
        import_status = "pass" if r.import_ok else "FAIL"

        row = (
            f"| {r.name} "
            f"| {_format_bytes(r.original_bytes)} "
            f"| {_format_bytes(r.combined_bytes)} "
            f"| {_format_bytes(r.saved_bytes)} "
            f"| {r.saved_pct:.1f}% "
        )
        for name in opt_names:
            saved = r.per_optimizer.get(name, 0)
            total_per_opt[name] += saved
            row += f"| {_format_bytes(saved)} " if saved > 0 else "| - "
        row += f"| {import_status} |"
        lines.append(row)

    total_saved = total_original - total_combined
    total_pct = (total_saved / total_original * 100) if total_original else 0
    total_row = (
        f"| **Total** "
        f"| **{_format_bytes(total_original)}** "
        f"| **{_format_bytes(total_combined)}** "
        f"| **{_format_bytes(total_saved)}** "
        f"| **{total_pct:.1f}%** "
    )
    for name in opt_names:
        s = total_per_opt[name]
        total_row += f"| **{_format_bytes(s)}** " if s > 0 else "| - "
    total_row += "| |"
    lines.append(total_row)

    lines.append("")
    lines.append(
        "Config: all optimizers enabled except `compile_pyc` "
        "(to keep `.py` files importable for verification)"
    )

    return "\n".join(lines)


@pytest.mark.benchmark
def test_benchmark(tmp_path: Path) -> None:
    optimized_dirs: list[Path] = []
    wheel_results: list[WheelResult] = []
    opt_names = _OPTIMIZER_FIELDS

    for wheel_info in BENCHMARK_WHEELS:
        spec = wheel_info["spec"]
        import_name = wheel_info["import_name"]
        name = spec.split(">=")[0].split("==")[0]

        download_dir = tmp_path / "downloads" / name
        download_dir.mkdir(parents=True)
        whl = _download_wheel(spec, download_dir)

        original_dir = tmp_path / "original" / name
        original_dir.mkdir(parents=True)
        _unpack_wheel(whl, original_dir)
        original_size = _dir_size(original_dir)

        per_optimizer: dict[str, int] = {}
        for opt_name in opt_names:
            work_dir = tmp_path / "single" / name / opt_name
            after_size = _run_single_optimizer(original_dir, work_dir, opt_name)
            saved = original_size - after_size
            if saved > 0:
                per_optimizer[opt_name] = saved

        combined_dir = tmp_path / "optimized" / name
        shutil.copytree(original_dir, combined_dir)
        all_opts = {n: True for n in opt_names}  # noqa: C420
        all_config = OptimizerConfig(**all_opts)
        OptimizerPipeline(all_config).run(combined_dir)
        combined_size = _dir_size(combined_dir)

        optimized_dirs.append(combined_dir)
        wheel_results.append(
            WheelResult(
                name=name,
                original_bytes=original_size,
                combined_bytes=combined_size,
                per_optimizer=per_optimizer,
                import_ok=False,
            )
        )

        whl.unlink()

    for i, wr in enumerate(wheel_results):
        import_name = BENCHMARK_WHEELS[i]["import_name"]
        wr_mut = dataclasses.replace(
            wr,
            import_ok=_try_import(
                optimized_dirs[i], import_name, extra_paths=optimized_dirs
            ),
        )
        wheel_results[i] = wr_mut

    markdown = _generate_markdown(wheel_results)

    output_path = os.environ.get("BENCHMARK_OUTPUT")
    if output_path:
        Path(output_path).write_text(markdown)

    print("\n" + markdown)

    for r in wheel_results:
        assert r.import_ok, f"Import failed for {r.name} after optimization"

    total_saved = sum(r.saved_bytes for r in wheel_results)
    assert total_saved > 0, "Expected some size reduction across benchmark wheels"
