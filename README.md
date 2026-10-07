# autofit_visualization

**[Browse the gallery → GALLERY.md](GALLERY.md)**

The permanent, rendered gallery of every figure PyAutoFit draws for a model-fit — the
**fit visualization project repo** of the PyAutoLabs organism.

This repo owns the PyAutoFit figures: the producer scripts, the 1D toy datasets and their
simulator, the all-on [`config/`](config/) (every search plot, the model figure and the EP
factor-search visuals switched on), the tracked PNGs, [`GALLERY.md`](GALLERY.md) and the render
harness. The organ [PyAutoEyes](https://github.com/PyAutoLabs/PyAutoEyes) is the cross-project
visualization dashboard: it reads this repo's tracked figure manifest
([`gallery/viz_manifest.yaml`](gallery/viz_manifest.yaml)) and links to the PNGs here — it never
renders or copies them. It is the sibling of
[autolens_visualization](https://github.com/PyAutoLabs/autolens_visualization) and
[autogalaxy_visualization](https://github.com/PyAutoLabs/autogalaxy_visualization), in the same
shape.

## Vision

Until now, the only way to see what a PyAutoFit figure looks like was to run a fit and open its
`output/` folder. This repo keeps the most up-to-date rendering of every figure PyAutoFit itself
draws in git, so there is one place to see every figure, judge it, and improve it (by hand or in
an AI chat pointed at the plotting source) without re-running anything:

- **samples** — the search plots drawn from a fit's `Samples`: `corner_anesthetic` and
  `corner_cornerpy` for two nested samplers (DynestyStatic, Nautilus) and two MCMC samplers
  (Emcee, Zeus); the six MLE traces of LBFGS (`subplot_parameters` and
  `log_likelihood_vs_iteration`, each plain / log-y / last-50-percent); the
  `figure_of_merit_vs_iteration` trace of the JAX multi-start gradient search MultiStartAdam.
- **model** — `af.ModelPlotter` model figures (the `model.png` beside `model.info`) for a single
  Gaussian, a collection, a linked model (a shared prior and a fixed parameter) and an EP
  factor graph's global model, each by names and by priors, collapsed and not.
- **ep** — an expectation-propagation fit over three datasets: `graph.png`,
  `graph_factors.png`, `graph_model.png`, `graph_state.png`, `mean_field_evolution.png`, the
  `af.EPPlotter` views with prior factors, and each factor search's own figures.
- **visualizer** — what the `af.ex` example `Analysis`'s `VisualizerExample` writes
  (`data.png`, `model_fit.png`) plus the search's `model.png`: the template every user's own
  visualizer starts from.

Every figure is a real render from a real (small) fit to this repo's 1D Gaussian datasets
(`dataset/example_1d/`). Unlike the lens and galaxy siblings there is no `instruments/`
directory: the data are 100-pixel 1D toy profiles, not telescope images, so there is no
instrument to preset.

## Render locally

```bash
source activate.sh                  # PyAutoNerves + PyAutoFit checkouts on PYTHONPATH (see the file)
bash gallery/gallery_run.sh --all   # run every producer, rebuild GALLERY.md + manifest, --check
```

Or one domain: `python scripts/samples/visualization.py`, then `python gallery/gallery_build.py`.
Commit the regenerated PNGs under `scripts/<domain>/images/` together with `GALLERY.md` and
`gallery/viz_manifest.yaml` (every figure's producer, domain, source type, path, byte size and
sha256, plus the autofit version it was rendered with). On every PyAutoFit release,
[`render.yml`](.github/workflows/render.yml) re-renders with the released stack, commits the
result and pings PyAutoEyes (`repository_dispatch: eyes-refresh`) to refresh its dashboard.

Runtime on an 8-core laptop (CPU): `model` ~3 s (no fit), `visualizer` ~10 s, `samples`
~1.5-2.5 min (six fits; Nautilus is the slowest at 30-60 s), `ep` ~0.5-2.5 min (up to five EP
sweeps of three dynesty factor fits, stopping early once the KL tolerance is met) — 2-5 min
for `--all` (measured 2m12s and 5m01s). The fits are real, so the samplers' randomness means a re-render changes
PNG bytes even when nothing else changed.

## Add a domain

- Add a dataset to [`scripts/misc/simulators/gaussian.py`](scripts/misc/simulators/gaussian.py)
  (or a new simulator) and track it under `dataset/example_1d/<name>/`.
- Add a flat producer `scripts/<domain>/visualization.py` modelled on
  [`scripts/samples/visualization.py`](scripts/samples/visualization.py).
- Run `bash gallery/gallery_run.sh --all` and commit the PNGs + `GALLERY.md` +
  `gallery/viz_manifest.yaml`.

## Improve a figure

Three edit surfaces, from cheapest to deepest:

- **Config** — [`config/`](config/): `visualize/plots_search.yaml` (which search plots a fit
  writes), `output.yaml` `model_figure`, `general.yaml` `visualize_ep_factor_searches`.
- **Plot API** — the plotting code in PyAutoFit: `autofit/non_linear/plot/` (corner and MLE
  plots), `autofit/model_figure/` (model and EP graph figures),
  `autofit/graphical/expectation_propagation/` (`graph.png`, `graph_factors.png`,
  `mean_field_evolution.png`), `autofit/example/visualize.py` (the example visualizer). Change
  it there (normal library workflow), then re-render here.
- **Script** — the producer in `scripts/<domain>/visualization.py` (dataset, model, search).

The Brain Eyes agent runs the review loop on this repo:
`bin/pyauto-brain eyes survey fit/autofit_visualization` (or `/eyes review fit`). Accepted
critiques are filed with the `eyes-critique` label.

## Related repos

- [PyAutoEyes](https://github.com/PyAutoLabs/PyAutoEyes) — the organ: the cross-project
  visualization dashboard that aggregates this repo (reads `gallery/viz_manifest.yaml`, links to
  the PNGs here).
- [autogalaxy_visualization](https://github.com/PyAutoLabs/autogalaxy_visualization) — the galaxy
  sibling this repo was copied from (harness, builder, workflows).
- [autolens_visualization](https://github.com/PyAutoLabs/autolens_visualization) — the lens
  sibling.
- [autofit_workspace](https://github.com/PyAutoLabs/autofit_workspace) — user-facing scripts and
  tutorials; the source of the datasets' recipe, the EP example and the config.

## Community & Contributing

**PyAutoFit** is built in the open by its users: everyone is welcome to ask questions,
share what they have made with it, and contribute.

Questions, ideas and bug reports: the [PyAutoLabs Discussions](https://github.com/orgs/PyAutoLabs/discussions).
Chat with us on [Slack](https://join.slack.com/t/pyautolens/shared_invite/zt-2cufp4eyf-fXfgMxRGuvg~bMrI3uOAxg).

Community-built tools and tutorials, and how to contribute: the [**PyAutoFit** community page](https://pyautofit.readthedocs.io/en/latest/general/community.html).
