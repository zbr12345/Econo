# README
# Project Setup and Execution Guide

## 1. Install the environment

Install Anaconda or Miniconda, then open Anaconda Prompt and run:

```bash
conda create -n eco-repro python=3.12
conda activate eco-repro
```

Change to the project folder, replacing the path below with your own:

```bash
cd "PATH/TO/PROJECT"
python -m pip install -r requirements.txt
```

Keep the supplied CSV files in `data/raw/`. No additional data download is needed.

The original datasets are from:
API_SH.XPD.GHED.GE.ZS_DS2_en_csv_v2_8352.csv : https://data.worldbank.org/indicator/SH.XPD.GHED.GE.ZS

gdp_per_capita.csv : https://www.kaggle.com/datasets/zgrcemta/world-gdpgdp-gdp-per-capita-and-annual-growths

life_expectancy_by_country.csv : https://www.kaggle.com/datasets/ulrikthygepedersen/life-expectancy

kaggle_life_expectancy.csv : https://www.kaggle.com/datasets/vikramamin/life-expectancy-who

## 2. Prepare the data

Run this first:

```bash
python data_process.py
```

The script merges the replacement data, cleans the dataset, and creates `data/processed/life_expectancy_final_clean.csv`. It prints `done` when finished.

## 3. Run the analysis

After preparing the data, run the following scripts from the project folder:

| Command                                                      | Purpose                                                      |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| `python analyze_life_expectancy.py --input data/processed/life_expectancy_final_clean.csv --output output/descriptive_analysis` | Generate descriptive statistics, correlations, and exploratory figures. |
| `python plot_descriptive_evidence.py`                        | Generate the descriptive scatter plots and correlation matrix. |
| `python regression_no_lagged.py`                             | Run the baseline regressions with and without Adult Mortality and generate comparison figures. |
| `python regression_marginal_effect.py`                       | Run the six nonlinear regressions and generate fitted-curve and slope figures. |
| `python analysis_simpson_alcohol.py`                         | Analyze alcohol consumption and life expectancy under different controls and country groups. |
| `python check_alcohol_bins.py`                               | Compare alcohol–life expectancy correlations across income and expenditure groups. |
| `python plot_simpson_alcohol_visualizations.py`              | Generate the alcohol-analysis presentation figures.          |
| `python regression_lagged.py --lag 1`                        | Run the one-year-lagged linear regression. Replace `1` with `3` for the three-year lag. |
| `python regression_marginal_lagged_piecewise.py --lags 0 1 3` | Compare contemporaneous, one-year, and three-year piecewise regressions. |
| `python regression_reverse_causality.py`                     | Run the health-shock and reverse-causality checks.           |
| `python visualize_results_marginal_lagged.py`                | Generate summary figures for the lagged and health-shock analyses. |

Regression results appear in the terminal. Generated figures and saved analysis tables are placed under `output/`. Re-running a script updates its outputs.

# Contributions of each members:
ZHANG Bairong:I developed the data-processing pipeline to harmonize and merge life expectancy, GDP per capita, and government healthcare expenditure data, handle missing values, and correct development-status classifications. I implemented baseline OLS models with and without adult mortality, tested nonlinear relationships in the full sample and within development groups, and created visualizations to present and interpret the results.

TALEL Khemiri:
I conducted the exploratory data analysis of the dataset. I analyzed the distribution of life expectancy and examined its relationships with key socioeconomic and health indicators, including GDP per capita, schooling, government healthcare expenditure, and adult mortality. I calculated Pearson and Spearman correlations, and generated the correlation matrix and corresponding visualizations. I also analyzed and interpretedpotential multicollinearity between explanatory variables.

Enzo Sakhinis:
I extended the analysis to test whether the effect of government healthcare expenditure appears with a delay and whether the results are affected by reverse causality. I estimated a piecewise linear model with expenditure lagged by 0, 1 and 3 years on a common sample, with a fixed threshold at the median spending and country-clustered standard errors, and compared it with a linear specification using AIC and BIC. I also estimated fixed-effects models with country and year effects and log, lagged expenditure. To address reverse causality, I defined a health-shock indicator (a fall in life expectancy of at least one year), tested whether shocks lead to higher spending, ran an event study around the shocks, and re-estimated the effect of lagged expenditure with shock and HIV/AIDS controls, after dropping shock observations and shock countries, with and without fixed effects. I also created the visualizations for these results and presented this part of the project.
