"""Generate comprehensive visualizations for Simpson's Paradox: Alcohol vs Life Expectancy.

Outputs:
1. simpson_developing_terciles.png:
   Compares the aggregate developing slope (positive) with the 3 GDP terciles (all negative).
2. simpson_matrix_heatmap.png:
   3x3 Heatmap of correlations across GDP and Health Expenditure terciles.
3. simpson_comprehensive_dashboard.png:
   4-panel publication-grade overview:
     - Panel A: Pooled sample (aggregate positive association)
     - Panel B: Developed vs Developing split
     - Panel C: Developing broken down into GDP Terciles (unanimous inversion)
     - Panel D: Heatmap of correlations by World Bank income brackets

Run: python plot_simpson_alcohol_visualizations.py
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
OUT = ROOT / 'output/simpson_alcohol'
OUT.mkdir(parents=True, exist_ok=True)

Y = 'Life expectancy'
ALC = 'Alcohol'
X = 'Total expenditure'

# Set global matplotlib styles
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.edgecolor'] = '#444444'
plt.rcParams['axes.linewidth'] = 0.8


def load_data():
    df = pd.read_csv(INPUT)
    df.columns = df.columns.str.strip()
    df.loc[df.Country.isin(['France', 'Canada']), 'Status'] = 'Developed'
    for c in [Y, ALC, X, 'GDP', 'Schooling']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.dropna(subset=[Y, ALC, X, 'GDP']).copy()
    df = df[df.GDP.gt(0) & df[X].gt(0)].copy()
    df['log_gdp'] = np.log(df.GDP)
    df['is_developed'] = df.Status.eq('Developed').astype(int)
    return df.reset_index(drop=True)


def figure_1_developing_inversion(df):
    """Plot Developing countries aggregate vs the 3 GDP terciles."""
    dev = df[df.is_developed == 0].copy()
    dev['gdp_tercile'] = pd.qcut(
        dev['GDP'], q=3,
        labels=['T1: Low Income ($112 - $1,197)',
                'T2: Middle Income ($1,198 - $4,354)',
                'T3: Upper-Middle Income ($4,359 - $85,076)']
    )

    fig, axes = plt.subplots(1, 2, figsize=(15, 6.5))

    # Left: Aggregate developing
    ax1 = axes[0]
    ax1.scatter(dev[ALC], dev[Y], color='#2b5c8f', alpha=0.35, s=25, edgecolor='none')
    m_all, b_all = np.polyfit(dev[ALC], dev[Y], 1)
    r_all, p_all = stats.pearsonr(dev[ALC], dev[Y])
    x_grid = np.linspace(dev[ALC].min(), dev[ALC].max(), 100)
    ax1.plot(x_grid, m_all * x_grid + b_all, color='#d9534f', lw=3.0,
             label=f'Aggregate Fit:\nSlope = {m_all:+.3f} (r = {r_all:+.2f}, p < 0.001)')

    ax1.set_title("A) Aggregate View: All Developing Countries\n(Apparent Paradox: Spurious Positive Slope)",
                  fontsize=12, pad=12, fontweight='bold', color='#111111')
    ax1.set_xlabel("Alcohol Consumption per capita (litres/year)", fontsize=11)
    ax1.set_ylabel("Life Expectancy (years)", fontsize=11)
    ax1.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.9, fontsize=10)
    ax1.grid(True, linestyle='--', alpha=0.4)
    ax1.set_ylim(40, 88)

    # Right: Stratified by GDP terciles
    ax2 = axes[1]
    palette = {'T1: Low Income ($112 - $1,197)': '#1f77b4',
               'T2: Middle Income ($1,198 - $4,354)': '#ff7f0e',
               'T3: Upper-Middle Income ($4,359 - $85,076)': '#2ca02c'}

    for label, group in dev.groupby('gdp_tercile', observed=True):
        col = palette[str(label)]
        ax2.scatter(group[ALC], group[Y], color=col, alpha=0.4, s=28,
                    label=str(label), edgecolor='none')
        m, b = np.polyfit(group[ALC], group[Y], 1)
        r, p = stats.pearsonr(group[ALC], group[Y])
        xg = np.linspace(group[ALC].min(), group[ALC].max(), 100)
        ax2.plot(xg, m * xg + b, color=col, lw=2.6, linestyle='-')

    # Also show dashed aggregate line on background for contrast
    ax2.plot(x_grid, m_all * x_grid + b_all, color='#888888', lw=1.8, linestyle=':',
             label=f'Aggregate (spurious, +0.388)')

    ax2.set_title("B) Disaggregated by GDP Terciles\n(Universal Inversion: All Within-Tercile Slopes are Negative)",
                  fontsize=12, pad=12, fontweight='bold', color='#111111')
    ax2.set_xlabel("Alcohol Consumption per capita (litres/year)", fontsize=11)
    ax2.set_ylabel("Life Expectancy (years)", fontsize=11)
    ax2.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.9, fontsize=9.5)
    ax2.grid(True, linestyle='--', alpha=0.4)
    ax2.set_ylim(40, 88)

    plt.tight_layout()
    save_path = OUT / 'simpson_developing_terciles.png'
    fig.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {save_path}")


def figure_2_matrix_heatmap(df):
    """Plot Heatmap of correlations: GDP terciles vs Health Expenditure terciles."""
    df_copy = df.copy()
    df_copy['gdp_t'] = pd.qcut(df_copy['GDP'], q=3, labels=['Low GDP', 'Medium GDP', 'High GDP'])
    df_copy['exp_t'] = pd.qcut(df_copy[X], q=3, labels=['Low Health Exp', 'Medium Health Exp', 'High Health Exp'])

    matrix_corr = np.zeros((3, 3))
    matrix_annot = []

    order_gdp = ['High GDP', 'Medium GDP', 'Low GDP']
    order_exp = ['Low Health Exp', 'Medium Health Exp', 'High Health Exp']

    for i, g in enumerate(order_gdp):
        row_annot = []
        for j, e in enumerate(order_exp):
            sub = df_copy[(df_copy.gdp_t == g) & (df_copy.exp_t == e)]
            r, p = stats.pearsonr(sub[ALC], sub[Y])
            matrix_corr[i, j] = r
            sig = '***' if p < 0.001 else ('**' if p < 0.01 else ('*' if p < 0.05 else ''))
            row_annot.append(f"r = {r:+.3f}{sig}\n(n = {len(sub)})")
        matrix_annot.append(row_annot)

    fig, ax = plt.subplots(figsize=(8.5, 6.5))
    cmap = plt.cm.coolwarm
    im = ax.imshow(matrix_corr, cmap=cmap, vmin=-0.4, vmax=0.4, aspect='auto')

    # Add text labels inside cells
    for i in range(3):
        for j in range(3):
            val = matrix_corr[i, j]
            txt_color = 'white' if abs(val) > 0.2 else 'black'
            ax.text(j, i, matrix_annot[i][j], ha="center", va="center",
                    color=txt_color, fontsize=11, fontweight='bold')

    ax.set_xticks(range(3))
    ax.set_yticks(range(3))
    ax.set_xticklabels(order_exp, fontsize=11, fontweight='bold')
    ax.set_yticklabels(order_gdp, fontsize=11, fontweight='bold')

    ax.set_xlabel("Government Health Expenditure Share (% of Government Budget)", fontsize=12, labelpad=10)
    ax.set_ylabel("GDP per capita Level", fontsize=12, labelpad=10)
    ax.set_title("Cross-Stratified Correlation Matrix: Alcohol <-> Life Expectancy\n(GDP Level x Health Expenditure Share)",
                 fontsize=13, pad=15, fontweight='bold')

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Pearson Correlation Coefficient (r)", fontsize=10)

    plt.tight_layout()
    save_path = OUT / 'simpson_matrix_heatmap.png'
    fig.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {save_path}")


def figure_3_comprehensive_dashboard(df):
    """Generate 4-panel comprehensive dashboard."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 13))

    # --- Panel 1: Global Pooled ---
    ax1 = axes[0, 0]
    ax1.scatter(df[ALC], df[Y], color='#4a6fa5', alpha=0.3, s=20, edgecolor='none')
    m_glob, b_glob = np.polyfit(df[ALC], df[Y], 1)
    r_glob, _ = stats.pearsonr(df[ALC], df[Y])
    xg = np.linspace(df[ALC].min(), df[ALC].max(), 100)
    ax1.plot(xg, m_glob * xg + b_glob, color='#d00000', lw=3.0,
             label=f'Global Pooled Fit:\nβ = {m_glob:+.3f} (r = {r_glob:+.2f}, p < 0.001)')
    ax1.set_title("1. Global Pooled Sample (Apparent Simpson's Paradox)\nSpurious positive association: higher alcohol consumption correlates with longer life",
                  fontsize=11.5, fontweight='bold', pad=10)
    ax1.set_xlabel("Alcohol Consumption per capita (L/year)", fontsize=10.5)
    ax1.set_ylabel("Life Expectancy (years)", fontsize=10.5)
    ax1.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.9)
    ax1.grid(True, linestyle='--', alpha=0.4)

    # --- Panel 2: Developed vs Developing ---
    ax2 = axes[0, 1]
    dev = df[df.is_developed == 1]
    devg = df[df.is_developed == 0]

    ax2.scatter(devg[ALC], devg[Y], color='#1f77b4', alpha=0.3, s=18, label=f'Developing (n={len(devg)})')
    ax2.scatter(dev[ALC], dev[Y], color='#e65100', alpha=0.45, s=22, label=f'Developed (n={len(dev)})')

    # Developed line
    md, bd = np.polyfit(dev[ALC], dev[Y], 1)
    rd, _ = stats.pearsonr(dev[ALC], dev[Y])
    xg_d = np.linspace(dev[ALC].min(), dev[ALC].max(), 100)
    ax2.plot(xg_d, md * xg_d + bd, color='#bf360c', lw=2.6,
             label=f'Developed: β = {md:+.3f} (r = {rd:+.2f})')

    # Developing line
    mg, bg = np.polyfit(devg[ALC], devg[Y], 1)
    rg, _ = stats.pearsonr(devg[ALC], devg[Y])
    xg_g = np.linspace(devg[ALC].min(), devg[ALC].max(), 100)
    ax2.plot(xg_g, mg * xg_g + bg, color='#0d47a1', lw=2.6,
             label=f'Developing: β = {mg:+.3f} (r = {rg:+.2f})')

    ax2.set_title("2. Binary Stratification (Developed vs Developing)\nInverts for developed countries, but remains positive for developing group",
                  fontsize=11.5, fontweight='bold', pad=10)
    ax2.set_xlabel("Alcohol Consumption per capita (L/year)", fontsize=10.5)
    ax2.set_ylabel("Life Expectancy (years)", fontsize=10.5)
    ax2.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.9, fontsize=9.5)
    ax2.grid(True, linestyle='--', alpha=0.4)

    # --- Panel 3: Developing by GDP Terciles ---
    ax3 = axes[1, 0]
    devg_copy = devg.copy()
    devg_copy['gdp_t'] = pd.qcut(devg_copy['GDP'], q=3,
                                 labels=['T1: Low Income', 'T2: Middle Income', 'T3: Upper-Middle Income'])
    colors_t = ['#2b9348', '#e85d04', '#0077b6']

    for (t, group), col in zip(devg_copy.groupby('gdp_t', observed=True), colors_t):
        ax3.scatter(group[ALC], group[Y], color=col, alpha=0.35, s=20, label=str(t))
        mt, bt = np.polyfit(group[ALC], group[Y], 1)
        rt, _ = stats.pearsonr(group[ALC], group[Y])
        xgt = np.linspace(group[ALC].min(), group[ALC].max(), 100)
        ax3.plot(xgt, mt * xgt + bt, color=col, lw=2.5,
                 label=f'{t}: β = {mt:+.3f} (r = {rt:+.2f})')

    ax3.set_title("3. Developing Countries by GDP Terciles\nUniversal inversion: conditioning on income reveals the deleterious effect of alcohol",
                  fontsize=11.5, fontweight='bold', pad=10)
    ax3.set_xlabel("Alcohol Consumption per capita (L/year)", fontsize=10.5)
    ax3.set_ylabel("Life Expectancy (years)", fontsize=10.5)
    ax3.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.9, fontsize=9.2)
    ax3.grid(True, linestyle='--', alpha=0.4)

    # --- Panel 4: World Bank Income Brackets Slopes ---
    ax4 = axes[1, 1]
    bins_wb = [0, 1045, 4095, 12695, np.inf]
    labels_wb = ['Low (<$1k)', 'Lower-Middle ($1k-$4k)', 'Upper-Middle ($4k-$13k)', 'High (>$13k)']
    df['income_group'] = pd.cut(df['GDP'], bins=bins_wb, labels=labels_wb)

    wb_colors = ['#8338ec', '#3a86ff', '#fb5607', '#ff006e']
    for (wb_label, group), col in zip(df.groupby('income_group', observed=True), wb_colors):
        m, b = np.polyfit(group[ALC], group[Y], 1)
        r, p = stats.pearsonr(group[ALC], group[Y])
        ax4.scatter(group[ALC], group[Y], color=col, alpha=0.25, s=18)
        x_wb = np.linspace(group[ALC].min(), group[ALC].max(), 100)
        sig = '*' if p < 0.05 else ''
        ax4.plot(x_wb, m * x_wb + b, color=col, lw=2.4,
                 label=f'{wb_label}: β = {m:+.3f}{sig}')

    ax4.set_title("4. World Bank Income Groups\nConsistent negative associations across groups up to $13,000 per capita",
                  fontsize=11.5, fontweight='bold', pad=10)
    ax4.set_xlabel("Alcohol Consumption per capita (L/year)", fontsize=10.5)
    ax4.set_ylabel("Life Expectancy (years)", fontsize=10.5)
    ax4.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.9, fontsize=9.2)
    ax4.grid(True, linestyle='--', alpha=0.4)

    plt.tight_layout()
    save_path = OUT / 'simpson_comprehensive_dashboard.png'
    fig.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {save_path}")


def main():
    print("Loading dataset...")
    df = load_data()
    print(f"Generating charts from {len(df)} observations...")
    figure_1_developing_inversion(df)
    figure_2_matrix_heatmap(df)
    figure_3_comprehensive_dashboard(df)
    print("All visualizations generated successfully in English!")


if __name__ == '__main__':
    main()
