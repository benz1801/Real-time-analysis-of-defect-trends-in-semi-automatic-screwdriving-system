##########################################################################
########################### POISSON MODEL ################################
############# COUNT REGRESSION ON PSET_COND_DF.csv########################
library(lmtest)
library(MASS)
library(pscl)
library(sandwich)
library(xtable)
library(VGAM)
library(AER)

clog <- function(x) log(x + 0.5)

cfac <- function(x, breaks = NULL) {
  if(is.null(breaks)) breaks <- unique(quantile(x, 0:10/10))
  x <- cut(x, breaks, include.lowest = TRUE, right = FALSE)
  levels(x) <- paste(breaks[-length(breaks)], ifelse(diff(breaks) > 1,
               c(paste("-", breaks[-c(1, length(breaks))] - 1, sep = ""), "+"), ""), sep = "")
  return(x)
  }

setwd('C:\\Users\\leonardo.livi\\OneDrive - S3K S.p.A\\Desktop')
file_path <- file.path(getwd(),'Dataframe_PBI.csv')

data <- read.csv(file_path)

for(i in unique(data$Global_ID)){
  print(i)
  print(dim(data[data$Global_ID==i,])[1])
}

# 6AGC085488
data <- data[data$Global_ID=='6AGC085488',]
data <- data[data$Fase!='FASE0',]
data <- data[data$Fase!='FASE5',]

#data$DeriveBool <- data$Derive == 'True'
head(data)
str(data)
summary(data)
colnames(data)

#data <- data[,c("Fase","Batch","group_size","Errors",
#                "Duration","Derive")]

data <- data[,c("Fase","Batch","Errors",
                "Duration","Derive")]

head(data)


plot(table(data$Errors), ylab = 'Frequency', xlab = 'Errors')


attach(data)

plot(clog(Errors)~cfac(Batch), xlab = 'Batch')
boxplot(clog(Errors)~Fase, varwidth = TRUE)
boxplot(clog(Errors)~Derive)

plot(Errors~Duration)

# Poisson regression
pois_model <- glm(Errors ~ ., data = data, family = poisson)

# Estrai le informazioni di riepilogo
model_summary <- summary(pois_model)
model_summary
# Estrai i gradi di libertà
df_resid <- model_summary$df.residual  # Gradi di libertà per la devianza residua
df_null <- model_summary$df.null    # Gradi di libertà per la devianza nulla
#df_total <- pois_model$df.residual + pois_model$df.null # Numero totale di gradi di libertà stimati

# Estrai l'AIC
aic <- AIC(pois_model)

# Costruisci una tabella
table_data <- data.frame(
  Metric = c("Null Deviance", "Residual Deviance", "AIC"),
  Value = c(model_summary$null.deviance, model_summary$deviance, aic),
  df = c(df_null, df_resid, NA)
)
# Stampa la tabella
print(xtable(table_data, caption = "Summary of Poisson Regression Model", label = "tab:poisson_regression_summary"), caption.placement = "bottom")

options(scipen = 0)

# Sandwich correction
coeftest_result <- coeftest(pois_model, vcov = sandwich)
coeftest_result

# Costruisci una tabella con i risultati del test dei coefficienti
coeftest_table <- cbind(coeftest_result[, 1:2], est = coeftest_result[, 1] - coeftest_result[, 2])

# Stampa la tabella
print(xtable(coeftest_table, caption = "Test dei coefficienti", label = "tab:test_coefficients"), caption.placement = "top")


dispersiontest(pois_model,trafo = 1)
# Quasi-Poisson regression
qpois_model <- glm(Errors~., data = data, family = quasipoisson)
summary(qpois_model)

# Negative Binomial regression
nbin_model <- glm.nb(Errors~., data = data)
summary(nbin_model)

# Hurdle model
hurdle_model_negbin <- hurdle(Errors~., data = data, dist="negbin")
hurdle_model_pois <- hurdle(Errors~., data = data, dist="pois")

summary(hurdle_model_negbin)
summary(hurdle_model_pois)

summary_table <- summary(hurdle_model_pois)


hurdle_model_pois1 <- hurdle(Errors~.|  Batch  + Duration + Derive, data = data, dist="pois")
summary(hurdle_model_pois1)

# Compare full model vs restricted model with Wald or LR test
waldtest(hurdle_model_pois,hurdle_model_pois1)
lrtest(hurdle_model_pois,hurdle_model_pois1)


# Zero Inflated model
zinfl_model_negbin <- zeroinfl(Errors~., data = data, dist = 'negbin')
zinfl_model_pois <- zeroinfl(Errors~., data = data, dist = 'poisson')

summary(zinfl_model_negbin)
summary(zinfl_model_pois)

fm <- list("ML-Pois" = pois_model ,"Quasi-Pois" = qpois_model, "NB" = nbin_model,
           "Hurdle-NB" = hurdle_model_negbin, "ZINB" = zinfl_model_negbin)

sapply(fm, function(x) coef(x)[1:7])

cbind("ML-Pois" = sqrt(diag(vcov(pois_model))),
      "Adj-Pois" = sqrt(diag(sandwich(pois_model))),
      sapply(fm[-1], function(x) sqrt(diag(vcov(x)))[1:7]))

rbind(logLik = sapply(fm, function(x) round(logLik(x), digits = 0)),
      Df = sapply(fm, function(x) attr(logLik(x), "df")))

round(c("Obs" = sum(Errors < 1),
        "ML-Pois" = sum(dpois(0, fitted(pois_model))),
        "NB" = sum(dnbinom(0, mu = fitted(nbin_model), size = nbin_model$theta)),
        "Hurdle-NB" = sum(predict(hurdle_model_negbin, type = "prob")[,1]),
        "ZINB" = sum(predict(zinfl_model_negbin, type = "prob")[,1])))

t(sapply(fm[4:5], function(x) round(x$coefficients$zero, digits = 3)))

# Prediction
new = data.frame(Fase = 'FASE4', Batch = 7, Derive = 'False', Duration=20)
predict(hurdle_model_negbin, newdata = new, type = "response")


         
         