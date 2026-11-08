"""Generate motivating descriptive visualizations for the research report.

Panels:
A) Life Expectancy vs Government Health Expenditure Share (%)
B) Life Expectancy vs log(GDP per capita)
C) Life Expectancy vs Average Schooling (years)
D) Pearson Correlation Heatmap across key econometric indicators

Output: output/descriptive_scatter_matrix.png
Run: python plot_descriptive_evidence.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / 'data/processed/life_expectancy_final_clean.csv'
OUT = ROOT / 'output'
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.edgecolor'] = '#444444'
plt.rcParams['axes.linewidth'] = 0.8

def main():
    df = pd.read_csv(INPUT)
    df.columns = df.columns.str.strip()
    df.loc[df.Country.isin(['France', 'Canada']), 'Status'] = 'Developed'
    for c in ['Life expectancy', 'Total expenditure', 'GDP', 'Schooling', 'Alcohol']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.dropna(subset=['Life expectancy', 'Total expenditure', 'GDP', 'Schooling']).copy()
    df = df[df.GDP.gt(0) & df['Total expenditure'].gt(0)].copy()
    df['log_gdp'] = np.log(df['GDP'])
    df['is_developed'] = df.Status.eq('Developed').astype(int)

    fig, axes = plt.subplots(2, 2, figsize=(15, 12))

    dev = df[df.is_developed == 1]
    devg = df[df.is_developed == 0]

    # Panel A: Life Expectancy vs Health Exp Share (%)
    ax1 = axes[0, 0]
    ax1.scatter(devg['Total expenditure'], devg['Life expectancy'], color='#1f77b4', alpha=0.35, s=20, label=f'Developing (n={len(devg)})')
    ax1.scatter(dev['Total expenditure'], dev['Life expectancy'], color='#e65100', alpha=0.5, s=24, label=f'Developed (n={len(dev)})')
    m, b = np.polyfit(df['Total expenditure'], df['Life expectancy'], 1)
    r, p = stats.pearsonr(df['Total expenditure'], df['Life expectancy'])
    x_grid = np.linspace(df['Total expenditure'].min(), df['Total expenditure'].max(), 100)
    ax1.plot(x_grid, m * x_grid + b, color='#d00000', lw=2.8, label=f'Overall: β = {m:+.3f} (r = {r:+.2f})')
    ax1.axvline(x=8.76, color='black', linestyle='--', lw=1.5, label='Median Threshold: 8.76%')
    ax1.set_title("A) Motivating Evidence: Life Expectancy vs Health Expenditure Share\n(Budget Share: % of Total Government Spending)", fontsize=11, fontweight='bold', pad=10)
    ax1.set_xlabel("Government Health Expenditure (% of Total Government Expenditure)", fontsize=10.5)
    ax1.set_ylabel("Life Expectancy (years)", fontsize=10.5)
    ax1.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.9, fontsize=9.2)
    ax1.grid(True, linestyle='--', alpha=0.35)

    # Panel B: Life Expectancy vs log(GDP per capita)
    ax2 = axes[0, 1]
    ax2.scatter(devg['log_gdp'], devg['Life expectancy'], color='#1f77b4', alpha=0.35, s=20, label='Developing')
    ax2.scatter(dev['log_gdp'], dev['Life expectancy'], color='#e65100', alpha=0.5, s=24, label='Developed')
    m_gdp, b_gdp = np.polyfit(df['log_gdp'], df['Life expectancy'], 1)
    r_gdp, _ = stats.pearsonr(df['log_gdp'], df['Life expectancy'])
    xg_gdp = np.linspace(df['log_gdp'].min(), df['log_gdp'].max(), 100)
    ax2.plot(xg_gdp, m_gdp * xg_gdp + b_gdp, color='#0b3954', lw=2.8, label=f'Fit: β = {m_gdp:+.3f} (r = {r_gdp:+.2f})')
    ax2.set_title("B) The Dominant Driver: Life Expectancy vs log(GDP per capita)\n(Strong linear relationship across the entire income distribution)", fontsize=11, fontweight='bold', pad=10)
    ax2.set_xlabel("log(GDP per capita in constant USD)", fontsize=10.5)
    ax2.set_ylabel("Life Expectancy (years)", fontsize=10.5)
    ax2.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.9, fontsize=9.2)
    ax2.grid(True, linestyle='--', alpha=0.35)

    # Panel C: Life Expectancy vs Schooling
    ax3 = axes[1, 0]
    ax3.scatter(devg['Schooling'], devg['Life expectancy'], color='#1f77b4', alpha=0.35, s=20, label='Developing')
    ax3.scatter(dev['Schooling'], dev['Life expectancy'], color='#e65100', alpha=0.5, s=24, label='Developed')
    m_sch, b_sch = np.polyfit(df['Schooling'], df['Life expectancy'], 1)
    r_sch, _ = stats.pearsonr(df['Schooling'], df['Life expectancy'])
    xg_sch = np.linspace(df['Schooling'].min(), df['Schooling'].max(), 100)
    ax3.plot(xg_sch, m_sch * xg_sch + b_sch, color='#2ca02c', lw=2.8, label=f'Fit: β = {m_sch:+.3f} (r = {r_sch:+.2f})')
    ax3.set_title("C) Human Capital: Life Expectancy vs Schooling (years)\n(Fundamental pre-determined development confounder)", fontsize=11, fontweight='bold', pad=10)
    ax3.set_xlabel("Average Schooling (years of education)", fontsize=10.5)
    ax3.set_ylabel("Life Expectancy (years)", fontsize=10.5)
    ax3.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.9, fontsize=9.2)
    ax3.grid(True, linestyle='--', alpha=0.35)

    # Panel D: Pearson Correlation Matrix Heatmap
    ax4 = axes[1, 1]
    cols = ['Life expectancy', 'Total expenditure', 'log_gdp', 'Schooling', 'Alcohol']
    col_labels = ['Life Exp.', 'Health Exp. %', 'log(GDPpc)', 'Schooling', 'Alcohol']
    corr_mat = df[cols].corr().to_numpy()

    im = ax4.imshow(corr_mat, cmap='coolwarm', vmin=-0.2, vmax=1.0)
    for i in range(len(cols)):
        for j in range(len(cols)):
            val = corr_mat[i, j]
            txt_color = 'white' if val > 0.6 else 'black'
            ax4.text(j, i, f"{val:.3f}", ha='center', va='center', color=txt_color, fontsize=11, fontweight='bold')

    ax4.set_xticks(range(len(cols)))
    ax4.set_yticks(range(len(cols)))
    ax4.set_xticklabels(col_labels, fontsize=10, fontweight='bold')
    ax4.set_yticklabels(col_labels, fontsize=10, fontweight='bold')
    ax4.set_title("D) Pearson Correlation Matrix across Key Identifiers\n(High collinearity between Wealth, Education and Health Spending)", fontsize=11, fontweight='bold', pad=10)
    fig.colorbar(im, ax=ax4, fraction=0.046, pad=0.04)

    plt.tight_layout()
    save_path = OUT / 'descriptive_scatter_matrix.png'
    fig.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {save_path}")

if __name__ == '__main__':
    main()
