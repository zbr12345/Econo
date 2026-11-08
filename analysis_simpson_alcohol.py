"""Simpson's Paradox illustration: Alcohol consumption and life expectancy.

Overall correlation: POSITIVE (richer countries drink more AND live longer).
Within-group correlation: NEGATIVE or WEAKER (alcohol is harmful to health).

This script demonstrates the paradox with:
  1. Descriptive statistics by development status
  2. OLS regressions: pooled vs. within-group vs. with controls
  3. Scatter plot with overall and within-group regression lines
  4. Comparison table showing sign reversal

Run: python analysis_simpson_alcohol.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / 'data/processed/life_expectancy_final_clean.csv'
OUT = ROOT / 'output/simpson_alcohol'
Y = 'Life expectancy'
ALC = 'Alcohol'


def load(path):
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df.loc[df.Country.isin(['France', 'Canada']), 'Status'] = 'Developed'
    for c in [Y, ALC, 'GDP', 'Schooling']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.dropna(subset=[Y, ALC, 'GDP', 'Schooling']).copy()
    df = df[df.GDP.gt(0)].copy()
    df['log_gdp'] = np.log(df.GDP)
    df['is_developed'] = df.Status.eq('Developed').astype(int)
    return df.reset_index(drop=True)


def run_ols(data, name, y_col, x_terms, cluster=True):
    """Fit OLS with optional country-clustered SE."""
    X = sm.add_constant(data[x_terms].astype(float), has_constant='add')
    fit = sm.OLS(data[y_col], X).fit()
    if cluster:
        groups = pd.factorize(data.Country)[0]
        fit_clu = sm.OLS(data[y_col], X).fit(cov_type='cluster',
                                              cov_kwds={'groups': groups})
    else:
        fit_clu = fit

    ci = fit_clu.conf_int()
    coefs = pd.DataFrame({
        'term': fit_clu.params.index,
        'coefficient': fit_clu.params.values,
        'std_error': fit_clu.bse.values,
        't_statistic': fit_clu.tvalues.values,
        'p_value': fit_clu.pvalues.values,
        'ci95_low': ci[0].values,
        'ci95_high': ci[1].values,
    })
    ff = lambda v: f'{v:.6g}'
    print(f'\n{"="*70}')
    print(f'MODEL: {name}')
    print(f'{"="*70}')
    print(coefs.to_string(index=False, float_format=ff))
    print(f'N = {int(fit.nobs)};  Countries = {data.Country.nunique()};  '
          f'R² = {fit.rsquared:.6f};  Adj R² = {fit.rsquared_adj:.6f}')
    return {
        'model': name,
        'n': int(fit.nobs),
        'countries': int(data.Country.nunique()),
        'alcohol_coef': fit.params[ALC],
        'alcohol_coef_clu': fit_clu.params[ALC],
        'alcohol_SE_clu': fit_clu.bse[ALC],
        'alcohol_p_clu': fit_clu.pvalues[ALC],
        'R2': fit.rsquared,
        'adj_R2': fit.rsquared_adj,
    }, fit


def make_scatter(df, out_dir):
    """Scatter plot with overall and within-group regression lines."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # --- Panel A: Raw scatter with overall line ---
    ax = axes[0]
    dev = df[df.is_developed == 1]
    devg = df[df.is_developed == 0]
    ax.scatter(devg[ALC], devg[Y], alpha=0.25, s=12, c='#2196F3',
               label=f'Developing (n={len(devg)})')
    ax.scatter(dev[ALC], dev[Y], alpha=0.4, s=18, c='#FF5722',
               label=f'Developed (n={len(dev)})')

    # Overall line
    z_all = np.polyfit(df[ALC], df[Y], 1)
    x_line = np.linspace(df[ALC].min(), df[ALC].max(), 100)
    ax.plot(x_line, np.polyval(z_all, x_line), 'k-', lw=2.5,
            label=f'Overall: β={z_all[0]:+.3f}')

    # Within-group lines
    z_dev = np.polyfit(dev[ALC], dev[Y], 1)
    x_dev = np.linspace(dev[ALC].min(), dev[ALC].max(), 100)
    ax.plot(x_dev, np.polyval(z_dev, x_dev), '--', c='#FF5722', lw=2,
            label=f'Developed: β={z_dev[0]:+.3f}')

    z_devg = np.polyfit(devg[ALC], devg[Y], 1)
    x_devg = np.linspace(devg[ALC].min(), devg[ALC].max(), 100)
    ax.plot(x_devg, np.polyval(z_devg, x_devg), '--', c='#2196F3', lw=2,
            label=f'Developing: β={z_devg[0]:+.3f}')

    ax.set_xlabel('Alcohol Consumption (litres per capita)', fontsize=12)
    ax.set_ylabel('Life Expectancy (years)', fontsize=12)
    ax.set_title("A) Simpson's Paradox: Alcohol & Life Expectancy", fontsize=13)
    ax.legend(fontsize=9, loc='lower right')
    ax.grid(alpha=0.3)

    # --- Panel B: Box plot of alcohol by status ---
    ax2 = axes[1]
    data_box = [devg[ALC].dropna().values, dev[ALC].dropna().values]
    bp = ax2.boxplot(data_box, labels=['Developing', 'Developed'],
                     patch_artist=True, widths=0.5)
    bp['boxes'][0].set_facecolor('#2196F3')
    bp['boxes'][1].set_facecolor('#FF5722')
    for b in bp['boxes']:
        b.set_alpha(0.5)

    # Add means
    means = [np.mean(d) for d in data_box]
    ax2.scatter([1, 2], means, c='black', zorder=5, s=60, marker='D',
                label='Mean')
    for i, m in enumerate(means):
        ax2.annotate(f'{m:.1f} L', (i+1, m), textcoords="offset points",
                     xytext=(15, 5), fontsize=11, fontweight='bold')

    ax2.set_ylabel('Alcohol Consumption (litres per capita)', fontsize=12)
    ax2.set_title('B) Alcohol by Development Status', fontsize=13)
    ax2.legend(fontsize=10)
    ax2.grid(alpha=0.3, axis='y')

    plt.tight_layout()
    fig.savefig(out_dir / 'simpson_alcohol_scatter.png', dpi=200,
                bbox_inches='tight')
    plt.close(fig)
    print(f'\nScatter plot saved to {out_dir / "simpson_alcohol_scatter.png"}')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    df = load(INPUT)
    dev = df[df.is_developed == 1].reset_index(drop=True)
    devg = df[df.is_developed == 0].reset_index(drop=True)

    print(f'Total sample: {len(df)} obs, {df.Country.nunique()} countries')
    print(f'  Developed:  {len(dev)} obs, {dev.Country.nunique()} countries, '
          f'mean alcohol = {dev[ALC].mean():.2f} L')
    print(f'  Developing: {len(devg)} obs, {devg.Country.nunique()} countries, '
          f'mean alcohol = {devg[ALC].mean():.2f} L')
    print(f'  Mean life exp — Developed: {dev[Y].mean():.2f}, '
          f'Developing: {devg[Y].mean():.2f}')

    # ---- Correlations ----
    corr_all = df[[ALC, Y]].corr().iloc[0, 1]
    corr_dev = dev[[ALC, Y]].corr().iloc[0, 1]
    corr_devg = devg[[ALC, Y]].corr().iloc[0, 1]
    print(f'\nCorrelation Alcohol <-> Life Expectancy:')
    print(f'  Overall:    r = {corr_all:+.4f}')
    print(f'  Developed:  r = {corr_dev:+.4f}')
    print(f'  Developing: r = {corr_devg:+.4f}')

    results = []

    # Model 1: Simple bivariate — Alcohol only (pooled)
    r, _ = run_ols(df, '1_pooled_alcohol_only', Y, [ALC])
    results.append(r)

    # Model 2: Alcohol + development status dummy
    r, _ = run_ols(df, '2_pooled_alcohol_plus_status', Y,
                   [ALC, 'is_developed'])
    results.append(r)

    # Model 3: Alcohol + full controls (log GDP, Schooling, Status)
    r, _ = run_ols(df, '3_pooled_alcohol_plus_controls', Y,
                   [ALC, 'log_gdp', 'Schooling', 'is_developed'])
    results.append(r)

    # Model 4: Developed countries only
    r, _ = run_ols(dev, '4_developed_only', Y, [ALC, 'log_gdp', 'Schooling'])
    results.append(r)

    # Model 5: Developing countries only
    r, _ = run_ols(devg, '5_developing_only', Y, [ALC, 'log_gdp', 'Schooling'])
    results.append(r)

    # Model 6: TWFE (country + year fixed effects)
    print(f'\n{"="*70}')
    print('MODEL: 6_twfe_alcohol')
    print(f'{"="*70}')
    terms_fe = [ALC, 'log_gdp', 'Schooling']
    X_fe = df[terms_fe].astype(float)
    X_fe = X_fe.join(pd.get_dummies(df.Year, prefix='yr',
                                     drop_first=True, dtype=float))
    X_fe = X_fe.join(pd.get_dummies(df.Country, prefix='cty',
                                     drop_first=True, dtype=float))
    X_fe = sm.add_constant(X_fe, has_constant='add')
    groups = pd.factorize(df.Country)[0]
    fit_fe = sm.OLS(df[Y], X_fe).fit(cov_type='cluster',
                                      cov_kwds={'groups': groups})
    print(f'Alcohol coef = {fit_fe.params[ALC]:.6f}, '
          f'SE = {fit_fe.bse[ALC]:.6f}, '
          f'p = {fit_fe.pvalues[ALC]:.6g}')
    ci_fe = fit_fe.conf_int()
    print(f'95% CI = [{ci_fe.loc[ALC, 0]:.6f}, {ci_fe.loc[ALC, 1]:.6f}]')
    print(f'N = {int(fit_fe.nobs)};  R² = {fit_fe.rsquared:.6f}')
    results.append({
        'model': '6_twfe_alcohol',
        'n': int(fit_fe.nobs),
        'countries': int(df.Country.nunique()),
        'alcohol_coef': fit_fe.params[ALC],
        'alcohol_coef_clu': fit_fe.params[ALC],
        'alcohol_SE_clu': fit_fe.bse[ALC],
        'alcohol_p_clu': fit_fe.pvalues[ALC],
        'R2': fit_fe.rsquared,
        'adj_R2': fit_fe.rsquared_adj,
    })

    # ---- Summary table ----
    comparison = pd.DataFrame(results)
    comparison.to_csv(OUT / 'simpson_alcohol_results.csv', index=False)
    pd.set_option('display.width', 250)
    print(f'\n{"="*70}')
    print("SIMPSON'S PARADOX — SUMMARY TABLE")
    print(f'{"="*70}')
    print(comparison[['model', 'n', 'countries', 'alcohol_coef_clu',
                       'alcohol_SE_clu', 'alcohol_p_clu', 'R2']].to_string(
        index=False, float_format=lambda v: f'{v:.4f}'))

    sign_overall = '+' if results[0]['alcohol_coef'] > 0 else '−'
    sign_controlled = '+' if results[2]['alcohol_coef'] > 0 else '−'
    print(f'\n*** SIMPSON\'S PARADOX CHECK ***')
    print(f'  Pooled (no controls):   alcohol coefficient is {sign_overall} '
          f'({results[0]["alcohol_coef"]:+.4f})')
    print(f'  Pooled (with controls): alcohol coefficient is {sign_controlled} '
          f'({results[2]["alcohol_coef"]:+.4f})')
    if results[0]['alcohol_coef'] > 0 and results[2]['alcohol_coef'] < 0:
        print('  → SIGN REVERSAL CONFIRMED: Simpson\'s Paradox present!')
    elif results[0]['alcohol_coef'] > 0 and results[2]['alcohol_coef'] > 0:
        coef_ratio = results[2]['alcohol_coef'] / results[0]['alcohol_coef']
        print(f'  → Sign did not reverse, but coefficient shrank by '
              f'{(1-coef_ratio)*100:.0f}%')
        if coef_ratio < 0.5:
            print('  → Substantial attenuation consistent with partial '
                  'Simpson\'s pattern')

    # ---- Scatter plot ----
    make_scatter(df, OUT)
    print('\nDone.')


if __name__ == '__main__':
    main()
