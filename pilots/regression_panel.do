/**********************************************************************
  Project: InvestmentData (Pilots)
  Purpose: Produce regression tabels
**********************************************************************/


clear all
set more off

*-------------------------------
* 0) Load data
*-------------------------------
local directory "/Users/mariuszoican/Research/InvestmentData/"
local datafile  "`directory'pilots/processed_data_pilots"   // add .csv if needed
local out_bel   "`directory'tables/beliefs_table.tex"
local out_for   "`directory'tables/forecast_table.tex"
local out_iv   "`directory'tables/iv_table.tex"
local out_select   "`directory'tables/select_table.tex"

import delimited using "`datafile'", clear


*-------------------------------
* 2) Data quality / attention measures
*-------------------------------
* Correct belief indicator: belief matches objective informative state
gen byte correct_belief = (belief_informative == informative)
label var correct_belief "Correct belief (belief_informative == informative)"

* Share correct per participant
bysort participant_code: egen share_correct = mean(correct_belief)
label var share_correct "Share correct beliefs (participant)"

* Optional restriction (uncomment if desired)
* keep if share_correct >= 0.30


*-------------------------------
* 3) Variable labels 
*-------------------------------
label var fin_quiz           "Financial quiz score"
label var age                "Age"
label var gender_female      "Gender (female)"
label var finance_course     "Finance course taken"
label var self_literacy      "Self-assessed financial literacy"
label var overconfidence     "Overconfidence"
label var trading_experience "Trading experience"
label var risk_aversion      "Risk tolerance"
label var round_number       "Round number"
label var return_forecast    "Return forecast"
label var investment_share   "Investment (\%)"
label var investment_amount   "Investment (E\$)"

label var treated            "Treated"
label var paid_round         "Paid round"
label var pay_for_data       "Choose to pay"
label var informative        "Informative round"
label var belief_informative "Belief informative"
label var last_imbalance_1   "Last imbalance"
label var last_return_1      "Last return"

*-------------------------------
* 4) Controls & constructed variables
*-------------------------------
local controls overconfidence fin_quiz gender_female age finance_course ///
               trading_experience risk_aversion



* Pay choice (only relevant if pay_for_data varies)
gen byte pay_choice = treated * pay_for_data
label var pay_choice "Choose to pay"

* Interactions used in regressions
gen double choice_imbalance = pay_choice * last_imbalance_1
label var choice_imbalance "Choose to pay $\times$ Imbalance"

gen byte paid_informative   = paid_round * informative
label var paid_informative "Paid round $\times$ Informative"

gen byte paid_uninformative = paid_round * (1 - informative)
label var paid_uninformative "Paid round $\times$ Uninformative"

gen byte paid_belief_informative   = paid_round * belief_informative
label var paid_belief_informative "Paid round $\times$ Belief informative"

gen byte paid_belief_uninformative = paid_round * (1 - belief_informative)
label var paid_belief_uninformative "Paid round $\times$ Belief uninformative"

gen double paid_informative_imbalance   = paid_round * belief_informative * last_imbalance_1
label var paid_informative_imbalance "Paid round $\times$ Belief informative $\times$ Imbalance"

gen double paid_uninformative_imbalance = paid_round * (1 - belief_informative) * last_imbalance_1
label var paid_uninformative_imbalance "Paid round $\times$ Belief uninformative $\times$ Imbalance"

gen double belief_informative_imbalance = belief_informative * last_imbalance_1
label var belief_informative_imbalance "Belief informative $\times$ Imbalance"

*-------------------------------
* 5) Table 1: Beliefs
*-------------------------------

reghdfe belief_informative ///
    paid_informative paid_uninformative treated informative pay_choice ///
    last_return_1 last_imbalance_1 round_number `controls', ///
    vce(cluster participant_code round_number)
outreg2 using "`out_bel'", r2 replace tex tstat label dec(2) tdec(2) ///
    eqdrop(/) keep(*)
	
reghdfe belief_informative ///
    paid_informative paid_uninformative treated informative pay_choice ///
	last_return_1 last_imbalance_1 round_number, ///
    vce(cluster participant_code round_number)
outreg2 using "`out_bel'", r2 append tex tstat label dec(2) tdec(2) ///
    eqdrop(/) keep(*)

reghdfe belief_informative ///
    paid_informative paid_uninformative treated informative pay_choice, ///
    vce(cluster participant_code round_number)
outreg2 using "`out_bel'", r2 append tex tstat label dec(2) tdec(2) ///
    eqdrop(/) keep(*)
	
reghdfe belief_informative ///
    paid_round treated informative pay_choice ///
    last_return_1 last_imbalance_1 round_number `controls', ///
    vce(cluster participant_code round_number)
outreg2 using "`out_bel'", r2 append tex tstat label dec(2) tdec(2) ///
    eqdrop(/) keep(*)
	
