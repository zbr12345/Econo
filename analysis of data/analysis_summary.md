# Life Expectancy: Read-only exploratory data analysis

**Input CSV:** `C:\Users\talel\Downloads\Econo\data\processed\life_expectancy_final_clean.csv`
**Original dimensions:** 2702 rows x 22 columns
**Target:** `Life expectancy`

## Data integrity

The original CSV was read only. No rows were deleted, no values were imputed, and no source columns were changed or overwritten.

- SHA-256 before analysis: `585b035171a981d2d1e66a2230a7f219a3765c2f572380f9bcf19b22616fde4e`
- SHA-256 after analysis: `585b035171a981d2d1e66a2230a7f219a3765c2f572380f9bcf19b22616fde4e`
- Source file unchanged: **YES**

Missing values are reported here, not repaired:

| Column | Missing count | Missing % |
|---|---:|---:|
| Country | 0 | 0.00% |
| Year | 0 | 0.00% |
| Status | 0 | 0.00% |
| Life expectancy | 0 | 0.00% |
| Adult Mortality | 0 | 0.00% |
| infant deaths | 0 | 0.00% |
| Alcohol | 165 | 6.11% |
| percentage expenditure | 0 | 0.00% |
| Hepatitis B | 484 | 17.91% |
| Measles | 0 | 0.00% |
| BMI | 16 | 0.59% |
| under-five deaths | 0 | 0.00% |
| Polio | 0 | 0.00% |
| Total expenditure | 0 | 0.00% |
| Diphtheria | 0 | 0.00% |
| HIV/AIDS | 0 | 0.00% |
| GDP | 0 | 0.00% |
| Population | 464 | 17.17% |
| thinness  1-19 years | 16 | 0.59% |
| thinness 5-9 years | 16 | 0.59% |
| Income composition of resources | 0 | 0.00% |
| Schooling | 0 | 0.00% |

## Relationships with life expectancy

Each plot and correlation uses only rows where that particular pair of variables is observed. This pairwise handling is local to that calculation; it does not remove rows from the source CSV.

| Feature | n | Pearson r | Pearson p-value | Spearman rho | Spearman p-value |
|---|---:|---:|---:|---:|---:|
| Schooling | 2702 | 0.770 | < 0.001 | 0.827 | < 0.001 |
| ln(GDP per capita) | 2702 | 0.797 | < 0.001 | 0.846 | < 0.001 |
| Total expenditure on health | 2702 | 0.497 | < 0.001 | 0.588 | < 0.001 |
| Adult mortality | 2702 | -0.684 | < 0.001 | -0.646 | < 0.001 |

## GDP transformation: raw GDP vs natural log GDP

The GDP scatterplot uses the natural logarithm of GDP per capita, calculated only for strictly positive GDP observations. The raw GDP column in the source CSV is preserved unchanged. The table below compares the two bivariate relationships using the same pairwise available-observation rule.

| GDP version | n | Pearson r | Pearson p-value | Spearman rho | Spearman p-value |
|---|---:|---:|---:|---:|---:|
| Raw GDP per capita | 2702 | 0.583 | < 0.001 | 0.846 | < 0.001 |
| ln(GDP per capita) | 2702 | 0.797 | < 0.001 | 0.846 | < 0.001 |

## Automatically generated observations

- Strongest positive Pearson association: **ln_GDP** (r = 0.797; n = 2702).
- Strongest negative Pearson association: **Adult Mortality** (r = -0.684; n = 2702).
- Very weak linear associations (|r| < 0.20): `infant deaths`, `Measles`, `Population`.

## Interpretation cautions

- Correlation does not establish causation.
- These are observational country-year records. Countries may appear in multiple years, so observations may not be independent.
- GDP per capita is often highly skewed. The GDP scatterplot uses ln(GDP) to reduce right-skew; non-positive GDP values cannot be logged and are omitted only from the log-GDP plot and its statistics. Raw GDP is retained in the correlation matrix and compared in a separate table.
- `Total expenditure` is general government expenditure on health as a percentage of total government expenditure. It is not the same as `percentage expenditure` (health expenditure as a percentage of GDP per capita).
- Pearson correlation describes linear association; Spearman correlation describes monotonic rank association.

## Correlation matrix

The matrix includes numeric variables and excludes `Country`, `Status`, and `Year` from the correlation analysis, consistent with the GitHub project's decision to remove Country and Year from predictor analysis. The original file still retains those columns.

`Life expectancy`, `Adult Mortality`, `infant deaths`, `Alcohol`, `percentage expenditure`, `Hepatitis B`, `Measles`, `BMI`, `under-five deaths`, `Polio`, `Total expenditure`, `Diphtheria`, `HIV/AIDS`, `GDP`, `Population`, `thinness  1-19 years`, `thinness 5-9 years`, `Income composition of resources`, `Schooling`, `ln_GDP`

## Generated files

- `figures/schooling_vs_life_expectancy.png`
- `figures/gdp_vs_life_expectancy.png`
- `figures/total_expenditure_vs_life_expectancy.png`
- `figures/adult_mortality_vs_life_expectancy.png`
- `figures/correlation_matrix.png`
- `figures/life_expectancy_distribution.png`
- `tables/pearson_correlation_matrix.csv`
- `tables/correlation_pair_counts.csv`
- `tables/life_expectancy_correlations.csv`
- `tables/four_feature_correlations.csv`
- `tables/gdp_raw_vs_log_comparison.csv`
- `data_audit.csv`
