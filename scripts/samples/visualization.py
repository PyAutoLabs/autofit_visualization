"""
Visualization: Samples (Search Plots)
=====================================

Renders every figure PyAutoFit's search plotters draw from a fit's ``Samples`` — the
corner plots of nested samplers and MCMC, and the maximum-likelihood (MLE) traces of
the optimisers — from REAL, small fits of a single ``af.ex.Gaussian`` to
``dataset/example_1d/gaussian_x1``, so the most up-to-date version of each figure lives
in git and can be browsed on GitHub (``GALLERY.md``) without re-running a fit.

This script RENDERS, it does not test: there are no assertions on the posterior. Which
figures a search would write itself is governed by ``config/visualize/plots_search.yaml``
(every toggle on); here the ``autofit.non_linear.plot`` functions are called directly
on each fit's samples, so every variant is drawn with a distinct filename.

Output tree (wiped at the start of every run so stale PNGs never linger)::

    scripts/samples/images/visualization/
        dynesty_static/   corner_anesthetic.png, corner_cornerpy.png  (nested)
        nautilus/         corner_anesthetic.png, corner_cornerpy.png  (nested)
        emcee/            corner_anesthetic.png, corner_cornerpy.png  (MCMC)
        zeus/             corner_anesthetic.png, corner_cornerpy.png  (MCMC)
        lbfgs/            subplot_parameters{,_log_y,_last_50_percent}.png,
                          log_likelihood_vs_iteration{,_log_y,_last_50_percent}.png
        multistart_adam/  figure_of_merit_vs_iteration.png  (JAX multi-start gradient)

``corner_anesthetic`` is the nested-sampling corner (``plots_search.yaml`` -> ``nest``)
and ``corner_cornerpy`` the MCMC one (``mcmc``); both accept any weighted samples, so
both are drawn for all four samplers. The plot functions wrap their body in
``log_plot_exception`` (a failed corner is logged at INFO, not raised), so the script
checks every expected file exists and exits non-zero if one is missing.

The search's own scratch output (samples.csv, its own image/ folder, search_internal)
goes to the gitignored ``output/visualization/samples/``.

Run from the repo root::

    python scripts/samples/visualization.py
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

DOMAIN = "samples"
image_path = REPO_ROOT / "scripts" / DOMAIN / "images" / "visualization"
scratch_root = REPO_ROOT / "output" / "visualization" / DOMAIN

# Push the all-true config before any autofit code path reads it. The search output
# root is the gitignored scratch folder; figures are written with explicit paths.
from autonerves import conf

conf.instance.push(new_path=str(REPO_ROOT / "config"), output_path=str(scratch_root))

import matplotlib

matplotlib.use("Agg")

import autofit as af
from autofit.non_linear.plot import (
    corner_anesthetic,
    corner_cornerpy,
    figure_of_merit_vs_iteration,
    log_likelihood_vs_iteration,
    subplot_parameters,
)

from _viz_cli import load_dataset

if image_path.exists():
    shutil.rmtree(image_path)
image_path.mkdir(parents=True)
if scratch_root.exists():
    shutil.rmtree(scratch_root)

"""
__Dataset + Model__

One Gaussian (centre=50, normalization=25, sigma=10; 100 pixels, S/N 25) fitted with
the library's default priors for ``af.ex.Gaussian`` — three free parameters, so each
corner is a 3x3 triangle.
"""
data, noise_map = load_dataset("gaussian_x1")


def _fit(search, use_jax=False):
    model = af.Model(af.ex.Gaussian)
    analysis = af.ex.Analysis(data=data, noise_map=noise_map, use_jax=use_jax)
    t0 = time.perf_counter()
    result = search.fit(model=model, analysis=analysis)
    print(f"fit [{search.name}]: {time.perf_counter() - t0:.1f}s")
    return result.samples


"""
__Searches__

Deliberately small but real: every search converges on this 3-parameter problem in
seconds. The seeds / small live-point counts keep the renders quick and repeatable.
"""
SEARCHES = {
    "dynesty_static": lambda: af.DynestyStatic(name="dynesty_static", nlive=75, sample="rwalk"),
    "nautilus": lambda: af.Nautilus(name="nautilus", n_live=100, seed=1),
    "emcee": lambda: af.Emcee(name="emcee", nwalkers=30, nsteps=500),
    "zeus": lambda: af.Zeus(name="zeus", nwalkers=30, nsteps=500),
}

expected: list[Path] = []

for source, make_search in SEARCHES.items():
    samples = _fit(make_search())
    out = image_path / source
    corner_anesthetic(samples=samples, path=out, filename="corner_anesthetic", format="png")
    corner_cornerpy(samples=samples, path=out, filename="corner_cornerpy", format="png")
    expected += [out / "corner_anesthetic.png", out / "corner_cornerpy.png"]

"""
__MLE: LBFGS__

The six MLE trace variants: ``subplot_parameters`` and ``log_likelihood_vs_iteration``,
each plain, with ``use_log_y`` and with ``use_last_50_percent``. The functions append
``_log_y`` / ``_last_50_percent`` to the filename themselves, so the variants never
collide.
"""
samples = _fit(af.LBFGS(name="lbfgs"))
out = image_path / "lbfgs"
for func in (subplot_parameters, log_likelihood_vs_iteration):
    for suffix, kwargs in (
        ("", {}),
        ("_log_y", {"use_log_y": True}),
        ("_last_50_percent", {"use_last_50_percent": True}),
    ):
        func(samples=samples, path=out, filename=func.__name__, format="png", **kwargs)
        expected.append(out / f"{func.__name__}{suffix}.png")

"""
__MLE: MultiStartAdam (JAX)__

The multi-start gradient searches record the per-step global-best figure of merit
(``samples.samples_info["fom_history"]``), which ``figure_of_merit_vs_iteration``
draws. JAX is required (``use_jax=True`` on the analysis). ``learning_rate=0.3``
(default 0.01) lets the 16 starts reach the plateau and auto-converge in ~200 steps on
this unscaled problem, so the trace shows the stop the figure exists to inspect.
"""
samples = _fit(
    af.MultiStartAdam(name="multistart_adam", n_starts=16, n_steps=400, learning_rate=0.3, seed=1),
    use_jax=True,
)
out = image_path / "multistart_adam"
figure_of_merit_vs_iteration(
    samples=samples, path=out, filename="figure_of_merit_vs_iteration", format="png"
)
expected.append(out / "figure_of_merit_vs_iteration.png")

missing = [p.relative_to(REPO_ROOT).as_posix() for p in expected if not p.is_file()]
n_png = len(list(image_path.rglob("*.png")))
print(f"Wrote {n_png} PNGs under {image_path.relative_to(REPO_ROOT)}")
if missing:
    print("MISSING (a plot function swallowed its exception):")
    for m in missing:
        print(f"  {m}")
    sys.exit(1)
