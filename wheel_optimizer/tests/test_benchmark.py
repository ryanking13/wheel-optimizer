"""Integration benchmark: measure size reduction on real PyPI wheels.

Run with: uv run pytest -m benchmark -v
Skipped by default in normal test runs.
"""

from __future__ import annotations

import importlib
import os
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
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
]

OPTIMIZER_CONFIG = OptimizerConfig(
    remove_docstrings=True,
    remove_type_annotations=True,
    remove_assertions=True,
    remove_comments=True,
    remove_tests=True,
    remove_typestubs=True,
    remove_pycache=True,
    remove_c_source=True,
    remove_cython_source=True,
)


@dataclass
class BenchmarkResult:
    name: str
    original_bytes: int
    optimized_bytes: int
    import_ok: bool

    @property
    def saved_bytes(self) -> int:
        return self.original_bytes - self.optimized_bytes

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


def _try_import(wheel_dir: Path, import_name: str) -> bool:
    pkg_dirs = [
        d
        for d in wheel_dir.iterdir()
        if d.is_dir() and not d.name.endswith(".dist-info")
    ]
    if not pkg_dirs:
        return False

    saved_path = sys.path[:]
    saved_modules = {
        k: v
        for k, v in sys.modules.items()
        if k == import_name or k.startswith(import_name + ".")
    }

    try:
        for k in saved_modules:
            del sys.modules[k]
        sys.path.insert(0, str(wheel_dir))
        importlib.import_module(import_name)
        return True
    except Exception:
        return False
    finally:
        sys.path[:] = saved_path
        for k in list(sys.modules):
            if k == import_name or k.startswith(import_name + "."):
                del sys.modules[k]
        sys.modules.update(saved_modules)


def _generate_markdown(results: list[BenchmarkResult]) -> str:
    lines = [
        "## Wheel Optimizer Benchmark Results",
        "",
        "| Wheel | Original | Optimized | Saved | % | Import |",
        "|-------|----------|-----------|-------|---|--------|",
    ]

    total_original = 0
    total_optimized = 0

    for r in results:
        total_original += r.original_bytes
        total_optimized += r.optimized_bytes
        import_status = "pass" if r.import_ok else "FAIL"
        lines.append(
            f"| {r.name} "
            f"| {_format_bytes(r.original_bytes)} "
            f"| {_format_bytes(r.optimized_bytes)} "
            f"| {_format_bytes(r.saved_bytes)} "
            f"| {r.saved_pct:.1f}% "
            f"| {import_status} |"
        )

    total_saved = total_original - total_optimized
    total_pct = (total_saved / total_original * 100) if total_original else 0
    lines.append(
        f"| **Total** "
        f"| **{_format_bytes(total_original)}** "
        f"| **{_format_bytes(total_optimized)}** "
        f"| **{_format_bytes(total_saved)}** "
        f"| **{total_pct:.1f}%** "
        f"| |"
    )

    lines.append("")
    lines.append(
        "Config: all optimizers enabled except `compile_pyc` "
        "(to keep `.py` files importable for verification)"
    )

    return "\n".join(lines)


@pytest.mark.benchmark
def test_benchmark(tmp_path: Path) -> None:
    results: list[BenchmarkResult] = []

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

        optimized_dir = tmp_path / "optimized" / name
        shutil.copytree(original_dir, optimized_dir)

        pipeline = OptimizerPipeline(OPTIMIZER_CONFIG)
        pipeline.run(optimized_dir)
        optimized_size = _dir_size(optimized_dir)

        import_ok = _try_import(optimized_dir, import_name)

        results.append(
            BenchmarkResult(
                name=name,
                original_bytes=original_size,
                optimized_bytes=optimized_size,
                import_ok=import_ok,
            )
        )

        whl.unlink()

    markdown = _generate_markdown(results)

    output_path = os.environ.get("BENCHMARK_OUTPUT")
    if output_path:
        Path(output_path).write_text(markdown)

    print("\n" + markdown)

    for r in results:
        assert r.import_ok, f"Import failed for {r.name} after optimization"

    total_saved = sum(r.saved_bytes for r in results)
    assert total_saved > 0, "Expected some size reduction across benchmark wheels"