reghdfe belief_informative ///
    paid_round treated informative pay_choice ///
	last_return_1 last_imbalance_1 round_number, ///
    vce(cluster participant_code round_number)
outreg2 using "`out_bel'", r2 append tex tstat label dec(2) tdec(2) ///
    eqdrop(/) keep(*)
	



*-------------------------------
* 6) Table 2: Forecasts and investment
*-------------------------------
* Forecast equation — full controls
reghdfe return_forecast ///
    treated ///
    paid_informative_imbalance paid_uninformative_imbalance ///
    belief_informative belief_informative_imbalance ///
    pay_choice choice_imbalance ///
    paid_belief_informative paid_belief_uninformative ///
    last_return_1 last_imbalance_1 round_number `controls', ///
    vce(cluster participant_code round_number)

outreg2 using "`out_for'", r2 replace tex tstat label dec(2) tdec(2) ///
    eqdrop(/) keep(*)

* Forecast equation — no controls
reghdfe return_forecast ///
    treated ///
    paid_informative_imbalance paid_uninformative_imbalance ///
    belief_informative belief_informative_imbalance ///
    pay_choice choice_imbalance ///
    last_return_1 last_imbalance_1 round_number, ///
    vce(cluster participant_code round_number)

outreg2 using "`out_for'", r2 append tex tstat label dec(2) tdec(2) ///
    eqdrop(/) keep(*)

* Investment equation — full controls
reghdfe investment_amount ///
    treated ///
    paid_informative_imbalance paid_uninformative_imbalance ///
    belief_informative belief_informative_imbalance ///
    pay_choice choice_imbalance ///
    paid_belief_informative paid_belief_uninformative ///
    last_return_1 last_imbalance_1 round_number `controls', ///
    vce(cluster participant_code round_number)
outreg2 using "`out_for'", r2 append tex tstat label dec(2) tdec(2) ///
    eqdrop(/) keep(*)
	
* Investment equation — full controls
reghdfe investment_amount ///
    treated ///
    paid_informative_imbalance paid_uninformative_imbalance ///
    belief_informative belief_informative_imbalance ///
    pay_choice choice_imbalance ///
    paid_round ///
    last_return_1 last_imbalance_1 round_number `controls', ///
    vce(cluster participant_code round_number)
outreg2 using "`out_for'", r2 append tex tstat label dec(2) tdec(2) ///
    eqdrop(/) keep(*)


	
gen double rf_x_paid = return_forecast * paid_round
gen double z_x_paid  = last_imbalance_1 * paid_round
gen double r_x_paid  = last_return_1 * paid_round

label variable rf_x_paid "Return forecast $\times$ Paid round"

ivreghdfe investment_amount ///
    treated pay_choice round_number paid_round `controls' ///
    (return_forecast rf_x_paid = last_imbalance_1 last_return_1 z_x_paid) ///
    if belief_informative == 1, ///
    vce(cluster participant_code round_number)
outreg2 using "`out_iv'", r2 replace tex tstat label dec(2) tdec(2) ///
    eqdrop(/) keep(*)
	
ivreghdfe investment_amount ///
    treated pay_choice round_number paid_round `controls' ///
    (return_forecast rf_x_paid = last_imbalance_1 last_return_1 z_x_paid), ///
    vce(cluster participant_code round_number)
outreg2 using "`out_iv'", r2 append tex tstat label dec(2) tdec(2) ///
    eqdrop(/) keep(*)
	
ivreghdfe investment_share ///
    treated pay_choice round_number paid_round `controls' ///
    (return_forecast rf_x_paid = last_imbalance_1 last_return_1 z_x_paid) ///
    if belief_informative == 1, ///
    vce(cluster participant_code round_number)
outreg2 using "`out_iv'", r2 append tex tstat label dec(2) tdec(2) ///
    eqdrop(/) keep(*)
	
ivreghdfe investment_share ///
    treated pay_choice round_number paid_round `controls' ///
    (return_forecast rf_x_paid = last_imbalance_1 last_return_1 z_x_paid), ///
    vce(cluster participant_code round_number)
outreg2 using "`out_iv'", r2 append tex tstat label dec(2) tdec(2) ///
    eqdrop(/) keep(*)
	
reghdfe pay_for_data ///
    overconfidence fin_quiz ///
    gender_female age finance_course trading_experience risk_aversion ///
    round_number if treated==1, ///
    vce(cluster participant_code round_number)
outreg2 using "`out_select'", r2 replace tex tstat label dec(2) tdec(2) ///
    eqdrop(/) keep(*)
