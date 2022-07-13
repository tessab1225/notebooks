
library(gpinter)
library(tidyverse)


df<- read.csv('API_output/percentiles/all_percentiles.csv')

head(df)

# Another cell

df<- df %>%
     group_by(entity, year) %>% 
     arrange(headcount)



df <- 
    df %>%
    group_by(entity, year) %>%
    mutate(lag.poverty_line = dplyr::lag(poverty_line, n = 1, default = NA))

head(df)

# Reorder to inspect the lag

df<- df %>%
     arrange(entity, year, headcount)

head(df)

df %>%
filter(lag.poverty_line>poverty_line)


