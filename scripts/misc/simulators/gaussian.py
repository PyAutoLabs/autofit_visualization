"""
Simulator: 1D Gaussian Datasets
===============================

Simulates the 1D Gaussian toy datasets every producer in this repo fits, and writes
``data.json``, ``noise_map.json`` and ``model.json`` into
``dataset/example_1d/<name>/`` (the dataset's own ``image.png`` the library helper
also draws is deleted: the gallery only tracks figures under ``scripts/``).

Ported from ``autofit_workspace/scripts/simulators/simulators.py`` (the ``Gaussian x1``
and ``Gaussian x1 (0/1/2)`` sections), with a fixed NumPy seed per dataset so the
tracked datasets are reproducible:

- ``gaussian_x1``   — ``centre=50, normalization=25, sigma=10`` (samples, model,
  visualizer producers).
- ``gaussian_x1_0`` / ``_1`` / ``_2`` — the same Gaussian with ``sigma`` = 1, 5, 10: the
  three datasets of the expectation-propagation (``ep``) producer, which share
  ``centre``.

100 pixels, signal-to-noise 25 (``af.ex.util`` defaults).

Usage
-----

    python scripts/misc/simulators/gaussian.py
"""

from pathlib import Path as _Path


def _repo_root() -> _Path:
    for _p in _Path(__file__).resolve().parents:
        if (_p / "ruff.toml").exists():
            return _p
    raise RuntimeError("autofit_visualization root (ruff.toml) not found")


_REPO_ROOT = _repo_root()

#: name -> (Gaussian kwargs, NumPy seed)
DATASETS = {
    "gaussian_x1": (dict(centre=50.0, normalization=25.0, sigma=10.0), 1),
    "gaussian_x1_0": (dict(centre=50.0, normalization=25.0, sigma=1.0), 2),
    "gaussian_x1_1": (dict(centre=50.0, normalization=25.0, sigma=5.0), 3),
    "gaussian_x1_2": (dict(centre=50.0, normalization=25.0, sigma=10.0), 4),
}


def simulate(output_root: _Path | None = None) -> list[_Path]:
    """Simulate every dataset in ``DATASETS``. Returns the dataset dirs."""
    import matplotlib

    matplotlib.use("Agg")
    import autofit as af
    import numpy as np

    root = output_root if output_root is not None else _REPO_ROOT
    written = []
    for name, (kwargs, seed) in DATASETS.items():
        dataset_path = root / "dataset" / "example_1d" / name
        dataset_path.mkdir(parents=True, exist_ok=True)
        np.random.seed(seed)
        af.ex.util.simulate_dataset_1d_via_gaussian_from(
            gaussian=af.ex.Gaussian(**kwargs), dataset_path=str(dataset_path)
        )
        (dataset_path / "image.png").unlink(missing_ok=True)
        print(f"  wrote {dataset_path}")
        written.append(dataset_path)
    return written


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--output-root",
        type=_Path,
        default=None,
        help="Override the repo root that holds dataset/ (default: inferred from this file).",
    )
    args = parser.parse_args()
    simulate(output_root=args.output_root)
