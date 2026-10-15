# The aim of this script is to extract and consolidate in final dataframe
# The data comes from eurostat table EU trade since 1988 by HS2-4-6 and CN8 - Online data code: ds-04540
# Filters : frequency : annual - Time period : 1999 - 2025 - Partner = LU, 2-digits products

suppressPackageStartupMessages(library(jsonlite))

# Parameters

API      <- "https://ec.europa.eu/eurostat/api/comext/dissemination/statistics/1.0/data/ds-045409"
SINCE    <- "1999"
REPORTER <- "LU"

OUT_RDS  <- "final_df.rds"
TMP_DIR  <- tempfile("comext_LU_")

PAUSE    <- 1
RETRIES  <- 6
WAIT     <- 20

PRODUCTS <- c("TOTAL", sprintf("%02d", 1:99))
FLOWS    <- c("1", "2")

dir.create(TMP_DIR, recursive = TRUE)

# Build URL

build_url <- function(partner = NULL) {
  
  q <- c(
    format = "JSON",
    lang = "EN",
    freq = "A",
    indicators = "VALUE_IN_EUROS",
    reporter = REPORTER,
    sinceTimePeriod = SINCE
  )
  
  if (!is.null(partner)) {
    q <- c(q, partner = partner)
  }
  
  q <- c(
    q,
    setNames(PRODUCTS, rep("product", length(PRODUCTS))),
    setNames(FLOWS, rep("flow", length(FLOWS)))
  )
  
  paste0(
    API, "?",
    paste(
      names(q),
      vapply(q, URLencode, character(1), reserved = TRUE),
      sep = "=",
      collapse = "&"
    )
  )
}

# Download

fetch_json <- function(url) {
  
  for (attempt in seq_len(RETRIES)) {
    
    js <- tryCatch(
      fromJSON(url, simplifyVector = FALSE),
      error = function(e) e
    )
    
    if (!inherits(js, "error") && !is.null(js$id)) {
      return(js)
    }
    
    msg <- if (inherits(js, "error")) {
      conditionMessage(js)
    } else {
      "No valid JSON-stat response"
    }
    
    message(
      "Request failed: ",
      substr(msg, 1, 150),
      " | attempt ", attempt, "/", RETRIES
    )
    
    if (attempt < RETRIES) Sys.sleep(WAIT)
  }
  
  stop("Eurostat request failed after ", RETRIES, " attempts.")
}

# JSON-stat -> data.frame

jsonstat_to_df <- function(js) {
  
  ids   <- unlist(js$id)
  sizes <- as.integer(unlist(js$size))
  
  cats <- lapply(ids, function(d) {
    
    cat <- js$dimension[[d]]$category
    
    codes <- if (!is.null(names(cat$index))) {
      names(cat$index)[order(unlist(cat$index))]
    } else {
      unlist(cat$index)
    }
    
    labels <- if (!is.null(cat$label)) {
      unlist(cat$label)[codes]
    } else {
      codes
    }
    
    labels[is.na(labels)] <- codes[is.na(labels)]
    
    list(
      codes = codes,
      labels = unname(labels)
    )
  })
  
  vals <- js$value
  
  if (!is.null(names(vals))) {
    
    pos <- as.integer(names(vals))
    v   <- as.numeric(unlist(vals))
    
  } else {
    
    v <- vapply(
      vals,
      function(x) {
        if (is.null(x)) NA_real_ else as.numeric(x)
      },
      numeric(1)
    )
    
    pos <- which(!is.na(v)) - 1L
    v   <- v[pos + 1L]
  }
  
  if (!length(pos)) return(NULL)
  
  idx <- matrix(
    0L,
    nrow = length(pos),
    ncol = length(sizes)
  )
  
  rem <- pos
  
  for (k in rev(seq_along(sizes))) {
    idx[, k] <- rem %% sizes[k]
    rem <- rem %/% sizes[k]
  }
  
  out <- list()
  
  for (k in seq_along(ids)) {
    
    out[[paste0(toupper(ids[k]), "_CODE")]] <-
      cats[[k]]$codes[idx[, k] + 1L]
    
    out[[paste0(toupper(ids[k]), "_LABEL")]] <-
      cats[[k]]$labels[idx[, k] + 1L]
  }
  
  df <- as.data.frame(out, stringsAsFactors = FALSE)
  df$VALUE <- v
  
  df
}

