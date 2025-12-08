import pandas as pd
import numpy as np

data = pd.read_csv("bots/all_apps_wide.csv")

code_test = "nj2l4vlq"


def payoff_check(participant_code):

    test = data[data["participant.code"] == participant_code]

    pr = int(test["main.1.player.payable_round"].mean())  # get payable round

    string_main = f"main.%d.player" % pr
    condition = test[string_main + ".condition"].values[0]
    round_type = test[string_main + ".round_type"].values[0]
    payoff = test[string_main + ".payoff"].values[0]

    investment = test[string_main + ".investment_amount"].values[0]
    realized_return = test[string_main + ".realized_return"].values[0]

    hl_pay = test["participant.payoff_for_holt_laury"].values[0]

    if round_type == "brokerage_fee":
        cash = (
            test["session.config.endowment"] - test["session.config.fee_amount"]
        ).values[0]
    else:  # subtract investment and brokerage fee
        cash = (
            test["session.config.endowment"]
            - test["session.config.fee_amount"] * test[string_main + ".pay_for_data"]
        ).values[0]

    portfolio_value = cash + investment * realized_return / 100
    bonuses = test["main.14.player.cumulative_bonuses"].values[0]

    bonuses_informative = 0
    bonuses_forecast = 0

    for rnd in range(3, 15):

        if test[f"main.{rnd}.player.round_type"].values[0] == "brokerage_fee":

            bonuses_informative += 1 * (
                test[f"main.{rnd}.player.imbalance_informative"]
                == test[f"main.{rnd}.player.imbalance_was_informative"]
            )
        else:
            bonuses_informative += (
                1
                * (
                    test[f"main.{rnd}.player.imbalance_informative"]
                    == test[f"main.{rnd}.player.imbalance_was_informative"]
                )
                * test[f"main.{rnd}.player.pay_for_data"]
            )

        bonuses_forecast += 1 * (
            np.abs(
                test[f"main.{rnd}.player.return_forecast"]
                - test[f"main.{rnd}.player.realized_return"]
            )
            <= 1
        )

    bonuses_compute = (bonuses_informative + bonuses_forecast).values[0]

    payoff_bonus = portfolio_value + bonuses_compute

    quiz_questions = test["post_exp.1.player.num_correct_answers"].values[0]
    bonus_quiz = (
        quiz_questions * test["session.config.fee_per_correct_answer"].values[0]
    )

    payoff_computed = payoff_bonus + bonus_quiz + hl_pay
    payoff_df = test["post_exp.1.player.payoff"].values[0]

    df = pd.DataFrame(
        {
            "bonus_quiz": [bonus_quiz],
            "bonuses_compute": [bonuses_compute],
            "bonuses": [bonuses],
            "portfolio_value": [portfolio_value],
            "portfolio_df": [payoff],
            "cash": [cash],
            "investment": [investment],
            "realized_return": [realized_return],
            "payoff_computed": [payoff_computed],
            "payoff_df": [payoff_df],
        }
    )

    df["participant_code"] = participant_code

    return df


if __name__ == "__main__":

    codes = [data["participant.code"].unique()]
    results = pd.DataFrame()
    for code in codes[0]:
        result = payoff_check(code)
        results = pd.concat([results, result], ignore_index=True)

    results["payoff_difference"] = results["payoff_df"] - results["payoff_computed"]
    print(results)
