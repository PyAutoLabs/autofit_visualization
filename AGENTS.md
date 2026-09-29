# autofit_visualization — Agent Instructions

This repo is the single home for **what PyAutoFit figures look like**: it stores, in git, the
most up-to-date rendering of every figure PyAutoFit itself draws for a model-fit — search plots
(corner, MLE traces), model figures, expectation-propagation (EP) graph figures and the example
visualizer — rendered from real small fits to 1D toy Gaussian datasets, so visualization can be
judged and improved (by humans or AI chats against the source) without re-running a fit. It is a
collection of standalone producer scripts, **not** an installable package — there is no
`pyproject.toml`. These are the canonical, agent-agnostic instructions for this repo; the
`README.md` is the human-facing overview and `GALLERY.md` is the browsable gallery. It is the fit
sibling of `galaxy/autogalaxy_visualization` and `lens/autolens_visualization` and mirrors their
layout.

## Layering: project repo vs organ

This is a **project repo** (category `project`, like its lens and galaxy siblings): it makes,
stores and tracks the PyAutoFit figures — producers, simulator, datasets, the all-on config,
tracked PNGs, `GALLERY.md`, the render harness. The organ **PyAutoEyes** is the cross-project
visualization dashboard over the `<lib>_visualization` project repos: it reads this repo's
tracked `gallery/viz_manifest.yaml` and links to the PNGs here; it renders nothing and copies no
figures. Judging figures is the Brain's Eyes conductor; figure changes land here (producer /
config) or in PyAutoFit (plot API), never in the organ.

## Repository Structure

Producers are laid out **flat, one per domain** (`scripts/<domain>/visualization*.py`), because
the Brain Eyes agent scans `scripts/<domain>/*.py` non-recursively for stems containing
`visualization`:

```
scripts/
  samples/visualization.py          search plots from real fits of af.ex.Gaussian to gaussian_x1
  samples/images/visualization/     dynesty_static/ nautilus/ emcee/ zeus/ (corners),
                                    lbfgs/ (6 MLE traces), multistart_adam/ (FoM trace)
  model/visualization.py            af.ModelPlotter figures (no fit)
  model/images/visualization/       gaussian/ collection/ linked/ graph/
  ep/visualization.py               EP fit of 3 AnalysisFactors on gaussian_x1_0/1/2
  ep/images/visualization/          graph*.png + mean_field_evolution.png, ep_plotter/, factor_<i>/
  visualizer/visualization.py       one DynestyStatic fit with af.ex.Analysis (VisualizerExample)
  visualizer/images/visualization/  data.png, model_fit.png, model.png
  misc/simulators/gaussian.py       regenerates every dataset/example_1d/* (seeded)
  misc/test/                        hermetic pytest for the gallery builder
gallery/gallery_build.py            GALLERY.md + gallery/viz_manifest.yaml + output/gallery/
gallery/viz_manifest.yaml           TRACKED, generated figure manifest (PyAutoEyes read contract)
gallery/gallery_run.sh              run producers -> build -> --check
config/                             the autofit_workspace config with every figure switched on
dataset/example_1d/                 TRACKED: gaussian_x1, gaussian_x1_0/1/2 (data/noise_map/model .json)
_viz_cli.py                         repo-root finder, dataset paths/loader, auto-simulate hook
GALLERY.md                          TRACKED, generated — never edit by hand
```

**No `instruments/`.** The lens and galaxy siblings carry telescope presets; this repo's data are
100-pixel 1D toy profiles, so there is nothing to preset and the directory is deliberately absent.

**What is tracked.** PNG figures under `scripts/<domain>/images/**`, `GALLERY.md`,
`gallery/viz_manifest.yaml` and the datasets (JSON). The FITS / CSV / JSON data products are
gitignored, as is `output/` (every search's scratch output tree).

**Import model.** Producers find the repo root by walking up to the directory containing
`ruff.toml` (a depth-proof sentinel) and put it on `sys.path`, so `_viz_cli` imports by name.

## Rendering

From the repo root, with the library checkouts on `PYTHONPATH` (`source activate.sh`):

```bash
bash gallery/gallery_run.sh --all        # every producer, then build + --check (2-5 min)
python scripts/model/visualization.py    # one producer (~3 s)
python gallery/gallery_build.py          # rebuild GALLERY.md + gallery/viz_manifest.yaml + output/gallery/
python gallery/gallery_build.py --check  # fail if GALLERY.md or the manifest is stale vs the PNGs on disk
```

Each producer pushes `config/` via `conf.instance.push(new_path=config, output_path=output/visualization/<domain>)`
before any autofit code reads config — so every search's own output tree (samples.csv,
search_internal, its own `image/`) lands in the gitignored scratch folder — then wipes its
`scripts/<domain>/images/visualization/` tree, so the committed PNG set is exactly what the last
run produced. Figures reach `images/` in one of two ways: drawn directly with `path=` /
`format="png"` (the `autofit.non_linear.plot` functions, `af.ModelPlotter`, `af.EPPlotter`), or
copied out of the scratch fit output (EP's `graph*.png`, the per-factor and example-visualizer
`image/*.png`, `model.png`). Every producer lists the files it expects and **exits non-zero if
one is missing** — the corner functions are wrapped in `log_plot_exception`, which logs a failure
at INFO rather than raising, so a silent miss would otherwise ship a hole in the gallery. Commit
the PNGs, `GALLERY.md` and `gallery/viz_manifest.yaml` together.

