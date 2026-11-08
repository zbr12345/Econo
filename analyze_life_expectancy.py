#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr


ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT_DIR = ROOT / "data" / "raw"
DEFAULT_OUTPUT_DIR = ROOT / "analysis of data"

ALIASES = {
    "life_expectancy": {"lifeexpectancy", "lifeexpectancyyears"},
    "schooling": {"schooling", "yearsofschooling"},
    "gdp": {"gdp", "grossdomesticproduct"},
    "total_expenditure": {
        "totalexpenditure", "totalgovernmentexpenditureonhealth"
    },
    "adult_mortality": {
        "adultmortality", "adultmortalityrate", "mortalityrate"
    },
}

FEATURES = [
    ("schooling", "Schooling", "Years of schooling",
     "schooling_vs_life_expectancy.png"),
    ("gdp", "ln(GDP per capita)", "Natural log of GDP per capita (ln USD)",
     "gdp_vs_life_expectancy.png"),
    ("total_expenditure", "Total expenditure on health",
     "General government health expenditure (% of total government expenditure)",
     "total_expenditure_vs_life_expectancy.png"),
    ("adult_mortality", "Adult mortality",
     "Adult mortality rate (probability of dying between ages 15 and 60, per 1,000 population)",
     "adult_mortality_vs_life_expectancy.png"),
]


def key(name):
    """Case- and punctuation-insensitive column-name comparison."""
    return re.sub(r"[^a-z0-9]", "", str(name).strip().lower())


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def find_input(input_arg):
    if input_arg:
        path = Path(input_arg).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        if not path.is_file():
            raise FileNotFoundError(f"CSV not found: {path}")
        if path.suffix.lower() != ".csv":
            raise ValueError("The input must be a .csv file.")
        return path.resolve()

    if DEFAULT_INPUT_DIR.exists():
        files = sorted(DEFAULT_INPUT_DIR.glob("*.csv"))
        if len(files) == 1:
            return files[0].resolve()
        if len(files) > 1:
            matching = [p for p in files if "life" in p.stem.lower()
                        and "expect" in p.stem.lower()]
            if len(matching) == 1:
                return matching[0].resolve()
            raise RuntimeError(
                "Several CSV files exist in data/raw. Specify one with --input:\n"
                + "\n".join(str(p) for p in files)
            )

    files = sorted(ROOT.glob("*.csv"))
    if len(files) == 1:
        return files[0].resolve()
    matching = [p for p in files if "life" in p.stem.lower()
                and "expect" in p.stem.lower()]
    if len(matching) == 1:
        return matching[0].resolve()

    raise FileNotFoundError(
        "Dataset not found. Place the original CSV in:\n"
        f"  {DEFAULT_INPUT_DIR / 'Life Expectancy Data.csv'}\n"
        "or pass its path using --input."
    )


def read_source(path):
    """Read the CSV without writing to it."""
    errors = []
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            df = pd.read_csv(path, encoding=encoding, sep=None,
                             engine="python")
            if df.empty:
                raise ValueError("The CSV has no data rows.")
            return df
        except Exception as exc:
            errors.append(f"{encoding}: {exc}")
    raise RuntimeError("Could not read CSV:\n" + "\n".join(errors))


def resolve_column(df, canonical):
    matches = [
        col for col in df.columns
        if key(col) in ALIASES[canonical]
    ]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise KeyError(
            f"Required column '{canonical}' was not found.\n"
            f"Columns in your file: {list(df.columns)}"
        )
    raise KeyError(
        f"Ambiguous columns for '{canonical}': {matches}. "
        "Please check the source CSV manually; this script will not alter it."
    )


def numeric_copy(series):
    """Convert a separate Series copy for calculations; never changes df."""
    s = series.copy(deep=True)
    if s.dtype == object or str(s.dtype).startswith("string"):
        s = s.astype("string").str.strip().str.replace(",", "", regex=False)
    return pd.to_numeric(s, errors="coerce")