# Standardise columns

standardise <- function(df) {
  
  names(df) <- sub(
    "^INDICATORS_",
    "INDICATOR_",
    names(df)
  )
  
  if ("TIME_CODE" %in% names(df)) {
    df$TIME <- as.integer(df$TIME_CODE)
    df$TIME_CODE <- NULL
    df$TIME_LABEL <- NULL
  }
  
  if ("FREQ_CODE" %in% names(df)) {
    df$FREQ_CODE <- NULL
    df$FREQ_LABEL <- NULL
  }
  
  df$VALUE_IN_EUROS <- df$VALUE
  df$VALUE <- NULL
  df$INDICATOR_LABEL <- NULL
  
  keep <- c(
    "REPORTER_CODE", "REPORTER_LABEL",
    "PRODUCT_CODE", "PRODUCT_LABEL",
    "FLOW_CODE", "FLOW_LABEL",
    "PARTNER_CODE", "PARTNER_LABEL",
    "TIME", "INDICATOR_CODE", "VALUE_IN_EUROS"
  )
  
  df[, intersect(keep, names(df)), drop = FALSE]
}

# Get all available partners

message("Retrieving available partners...")

js_meta <- fetch_json(build_url())

if (is.null(js_meta$dimension$partner$category$index)) {
  stop("Partner dimension not found in Eurostat response.")
}

partner_index <- js_meta$dimension$partner$category$index

PARTNERS <- if (!is.null(names(partner_index))) {
  names(partner_index)
} else {
  as.character(unlist(partner_index))
}

message(length(PARTNERS), " partners found.")

# Download one partner at a time

for (i in seq_along(PARTNERS)) {
  
  partner <- PARTNERS[i]
  
  part_file <- file.path(
    TMP_DIR,
    paste0("partner_", i, ".rds")
  )
  
  message(
    "[", i, "/", length(PARTNERS), "] Partner: ", partner
  )
  
  df <- tryCatch({
    
    js <- fetch_json(build_url(partner))
    
    if (is.null(js$value)) {
      message("  No observations.")
      return(NULL)
    }
    
    df <- jsonstat_to_df(js)
    
    if (is.null(df) || !nrow(df)) {
      message("  No observations.")
      return(NULL)
    }
    
    df <- standardise(df)
    
    saveRDS(df, part_file)
    
    message("  ", format(nrow(df), big.mark = " "), " rows saved.")
    
    df
    
  }, error = function(e) {
    
    message("  ERROR: ", conditionMessage(e))
    NULL
  })
  
  Sys.sleep(PAUSE)
}

# Consolidate temporary RDS files

files <- list.files(
  TMP_DIR,
  pattern = "^partner_[0-9]+\\.rds$",
  full.names = TRUE
)

if (!length(files)) {
  stop("No partner data downloaded successfully.")
}

message("Consolidating ", length(files), " temporary files...")

data_list <- lapply(files, readRDS)

result <- do.call(rbind, data_list)

result <- result[
  order(
    result$PARTNER_CODE,
    result$FLOW_CODE,
    result$TIME,
    result$PRODUCT_CODE
  ),
]

rownames(result) <- NULL

result <- result %>%
  select(-REPORTER_CODE, -REPORTER_LABEL)

saveRDS(result, OUT_RDS)

message(
  "\nCompleted: ",
  format(nrow(result), big.mark = " "),
  " rows saved to ", OUT_RDS,
  "\nPartners: ", length(unique(result$PARTNER_CODE)),
  "\nYears: ", min(result$TIME, na.rm = TRUE),
  "-", max(result$TIME, na.rm = TRUE)
)

# Remove temporary files after successful consolidation
unlink(TMP_DIR, recursive = TRUE)