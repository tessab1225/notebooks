import datetime

import epiweeks
import pandas as pd


SOURCE_USA = "https://data.cdc.gov/api/views/3rge-nu2a/rows.csv?accessType=DOWNLOAD"
SOURCE_CHL = "https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto89/incidencia_en_vacunados_edad.csv"
SOURCE_ENG = "input/datasetfinalcorrected3.xlsx"

VACCINE_MAPPING = {
    "Janssen": "Johnson&Johnson",
    "Pfizer": "Pfizer/BioNTech",
    "all_types": "Fully vaccinated (all vaccines)",
}


def epiweek_to_date(epiweek_number: int):
    assert datetime.datetime.now().year == 2021
    week = epiweeks.Week(2021, epiweek_number)
    return week.enddate()


def process_usa(source: str):
    df = pd.read_csv(source)
    df = df[df.outcome == "death"]
    df["Vaccine product"] = df["Vaccine product"].replace(VACCINE_MAPPING)

    df.loc[df["Age adjusted vax IR"].notnull(), "crude_vax_ir"] = df[
        "Age adjusted vax IR"
    ]
    df.loc[df["Age adjusted unvax IR"].notnull(), "crude_unvax_ir"] = df[
        "Age adjusted unvax IR"
    ]

    vax = df[["Age group", "Week date", "Vaccine product", "Crude vax IR"]].rename(
        columns={
            "Crude vax IR": "incidence_rate",
            "Vaccine product": "vaccine_product",
        }
    )

    unvax = (
        df[["Age group", "Week date", "Vaccine product", "Crude unvax IR"]]
        .rename(
            columns={
                "Crude unvax IR": "incidence_rate",
                "Vaccine product": "vaccine_product",
            }
        )
        .assign(vaccine_product="Unvaccinated")
        .drop_duplicates()
    )

    df = pd.concat([vax, unvax], ignore_index=True).rename(
        columns={
            "Age group": "age_group",
            "Week date": "week_date",
        }
    )

    df = (
        df.pivot(
            index=["age_group", "week_date"],
            columns="vaccine_product",
            values="incidence_rate",
        )
        .reset_index()
        .rename(columns={"week_date": "Year", "age_group": "Entity"})
    )

    assert datetime.datetime.now().year == 2021
    df["Year"] = pd.to_datetime(
        df.Year.str.extract("-(.*)", expand=False) + " 2021", format="%b %d %Y"
    )
    df["Year"] = (df.Year - pd.to_datetime("20210101")).dt.days

    df["Entity"] = df.Entity.replace({"all_ages_adj": "All ages"})

    df.to_csv(
        "output/COVID-19 - Deaths by vaccination status - United States.csv",
        index=False,
    )


