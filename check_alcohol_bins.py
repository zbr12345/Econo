"""Analyze Alcohol vs Life Expectancy correlations across bins of GDP and Total expenditure.

Tests whether conditioning on narrower economic bands (GDP brackets / quartiles,
and Total expenditure brackets) causes the raw positive correlation to invert to negative.

Run: python check_alcohol_bins.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import scipy.stats as stats

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / 'data/processed/life_expectancy_final_clean.csv'
OUT = ROOT / 'output/simpson_alcohol'
Y = 'Life expectancy'
ALC = 'Alcohol'
X = 'Total expenditure'


def load(path):
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df.loc[df.Country.isin(['France', 'Canada']), 'Status'] = 'Developed'
    for c in [Y, ALC, X, 'GDP', 'Schooling']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.dropna(subset=[Y, ALC, X, 'GDP']).copy()
    df = df[df.GDP.gt(0) & df[X].gt(0)].copy()
    df['log_gdp'] = np.log(df.GDP)
    df['is_developed'] = df.Status.eq('Developed').astype(int)
    return df.reset_index(drop=True)


def calc_corr(sub, label):
    if len(sub) < 10:
        return {'group': label, 'n': len(sub), 'countries': sub['Country'].nunique(),
                'corr': np.nan, 'p_value': np.nan, 'slope': np.nan, 'sign': 'N/A'}
    r, p = stats.pearsonr(sub[ALC], sub[Y])
    slope, intercept, r_val, p_val, std_err = stats.linregress(sub[ALC], sub[Y])
    return {
        'group': label,
        'n': len(sub),
        'countries': sub['Country'].nunique(),
        'mean_alc': sub[ALC].mean(),
        'mean_le': sub[Y].mean(),
        'corr': r,
        'p_value': p,
        'slope': slope,
        'sign': 'NEGATIVE (-)' if r < 0 else 'POSITIVE (+)'
    }


def main():
    df = load(INPUT)
    OUT.mkdir(parents=True, exist_ok=True)

    print(f"Dataset loaded: {len(df)} observations, {df['Country'].nunique()} countries.\n")

    # 0. Baseline: Overall, Developed, and Developing
    print("=== 0. BASELINE BIVARIATE CORRELATIONS (ALCOHOL vs LIFE EXPECTANCY) ===")
    base_results = [
        calc_corr(df, "1. Overall Sample"),
        calc_corr(df[df.is_developed == 1], "2. Developed Only"),
        calc_corr(df[df.is_developed == 0], "3. Developing Only")
    ]
    print(pd.DataFrame(base_results)[['group', 'n', 'countries', 'mean_alc', 'corr', 'p_value', 'slope', 'sign']].to_string(index=False))
    print("\n" + "="*80 + "\n")

    # 1. GDP Quartiles
    print("=== 1. CORRELATIONS BY GDP PER CAPITA QUARTILES ===")
    df['gdp_quartile'] = pd.qcut(df['GDP'], q=4, labels=['Q1 (Poorest)', 'Q2 (Lower-Middle)', 'Q3 (Upper-Middle)', 'Q4 (Richest)'])
    gdp_q_results = []
    for q, sub in df.groupby('gdp_quartile', observed=True):
        min_gdp, max_gdp = sub['GDP'].min(), sub['GDP'].max()
        label = f"{q} [${min_gdp:.0f} - ${max_gdp:.0f}]"
        gdp_q_results.append(calc_corr(sub, label))
    df_gdp_q = pd.DataFrame(gdp_q_results)
    print(df_gdp_q[['group', 'n', 'countries', 'corr', 'p_value', 'slope', 'sign']].to_string(index=False))
    print("\n" + "="*80 + "\n")

    # 2. World Bank Income Groups
    print("=== 2. CORRELATIONS BY WORLD BANK INCOME GROUPS (Approximate GDPpc) ===")
    bins_wb = [0, 1045, 4095, 12695, np.inf]
    labels_wb = ['Low Income (<$1,045)', 'Lower-Middle Income ($1,045-$4,095)', 'Upper-Middle Income ($4,096-$12,695)', 'High Income (>$12,695)']
    df['income_group'] = pd.cut(df['GDP'], bins=bins_wb, labels=labels_wb)
    wb_results = []
    for g, sub in df.groupby('income_group', observed=True):
        wb_results.append(calc_corr(sub, str(g)))
    df_wb = pd.DataFrame(wb_results)
    print(df_wb[['group', 'n', 'countries', 'corr', 'p_value', 'slope', 'sign']].to_string(index=False))
    print("\n" + "="*80 + "\n")

    # 3. Total Health Expenditure Quartiles (% of Government Budget)
    print("=== 3. CORRELATIONS BY TOTAL HEALTH EXPENDITURE QUARTILES (% Government Expenditure) ===")
    df['exp_quartile'] = pd.qcut(df[X], q=4, labels=['Q1 (Low Share)', 'Q2 (Lower-Middle Share)', 'Q3 (Upper-Middle Share)', 'Q4 (High Share)'])
    exp_q_results = []
    for q, sub in df.groupby('exp_quartile', observed=True):
        min_x, max_x = sub[X].min(), sub[X].max()
        label = f"{q} [{min_x:.1f}% - {max_x:.1f}%]"
        exp_q_results.append(calc_corr(sub, label))
    df_exp_q = pd.DataFrame(exp_q_results)
    print(df_exp_q[['group', 'n', 'countries', 'corr', 'p_value', 'slope', 'sign']].to_string(index=False))
    print("\n" + "="*80 + "\n")

    # 4. Within Developing Countries: GDP Terciles
    print("=== 4. WITHIN DEVELOPING COUNTRIES: CORRELATION BY GDP TERCILES ===")
    dev_sub = df[df.is_developed == 0].copy()
    dev_sub['gdp_tercile'] = pd.qcut(dev_sub['GDP'], q=3, labels=['T1 (Poorest)', 'T2 (Intermediate)', 'T3 (Richest among Developing)'])
    dev_gdp_results = []
    for t, sub in dev_sub.groupby('gdp_tercile', observed=True):
        min_gdp, max_gdp = sub['GDP'].min(), sub['GDP'].max()
        label = f"Developing {t} [${min_gdp:.0f} - ${max_gdp:.0f}]"
        dev_gdp_results.append(calc_corr(sub, label))
    df_dev_gdp = pd.DataFrame(dev_gdp_results)
    print(df_dev_gdp[['group', 'n', 'countries', 'corr', 'p_value', 'slope', 'sign']].to_string(index=False))
    print("\n" + "="*80 + "\n")

    # 5. 2D Cross-Matrix: GDP Terciles x Health Expenditure Terciles
    print("=== 5. 2D CROSS-MATRIX: GDP TERCILES x HEALTH EXPENDITURE TERCILES ===")
    df['gdp_t'] = pd.qcut(df['GDP'], q=3, labels=['Low GDP', 'Medium GDP', 'High GDP'])
    df['exp_t'] = pd.qcut(df[X], q=3, labels=['Low Health Exp', 'Medium Health Exp', 'High Health Exp'])
    matrix_results = []
    for (g, e), sub in df.groupby(['gdp_t', 'exp_t'], observed=True):
        r_val, p_val = stats.pearsonr(sub[ALC], sub[Y])
        matrix_results.append({
            'GDP_Bracket': g,
            'Health_Exp_Bracket': e,
            'n': len(sub),
            'corr': r_val,
            'p_value': p_val,
            'sign': 'NEGATIVE (-)' if r_val < 0 else 'POSITIVE (+)'
        })
    df_matrix = pd.DataFrame(matrix_results)
    pivot_corr = df_matrix.pivot(index='GDP_Bracket', columns='Health_Exp_Bracket', values='corr')
    pivot_sign = df_matrix.pivot(index='GDP_Bracket', columns='Health_Exp_Bracket', values='sign')
    print("Pearson Correlation Matrix r(Alcohol, Life Expectancy):")
    print(pivot_corr.round(4).to_string())
    print("\nSign Matrix:")
    print(pivot_sign.to_string())

    # Save summary tables to CSV
    all_summary = pd.concat([
        pd.DataFrame(base_results).assign(category='0. Baseline'),
        df_gdp_q.assign(category='1. GDP Quartiles'),
        df_wb.assign(category='2. WB Income Groups'),
        df_exp_q.assign(category='3. Health Exp Quartiles'),
        df_dev_gdp.assign(category='4. Developing GDP Terciles')
    ], ignore_index=True)
    all_summary.to_csv(OUT / 'alcohol_bins_correlations.csv', index=False)
    df_matrix.to_csv(OUT / 'alcohol_cross_matrix_gdp_exp.csv', index=False)
    print(f"\nResults successfully saved to {OUT}")


if __name__ == '__main__':
    main()
