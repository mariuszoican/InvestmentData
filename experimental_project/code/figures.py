import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf
from matplotlib import font_manager

sizeOfFont = 18
ticks_font = font_manager.FontProperties(size=sizeOfFont)


def settings_plot(ax):
    for label in ax.get_xticklabels():
        label.set_fontproperties(ticks_font)
    for label in ax.get_yticklabels():
        label.set_fontproperties(ticks_font)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    return ax


panel = pd.read_csv("../processed_panels.csv")

# standardizations
for col in [
    "round_number",
    "age",
    "fin_quiz",
    "overconfidence",
    "risk_aversion",
    "last_imbalance_1",
    "last_return_1",
    "imb_difference",
    "return_difference",
]:
    panel[col] = (panel[col] - panel[col].mean()) / panel[col].std()
panel["pay_choice"] = panel["treated"] * panel["pay_for_data"]

gs = gridspec.GridSpec(1, 2)
sizefigs_L = (16, 8)
fig = plt.figure(facecolor="white", figsize=sizefigs_L)

ax = fig.add_subplot(gs[0, 0])
ax = settings_plot(ax)

panel["paid_round_legend"] = np.where(panel["paid_round"] == 1, "Yes", "No")
panel["pay_choice_legend"] = np.where(panel["pay_choice"] == 1, "Yes", "No")

sns.barplot(
    data=panel,
    y="belief_informative",
    x="informative",
    hue="paid_round_legend",
    errorbar=("ci", 95),
    capsize=0.1,
    palette="Blues",
)


plt.xlabel("Informative round", fontsize=22)
plt.ylabel("Belief round is informative", fontsize=22)
plt.title("(A) Impact of payments on beliefs", fontsize=22, pad=50)


plt.legend(
    title="Paid data round",
    fontsize=22,
    title_fontsize=22,
    frameon=False,
    loc="upper center",
    bbox_to_anchor=(0.3, 1.12),
    ncol=2,
)
ax.set_xticklabels(["No", "Yes"], fontsize=22)

ax = fig.add_subplot(gs[0, 1])
ax = settings_plot(ax)


sns.barplot(
    data=panel[panel.treated == 1],
    y="belief_informative",
    hue="pay_choice_legend",
    hue_order=["No", "Yes"],
    x="informative",
    errorbar=("ci", 95),
    capsize=0.1,
    palette="Blues",
)

plt.title("(B) Selection effect", fontsize=22, pad=50)
plt.xlabel("Informative round", fontsize=22)
plt.ylabel("Choose to pay", fontsize=22)


plt.legend(
    title="Pay choice",
    fontsize=22,
    title_fontsize=22,
    frameon=False,
    loc="upper center",
    bbox_to_anchor=(0.3, 1.12),
    ncol=2,
)
ax.set_xticklabels(["No", "Yes"], fontsize=22)

plt.tight_layout(pad=2.0)
# plt.show()
plt.savefig("../figures/paid_beliefs.eps")

panel["high_quiz"] = np.where(panel["fin_quiz"] >= panel["fin_quiz"].mean(), 1, 0)
panel["positive_imbalance"] = np.where(panel["last_imbalance_1"] >= 0, 1, 0)

plt.clf()


model = smf.ols(
    "return_forecast ~ last_return_1 + overconfidence + treated + pay_choice + fin_quiz + gender_female + age + round_number",
    data=panel[panel.belief_informative == 1],
    missing="drop",
).fit()
loc = ("top left",)

panel["return_forecast_resid"] = (
    model.resid + panel[panel.belief_informative == 1]["return_forecast"].mean()
)  # add back mean for interpretability


gs = gridspec.GridSpec(1, 3)
sizefigs_L = (21, 9)
fig = plt.figure(facecolor="white", figsize=sizefigs_L)

ax = fig.add_subplot(gs[0, 0])
ax = settings_plot(ax)


