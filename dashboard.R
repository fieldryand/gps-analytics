library(dotenv)
library(ggplot2)
library(readr)
library(dplyr)
library(purrr)
library(leaflet)
library(lubridate)
library(plotly)
library(htmltools)

load_dot_env()

# Path to the directory containing GPX files
DATADIR <- Sys.getenv("DATADIR")

# Filter out instantaneous speeds above this
# threshold since they're probably noise
MAX_SPEED <- as.integer(Sys.getenv("MAX_SPEED"))

# Constants
KM_TO_MI <- 0.6213712

# Returns just the filename from the full path
file_from_path <- function(path) {
  first(rev(flatten(strsplit(path, "/"))))
}

# Returns 91278497 from "2019-09-02_91278497.csv"
get_gpx_id <- function(f) {
  r <- regexpr("[0-9]*\\.", f)
  as.integer(substr(f, r[1], r[1] + attr(r, "match.length") - 2))
}

# Parse metadata from the filename and insert it as a column
read_gpx <- function(f) {
  gpx_id <- get_gpx_id(file_from_path(f))
  suppressMessages(read_csv(f)) %>%
    mutate(gpx_id = gpx_id)
}

main <- function() {
  tours <- list.files(DATADIR, full.names = TRUE) %>%
    map(read_gpx) %>%
    bind_rows %>%
    mutate(trk_mov_dist = KM_TO_MI * trk_mov_dist / 1000,
           trk_mov_time = trk_mov_time / 60,
           speed = KM_TO_MI * speed,
           date = as_date(trk_start_time))

  duration_trend <- tours %>%
    select(gpx_name, gpx_id, date, duration = trk_mov_time, trk_mov_dist) %>%
    unique %>%
    ggplot(data = ., aes(x = date, y = duration, color = gpx_name)) +
      geom_line()

  tours %>%
    filter(speed < MAX_SPEED) %>%
    ggplot(data = ., aes(x = trk_mov_dist, y = speed)) +
      geom_point() +
      facet_wrap(~gpx_name)

  speed_profiles <- tours %>%
    filter(speed < MAX_SPEED) %>%
    ggplot(data = ., aes(x = dist_from_start, y = speed, group = date,
                         color = as.factor(date))) +
      geom_smooth(se = FALSE, method = "gam") +
      facet_wrap(~gpx_name)

  map_palette <- tours %>%
    filter(speed < MAX_SPEED) %>%
    colorNumeric(palette = "Reds", domain = .$speed)

  tour_map <- tours %>%
    filter(speed < MAX_SPEED) %>%
    leaflet(data = .) %>%
    addTiles() %>%
    addCircleMarkers(~long, ~lat, color = ~map_palette(speed))

  browsable(
    tagList(
      tags$div(tour_map),
      tags$div(ggplotly(duration_trend)),
      tags$div(ggplotly(speed_profiles))
    )
  )
}

main()
