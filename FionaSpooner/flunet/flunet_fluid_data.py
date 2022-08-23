import os
from pathlib import Path
import pandas as pd
from functools import reduce
from flu_utils import (
    get_country_codes,
    download_country_flu_data,
    combine_country_datasets,
    aggregate_surveillance_type,
    combine_columns_calc_percent,
    standardise_countries,
    aggregate_regions,
    get_metadata,
    clean_fluid_data,
    calculate_fluid_rates,
)

PATH = str(Path(__file__).parent.resolve())
PATH = "/Users/fionaspooner/Documents/OWID/repos/notebooks/FionaSpooner/flunet/"
FLUNET_DATA_DIR = os.path.join(PATH, "data/flunet/")
FLUNET_URL = "https://frontdoor-l4uikgap6gz3m.azurefd.net/FLUMART/VIW_FNT"
FLUNET_COLS = [
    "COUNTRY/AREA/TERRITORY",
    "HEMISPHERE",
    "ISO_WEEKSTARTDATE",
    "ORIGIN_SOURCE",
    "AH1N12009",
    "AH1",
    "AH3",
    "AH5",
    "AH7N9",
    "ANOTSUBTYPED",
    "ANOTSUBTYPABLE",
    "AOTHER_SUBTYPE",
    "INF_A",
    "BVIC_2DEL",
    "BVIC_3DEL",
    "BVIC_NODEL",
    "BVIC_DELUNK",
    "BYAM",
    "BNOTDETERMINED",
    "INF_B",
    "INF_ALL",
    "INF_NEGATIVE",
    "SPEC_PROCESSED_NB",
    "SPEC_RECEIVED_NB",
]

FLUID_DATA_DIR = os.path.join(PATH, "data/fluid/")
FLUID_URL = "https://frontdoor-l4uikgap6gz3m.azurefd.net/FLUMART/VIW_FID"


def main():
    get_metadata(os.path.join(PATH, "data", "metadata.csv"))
    flunet_df = run_flunet()
    fluid_df = run_fluid()
    flu_df = reduce(
        lambda left, right: pd.merge(
            flunet_df, fluid_df, on=["Country", "date"], how="outer"
        ),
    )
    return flu_df


def run_flunet():
    country_codes = get_country_codes(base_url=FLUNET_URL)
    download_country_flu_data(
        data_dir=FLUNET_DATA_DIR, base_url=FLUNET_URL, country_codes=country_codes
    )
    combined_df = combine_country_datasets(
        data_dir=FLUNET_DATA_DIR, country_codes=country_codes
    )
    df = aggregate_surveillance_type(combined_df, FLUNET_COLS)
    df = aggregate_regions(df)
    df = combine_columns_calc_percent(df)
    flunet_df = standardise_countries(df, PATH)
    # flunet_df.to_csv(
    #    os.path.join(PATH, "data", "flunet.csv"),
    #    index=False,
    # )
    return flunet_df


def run_fluid():
    country_codes = get_country_codes(base_url=FLUID_URL)
    download_country_flu_data(
        data_dir=FLUID_DATA_DIR, base_url=FLUID_URL, country_codes=country_codes
    )
    combined_df = combine_country_datasets(
        data_dir=FLUID_DATA_DIR, country_codes=country_codes
    )
    df = clean_fluid_data(combined_df)
    df = aggregate_regions(df)
    df = calculate_fluid_rates(df)
    fluid_df = standardise_countries(df, PATH)
    return fluid_df


if __name__ == "__main__":
    main()
