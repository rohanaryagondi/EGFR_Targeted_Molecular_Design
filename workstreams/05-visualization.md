# Workstream 05: Matplotlib Visualization

## Goal

Add publication-quality matplotlib figures alongside the existing ASCII figures. This makes the project visually impressive for portfolio presentation and technically credible for scientific review.

## Prerequisites

**Workstream 03 must be complete** (or at least `statistics.py` and `sensitivity.py` must exist) for statistical annotations on plots.

Can run in parallel with Workstreams 01, 02, 04, 06 (only touches `evaluation/`).

## Files to Create

### `src/statebind/evaluation/plotting.py`

All functions return `matplotlib.figure.Figure` and optionally save to a file path.

```python
"""Publication-quality matplotlib figures for pipeline comparison.

All figures are optional — generated only when matplotlib is available.
Each function returns a Figure object and optionally saves to disk.
"""

from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from matplotlib.figure import Figure

try:
    import matplotlib
    matplotlib.use("Agg")  # non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def plot_score_distributions(result: ComparativeResult, output_path: Path | None = None) -> Figure | None:
    """Violin/box plot of composite scores split by pipeline.

    Annotate with Mann-Whitney p-value and Cohen's d if statistical
    tests are available in result.statistical_tests.
    """

def plot_score_components_heatmap(merged: MergedRanking, top_n: int = 20, output_path: Path | None = None) -> Figure | None:
    """Heatmap: rows = top-N candidates, columns = score components.

    Color-coded sidebar showing pipeline origin (static vs state-aware).
    """

def plot_diversity_radar(result: ComparativeResult, output_path: Path | None = None) -> Figure | None:
    """Radar/spider chart comparing diversity metrics across dimensions.

    Axes: n_candidates, diversity_score, n_unique_smiles, mean_pairwise_tanimoto.
    """

def plot_sensitivity_heatmap(summary: SensitivitySummary, output_path: Path | None = None) -> Figure | None:
    """Heatmap of weight sensitivity results.

    X-axis: weight configurations (sorted by state_specificity weight).
    Y-axis: pipeline advantage (positive = state-aware wins).
    Color: delta score.
    """

def plot_rank_shift_waterfall(merged: MergedRanking, n: int = 20, output_path: Path | None = None) -> Figure | None:
    """Waterfall chart of biggest rank shifts from pipeline-local to global.

    Green bars = promoted, red bars = demoted.
    """

def plot_strategy_contribution(result: ComparativeResult, output_path: Path | None = None) -> Figure | None:
    """Stacked bar chart: novel candidates by generation strategy per state.

    One bar per state, segments colored by strategy.
    """

def plot_sa_score_distribution(merged: MergedRanking, output_path: Path | None = None) -> Figure | None:
    """Histogram of SA scores split by pipeline (requires chemistry module).

    Only generates if statebind.chemistry.sa_score is available.
    """

def generate_all_plots(
    result: ComparativeResult,
    merged: MergedRanking,
    output_dir: Path,
    sensitivity: SensitivitySummary | None = None,
) -> dict[str, Path]:
    """Generate all available plots and save to output_dir.

    Returns dict mapping figure name to saved file path.
    Skips figures whose dependencies are not available.
    """
```

### `tests/test_plotting.py`

Target: ~12-15 tests.

1. **Figure generation tests:**
   - `test_score_distributions_returns_figure()` — verify type is Figure
   - `test_score_components_heatmap_returns_figure()`
   - `test_diversity_radar_returns_figure()`
   - `test_rank_shift_waterfall_returns_figure()`
   - `test_strategy_contribution_returns_figure()`

2. **Save tests:**
   - `test_save_to_file()` — verify PNG file created at output_path
   - `test_generate_all_plots()` — verify dict of paths returned

3. **Edge case tests:**
   - `test_empty_merged_ranking()` — no crash on empty data
   - `test_single_candidate()` — no crash with minimal data

4. **Fallback tests:**
   - `test_no_matplotlib_returns_none()` — mock ImportError, verify None returned

5. **Style tests:**
   - `test_figure_has_labels()` — axes have labels
   - `test_figure_has_title()` — figures have titles

## Files to Modify

### `src/statebind/evaluation/figures.py`

Update `generate_all_figures()` to optionally also generate matplotlib plots:

```python
def generate_all_figures(
    result: ComparativeResult,
    merged: MergedRanking,
    output_dir: Path | str,
    generate_plots: bool = True,  # NEW PARAMETER
) -> dict[str, str | Path]:
    """Generate all figures.

    Returns dict including ASCII figures (str values) and optionally
    matplotlib plot paths (Path values) when generate_plots=True
    and matplotlib is available.
    """
    figures = {}
    # ... existing ASCII figure generation ...

    if generate_plots:
        try:
            from statebind.evaluation.plotting import generate_all_plots
            plot_paths = generate_all_plots(result, merged, Path(output_dir))
            figures.update(plot_paths)
        except ImportError:
            pass

    return figures
```

## Files NOT to Touch

- `src/statebind/baselines/*` — other workstreams
- `src/statebind/ranking/*` — other workstreams
- `src/statebind/chemistry/*` — Workstream 01 owns this
- `src/statebind/evaluation/statistics.py` — Workstream 03 owns this (only import from it)
- `src/statebind/evaluation/comparison.py` — Workstream 03 owns this (only import result types)

## Existing Code to Reuse

| What | Where | How |
|------|-------|-----|
| `_bar()` helper | `evaluation/figures.py` | Reference for visual style |
| `ComparativeResult` | `evaluation/comparison.py` | Input data type |
| `MergedRanking` | `ranking/models.py` | Input data type |
| `StatisticalTest` | `evaluation/statistics.py` (from WS03) | For annotations |
| `SensitivitySummary` | `evaluation/sensitivity.py` (from WS03) | For sensitivity plot |
| `compute_rank_shifts()` | `ranking/aggregation.py` | For waterfall data |

## Style Guidelines

- Use a clean, publication-ready style: `plt.style.use('seaborn-v0_8-whitegrid')` or similar
- Color scheme: blue for static, orange for state-aware (consistent across all figures)
- Font size: 12pt for labels, 10pt for tick labels
- Figure size: default 8x6 inches, adjust per figure type
- Always include axis labels, title, and legend
- Save at 150 DPI for reasonable file size

## Definition of Done

- [ ] `plotting.py` with 7 plot functions + `generate_all_plots()`
- [ ] `tests/test_plotting.py` with 12+ tests
- [ ] All plots generate without errors on the current benchmark data
- [ ] All plots save as PNG files
- [ ] `figures.py` updated to optionally call matplotlib generation
- [ ] Graceful behavior when matplotlib is not installed (returns None)
- [ ] All existing 359+ tests pass
- [ ] Figures look publication-ready (clean axes, labels, legends)
