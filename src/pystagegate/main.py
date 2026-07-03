from pystagegate import prov_fin, functions
import pandas as pd
from itertools import product

# Params
age_min = 0
age_max = 200
year = 2024


def main():
    # Load config
    config = functions.load_config("testing_config.json")

    # Load datasets
    ltim_lookup = pd.read_csv(config["lookup_tables"]["ltim_lookup"])

    las_lookup = pd.read_csv(config["lookup_tables"]["las_lookup"])

    ltim_immigration = prov_fin.load_summary_data(
        path=config["prov_fin_paths"]["spring_immigration"],
        age_var="Age",
        age_min=age_min,
        age_max=age_max,
        lan_var="Local Authority Name",
        date_var="Date Updated",
    )

    ltim_emigration = prov_fin.load_summary_data(
        path=config["prov_fin_paths"]["spring_emigration"],
        age_var="Age",
        age_min=age_min,
        age_max=age_max,
        lan_var="Local Authority Name",
        date_var="Date Updated",
    )

    ltim_provisional = prov_fin.load_summary_data(
        path=config["prov_fin_paths"]["provisional_mye"],
        age_var="Age",
        age_min=age_min,
        age_max=age_max,
    )

    ltim_provisional_scot = prov_fin.load_summary_data(
        path=config["prov_fin_paths"]["provisional_scot"],
        age_var="Age",
        age_min=age_min,
        age_max=age_max,
    )

    # Merge immigration and emmigration
    ltim_merged = pd.merge(
        ltim_immigration,
        ltim_emigration,
        on=["Age", "Local Authority Code", "Year", "Sex", "Nationality Group"],
        how="left",
        suffixes=("_imm", "_em"),
    )

    ltim_merged["Net_Cell"] = ltim_merged["Count_imm"] - ltim_merged["Count_em"]

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

    ltim_provisional_subset["Year"] = year

    # Create aggregated provisional data
    ltim_provisional_agg = (
        ltim_provisional_subset.groupby(["code", "Year"])
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
    ltim_provisional_scot_merged = pd.merge(
        scot_cartesian, ltim_provisional_scot, on=scot_column_select, how="left"
    ).fillna(0)

    # Aggregate the merged Scotland data, summing count for sex
    ltim_provisional_scot_agg = (
        ltim_provisional_scot_merged.groupby(["ca_code", "year", "dir", "Age"])
        .agg({"count": "sum"})
        .reset_index()
    )

    print(ltim_provisional_scot_agg.head())

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

    print(ltim_provisional_scot_agg[ltim_provisional_scot_agg["year"] == year].head())


if __name__ == "__main__":
    main()
