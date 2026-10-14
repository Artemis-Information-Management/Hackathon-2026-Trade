#!/usr/bin/env Rscript
# Seasonal decomposition of monthly trade series (STL, base R only).
#
# Contract (see r/README.md):
#   Rscript r/seasonality.R --input in.csv --output out.csv
#
# Input  : tidy schema  reporter, partner, product, flow, freq, period, value
#          (freq must be "M", period like "2024-03")
# Output : one row per observation with the decomposition
#          series_id, period, value, trend, seasonal, remainder
#
# This is a working placeholder so the Python side can be tested end to end.
# Replace / extend freely (forecast::stlf, seasonal::seas, X-13...), but keep
# the input and output columns, or update r/README.md and pages/4_R_Seasonality.py.

args <- commandArgs(trailingOnly = TRUE)
get_arg <- function(flag, default = NULL) {
  i <- match(flag, args)
  if (is.na(i) || i == length(args)) return(default)
  args[i + 1]
}
input  <- get_arg("--input")
output <- get_arg("--output")
if (is.null(input) || is.null(output)) stop("Usage: --input <csv> --output <csv>")

df <- read.csv(input, stringsAsFactors = FALSE, colClasses = c(product = "character", flow = "character"))
df <- df[df$freq == "M", ]
df$series_id <- paste(df$reporter, df$partner, df$product, df$flow, sep = "|")

decompose_one <- function(s) {
  s <- s[order(s$period), ]
  if (nrow(s) < 24 || any(is.na(s$value))) return(NULL)
  start_year  <- as.integer(substr(s$period[1], 1, 4))
  start_month <- as.integer(substr(s$period[1], 6, 7))
  x <- ts(s$value, start = c(start_year, start_month), frequency = 12)
  fit <- stl(x, s.window = "periodic", robust = TRUE)
  data.frame(
    series_id = s$series_id[1],
    period    = s$period,
    value     = s$value,
    trend     = as.numeric(fit$time.series[, "trend"]),
    seasonal  = as.numeric(fit$time.series[, "seasonal"]),
    remainder = as.numeric(fit$time.series[, "remainder"]),
    stringsAsFactors = FALSE
  )
}

parts <- lapply(split(df, df$series_id), decompose_one)
res <- do.call(rbind, parts[!sapply(parts, is.null)])
if (is.null(res)) stop("No series with at least 24 monthly observations")

dir.create(dirname(output), showWarnings = FALSE, recursive = TRUE)
write.csv(res, output, row.names = FALSE)
cat(sprintf("Wrote %d rows for %d series to %s\n", nrow(res), length(unique(res$series_id)), output))
