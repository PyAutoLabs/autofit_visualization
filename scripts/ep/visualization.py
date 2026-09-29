"""
Visualization: Expectation Propagation
======================================

Renders every figure an expectation-propagation (EP) fit of a PyAutoFit factor graph
writes, from a REAL small EP fit, so the most up-to-date version of each figure lives
in git and can be browsed on GitHub (``GALLERY.md``) without re-running the fit.

Ported from ``autofit_workspace/scripts/features/expectation_propagation.py``: three
1D Gaussian datasets (``dataset/example_1d/gaussian_x1_0/1/2``, sigma = 1, 5, 10) that
share ``centre=50``, one ``af.ex.Gaussian`` model per dataset with a single shared
``centre`` prior, one ``af.AnalysisFactor`` per dataset (each fitted by a small
``DynestyStatic``), swept by ``factor_graph.optimise`` for a few EP steps.

Output tree (wiped at the start of every run so stale PNGs never linger)::

    scripts/ep/images/visualization/
        graph.png           global evidence + KL divergence vs EP step   (EP optimiser)
        graph_factors.png   the same per factor                          (EP optimiser)
        graph_model.png     the factor graph's structure                 (EP optimiser,
        graph_state.png     the graph with the run painted on it          model_figure on)
        mean_field_evolution.png  each variable's mean-field mean/std vs EP step
        ep_plotter/         af.EPPlotter(...).figure(kind="model" | "state",
                            show_prior_factors=True) drawn directly
        factor_<i>/         each factor search's own visuals from the LAST EP step:
                            data.png, model_fit.png (VisualizerExample), corner_anesthetic.png
                            (the search plot) and model.png (the factor's model figure)
                            (``general.yaml`` -> ``visualize_ep_factor_searches: true``)

The run's scratch output tree is the gitignored ``output/visualization/ep/``; the
figures above are copied out of it (or drawn directly, for ``ep_plotter/``).

Runtime: up to 5 EP steps x 3 factors of a 100-live-point dynesty fit, the slowest producer
in this repo (see README.md).

Run from the repo root::

    python scripts/ep/visualization.py
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

DOMAIN = "ep"
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

TOTAL_DATASETS = 3

"""
__Model + Factors__

Priors are centred away from the truth (centre 35 vs 50), exactly as in the workspace
example, so the EP history has something to show.
"""
centre_shared_prior = af.GaussianPrior(mean=35.0, sigma=30.0)

search = af.DynestyStatic(nlive=100, sample="rwalk", walks=10)

analysis_factor_list = []
for i in range(TOTAL_DATASETS):
    model = af.Model(af.ex.Gaussian)
    model.centre = centre_shared_prior  # one object, shared by all datasets
    model.normalization = af.GaussianPrior(mean=15.0, sigma=10.0)
    model.sigma = af.GaussianPrior(mean=5.0, sigma=10.0)
    data, noise_map = load_dataset(f"gaussian_x1_{i}")
    analysis_factor_list.append(
        af.AnalysisFactor(
            prior_model=model,
            analysis=af.ex.Analysis(data=data, noise_map=noise_map),
            optimiser=search,
            name=f"dataset_{i}",
        )
    )

factor_graph = af.FactorGraphModel(*analysis_factor_list)

"""
__EP Fit__

``visualise_interval=1`` redraws graph.png / graph_factors.png / graph_state.png every
sweep, so the files on disk show the final sweep.
"""
t0 = time.perf_counter()
factor_graph_result = factor_graph.optimise(
    optimiser=af.LaplaceOptimiser(),
    paths=af.DirectoryPaths(name="expectation_propagation"),
    ep_history=af.EPHistory(kl_tol=0.05),
    max_steps=5,
    visualise_interval=1,
)
print(f"EP fit: {time.perf_counter() - t0:.1f}s")

"""
__Copy the EP optimiser's figures__

The optimiser writes graph*.png into its own output folder; each factor search writes
its own image/ folder under a per-factor subfolder. Locate them by name (the
identifier folders are hashes).
"""
run_root = scratch_root / "expectation_propagation"
expected = []
EP_FIGURES = (
    "graph.png",
    "graph_factors.png",
    "graph_model.png",
    "graph_state.png",
    "mean_field_evolution.png",
)
for name in EP_FIGURES:
    found = sorted(run_root.rglob(name))
    if found:
        shutil.copy2(found[0], image_path / name)
    expected.append(image_path / name)

# Each factor's search re-runs once per EP step as ``dataset_<i>/optimization_<n>/``;
# the gallery keeps the LAST step's figures.
FACTOR_FIGURES = (
    "image/data.png",
    "image/model_fit.png",
    "image/search/corner_anesthetic.png",
    "model.png",
)
for i in range(TOTAL_DATASETS):
    out = image_path / f"factor_{i}"
    out.mkdir(parents=True, exist_ok=True)
    steps = sorted(
        (p for p in run_root.rglob(f"dataset_{i}/optimization_*") if p.is_dir()),
        key=lambda p: int(p.name.rsplit("_", 1)[-1]),
    )
    for rel in FACTOR_FIGURES:
        name = Path(rel).name
        with_file = [s for s in steps if (s / rel).is_file()]
        if with_file:
            shutil.copy2(with_file[-1] / rel, out / name)
        expected.append(out / name)

"""
__EPPlotter__

Drawn directly with the prior factors shown as nodes of their own (the optimiser's own
graph_model.png / graph_state.png leave them off).
"""
plotter = af.EPPlotter(factor_graph_result.factor_graph, ep_history=factor_graph_result.ep_history)
for kind in ("model", "state"):
    filename = f"graph_{kind}_prior_factors"
    plotter.figure(
        path=image_path / "ep_plotter",
        filename=filename,
        format="png",
        kind=kind,
        show_prior_factors=True,
    )
    expected.append(image_path / "ep_plotter" / f"{filename}.png")

missing = [p.relative_to(REPO_ROOT).as_posix() for p in expected if not p.is_file()]
n_png = len(list(image_path.rglob("*.png")))
print(f"Wrote {n_png} PNGs under {image_path.relative_to(REPO_ROOT)}")
if missing:
    print("MISSING:", *missing, sep="\n  ")
    sys.exit(1)