def paired_values(x, y):
    # Pairwise deletion is local to this calculation only.
    pair = pd.DataFrame({"x": numeric_copy(x), "y": numeric_copy(y)})
    pair = pair.replace([np.inf, -np.inf], np.nan).dropna()
    return pair["x"].to_numpy(float), pair["y"].to_numpy(float)


def natural_log_positive(series):
    """Return ln(x) for positive values only, without changing the source."""
    values = numeric_copy(series).replace([np.inf, -np.inf], np.nan)
    positive = values.where(values > 0)
    return np.log(positive)


def association_stats(x, y):
    n = len(x)
    out = {
        "n": int(n),
        "pearson_r": np.nan,
        "pearson_p": np.nan,
        "spearman_rho": np.nan,
        "spearman_p": np.nan,
    }
    if n < 3 or np.std(x) == 0 or np.std(y) == 0:
        return out

    p = pearsonr(x, y)
    s = spearmanr(x, y)
    out["pearson_r"] = float(p.statistic if hasattr(p, "statistic") else p[0])
    out["pearson_p"] = float(p.pvalue if hasattr(p, "pvalue") else p[1])
    out["spearman_rho"] = float(s.statistic if hasattr(s, "statistic") else s[0])
    out["spearman_p"] = float(s.pvalue if hasattr(s, "pvalue") else s[1])
    return out


def describe_strength(r):
    if not np.isfinite(r):
        return "not available"
    a = abs(r)
    if a < 0.20:
        strength = "very weak"
    elif a < 0.40:
        strength = "weak"
    elif a < 0.60:
        strength = "moderate"
    elif a < 0.80:
        strength = "strong"
    else:
        strength = "very strong"
    direction = "positive" if r > 0 else "negative" if r < 0 else "zero"
    return f"{strength} {direction}"


def p_text(p):
    if not np.isfinite(p):
        return "NA"
    return "< 0.001" if p < 0.001 else f"{p:.3g}"


