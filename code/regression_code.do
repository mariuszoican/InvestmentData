* regression_code.do
* Translation of regression_code.R (data prep section)

cd "/Users/mariuszoican/Research/DataPurchaseProject/datapurchase_analysis"
*-----------------------------------------------------------------------
* Load data
*-----------------------------------------------------------------------
* Run from the directory containing this .do file, or set the path manually.
import delimited "processed_data/processed_panels.csv", clear case(preserve)

* NOTE: if build_panels.py wrote booleans as "True"/"False" strings,
* the 0/1 columns below will import as text and break the arithmetic.
* Uncomment and adapt as needed:
* foreach v in treated informative belief_informative gender_female ///
*     finance_course trading_experience high_education {
*     capture confirm string variable `v'
*     if !_rc replace `v' = "1" if `v'=="True"
*     if !_rc replace `v' = "0" if `v'=="False"
*     destring `v', replace
* }

*-----------------------------------------------------------------------
* Save raw versions before standardizing
*-----------------------------------------------------------------------
gen round_number_raw   = round_number
gen age_raw            = age
gen fin_quiz_raw       = fin_quiz
gen overconfidence_raw = overconfidence
gen risk_aversion_raw  = risk_aversion
gen last_imbalance_raw = last_imbalance
gen last_imbalance_abs = abs(last_imbalance)
gen last_return_raw    = last_return
gen last_return_abs    = abs(last_return_raw)


gen pay_choice=pay_for_data*treated

*-----------------------------------------------------------------------
* Standardize (z-score: (x - mean)/sd, sd with n-1, missing ignored)
*-----------------------------------------------------------------------
foreach v in round_number age fin_quiz overconfidence risk_aversion ///
    last_imbalance last_imbalance_abs last_return last_return_abs {
    quietly summarize `v'
    replace `v' = (`v' - r(mean)) / r(sd)
}

*-----------------------------------------------------------------------
* Create variables
*-----------------------------------------------------------------------
* correct_belief is NA in R when either input is missing; guard preserves that
gen correct_belief = (belief_informative == informative) ///
    if !missing(belief_informative, informative)

gen treated_imbalance            = treated * last_imbalance
gen treated_return               = treated * last_return
gen treated_informative          = treated * informative
gen treated_uninformative        = treated * (1 - informative)
gen treated_belief_informative   = treated * belief_informative
gen treated_belief_uninformative = treated * (1 - belief_informative)
gen treated_binf_imbalance       = treated * belief_informative * last_imbalance
gen treated_buninf_imbalance     = treated * (1 - belief_informative) * last_imbalance
gen belief_informative_imbalance = belief_informative * last_imbalance

* In R, rf_x_treated is assigned twice in one mutate(); the SECOND wins.
* So the surviving definition uses (1 - treated), despite the name.
gen rf_x_treated = return_forecast * (1 - treated)

gen z_x_treated     = last_imbalance * treated
gen z_x_control     = last_imbalance * (1 - treated)
gen r_x_treated     = last_return * treated
gen correct_forecast = 15 + last_imbalance_raw
gen forecast_error   = abs(return_forecast - correct_forecast)

*-----------------------------------------------------------------------
* Participant-level share of correct beliefs (missing ignored)
*-----------------------------------------------------------------------
egen share_correct = mean(correct_belief), by(participant_code)

*-----------------------------------------------------------------------
* Controls
*-----------------------------------------------------------------------
global controls "overconfidence fin_quiz gender_female age finance_course trading_experience risk_aversion high_education"
* Use as $controls in your regressions, e.g.
* reghdfe investment_amount treated $controls, absorb(participant_code) vce(cluster participant_code)
