# fetch_eu27.R
# -----------------------------------------------------------------------------
# Builds data/eu27_df.rds: the Eurostat Comext extraction the Trade twins page
# needs next to final_df.rds (Luxembourg).
#
#   reporter   = each EU country except Luxembourg (26 requests, one per country)
#   partner    = WORLD only
#   product    = TOTAL + the HS2 chapters 01..99
#   flow       = 1 (imports) and 2 (exports)
#   time       = 1999 onwards, annual
#   indicator  = VALUE_IN_EUROS
#
# Output columns = the columns of final_df.rds + REPORTER_CODE / REPORTER_LABEL:
#   REPORTER_CODE, REPORTER_LABEL, PRODUCT_CODE, PRODUCT_LABEL, FLOW_CODE, FLOW_LABEL,
#   PARTNER_CODE, PARTNER_LABEL, TIME, INDICATOR_CODE, VALUE_IN_EUROS
#
# Run from the project folder:   Rscript r/fetch_eu27.R
# or from RStudio:               source("r/fetch_eu27.R")
# Needs only jsonlite (installed with plotly). Takes a few minutes; each country
# is saved as it arrives, so a stopped run resumes where it left off.
#
# Same API as scripts/fetch_data.py (JSON-stat 2.0). If Eurostat changes the
# endpoint or queues the request, see the messages printed per country.
# -----------------------------------------------------------------------------
suppressPackageStartupMessages(library(jsonlite))

API      <- "https://ec.europa.eu/eurostat/api/comext/dissemination/statistics/1.0/data/ds-045409"
SINCE    <- "1999"
OUT_RDS  <- "data/eu27_df.rds"
OUT_CSV  <- "data/eu27_df.csv"
CACHE    <- "data/eu27_parts"              # one .rds per country, so a crash does not lose everything
PAUSE    <- 2                              # seconds between requests (be polite with the API)
RETRIES  <- 6                              # when Eurostat answers "being processed asynchronously"
WAIT     <- 20                             # seconds between those retries

