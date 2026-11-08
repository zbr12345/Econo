# From Naive Correlation to Causal Identification: An Econometric Story of Government Health Expenditure and Longevity

**Course / Context**: Applied Econometrics
**Panel Dataset**: 2000–2015 (181 Countries, 2,702 Observations)
**Date**: November 2026

---

## 1. Introduction

Does allocating a larger share of a government's fiscal budget to healthcare increase population longevity? In global public policy discussions, an intuitive positive association is often presumed: nations with higher public health spending shares enjoy longer life expectancies. However, from an econometric perspective, observing that high-spending nations live longer does not establish that public budgetary reallocations causally generate those longevity gains. Cross-national comparisons are profoundly vulnerable to omitted-variable bias, reverse causality, and unobserved institutional heterogeneity.

This study develops an incremental empirical investigation across 181 nations from 2000 to 2015, moving step-by-step from raw cross-sectional correlations to panel identification with Two-Way Fixed Effects, nonlinear threshold tests, dynamic lag horizons, and health shock diagnostics.

---

## 2. Data Pre-Processing

### 2.1 Documenting the Primary Explanatory Variable

The core explanatory variable, `Total expenditure`, is defined strictly following the official World Bank:

$$
\text{Total expenditure} \equiv \text{Domestic general government expenditure on health as a percentage of general government expenditure}
$$

It is essential to emphasize what this variable measures: it captures **fiscal prioritization**—the proportion of the public budget envelope allocated to healthcare. It does *not* measure real per-capita monetary spending. In a low-income nation, a 15% budget share may represent less than \$20 per person annually, whereas an 8% share in an advanced economy represents thousands of dollars per citizen.

### 2.2 The Data Harmonization Pipeline (`data_process.py`)

The original Kaggle compilation suffered from crowdsourced discrepancies, unreconciled country names, and inaccurate developmental classifications. To establish an authoritative panel, primary sources were integrated:

1. Official WHO life expectancy records (`life_expectancy_by_country.csv`).
2. World Bank constant USD GDP per capita series (`gdp_per_capita.csv`).
3. World Bank health expenditure shares (`API_SH.XPD.GHED.GE.ZS`).