The fits are real (and, apart from Nautilus / MultiStartAdam, unseeded), so a re-render changes
PNG bytes; that is expected and is why the manifest carries sha256s.

**The tracked manifest** (`gallery/viz_manifest.yaml`, schema 1) lists every committed PNG as
`{file, producer, domain, source, bytes, sha256}` (`source` = the per-source sub-folder —
the search name for `samples`, the model shape for `model`, `ep_plotter` / `factor_<i>` for `ep`
— or `""` for top-level figures), plus `rendered_with:` (the autofit version) and `generated:`
(the date the figures or stack last changed — carried over on an unchanged rebuild). There are no
mtimes. `--check` ignores only `generated:` and `rendered_with:`; any added, removed or
byte-changed PNG fails it. It is the read contract of the PyAutoEyes dashboard — change its shape
only together with the organ.

**Config switched on here** (all in `config/`, copied from `autofit_workspace/config`):
`visualize/plots_search.yaml` has every key true including the `mle:` section;
`output.yaml` `model_figure: true` (model.png, graph_model.png, graph_state.png);
`general.yaml` `output.force_visualize_overwrite: true`,
`output.visualize_ep_factor_searches: true` (per-factor figures in the `ep` domain) and
`version.workspace_version_check: false`.

**Known library behaviour visible in the gallery.** `corner_anesthetic` sets matplotlib's global
`font.size` from its config and never restores it, so figures drawn later in the same process
(e.g. the EP per-factor `data.png` / `model_fit.png` after a factor search's corner plot) render
with larger text than the same figure in `visualizer/`. The EP state figure shows the run's real
`BAD_PROJECTION` / reverted-update flags when a factor's projection fails.

**Datasets.** Produced by `python scripts/misc/simulators/gaussian.py` (the
`autofit_workspace/scripts/simulators/simulators.py` recipes with a fixed NumPy seed per dataset):
`gaussian_x1` (centre 50, normalization 25, sigma 10) and `gaussian_x1_0/1/2` (sigma 1, 5, 10,
shared centre 50 — the EP datasets). The auto-simulate hook in `_viz_cli.py` only fires when
`data.json` is absent — it never deletes a tracked dataset.

## Adding a domain

1. Add a dataset to `scripts/misc/simulators/gaussian.py` (or a new simulator) and track it
   under `dataset/example_1d/<name>/`.
2. Add a flat producer `scripts/<domain>/visualization.py` modelled on the samples one, writing
   to `scripts/<domain>/images/visualization/` and failing on a missing expected figure.
3. Run `bash gallery/gallery_run.sh --all` and commit the PNGs + `GALLERY.md` +
   `gallery/viz_manifest.yaml`.

## Improving a figure (edit surfaces)

- **config** — `config/visualize/plots_search.yaml`, `config/output.yaml` (`model_figure`),
  `config/general.yaml` (`visualize_ep_factor_searches`): which figures are written at all.
- **plot API** — PyAutoFit: `autofit/non_linear/plot/` (corner + MLE traces),
  `autofit/model_figure/` (ModelPlotter, EPPlotter), `autofit/graphical/expectation_propagation/`
  (`visualise.py`, `diagnostics.py`), `autofit/example/visualize.py` (library changes go through
  the normal library workflow, then this repo is re-rendered).
- **script** — the producer in `scripts/<domain>/visualization.py` (dataset, model, searches).

## Eyes contracts

Two readers depend on this repo's layout:

- **The Brain Eyes conductor** (`organs/PyAutoBrain/agents/conductors/eyes/`) reviews it:
  `bin/pyauto-brain eyes survey fit/autofit_visualization` (or `/eyes review fit`). It expects
  flat `scripts/<domain>/visualization*.py` producers writing `scripts/<domain>/images/<stem>/**`,
  a `gallery/gallery_run.sh` harness, and `output/gallery/{gallery.html,viz_manifest.yaml}` (the
  latter a gitignored copy of the tracked manifest). Its staleness flag is mtime-based (producer
  newer than its newest PNG), so re-render after editing a producer. Accepted critiques are
  labelled `eyes-critique` and route through intake / start_dev like any other change.
- **The PyAutoEyes dashboard** reads the tracked `gallery/viz_manifest.yaml` and links to the
  PNGs; `render.yml` fires `repository_dispatch: eyes-refresh` at PyAutoLabs/PyAutoEyes after
  each release re-render.

Keep that layout when adding domains.

## Testing

The PR gate is `lint.yml` on Python 3.12 against the library mains (PyAutoNerves, PyAutoFit —
installed with `[optional]` so the samplers, corner and anesthetic are present):

```bash
ruff check .
ruff format --check .
python gallery/gallery_build.py --check
pytest scripts/misc/test -q
```

plus `lychee` on every `*.md`, then every producer runs for real followed by
`gallery_build.py --check` (a PR that changes the figure set without regenerating `GALLERY.md`
fails; there is no pixel diff). `render.yml` (manual + `repository_dispatch: pyautofit-release`)
re-renders with the released PyPI stack, commits PNGs + `GALLERY.md` + `gallery/viz_manifest.yaml`
back as `github-actions[bot]` `[skip ci]`, then dispatches `eyes-refresh` to PyAutoEyes (token:
`secrets.PAT_PYAUTOLABS`; the step warns and skips when the secret is unavailable).

## Sandboxed / restricted runs

```bash
NUMBA_CACHE_DIR=/tmp/numba_cache MPLCONFIGDIR=/tmp/matplotlib python scripts/model/visualization.py
```

The session shell may pin `OMP_NUM_THREADS=1` etc.; export 8 for a representative render time.

## Bulk-edit safety

When editing the same region across many scripts in one pass, only rewrite the targeted region.
**Never produce a whole-file write unless you have read the entire current file.**

## Related Repos

- `../PyAutoFit` — the plotting code being rendered (plus `../../organs/PyAutoNerves` on
  `PYTHONPATH`).
- `../autofit_workspace` — user-facing scripts; source of the dataset recipes, the EP example and
  `config/`.
- `../../galaxy/autogalaxy_visualization` — the galaxy sibling this repo was copied from (harness,
  builder, workflows); `../../lens/autolens_visualization` — the lens sibling.
- `../../organs/PyAutoEyes` — the organ: cross-project visualization dashboard that aggregates
  this repo via `gallery/viz_manifest.yaml` (links to the PNGs, never copies them).

## Task Workflows

When changing a producer, the config or a dataset, re-render (`gallery/gallery_run.sh --all`),
keep `ruff check .` / `ruff format --check .` clean, and commit the PNGs + `GALLERY.md` +
`gallery/viz_manifest.yaml` in the same PR. Do not commit machine-specific absolute paths.

<!-- repos_sync:history:begin -->
## Never rewrite history

Never rewrite pushed history on any repo with a remote — no `git init` over a
tracked repo, no force-push to `main`, no fresh-start "Initial commit", no
`filter-repo` / `filter-branch` / `rebase -i` on pushed branches. To get a
clean tree: `git fetch origin && git reset --hard origin/main && git clean -fd`.
<!-- repos_sync:history:end -->

<!-- repos_sync:deliverable:begin -->
## Sessions end at their deliverable

A session ends when it reports its deliverable — never arm anything that
outlives the turn to wait for CI, a review or a merge: no `send_later`, no
`subscribe_pr_activity`, no `CronCreate`, no `ScheduleWakeup`, no `/loop`, no
`RemoteTrigger` create/update/run. Judge once, report, stop; the human re-runs
`/prm` (or the batch review) when it is green. Measured: five batch members
armed hourly check-ins on 2026-08-31, and a mobile `/prm` re-armed a 60-minute
`send_later` hourly all night on 2026-09-03 with no task active, draining usage.
<!-- repos_sync:deliverable:end -->

<!-- repos_sync:filing:begin -->
## Where to file

Questions, help with code or an analysis, ideas, bug reports and results from a
user or collaborator — or an agent acting for one — go to
<https://github.com/orgs/PyAutoLabs/discussions> in the matching category
(Help & Questions, Ideas & Proposals, Bugs & Errors, Show and tell;
Announcements is maintainers-only), never to this repo's Issues. An agent never
runs `gh issue create` for such a report: it drafts the title, category and
body and hands them to the human (sessions cannot create Discussions). Only the
development flow — Mind prompt → `/start_dev` → `/create_issue` → one issue per
task → PR — opens issues here. Why: `PyAutoMind/policy/community_surface.md`.
<!-- repos_sync:filing:end -->