# Comext codes: Greece is "GR" and the United Kingdom "GB" (the main Eurostat database says EL / UK).
REPORTERS <- c("AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", "IT",
               "LV", "LT", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE")
ALT_CODE  <- c(GR = "EL")                  # tried when the first code returns nothing
PRODUCTS  <- c("TOTAL", sprintf("%02d", 1:99))
FLOWS     <- c("1", "2")

# ---- 1. query -----------------------------------------------------------------
build_url <- function(reporter) {
  q <- c(format = "JSON", lang = "EN", freq = "A", indicators = "VALUE_IN_EUROS",
         reporter = reporter, partner = "WORLD", sinceTimePeriod = SINCE)
  q <- c(q, setNames(PRODUCTS, rep("product", length(PRODUCTS))), setNames(FLOWS, rep("flow", length(FLOWS))))
  paste0(API, "?", paste(names(q), q, sep = "=", collapse = "&"))   # a repeated name = several values (Eurostat rule)
}

fetch_json <- function(url) {
  for (attempt in seq_len(RETRIES)) {
    js <- tryCatch(fromJSON(url, simplifyVector = FALSE), error = function(e) e)
    if (inherits(js, "error")) stop("request failed: ", substr(conditionMessage(js), 1, 160), call. = FALSE)
    if (!is.null(js$value)) return(js)
    msg <- js$warning %||% js$error %||% js$status %||% "no value in the answer"
    message(sprintf("    queued by Eurostat (%s), retry %d/%d in %ds", substr(paste(unlist(msg), collapse = " "), 1, 80),
                    attempt, RETRIES, WAIT))
    Sys.sleep(WAIT)
  }
  stop("Eurostat did not return the extraction in time", call. = FALSE)
}
`%||%` <- function(a, b) if (is.null(a)) b else a

# ---- 2. JSON-stat 2.0 -> data.frame -------------------------------------------
# One row per observation. Dimension codes AND labels are kept (DIM_CODE, DIM_LABEL),
# which is the layout of final_df.rds.
jsonstat_to_df <- function(js) {
  ids   <- unlist(js$id)
  sizes <- as.integer(unlist(js$size))
  cats  <- lapply(ids, function(d) {
    cat <- js$dimension[[d]]$category
    codes <- if (!is.null(names(cat$index))) names(cat$index)[order(unlist(cat$index))] else unlist(cat$index)
    labels <- if (!is.null(cat$label)) unlist(cat$label)[codes] else codes
    labels[is.na(labels)] <- codes[is.na(labels)]
    list(codes = codes, labels = unname(labels))
  })
  vals <- js$value
  if (!is.null(names(vals))) {                       # sparse: {"position": value}, 0-based positions
    pos <- as.integer(names(vals)); v <- as.numeric(unlist(vals))
  } else {                                           # dense array, null where missing
    v <- vapply(vals, function(x) if (is.null(x)) NA_real_ else as.numeric(x), numeric(1))
    pos <- which(!is.na(v)) - 1L; v <- v[pos + 1L]
  }
  if (!length(pos)) return(NULL)
  # unravel the position: the last dimension varies fastest (row-major, as in JSON-stat)
  idx <- matrix(0L, nrow = length(pos), ncol = length(sizes)); rem <- pos
  for (k in rev(seq_along(sizes))) { idx[, k] <- rem %% sizes[k]; rem <- rem %/% sizes[k] }
  out <- list()
  for (k in seq_along(ids)) {
    out[[paste0(toupper(ids[k]), "_CODE")]]  <- cats[[k]]$codes[idx[, k] + 1L]
    out[[paste0(toupper(ids[k]), "_LABEL")]] <- cats[[k]]$labels[idx[, k] + 1L]
  }
  df <- as.data.frame(out, stringsAsFactors = FALSE)
  df$VALUE <- v
  df
}

# Rename to the columns of final_df.rds (+ REPORTER_*)
standardise <- function(df) {
  names(df) <- sub("^INDICATORS_", "INDICATOR_", names(df))
  if ("TIME_CODE" %in% names(df)) { df$TIME <- as.integer(df$TIME_CODE); df$TIME_CODE <- NULL; df$TIME_LABEL <- NULL }
  if ("FREQ_CODE" %in% names(df)) { df$FREQ_CODE <- NULL; df$FREQ_LABEL <- NULL }
  df$VALUE_IN_EUROS <- df$VALUE; df$VALUE <- NULL
  df$INDICATOR_LABEL <- NULL
  keep <- c("REPORTER_CODE", "REPORTER_LABEL", "PRODUCT_CODE", "PRODUCT_LABEL", "FLOW_CODE", "FLOW_LABEL",
            "PARTNER_CODE", "PARTNER_LABEL", "TIME", "INDICATOR_CODE", "VALUE_IN_EUROS")
  df[, intersect(keep, names(df))]
}

# ---- 3. one country at a time, cached ------------------------------------------
fetch_reporter <- function(code) {
  part <- file.path(CACHE, paste0(code, ".rds"))
  if (file.exists(part)) { message(sprintf("  %s: cached", code)); return(readRDS(part)) }
  for (try_code in unique(c(code, ALT_CODE[code]))) {
    if (is.na(try_code)) next
    message(sprintf("  %s: requesting ...", try_code))
    df <- tryCatch(jsonstat_to_df(fetch_json(build_url(try_code))), error = function(e) { message("    ", conditionMessage(e)); NULL })
    if (!is.null(df) && nrow(df)) {
      df <- standardise(df)
      if (!"REPORTER_CODE" %in% names(df)) { df$REPORTER_CODE <- try_code; df$REPORTER_LABEL <- try_code }
      df$REPORTER_CODE <- code                               # keep one code per country whatever the API answered
      saveRDS(df, part)
      message(sprintf("    %s rows, %s-%s", format(nrow(df), big.mark = " "), min(df$TIME), max(df$TIME)))
      Sys.sleep(PAUSE)
      return(df)
    }
    Sys.sleep(PAUSE)
  }
  message(sprintf("  %s: NOTHING RECEIVED", code))
  NULL
}

run <- function() {
  dir.create(CACHE, recursive = TRUE, showWarnings = FALSE)
  message("Eurostat Comext ds-045409, ", length(REPORTERS), " reporters x WORLD x TOTAL + HS2 x 2 flows, since ", SINCE)
  parts <- lapply(REPORTERS, fetch_reporter)
  eu27 <- do.call(rbind, parts[!vapply(parts, is.null, logical(1))])
  if (is.null(eu27) || !nrow(eu27)) stop("Nothing fetched. Check the API URL in a browser: ", build_url("DE"))
  eu27 <- eu27[order(eu27$REPORTER_CODE, eu27$FLOW_CODE, eu27$TIME, eu27$PRODUCT_CODE), ]
  rownames(eu27) <- NULL
  saveRDS(eu27, OUT_RDS)
  write.csv(eu27, OUT_CSV, row.names = FALSE)

  # ---- 4. what we got ----------------------------------------------------------
  message("\nSaved ", format(nrow(eu27), big.mark = " "), " rows to ", OUT_RDS, " (and ", OUT_CSV, ")")
  got <- sort(unique(eu27$REPORTER_CODE)); missing <- setdiff(REPORTERS, got)
  message("Reporters (", length(got), "): ", paste(got, collapse = " "))
  if (length(missing)) message("MISSING: ", paste(missing, collapse = " "), "  -> run the script again, or check the code in the Data Browser")
  message("Years: ", min(eu27$TIME), "-", max(eu27$TIME), "   products: ", length(unique(eu27$PRODUCT_CODE)),
          "   flows: ", paste(sort(unique(eu27$FLOW_CODE)), collapse = ","))
  print(head(eu27, 5))
  invisible(eu27)
}

if (!exists("FETCH_EU27_NO_RUN")) run()