def process_chl(source: str):
    df = pd.read_csv(
        source,
        usecols=[
            "semana_epidemiologica",
            "grupo_edad",
            "estado_vacunacion",
            "incidencia_def",
        ],
    ).rename(
        columns={
            "semana_epidemiologica": "Year",
            "grupo_edad": "Entity",
            "estado_vacunacion": "status",
            "incidencia_def": "rate",
        }
    )

    df = df[df.Entity != "Total"]
    df["Entity"] = df.Entity.replace(
        {
            "06 - 11 años": "06-11",
            "12 - 20 años": "12-20",
            "21 - 30 años": "21-30",
            "31 - 40 años": "31-40",
            "41 - 50 años": "41-50",
            "51 - 60 años": "51-60",
            "61 - 70 años": "61-70",
            "71 - 80 años": "71-80",
            "80 años o más": "80+",
        }
    )

    # Age standardization based on single-year population estimates by the United Nations
    age_pyramid = {
        "06-11": 1521945,
        "12-20": 2244380,
        "21-30": 2980833,
        "31-40": 2932270,
        "41-50": 2574347,
        "51-60": 2345262,
        "61-70": 1774551,
        "71-80": 964821,
        "80+": 494118,
    }
    df["age_group_standard"] = df.Entity.replace(age_pyramid)
    df["age_group_proportion"] = df.age_group_standard / sum(age_pyramid.values())
    df["age_specific_adjusted_rate"] = df.rate * df.age_group_proportion
    all_ages = (
        df[["Year", "status", "age_specific_adjusted_rate"]]
        .groupby(["Year", "status"], as_index=False)
        .sum()
        .rename(columns={"age_specific_adjusted_rate": "rate"})
        .assign(Entity="All ages")
    )
    df = df.drop(
        columns=[
            "age_group_standard",
            "age_group_proportion",
            "age_specific_adjusted_rate",
        ]
    )
    df = pd.concat([df, all_ages], ignore_index=True)

    status_mapping = {
        "sin esquema completo": "Unvaccinated or not fully vaccinated",
        "con esquema completo": "Fully vaccinated",
        "con dosis refuerzo > 14 dias": "Fully vaccinated + booster dose",
    }
    assert set(status_mapping.keys()) == set(df.status)
    df["status"] = df.status.replace(status_mapping)

    df["Year"] = pd.to_datetime(df.Year.apply(epiweek_to_date))
    df["Year"] = (df.Year - pd.to_datetime("20210101")).dt.days

    df = df.pivot(
        index=["Entity", "Year"], columns="status", values="rate"
    ).reset_index()

    df.to_csv(
        "output/COVID-19 - Deaths by vaccination status - Chile.csv",
        index=False,
    )


def process_eng(source: str):
    # All ages
    df = pd.read_excel(source, sheet_name="Table 1", skiprows=4)
    df = df[df.index < df.index[df["Week ending"].isna()].min()].rename(
        columns={"Week ending": "Year"}
    )

    unvax = df[
        ["Year", "Age-standardised mortality rate per 100,000", "Unnamed: 5"]
    ].assign(Entity="All ages")
    unvax = (
        unvax[unvax["Unnamed: 5"] != "u"]
        .drop(columns="Unnamed: 5")
        .rename(columns={"Age-standardised mortality rate per 100,000": "Unvaccinated"})
    )

    vax = df[
        ["Year", "Age-standardised mortality rate per 100,000.3", "Unnamed: 26"]
    ].assign(Entity="All ages")
    vax = (
        vax[vax["Unnamed: 26"] != "u"]
        .drop(columns="Unnamed: 26")
        .rename(
            columns={
                "Age-standardised mortality rate per 100,000.3": "Fully vaccinated"
            }
        )
    )

    df = pd.merge(vax, unvax, how="outer", on=["Year", "Entity"])

    # Age groups
    by_age = pd.read_excel(source, sheet_name="Table 3", skiprows=3, na_values=":")
    by_age = by_age[
        by_age.index < by_age.index[by_age["Week ending"].isna()].min()
    ].rename(columns={"Week ending": "Year"})
    by_age = by_age[
        by_age["Vaccination status"].isin(["Unvaccinated", "Second dose"])
    ].replace({"Second dose": "Fully vaccinated"})
    by_age = (
        by_age[by_age["Unnamed: 8"] != "u"][
            ["Year", "Vaccination status", "Age group", "Age-specific rate per 100,000"]
        ]
        .pivot(
            index=["Year", "Age group"],
            columns="Vaccination status",
            values="Age-specific rate per 100,000",
        )
        .reset_index()
        .rename(columns={"Age group": "Entity"})
    )
    by_age = by_age[by_age.Entity != "10-59"]

    # Concatenate
    df = pd.concat([df, by_age], ignore_index=True)[
        ["Entity", "Year", "Unvaccinated", "Fully vaccinated"]
    ]
    df["Year"] = (df.Year - pd.to_datetime("20210101")).dt.days

    df.to_csv(
        "output/COVID-19 - Deaths by vaccination status - England.csv",
        index=False,
    )


def main():
    process_usa(SOURCE_USA)
    process_chl(SOURCE_CHL)
    process_eng(SOURCE_ENG)


if __name__ == "__main__":
    main()
