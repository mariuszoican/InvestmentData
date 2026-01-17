// Load data
// -------------------------------------
clear all
set more off
//local directory "C:\Research\data_experiment\"
local directory "/Users/mariuszoican/Research/InvestmentData/"
import delimited "`directory'pilots/processed_data_pilots"



// Table 1: WTP

gen treated_paid=treated*paid_round
gen treated_willing=treated*pay_for_data

local controls overconfidence fin_quiz gender_female age finance_course trading_experience risk_aversion 

reghdfe belief_informative treated_paid treated_willing treated last_imbalance_1 last_return_1 informative round_number `controls', vce(cl participant_code round_number)

gen paidimbalance=treated_paid*last_imbalance_1
gen willingimbalance=treated_willing*last_imbalance_1
gen treatedimbalance=treated*last_imbalance_1

reghdfe return_forecast last_imbalance_1 paidimbalance willingimbalance treatedimbalance treated_paid treated_willing treated last_return_1 round_number `controls' if belief_informative==1 & pay_for_data==1, vce(cl participant_code round_number)

reghdfe return_forecast last_imbalance_1 paidimbalance willingimbalance treatedimbalance treated_paid treated_willing treated last_return_1 round_number `controls' if belief_informative==1 & pay_for_data==0, vce(cl participant_code)


reghdfe investment_share `controls' if belief_informative==1 & pay_for_data==1, vce(cl participant_code round_number)