sns.barplot(
    data=panel[(panel.belief_informative == 1)],
    y="return_forecast_resid",
    x="positive_imbalance",
    hue="paid_round_legend",
    hue_order=["No", "Yes"],
    errorbar=("ci", 95),
    capsize=0.1,
    palette="Blues",
)

ax.set_xticklabels(["No", "Yes"], fontsize=22)
plt.title("(A) Full sample", fontsize=22)
plt.xlabel("Positive order imbalance", fontsize=22)
plt.ylabel("Return forecast", fontsize=22)
plt.legend(
    title="Paid data round",
    fontsize=22,
    title_fontsize=22,
    frameon=False,
    loc="upper left",
    ncol=2,
)
plt.ylim(0, 18)

ax = fig.add_subplot(gs[0, 1])
ax = settings_plot(ax)

sns.barplot(
    data=panel[(panel.belief_informative == 1) & (panel.high_quiz == 1)],
    y="return_forecast_resid",
    x="positive_imbalance",
    hue="paid_round_legend",
    hue_order=["No", "Yes"],
    errorbar=("ci", 95),
    capsize=0.1,
    palette="Blues",
)

plt.title("(B) Above average financial quiz score", fontsize=22)
plt.xlabel("Positive order imbalance", fontsize=22)
plt.ylabel("Return forecast", fontsize=22)
plt.legend(
    title="Paid data round",
    fontsize=22,
    title_fontsize=22,
    frameon=False,
    loc="upper left",
    ncol=2,
)
plt.ylim(0, 18)
ax.set_xticklabels(["No", "Yes"], fontsize=22)

ax = fig.add_subplot(gs[0, 2])
ax = settings_plot(ax)

sns.barplot(
    data=panel[(panel.belief_informative == 1) & (panel.high_quiz == 0)],
    y="return_forecast_resid",
    x="positive_imbalance",
    hue="paid_round_legend",
    hue_order=["No", "Yes"],
    errorbar=("ci", 95),
    capsize=0.1,
    palette="Blues",
)

plt.title("(C) Below average financial quiz score", fontsize=22)
plt.xlabel("Positive order imbalance", fontsize=22)
plt.ylabel("Return forecast", fontsize=22)
plt.legend(
    title="Paid data round",
    fontsize=22,
    title_fontsize=22,
    frameon=False,
    ncol=2,
    loc="upper left",
)
plt.ylim(0, 18)
ax.set_xticklabels(["No", "Yes"], fontsize=22)
plt.tight_layout(pad=3.0)
# plt.show()
plt.savefig("../figures/paid_forecasts.eps")


plt.clf()

panel["overconfidence_above"] = np.where(panel["overconfidence"] > 0, "Yes", "No")
panel["finquiz_above"] = np.where(panel["fin_quiz"] > 0, "Yes", "No")

gs = gridspec.GridSpec(1, 2)
sizefigs_L = (18, 8)
fig = plt.figure(facecolor="white", figsize=sizefigs_L)

ax = fig.add_subplot(gs[0, 0])
ax = settings_plot(ax)

sns.barplot(
    data=panel[panel.treated == 1],
    x="finquiz_above",
    y="pay_choice",
    errorbar=("ci", 95),
    order=["No", "Yes"],
    capsize=0.1,
    palette="Blues",
)
plt.title("(A) Financial literacy", fontsize=22)
plt.xlabel("Financial quiz score above average", fontsize=22)
plt.ylabel("Pay for data", fontsize=22)

ax = fig.add_subplot(gs[0, 1])
ax = settings_plot(ax)

sns.barplot(
    data=panel[panel.treated == 1],
    x="overconfidence_above",
    y="pay_choice",
    errorbar=("ci", 95),
    order=["No", "Yes"],
    capsize=0.1,
    palette="Blues",
)
plt.title("(B) Overconfidence", fontsize=22)
plt.xlabel("Overconfidence above average", fontsize=22)
plt.ylabel("Pay for data", fontsize=22)


plt.tight_layout(pad=2.0)
# plt.show()
plt.savefig("../figures/selection.eps")
