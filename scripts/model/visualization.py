"""
Visualization: Model Figures
============================

Renders the model figure ``af.ModelPlotter(model).figure()`` draws — the map of which
``model.info`` is the legend, and the ``model.png`` a search writes beside
``model.info`` when ``output.yaml`` -> ``model_figure`` is on — for four model shapes,
each in several presentation variants, so the most up-to-date version of each figure
lives in git and can be browsed on GitHub (``GALLERY.md``).

No fit is run: a model figure depends only on the model's structure and priors.

Output tree (wiped at the start of every run so stale PNGs never linger)::

    scripts/model/images/visualization/
        gaussian/     one ``af.Model(af.ex.Gaussian)``
        collection/   ``af.Collection`` of two Gaussians
        linked/       two Gaussians sharing one ``centre`` prior, one ``sigma`` fixed
        graph/        the ``global_prior_model`` of the expectation-propagation factor
                      graph the ``ep`` producer fits (three Gaussians, shared centre)

Each source is drawn with ``detail="names"`` (``model_names.png``) and
``detail="priors"`` (``model_priors.png``); sources with repeated sibling components
add ``collapse=False`` (``model_names_uncollapsed.png``), and sources with a fixed
parameter add ``show_fixed=False`` (``model_names_hide_fixed.png``).

Run from the repo root::

    python scripts/model/visualization.py
"""

import shutil
import sys
from pathlib import Path


def _repo_root() -> Path:
    for _p in Path(__file__).resolve().parents:
        if (_p / "ruff.toml").exists():
            return _p
    raise RuntimeError("autofit_visualization root (ruff.toml) not found")


REPO_ROOT = _repo_root()
sys.path.insert(0, str(REPO_ROOT))

DOMAIN = "model"
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

"""
__Models__
"""
gaussian = af.Model(af.ex.Gaussian)

collection = af.Collection(gaussian_0=af.Model(af.ex.Gaussian), gaussian_1=af.Model(af.ex.Gaussian))

# ``linked``: the second Gaussian's centre IS the first one's prior (one free
# parameter, drawn as a link), and its sigma is fixed to a number.
linked_0 = af.Model(af.ex.Gaussian)
linked_1 = af.Model(af.ex.Gaussian)
linked_1.centre = linked_0.centre
linked_1.sigma = 5.0
linked = af.Collection(gaussian_0=linked_0, gaussian_1=linked_1)

# ``graph``: the EP recipe of scripts/ep/visualization.py — three datasets, one
# Gaussian each, all sharing a single centre prior.
centre_shared_prior = af.GaussianPrior(mean=35.0, sigma=30.0)
analysis_factor_list = []
for i in range(3):
    model = af.Model(af.ex.Gaussian)
    model.centre = centre_shared_prior
    model.normalization = af.GaussianPrior(mean=15.0, sigma=10.0)
    model.sigma = af.GaussianPrior(mean=5.0, sigma=10.0)
    data, noise_map = load_dataset(f"gaussian_x1_{i}")
    analysis_factor_list.append(
        af.AnalysisFactor(
            prior_model=model,
            analysis=af.ex.Analysis(data=data, noise_map=noise_map),
            name=f"dataset_{i}",
        )
    )
graph = af.FactorGraphModel(*analysis_factor_list).global_prior_model

"""
__Variants__

``(filename, figure kwargs)`` per source; the plate / fixed-parameter variants only
where the source has repeated siblings / a fixed parameter.
"""
BASE = [
    ("model_names", {"detail": "names"}),
    ("model_priors", {"detail": "priors"}),
]
UNCOLLAPSED = [("model_names_uncollapsed", {"detail": "names", "collapse": False})]
HIDE_FIXED = [("model_names_hide_fixed", {"detail": "names", "show_fixed": False})]

SOURCES = {
    "gaussian": (gaussian, BASE),
    "collection": (collection, BASE + UNCOLLAPSED),
    "linked": (linked, BASE + UNCOLLAPSED + HIDE_FIXED),
    "graph": (graph, BASE + UNCOLLAPSED),
}

expected = []
for source, (model, variants) in SOURCES.items():
    out = image_path / source
    for filename, kwargs in variants:
        af.ModelPlotter(model).figure(path=out, filename=filename, format="png", **kwargs)
        expected.append(out / f"{filename}.png")
    print(f"model [{source}]: {len(variants)} figures")

missing = [p.relative_to(REPO_ROOT).as_posix() for p in expected if not p.is_file()]
n_png = len(list(image_path.rglob("*.png")))
print(f"Wrote {n_png} PNGs under {image_path.relative_to(REPO_ROOT)}")
if missing:
    print("MISSING:", *missing, sep="\n  ")
    sys.exit(1)
