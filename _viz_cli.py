"""Shared helpers for the visualization producers and simulators.

Copied from ``autogalaxy_visualization/_viz_cli.py`` (itself from
``autolens_visualization`` / ``autolens_profiling/_profile_cli.py``) and adapted to this
repo's 1D toy datasets (``data.json`` / ``noise_map.json``, no instrument presets):

- ``repo_root()`` — walk up from any file to the directory holding ``ruff.toml``
  (the depth-proof repo-root sentinel), so scripts work from any nesting level.
- ``bootstrap_sys_path()`` — put the repo root and ``scripts/misc/`` on
  ``sys.path`` so ``_viz_cli`` / ``simulators`` import by name.
- ``dataset_path(name)`` — ``<root>/dataset/example_1d/<name>``.
- ``auto_simulate_if_missing(...)`` — shell out to
  ``scripts/misc/simulators/<simulator>.py`` when a dataset's ``data.json`` is absent.
- ``load_dataset(name)`` — ``(data, noise_map)`` numpy arrays of a tracked dataset.
- ``mirror_to_scratch(domains)`` — copy ``scripts/<domain>/images/`` PNGs to the opt-in
  ``$PYAUTO_EYES_SCRATCH/<lib>/<domain>/`` for on-the-fly review (no-op when unset);
  also ``python _viz_cli.py scratch [domain ...]``. ``gallery/gallery_run.sh`` calls it.

Typical use at the top of a producer::

    import sys
    from pathlib import Path

    for _p in Path(__file__).resolve().parents:
        if (_p / "ruff.toml").exists():
            sys.path.insert(0, str(_p))
            break
    from _viz_cli import auto_simulate_if_missing, dataset_path, load_dataset
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def repo_root(start: Path | None = None) -> Path:
    """Return the autofit_visualization root (the directory containing ``ruff.toml``)."""
    here = Path(start if start is not None else __file__).resolve()
    for p in [here, *here.parents]:
        if (p / "ruff.toml").exists():
            return p
    raise RuntimeError("autofit_visualization root (ruff.toml) not found")


def bootstrap_sys_path() -> Path:
    """Put the repo root and ``scripts/misc`` on ``sys.path``; return the root."""
    root = repo_root()
    for p in (root, root / "scripts" / "misc"):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    return root


def dataset_path(name: str) -> Path:
    """``<root>/dataset/example_1d/<name>``."""
    return repo_root() / "dataset" / "example_1d" / name


def auto_simulate_if_missing(
    dataset_dir: Path,
    *,
    simulator: str = "gaussian",
    workspace_root: Path | None = None,
) -> None:
    """If ``dataset_dir/data.json`` is missing, run the matching simulator script.

    ``simulator`` maps to ``scripts/misc/simulators/<simulator>.py``, which writes
    every dataset it knows (they are tiny). The gate is a plain ``data.json``
    existence check: the datasets are tracked in git so every figure is
    reproducible, and this hook never deletes or overwrites one.
    """
    if (Path(dataset_dir) / "data.json").exists():
        return

    root = workspace_root if workspace_root is not None else repo_root()
    simulator_script = root / "scripts" / "misc" / "simulators" / f"{simulator}.py"
    if not simulator_script.exists():
        raise FileNotFoundError(
            f"Auto-simulate could not find simulator script at {simulator_script}."
        )

    print(
        f"  [auto-simulate] {dataset_dir} missing; invoking scripts/misc/simulators/{simulator}.py"
    )
    subprocess.run(
        [sys.executable, str(simulator_script), "--output-root", str(root)],
        check=True,
    )


def load_dataset(name: str, workspace_root: Path | None = None):
    """``(data, noise_map)`` of ``dataset/example_1d/<name>``, simulating it if absent."""
    import autofit as af

    root = workspace_root if workspace_root is not None else repo_root()
    path = root / "dataset" / "example_1d" / name
    auto_simulate_if_missing(path, workspace_root=root)
    data = af.util.numpy_array_from_json(file_path=str(path / "data.json"))
    noise_map = af.util.numpy_array_from_json(file_path=str(path / "noise_map.json"))
    return data, noise_map


# The PyAutoEyes dashboard names this repo's section by its library import name, and the
# scratch mirror reuses that name: ``$PYAUTO_EYES_SCRATCH/<EYES_LIB>/<domain>/``.
EYES_LIB = "autofit"
EYES_SCRATCH_ENV = "PYAUTO_EYES_SCRATCH"


def mirror_to_scratch(domains: list[str] | None = None) -> Path | None:
    """Copy freshly rendered PNGs to the opt-in Eyes scratch folder; return its lib folder.

    For on-the-fly figure review before any PR or CI. When ``$PYAUTO_EYES_SCRATCH`` is
    unset this is a silent no-op returning ``None`` (so CI and other machines are
    untouched). Otherwise each domain's ``$PYAUTO_EYES_SCRATCH/<EYES_LIB>/<domain>/`` is
    deleted and refilled with every PNG under ``scripts/<domain>/images/`` (subpaths
    below ``images/`` kept), so no stale figure survives a re-render. ``domains=None``
    mirrors every domain that has an ``images/`` folder (``misc`` never does).
    """
    scratch = os.environ.get(EYES_SCRATCH_ENV)
    if not scratch:
        return None
    scripts = repo_root() / "scripts"
    if domains is None:
        domains = sorted(p.parent.name for p in scripts.glob("*/images") if p.parent.name != "misc")
    lib_dir = Path(scratch).expanduser() / EYES_LIB
    for domain in domains:
        images = scripts / domain / "images"
        if not images.is_dir():
            print(f"  [eyes-scratch] skip {domain}: no {images.relative_to(scripts.parent)}")
            continue
        dest = lib_dir / domain
        shutil.rmtree(dest, ignore_errors=True)
        pngs = sorted(images.rglob("*.png"))
        for png in pngs:
            target = dest / png.relative_to(images)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(png, target)
        print(f"  [eyes-scratch] {len(pngs)} PNGs -> {dest}")
    return lib_dir


if __name__ == "__main__":
    # ``python _viz_cli.py scratch [domain ...]`` — mirror rendered PNGs to the Eyes scratch.
    if len(sys.argv) < 2 or sys.argv[1] != "scratch":
        sys.exit("usage: python _viz_cli.py scratch [domain ...]")
    if mirror_to_scratch(sys.argv[2:] or None) is None:
        print(f"  [eyes-scratch] ${EYES_SCRATCH_ENV} is unset; nothing mirrored")