def save_scatter(x, y, feature, x_label, filename, stats, fig_dir):
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(x, y, alpha=0.45, edgecolors="none",
               label="Country-year observations")

    # The line is a simple visual trend, not a causal or multivariable model.
    if len(x) >= 2 and np.unique(x).size >= 2:
        slope, intercept = np.polyfit(x, y, 1)
        x_line = np.linspace(np.min(x), np.max(x), 200)
        ax.plot(x_line, slope * x_line + intercept,
                linewidth=2, label="Simple linear trend")

    if np.isfinite(stats["pearson_r"]):
        note = (
            f"Pearson r = {stats['pearson_r']:.3f}\n"
            f"Spearman rho = {stats['spearman_rho']:.3f}\n"
            f"n = {stats['n']}"
        )
    else:
        note = f"n = {stats['n']}\nCorrelation unavailable"
    ax.text(
        0.03, 0.97, note, transform=ax.transAxes, va="top",
        bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "alpha": 0.85}
    )
    ax.set_title(f"{feature} vs. Life Expectancy", fontsize=14)
    ax.set_xlabel(x_label)
    ax.set_ylabel("Life expectancy (years)")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(fig_dir / filename, dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_heatmap(corr, path):
    ncols = len(corr.columns)
    side = max(10, min(22, 0.58 * ncols + 5))
    fig, ax = plt.subplots(figsize=(side, side * 0.86))
    image = ax.imshow(corr.to_numpy(), vmin=-1, vmax=1,
                      cmap="coolwarm", aspect="auto")
    labels = corr.columns.tolist()
    ax.set_xticks(np.arange(ncols))
    ax.set_yticks(np.arange(ncols))
    ax.set_xticklabels(labels, rotation=60, ha="right", fontsize=8)
    ax.set_yticklabels(labels, fontsize=8)

    if ncols <= 24:
        for i in range(ncols):
            for j in range(ncols):
                value = corr.iloc[i, j]
                text = "NA" if not np.isfinite(value) else f"{value:.2f}"
                ax.text(j, i, text, ha="center", va="center", fontsize=6.5)

    ax.set_title("Pearson Correlation Matrix\n(pairwise available observations)")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04,
                 label="Pearson correlation")
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def save_target_distribution(target, path):
    values = numeric_copy(target).replace([np.inf, -np.inf], np.nan).dropna()
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.hist(values, bins=30, edgecolor="white", alpha=0.85)
    ax.set_title("Distribution of Life Expectancy")
    ax.set_xlabel("Life expectancy (years)")
    ax.set_ylabel("Number of country-year observations")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def make_summary(path, source, shape, hash_before, hash_after,
                 missing, target_name, requested_stats, all_target_corr,
                 corr_columns, gdp_comparison):
    lines = [
        "# Life Expectancy: Read-only exploratory data analysis",
        "",
        f"**Input CSV:** `{source}`",
        f"**Original dimensions:** {shape[0]} rows x {shape[1]} columns",
        f"**Target:** `{target_name}`",
        "",
        "## Data integrity",
        "",
        "The original CSV was read only. No rows were deleted, no values were "
        "imputed, and no source columns were changed or overwritten.",
        "",
        f"- SHA-256 before analysis: `{hash_before}`",
        f"- SHA-256 after analysis: `{hash_after}`",
        f"- Source file unchanged: **{'YES' if hash_before == hash_after else 'CHECK HASH'}**",
        "",
        "Missing values are reported here, not repaired:",
        "",
        "| Column | Missing count | Missing % |",
        "|---|---:|---:|",
    ]
    for col, count in missing.items():
        pct = 100 * count / shape[0] if shape[0] else 0
        lines.append(f"| {col} | {int(count)} | {pct:.2f}% |")

    lines += [
        "",
        "## Relationships with life expectancy",
        "",
        "Each plot and correlation uses only rows where that particular pair "
        "of variables is observed. This pairwise handling is local to that "
        "calculation; it does not remove rows from the source CSV.",
        "",
        "| Feature | n | Pearson r | Pearson p-value | Spearman rho | Spearman p-value |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in requested_stats:
        r = row["pearson_r"]
        rho = row["spearman_rho"]
        r_str = f"{r:.3f}" if np.isfinite(r) else "NA"
        rho_str = f"{rho:.3f}" if np.isfinite(rho) else "NA"
        lines.append(
            f"| {row['feature']} | {row['n']} | {r_str} | "
            f"{p_text(row['pearson_p'])} | {rho_str} | "
            f"{p_text(row['spearman_p'])} |"
        )

    lines += [
        "",
        "## GDP transformation: raw GDP vs natural log GDP",
        "",
        "The GDP scatterplot uses the natural logarithm of GDP per capita, "
        "calculated only for strictly positive GDP observations. The raw GDP "
        "column in the source CSV is preserved unchanged. The table below "
        "compares the two bivariate relationships using the same pairwise "
        "available-observation rule.",
        "",
        "| GDP version | n | Pearson r | Pearson p-value | Spearman rho | Spearman p-value |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in gdp_comparison:
        r = row["pearson_r"]
        rho = row["spearman_rho"]
        r_str = f"{r:.3f}" if np.isfinite(r) else "NA"
        rho_str = f"{rho:.3f}" if np.isfinite(rho) else "NA"
        lines.append(
            f"| {row['feature']} | {row['n']} | {r_str} | "
            f"{p_text(row['pearson_p'])} | {rho_str} | "
            f"{p_text(row['spearman_p'])} |"
        )

    lines += ["", "## Automatically generated observations", ""]
    valid = all_target_corr.dropna(subset=["pearson_r"]).copy()
    if not valid.empty:
        valid = valid[valid["feature"] != target_name]
        if not valid.empty:
            positive = valid.loc[valid["pearson_r"].idxmax()]
            negative = valid.loc[valid["pearson_r"].idxmin()]
            lines.append(
                f"- Strongest positive Pearson association: **{positive['feature']}** "
                f"(r = {positive['pearson_r']:.3f}; n = {int(positive['n'])})."
            )
            lines.append(
                f"- Strongest negative Pearson association: **{negative['feature']}** "
                f"(r = {negative['pearson_r']:.3f}; n = {int(negative['n'])})."
            )
            weak = valid.loc[valid["pearson_r"].abs() < 0.20, "feature"].tolist()
            if weak:
                lines.append(
                    "- Very weak linear associations (|r| < 0.20): "
                    + ", ".join(f"`{name}`" for name in weak) + "."
                )
    else:
        lines.append("Not enough observed numeric pairs to rank correlations.")

    lines += [
        "",
        "## Interpretation cautions",
        "",
        "- Correlation does not establish causation.",
        "- These are observational country-year records. Countries may appear "
        "in multiple years, so observations may not be independent.",
        "- GDP per capita is often highly skewed. The GDP scatterplot uses "
        "ln(GDP) to reduce right-skew; non-positive GDP values cannot be logged "
        "and are omitted only from the log-GDP plot and its statistics. Raw GDP "
        "is retained in the correlation matrix and compared in a separate table.",
        "- `Total expenditure` is general government expenditure on health "
        "as a percentage of total government expenditure. It is not the same "
        "as `percentage expenditure` (health expenditure as a percentage of GDP per capita).",
        "- Pearson correlation describes linear association; Spearman correlation "
        "describes monotonic rank association.",
        "",
        "## Correlation matrix",
        "",
        "The matrix includes numeric variables and excludes `Country`, `Status`, "
        "and `Year` from the correlation analysis, consistent with the GitHub "
        "project's decision to remove Country and Year from predictor analysis. "
        "The original file still retains those columns.",
        "",
        ", ".join(f"`{c}`" for c in corr_columns),
        "",
        "## Generated files",
        "",
        "- `figures/schooling_vs_life_expectancy.png`",
        "- `figures/gdp_vs_life_expectancy.png`",
        "- `figures/total_expenditure_vs_life_expectancy.png`",
        "- `figures/adult_mortality_vs_life_expectancy.png`",
        "- `figures/correlation_matrix.png`",
        "- `figures/life_expectancy_distribution.png`",
        "- `tables/pearson_correlation_matrix.csv`",
        "- `tables/correlation_pair_counts.csv`",
        "- `tables/life_expectancy_correlations.csv`",
        "- `tables/four_feature_correlations.csv`",
        "- `tables/gdp_raw_vs_log_comparison.csv`",
        "- `data_audit.csv`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def analyze(source_path, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = output_dir / "figures"
    tables_dir = output_dir / "tables"
    figures_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    hash_before = sha256(source_path)
    df = read_source(source_path)
    original_shape = df.shape
    missing = df.isna().sum()

    # Resolve the exact source column names; never rename the source DataFrame.
    cols = {name: resolve_column(df, name) for name in ALIASES}
    target_name = cols["life_expectancy"]

    # Data audit is descriptive only.
    audit = pd.DataFrame({
        "column": [str(c) for c in df.columns],
        "dtype_as_loaded": [str(df[c].dtype) for c in df.columns],
        "missing_count": [int(df[c].isna().sum()) for c in df.columns],
        "missing_percent": [float(df[c].isna().mean() * 100) for c in df.columns],
    })
    audit.to_csv(output_dir / "data_audit.csv", index=False)

    # Build a separate numeric analysis frame. Country/Status/Year are not
    # included in the correlation matrix; all original columns remain intact.
    numeric_columns = {}
    for col in df.columns:
        if key(col) in {"country", "status", "year"}:
            continue
        series = numeric_copy(df[col])
        if series.notna().sum() >= 3 and series.nunique(dropna=True) > 1:
            numeric_columns[str(col)] = series

    if target_name not in numeric_columns:
        numeric_columns[target_name] = numeric_copy(df[target_name])

    # Add a derived ln(GDP) column for analysis only. The original GDP column
    gdp_source = cols["gdp"]
    log_gdp = natural_log_positive(df[gdp_source])
    numeric_columns["ln_GDP"] = log_gdp

    numeric_df = pd.DataFrame(numeric_columns, index=df.index)
    corr = numeric_df.corr(method="pearson", min_periods=3)
    valid_masks = numeric_df.notna().astype(int)
    pair_counts = valid_masks.T.dot(valid_masks)

    corr.to_csv(tables_dir / "pearson_correlation_matrix.csv", float_format="%.6f")
    pair_counts.to_csv(tables_dir / "correlation_pair_counts.csv")
    save_heatmap(corr, figures_dir / "correlation_matrix.png")

    # Correlations of each numeric feature with Life Expectancy.
    all_results = []
    for col in numeric_df.columns:
        if col == target_name:
            continue
        x, y = paired_values(numeric_df[col], df[target_name])
        stats = association_stats(x, y)
        all_results.append({"feature": col, **stats})

    all_corr = pd.DataFrame(all_results)
    if not all_corr.empty:
        all_corr["abs_pearson_r"] = all_corr["pearson_r"].abs()
        all_corr = all_corr.sort_values("abs_pearson_r", ascending=False)
    all_corr.to_csv(
        tables_dir / "life_expectancy_correlations.csv",
        index=False, float_format="%.6f"
    )

    # The four requested graphs and pairwise statistics. GDP is plotted on a
    requested_results = []
    gdp_comparison = []
    for key_name, label, x_label, filename in FEATURES:
        source_col = cols[key_name]
        if key_name == "gdp":
            raw_x, raw_y = paired_values(df[source_col], df[target_name])
            raw_stats = association_stats(raw_x, raw_y)
            gdp_comparison.append({"feature": "Raw GDP per capita", **raw_stats})

            x, y = paired_values(log_gdp, df[target_name])
            stats = association_stats(x, y)
            gdp_comparison.append({"feature": "ln(GDP per capita)", **stats})
        else:
            x, y = paired_values(df[source_col], df[target_name])
            stats = association_stats(x, y)

        requested_results.append({"feature": label, **stats})
        save_scatter(
            x, y, label, x_label, filename, stats, figures_dir
        )

    pd.DataFrame(requested_results).to_csv(
        tables_dir / "four_feature_correlations.csv",
        index=False, float_format="%.6f"
    )
    pd.DataFrame(gdp_comparison).to_csv(
        tables_dir / "gdp_raw_vs_log_comparison.csv",
        index=False, float_format="%.6f"
    )
    save_target_distribution(
        df[target_name], figures_dir / "life_expectancy_distribution.png"
    )

    hash_after = sha256(source_path)
    make_summary(
        output_dir / "analysis_summary.md",
        source_path, original_shape, hash_before, hash_after,
        missing, target_name, requested_results, all_corr,
        list(numeric_df.columns), gdp_comparison
    )

    print("\nREAD-ONLY ANALYSIS COMPLETED")
    print("----------------------------")
    print(f"Input CSV     : {source_path}")
    print(f"Original size : {original_shape[0]} rows x {original_shape[1]} columns")
    print(f"Output folder : {output_dir}")
    print(
        "GDP plot       : ln(GDP) (strictly positive GDP values only); "
        "raw GDP is retained in the source and correlation matrix."
    )
    print("\nCorrelations with Life Expectancy:")
    for result in requested_results:
        r = result["pearson_r"]
        rho = result["spearman_rho"]
        if np.isfinite(r):
            print(
                f"  {result['feature']:<30} "
                f"Pearson r={r: .3f}; Spearman rho={rho: .3f}; n={result['n']}"
            )
        else:
            print(f"  {result['feature']:<30} correlation unavailable; n={result['n']}")
    print(f"\nOriginal CSV unchanged: {'YES' if hash_before == hash_after else 'CHECK HASH'}")
    print("Read analysis of data/analysis_summary.md for interpretations.")


def main():
    parser = argparse.ArgumentParser(
        description="Read-only EDA for the WHO Life Expectancy dataset."
    )
    parser.add_argument(
        "--input", "-i", default=None,
        help="Path to the original CSV (default: data/raw/ or script folder)."
    )
    parser.add_argument(
        "--output", "-o", default=str(DEFAULT_OUTPUT_DIR),
        help=f"Output folder (default: {DEFAULT_OUTPUT_DIR})."
    )
    args = parser.parse_args()

    try:
        source = find_input(args.input)
        output = Path(args.output).expanduser()
        if not output.is_absolute():
            output = Path.cwd() / output
        analyze(source, output.resolve())
        return 0
    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
