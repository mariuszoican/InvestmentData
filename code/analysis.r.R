library(tidyverse)
library(lfe)
library(stargazer)
library(fixest)
library(modelsummary)
library(rstudioapi)
library(ggplot2)
library(ggfixest)
library(cowplot)
library(latex2exp)

# Load data
setwd(dirname(getActiveDocumentContext()$path))
df <- read.csv("../data/processed_data.csv")

controls <- c("age","gender_female","finance_course","fin_literacy_score")
controls_str <- paste(controls, collapse = " + ")

bel1 <- feols(
  as.formula(paste(
    "belief_informative ~ transaction_price + informative +",
    "last_return + last_imbalance +",
    controls_str, "| offer_price"
  )),
  data = subset(df)
)