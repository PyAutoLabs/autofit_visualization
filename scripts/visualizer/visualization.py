"""
Visualization: Example Visualizer
=================================

Renders the figures the ``af.ex`` example ``Analysis``'s visualizer
(``VisualizerExample``, ``autofit/example/visualize.py``) writes to a fit's ``image/``
folder, plus the ``model.png`` model figure the search writes beside ``model.info``,
from one REAL quick ``DynestyStatic`` fit of a single Gaussian to
``dataset/example_1d/gaussian_x1``. ``VisualizerExample`` is the template every
PyAutoFit user copies when writing their own visualizer, so what it draws is what a new
user's first fit shows them.

Output tree (wiped at the start of every run so stale PNGs never linger)::

    scripts/visualizer/images/visualization/
        data.png        VisualizerExample.visualize_before_fit  (the 1D data + errors)
        model_fit.png   VisualizerExample.visualize             (max-likelihood fit)
        model.png       the search's model figure (``output.yaml`` -> ``model_figure``)

The fit's scratch output is the gitignored ``output/visualization/visualizer/``; the
figures are copied out of it.

Run from the repo root::

    python scripts/visualizer/visualization.py
"""

import shutil
import sys
import time
from pathlib import Path


def _repo_root() -> Path:
    for _p in Path(__file__).resolve().parents:
        if (_p / "ruff.toml").exists():
            return _p
    raise RuntimeError("autofit_visualization root (ruff.toml) not found")


REPO_ROOT = _repo_root()
sys.path.insert(0, str(REPO_ROOT))

DOMAIN = "visualizer"
image_path = REPO_ROOT / "scripts" / DOMAIN / "images" / "visualization"
scratch_root = REPO_ROOT / "output" / "visualization" / DOMAIN

from autonerves import conf

conf.instance.push(new_path=str(REPO_ROOT / "config"), output_path=str(scratch_root))

import matplotlib

matplotlib.use("Agg")

import autofit as af

from _viz_cli import load_dataset

if image_path.exists():
    shutil.rmtree(image_path)
image_path.mkdir(parents=True)
if scratch_root.exists():
    shutil.rmtree(scratch_root)

data, noise_map = load_dataset("gaussian_x1")

model = af.Model(af.ex.Gaussian)
analysis = af.ex.Analysis(data=data, noise_map=noise_map)
search = af.DynestyStatic(name="visualizer", nlive=50, sample="rwalk")

t0 = time.perf_counter()
search.fit(model=model, analysis=analysis)
print(f"fit [visualizer]: {time.perf_counter() - t0:.1f}s")

run_root = scratch_root / "visualizer"
expected = []
for rel in ("image/data.png", "image/model_fit.png", "model.png"):
    name = Path(rel).name
    found = sorted(p for p in run_root.rglob(name) if p.as_posix().endswith(rel))
    if found:
        shutil.copy2(found[0], image_path / name)
    expected.append(image_path / name)

missing = [p.relative_to(REPO_ROOT).as_posix() for p in expected if not p.is_file()]
n_png = len(list(image_path.rglob("*.png")))
print(f"Wrote {n_png} PNGs under {image_path.relative_to(REPO_ROOT)}")
if missing:
    print("MISSING:", *missing, sep="\n  ")
    sys.exit(1)