Country identifiers were harmonized across 28 nation pairs (e.g., *Bolivia*, *Cote d'Ivoire*, *Tanzania*), non-positive GDP records removed, and developmental classifications corrected (specifically France and Canada, mislabeled as 'Developing' in the raw file, reclassified to 'Developed'). The resulting clean panel contains **2,702 balanced country-year records across 181 countries spanning 2000–2015.**

## 3. Motivating Evidence & Correlation Structure

### 3.1 Aligning Visualizations to Budget Share

To guarantee strict methodological alignment between descriptive patterns and econometric specifications, all motivating scatter plots and correlation matrices were explicitly formatted using `health_exp_share` (% of government expenditure) rather than level spending. This alignment avoids misleading impressions that could arise from mixing absolute dollar expenditures with budget shares.

### 3.2 Pearson Correlation Matrix & Interpretation

|                             | Life expectancy | Total expenditure | GDP per capita |    log(GDPpc)    |    Schooling    |     Alcohol     | Adult Mortality |
| --------------------------- | :--------------: | :---------------: | :------------: | :--------------: | :--------------: | :-------------: | :-------------: |
| **Life expectancy**   | **1.000** |      +0.497      |     +0.583     | **+0.797** | **+0.770** |     +0.385     |     −0.684     |
| **Total expenditure** |      +0.497      |  **1.000**  |     +0.365     | **+0.475** | **+0.503** |     +0.397     |     −0.303     |
| **log(GDPpc)**        | **+0.797** |      +0.475      |     +0.790     | **1.000** | **+0.788** |     +0.548     |     −0.488     |
| **Schooling**         | **+0.770** |      +0.503      |     +0.566     | **+0.788** | **1.000** |     +0.546     |     −0.452     |
| **Alcohol**           |      +0.385      |      +0.397      |     +0.432     |      +0.548      |      +0.546      | **1.000** |     −0.172     |
| **Adult Mortality**   |     −0.684     |      −0.303      |    −0.373    |     −0.488     |     −0.452     |     −0.172     | **1.000** |

Bivariate Pearson correlations highlight the underlying web of macroeconomic co-movements. While life expectancy exhibits a moderate positive association with health expenditure share ($r = +0.497$), it is far more powerfully correlated with national income ($r = +0.797$ with $\log(\text{GDPpc})$) and education ($r = +0.770$ with Schooling). Crucially, the health expenditure share is itself substantially correlated with $\log(\text{GDPpc})$ ($r = +0.475$) and Schooling ($r = +0.503$). Wealthier, more educated societies consistently dedicate larger fractions of their public budgets to healthcare. Consequently, unadjusted regressions between health spending and longevity are inevitably contaminated by the broader benefits of general national modernization.

---

## 4. Simpson's Paradox & The Confounding Role of National Wealth

To provide a vivid, intuitive demonstration of how omitted national wealth can distort empirical findings, we examined national alcohol consumption (`Alcohol`, pure litres per capita per year). In naive cross-country pooled data, drinking alcohol exhibits a strong, statistically significant positive association with longevity: each additional litre of alcohol appears associated with living 0.87 years longer ($\beta = +0.8651$, $r = +0.3851$, $p < 0.0001$).

This finding is a textbook illustration of **Simpson's Paradox**: high-income nations drink nearly three times as much alcohol as developing nations (9.75 L vs. 3.35 L), but their superior living standards, nutrition, and advanced medical infrastructure afford them vastly greater longevity (78.5 vs. 66.9 years).

Partitioning countries into 'Developed' and 'Developing' reversed the slope for developed nations ($\beta = -0.366$, $p < 0.001$), but left developing nations with an apparent positive slope ($\beta = +0.388$, $r = +0.148$). The reason is internal economic heterogeneity: developing nations span per-capita incomes from \$112 to \$85,000. Within that vast group, richer developing nations drink more and live longer than impoverished developing nations.

Once developing countries were stratified into homogeneous **GDP per capita terciles**, the relationship inverted to strictly negative in every single tier:

- **Tercile 1 (Poorest: \$112–\$1,197)**: $\beta = \mathbf{-0.5241}$ ($r = -0.17$, $p < 0.0001$)
- **Tercile 2 (Middle: \$1,198–\$4,354)**: $\beta = \mathbf{-0.2618}$ ($r = -0.11$, $p = 0.005$)
- **Tercile 3 (Richest developing: \$4,359–\$85,076)**: $\beta = \mathbf{-0.2277}$ ($r = -0.16$, $p < 0.0001$)
- **Two-Way Fixed Effects Panel Model**: $\beta_{\text{TWFE}} = \mathbf{-0.1458}$ ($p = 0.0040$)

This establishes the central econometric warning of our investigation: national income is a master confounder capable of masking deleterious health factors as positive, and it will distort public spending estimates unless properly addressed.

---

## 5. Progressive Econometric Modeling & Control Selection

### 5.1 Baseline Model Specification & Control Selection

The modeling sequence begins by establishing a contemporaneous baseline model across 2,702 country-year observations (171 countries) to assess the relationship between general government health expenditure share and national life expectancy.

A foundational methodological decision in this empirical design is the deliberate exclusion of `Adult Mortality`. **Adult Mortality** represents an endogenous mediator rather than an exogenous confounder: population life expectancy is mathematically calculated from age-specific mortality tables. Including adult mortality in the regression equation controls away the primary biological mechanism through which healthcare spending improves survival, inducing severe over-controlling bias (artificially compressing the estimated expenditure coefficient from $+0.1927$ down to $+0.1484$).

Consequently, the preferred baseline specification retains strictly pre-determined exogenous confounders—$\log(\text{GDP per capita})$ (economic productivity), `Schooling` (human capital), and development status (`Developed`):

$$
\text{LifeExpectancy}_{it} = \beta_0 + \beta_1 \text{TotalExpenditure}_{it} + \beta_2 \log(\text{GDP}_{it}) + \beta_3 \text{Schooling}_{it} + \beta_4 \text{Developed}_i + u_{it}
$$

Under this baseline specification, the estimated coefficient on government health expenditure share is $\beta_1 = +0.1927$ ($p < 0.001$, $R^2 = 0.695$), establishing a positive cross-sectional association after adjusting for fundamental socioeconomic development.

---

### 5.2 Analyzing Marginal Effects & Non-Linear Functional Forms

To analyze whether the marginal return to healthcare spending is constant or exhibits diminishing returns, the empirical strategy moves to examining non-linear functional forms. Four distinct non-linear specifications were estimated on the baseline sample (excluding `Adult Mortality` and conditioning on $\log(\text{GDP})$, `Schooling`, and `Developed`), the following was considered the most appropriate:

1. **Piecewise Linear Specification**: Allowing the slope to change above the median threshold ($k = 8.76\%$):
   - Slope below 8.76%: $b = +0.2707$ ($p < 0.001$, 95% CI: $[0.1573, 0.3842]$)
   - Slope change above 8.76%: $c = -0.1127$ ($p = 0.137$, 95% CI: $[-0.2612, 0.0359]$)
   - Slope above 8.76%: $b + c = +0.1581$ ($p < 0.001$, 95% CI: $[0.0921, 0.2241]$)

None of the non-linear curvature terms in the overall sample reach statistical significance at conventional levels ($p > 0.10$). While the piecewise linear specification delivers the strongest in-sample fit (lowest AIC and BIC), the estimated attenuation in slope above the median ($-0.1127$) remains statistically indistinguishable from zero. As a result, cross-sectional non-linear modeling fails to confirm the presence of diminishing marginal returns.

---

### 5.3 Panel Identification with Two-Way Fixed Effects

To eliminate potential bias arising from unobserved time-invariant country heterogeneity (such as geography, deep institutional quality, and long-term historical infrastructure) as well as global annual shocks, the empirical design incorporates a panel **Two-Way Fixed Effects (TWFE)** model:

$$
\text{LifeExpectancy}_{it} = \beta_1 \text{TotalExpenditure}_{it} + \beta_2 \log(\text{GDP}_{it}) + \beta_3 \text{Schooling}_{it} + \alpha_i + \lambda_t + u_{it}
$$

Once permanent country attributes ($\alpha_i$) and common global year shocks ($\lambda_t$) are conditioned out, the estimated within-country coefficient collapses to $\beta_1 = -0.0323$ ($p = 0.224$, 95% CI: $[-0.0843, 0.0197]$). Within-country reallocations of the public budget toward healthcare produce no statistically observable gains in population longevity over time.

---

### Summary of Model Progression

| Model Progression                  | Specification & Functional Form                  | Expenditure Coef ($\beta_1$) | Non-Linear Term ($c$) | p-value ($c$) | $R^2$ | Econometric Diagnosis                                               |
| ---------------------------------- | ------------------------------------------------ | :----------------------------: | :---------------------: | :-------------: | :-----: | ------------------------------------------------------------------- |
| **Baseline with Mediator**   | Linear + log(GDP) + Schooling + Adult Mortality  |            +0.1484            |           —           |       —       |  0.789  | Over-controlling bias from endogenous mediator                      |
| **Baseline Exogenous Model** | Linear + log(GDP) + Schooling + Developed        |       **+0.1927**       |           —           |       —       |  0.695  | Preferred baseline; positive cross-sectional association            |
| **Quadratic Curvature**      | $bX + cX^2$ + Exogenous Controls               |            +0.1619            |         +0.0012         |      0.614      |  0.695  | Quadratic term statistically insignificant                          |
| **Linear-Logarithmic**       | $bX + c\log(X)$ + Exogenous Controls           |            +0.1769            |         +0.1499         |      0.762      |  0.695  | Logarithmic term statistically insignificant                        |
| **Linear-Reciprocal**        | $bX + c/X$ + Exogenous Controls                |            +0.1960            |         +0.2166         |      0.877      |  0.695  | Reciprocal term statistically insignificant                         |
| **Piecewise Linear**         | $bX + c\max(X - 8.76, 0)$ + Exogenous Controls |            +0.2707            |   **−0.1127**   |      0.137      |  0.695  | Best in-sample fit, but slope change is statistically insignificant |
| **Two-Way Fixed Effects**    | Country FE + Year FE + log(GDP) + Schooling      |       **−0.0323**       |           —           |       —       |  0.985  | Within-country effect is statistically indistinguishable from zero  |

---

## 6. Dynamic Lags, Piecewise Thresholds & The Rejection of Diminishing Returns

To rigorously examine whether the null finding of Model 3 was masking underlying non-linearities, we tested for diminishing marginal returns. A standard economic conjecture posits that public health spending yields substantial returns at low levels of expenditure, but flattens out as systems mature.

To test diminishing returns, we estimated a piecewise linear model fixing a threshold at the sample median spending, 8.76 percent of government budget, and allowed the slope to change above it. If returns were diminishing, the estimated curve would flatten after the threshold. It does not. The estimated slope change is small and negative, minus 0.075 years per percentage point, but far from statistically significant, with a country-clustered p-value of 0.76. Consequently, we find no empirical evidence of diminishing marginal returns.

We next investigated whether the lack of contemporaneous effect was due to temporal delay: public health investments (such as constructing clinics, training medical professionals, or launching immunization drives) may take multiple years to manifest in national mortality tables. To test whether health spending takes years to work, we compared spending in the same year ($L=0$), one year earlier ($L=1$), and three years earlier ($L=3$) on a common, balanced sample of 2,189 observations across 171 countries.

The estimated effect does not grow with the lag. In fact, it slightly decreases (from 0.2456 at $L=0$ down to 0.1860 at $L=3$ for the base slope), and the confidence intervals for the slope change always include zero. There is no empirical sign of a delayed effect.

| Lag Horizon                         | Slope Below Knot (8.76%) | Slope Change Above Knot | p-value (Cluster SE) |  Net Slope Above Knot  |
| ----------------------------------- | :----------------------: | :---------------------: | :------------------: | :---------------------: |
| **Contemporaneous ($L=0$)** |         +0.2456         |        −0.0767        |        0.7456        | +0.1689 ($p = 0.074$) |
| **1-Year Lag ($L=1$)**      |         +0.2321         |        −0.0749        |        0.7562        | +0.1572 ($p = 0.115$) |
| **3-Year Lag ($L=3$)**      |         +0.1860         |        −0.0386        |        0.8783        | +0.1474 ($p = 0.174$) |

---

## 7. Reverse Causality, Health Shocks, and Panel Identification

A primary theoretical threat to causal identification is reverse causality: our initial proposal raised the concern that a severe health crisis lowers life expectancy and simultaneously pushes governments to increase health spending in response, which would disguise a true positive effect by biasing the regression coefficient downward.

To test this possibility, we defined a health crisis shock as an annual fall in national life expectancy of at least one year ($\Delta \text{LifeExp} \le -1.0$). Across the entire 2000–2015 panel, there are 26 such acute crisis episodes (such as Haiti in 2010 following the catastrophic earthquake, or Syria in 2012 during the outbreak of civil war). In the shock year, national life expectancy collapses by an average of about two and a half years. However, evaluating the fiscal response demonstrates that government health spending does not react in a clear or systematic way: the estimated annual spending change following a shock is an increase of approximately 0.2 percentage points and is statistically insignificant ($\beta = +0.2008$, $p = 0.465$; and $\beta = -0.0225$, $p = 0.724$ when regressed on lagged life expectancy drops).

This led to the ultimate diagnostic test: does controlling for shocks or removing crisis episodes reveal a positive spending effect? The empirical contrast is striking. Estimations without fixed effects (pooled cross-sectional models) show a positive association of about 0.2 years of life expectancy per percentage point of health expenditure ($\beta \approx +0.180$ to $+0.249$, $p < 0.05$), and neither controlling for lagged shocks, controlling for HIV prevalence, nor dropping shock-affected observations changes this magnitude.

However, once country and year fixed effects are added—comparing each country with itself over time—the estimated effect drops to precisely zero in every version ($\beta = -0.0085$ in baseline TWFE; $\beta = -0.0059$ with shock and HIV controls; $\beta = -0.0068$ dropping shock rows; and $\beta = -0.0007$ dropping shock countries entirely). This proves that the positive link observed in pooled regressions reflects broad cross-sectional development differences between nations, not changes in spending within a country over time.

To conclude: our empirical tests find **no diminishing returns, no delayed multi-year effect, and no detectable reverse causality**. Importantly, this does not prove that health spending is useless. Our primary measure captures a public budget share rather than real spending per person, and our identification is informed by a finite sample containing 26 acute health shock episodes.

---

## 8. Theoretical Context: Cross-Country Medical Technology Spillovers

A comprehensive theoretical discussion must address cross-country medical technology spillovers (such as vaccines, antivirals, and modern pharmaceuticals developed in advanced economies benefiting poorer nations). Advanced nations finance the massive fixed capital and scientific R&D costs required to invent medical technologies. Once discovered, these innovations diffuse globally at very low marginal cost, often distributed through international consortia (such as the WHO, Gavi, and the Global Fund).

As a result, developing nations achieve dramatic improvements in population longevity (e.g., eradicating polio, controlling measles, deploying antiretrovirals) without needing to expand their domestic health budget shares. This mechanism explains why cross-group slope comparisons are difficult to interpret cleanly: the observed return to domestic healthcare spending in developing nations is confounded and compressed by external global technology spillovers.

Some possible explanations are:

- Developed countries already have strong health infrastructure and are close to the medical frontier. Extra spending therefore tends to produce small and slow gains in life expectancy. Furthermore, our dataset covers only a 15-year period, which is relatively short for capturing the long-term effects of healthcare spending on life expectancy and may therefore limit our ability to identify its full impact.
- Developing countries have much more room to improve, and progress can be fast. But they often lack the funds to invest. In many cases, wealthier countries and international donors provide part of the money, so life expectancy can improve even without a large increase in the government’s own health budget. Our model does not capture this: it only measures domestic government spending as a share of the budget, not foreign aid.

---

## 9. Conclusion

### 1. The Empirical Reality: A Non-Causal Link

The naive cross-sectional association between government health expenditure share and life expectancy ($+0.84$ years per percentage point) is non-causal. Once national wealth ($\log \text{GDP}$) and education (`Schooling`) are controlled for, this positive effect completely collapses. When evaluating within-country changes over time via **Two-Way Fixed Effects (TWFE)**, the estimated impact falls to precisely zero ($\beta = -0.032$, $p = 0.224$). Our diagnostic tests confirm:

* **Diminishing returns**: A piecewise threshold at median spending (8.76%) shows no significant flattening ($p = 0.76$).
* **Delayed effect**: Dynamic lags (1-year and 3-year horizons) effects could not be observed.
* **Reverse causality**: Acute health crises ($\Delta \text{LifeExp} \le -1.0$ year across 26 historical shock episodes) do not trigger compensatory spending spikes.

### 2. Theoretical Mechanisms & Technology Spillovers

Two structural mechanisms explain why within-country budgetary reallocations fail to move aggregate longevity:

1. **Budget Share vs. Real Purchasing Power**: `Total expenditure` measures the political priority of health (% of the public budget), not real dollars per citizen. A 15% allocation in a poor country yields under \$20 per person, whereas an 8% share in a rich nation provides thousands. Real resources are dictated by GDP, which absorbs the cross-sectional explanatory power.
2. **Cross-Country Medical Spillovers**: Advanced nations finance the fixed R&D costs of medical breakthroughs (vaccines, antivirals, antibiotics). These technologies diffuse globally at near-zero marginal cost through agencies like the WHO, Gavi, and the Global Fund. Consequently, developing nations achieve massive longevity gains without needing to increase their domestic health budget shares, obscuring cross-group slope comparisons.
