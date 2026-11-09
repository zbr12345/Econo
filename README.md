# README

The group worked collaboratively throughout the project, despite having individual tasks. Everyone contributed to all stages, from choosing the project and making decisions about data processing to conducting the analyses and preparing the final presentation.

### Contributions of each members:

ZHANG Bairong:I developed the data-processing pipeline to harmonize and merge life expectancy, GDP per capita, and government healthcare expenditure data, handle missing values, and correct development-status classifications. I implemented baseline OLS models with and without adult mortality, tested nonlinear relationships in the full sample and within development groups, and created visualizations to present and interpret the results.

PINHEIRO PIERAZOLLI Enzo : Responsible for the analysis of spurious correlations, contributions to the interpretation and writing of the empirical report, and participation in data preprocessing. Identified and investigated Simpson's Paradox, examining how cross-country differences could distort the observed relationship between healthcare expenditure and life expectancy. Developed visualizations for the final presentation.

TALEL Khemiri:
I conducted the exploratory data analysis of the dataset. I analyzed the distribution of life expectancy and examined its relationships with key socioeconomic and health indicators, including GDP per capita, schooling, government healthcare expenditure, and adult mortality. I calculated Pearson and Spearman correlations, and generated the correlation matrix and corresponding visualizations. I also analyzed and interpretedpotential multicollinearity between explanatory variables.

Enzo Sakhinis:
I extended the analysis to test whether the effect of government healthcare expenditure appears with a delay and whether the results are affected by reverse causality. I estimated a piecewise linear model with expenditure lagged by 0, 1 and 3 years on a common sample, with a fixed threshold at the median spending and country-clustered standard errors, and compared it with a linear specification using AIC and BIC. I also estimated fixed-effects models with country and year effects and log, lagged expenditure. To address reverse causality, I defined a health-shock indicator (a fall in life expectancy of at least one year), tested whether shocks lead to higher spending, ran an event study around the shocks, and re-estimated the effect of lagged expenditure with shock and HIV/AIDS controls, after dropping shock observations and shock countries, with and without fixed effects. I also created the visualizations for these results and presented this part of the project.