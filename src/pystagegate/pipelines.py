from pystagegate import prov_fin, functions
import pandas as pd
from itertools import product


def prov_fin_main(config=None):
    print("\n\n")
    if config is None:
        config = functions.load_config("testing_config.json")

    age_min = config["parameters"]["age_min"]
    age_max = config["parameters"]["age_max"]
    year = config["parameters"]["year"]

    paths = functions.join_paths(config["root"], config["prov_fin_paths"])

    ltim_immigration = prov_fin.load_summary_data(
        path=paths["spring_immigration"],
        age_var="Age",
        age_min=age_min,
        age_max=age_max,
        lan_var="Local Authority Name",
        date_var="Date Updated",
    )

    ltim_emigration = prov_fin.load_summary_data(
        path=paths["spring_emigration"],
        age_var="Age",
        age_min=age_min,
        age_max=age_max,
        lan_var="Local Authority Name",
        date_var="Date Updated",
    )

    ltim_provisional = prov_fin.load_summary_data(
        path=paths["provisional_mye"],
        age_var="Age",
        age_min=age_min,
        age_max=age_max,
    )

    ltim_provisional_scot = prov_fin.load_summary_data(
        path=paths["provisional_scot"],
        age_var="Age",
        age_min=age_min,
        age_max=age_max,
    )

    # Merge immigration and emmigration
    ltim_merged = ltim_immigration.merge(
        ltim_emigration,
        on=["Age", "Local Authority Code", "Year", "Sex", "Nationality Group"],
        how="left",
        suffixes=("_imm", "_em"),
    )

    ltim_merged["Net_Cell"] = ltim_merged["Count_imm"] - ltim_merged["Count_em"]

    ltim_merged = ltim_merged[ltim_merged["Nationality Group"] == "All Nationalities"]
    ltim_merged = ltim_merged[ltim_merged["Year"] == year]

    # Complete processing of the merged data
    ltim_merged = (
        ltim_merged.groupby(["Local Authority Code", "Year", "Age"])
        .agg(
            {
                "Count_imm": "sum",
                "Count_em": "sum",
                "Net_Cell": "sum",
            }
        )
        .reset_index()
        .rename(
            columns={
                "Count_imm": "Imm_Fin",
                "Count_em": "Em_Fin",
                "Net_Cell": "Net_Fin",
            }
        )
    )

    # Filter provisional data for the specified year
    ltim_provisional_subset = pd.concat(
        [
            ltim_provisional.iloc[:, 0:3],
            ltim_provisional.loc[
                :,
                [
                    f"international_in_{year}",
                    f"international_out_{year}",
                    f"international_net_{year}",
                ],
            ],
        ],
        axis=1,
    )

    ltim_provisional_subset = ltim_provisional_subset.rename(
        columns={
            f"international_in_{year}": "international_in",
            f"international_out_{year}": "international_out",
            f"international_net_{year}": "international_net",
        }
    )

    # Create aggregated provisional data
    ltim_provisional_agg = (
        ltim_provisional_subset.groupby(["code", "Age"])
        .agg(
            {
                "international_in": "sum",
                "international_out": "sum",
                "international_net": "sum",
            }
        )
        .reset_index()
        .rename(
            columns={
                "code": "Local Authority Code",
                "international_in": "Imm_Prov",
                "international_out": "Em_Prov",
                "international_net": "Net_Prov",
            }
        )
    )

    ltim_provisional_agg["Year"] = year

    # Create a cartesian product of unique values for the provisional Scotland data
    unique_values = [
        ltim_provisional_scot[col].unique()
        for col in ltim_provisional_scot.columns
        if col != "count"
    ]

    scot_column_select = [
        col for col in ltim_provisional_scot.columns if col != "count"
    ]

    scot_cartesian = pd.DataFrame(
        set(product(*unique_values)), columns=scot_column_select
    )

    # Merge the cartesian product with the provisional Scotland data
    ltim_provisional_scot = scot_cartesian.merge(
        ltim_provisional_scot, on=scot_column_select, how="left"
    ).fillna(0)

    # Aggregate the merged Scotland data, summing count for sex
    ltim_provisional_scot_agg = (
        ltim_provisional_scot.groupby(["ca_code", "year", "dir", "Age"])
        .agg({"count": "sum"})
        .reset_index()
    )

    ltim_provisional_scot_agg = (
        pd.pivot_table(
            ltim_provisional_scot_agg,
            index=["ca_code", "year", "Age"],
            columns="dir",
            values="count",
        )
        .reset_index()
        .rename(columns={"in": "Imm_Prov", "out": "Em_Prov"})
    )

    ltim_provisional_scot_agg["Net_Prov"] = (
        ltim_provisional_scot_agg["Imm_Prov"] - ltim_provisional_scot_agg["Em_Prov"]
    )

    ltim_provisional_scot_agg = ltim_provisional_scot_agg[
        ltim_provisional_scot_agg["year"] == year
    ].rename(columns={"ca_code": "Local Authority Code", "year": "Year"})

    # Concatenate all aggregated provisional data
    ltim_provisional_all = pd.concat([ltim_provisional_agg, ltim_provisional_scot_agg])

    # Final dataframe with provisional and merged data
    ltim_final = ltim_provisional_all.merge(
        ltim_merged,
        on=["Local Authority Code", "Age", "Year"],
        how="left",
    )

    ltim_final["Nation"] = ltim_final["Local Authority Code"].str[0]

    # GB analysis
    gb_age, gb_la = prov_fin.regional_breakdown(
        ltim_final, "Imm_Prov", "Imm_Fin", "Em_Prov", "Em_Fin", "Net_Prov", "Net_Fin"
    )

    print("\n\n******** GB Analysis ********", gb_age, gb_la, sep="\n\n")

    # England analysis
    eng_age, eng_la = prov_fin.regional_breakdown(
        ltim_final,
        "Imm_Prov",
        "Imm_Fin",
        "Em_Prov",
        "Em_Fin",
        "Net_Prov",
        "Net_Fin",
        "E",
    )

    print("\n\n******** England Analysis ********", eng_age, eng_la, sep="\n\n")

    # Wales analysis
    wal_age, wal_la = prov_fin.regional_breakdown(
        ltim_final,
        "Imm_Prov",
        "Imm_Fin",
        "Em_Prov",
        "Em_Fin",
        "Net_Prov",
        "Net_Fin",
        "W",
    )

    print("\n\n******** Wales Analysis ********", wal_age, wal_la, sep="\n\n")

    # Scotland analysis
    scot_age, scot_la = prov_fin.regional_breakdown(
        ltim_final,
        "Imm_Prov",
        "Imm_Fin",
        "Em_Prov",
        "Em_Fin",
        "Net_Prov",
        "Net_Fin",
        "S",
    )

    print("\n\n******** Scotland Analysis ********", scot_age, scot_la, sep="\n\n")
