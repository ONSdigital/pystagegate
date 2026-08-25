import pandas as pd
from itertools import product


def filter_migration_data(migration_df: pd.DataFrame, key: str, config: dict):
    variables = config["datasets"][key]["variables"]
    migration_df = migration_df[
        migration_df[variables["nationality"]]
        == config["global_parameters"]["final_nationalities"][0]
    ]
    migration_df = migration_df[
        migration_df[variables["year"]] == config["global_parameters"]["year"]
    ]

    return migration_df


def merge_final_migration_data(
    immigration_df: pd.DataFrame, emigration_df: pd.DataFrame, config: dict
) -> pd.DataFrame:
    """
    Merge immigration and emigration dataframes on specified columns and calculate net migration.

    Args:
        immigration_df (pd.DataFrame): The immigration DataFrame.
        emigration_df (pd.DataFrame): The emigration DataFrame.
        config (dict): A dictionary configuration.

    Returns:
        merged_df (pd.DataFrame): A pandas DataFrame containing the merged data with net migration.
    """
    left_vars = config["datasets"]["final_immigration"]["variables"]
    right_vars = config["datasets"]["final_emigration"]["variables"]

    merged_df = immigration_df.merge(
        emigration_df,
        left_on=[
            left_vars["age"],
            left_vars["la_code"],
            left_vars["year"],
            left_vars["sex"],
            left_vars["nationality"],
        ],
        right_on=[
            right_vars["age"],
            right_vars["la_code"],
            right_vars["year"],
            right_vars["sex"],
            right_vars["nationality"],
        ],
        how="left",
        suffixes=("_imm", "_em"),
    )

    if left_vars["count"] == right_vars["count"]:
        immigration_col = f"{left_vars['count']}_imm"
        emigration_col = f"{left_vars['count']}_em"
    else:
        immigration_col = left_vars["count"]
        emigration_col = right_vars["count"]

    merged_df["net_cell"] = merged_df[immigration_col] - merged_df[emigration_col]

    merged_df = (
        merged_df.groupby([left_vars["la_code"], left_vars["year"], left_vars["age"]])
        .agg(
            imm_fin=(immigration_col, "sum"),
            em_fin=(emigration_col, "sum"),
            net_fin=("net_cell", "sum"),
        )
        .reset_index()
    )

    return merged_df[
        [
            left_vars["year"],
            left_vars["la_code"],
            left_vars["age"],
            "imm_fin",
            "em_fin",
            "net_fin",
        ]
    ]


def subset_provisional_data(provisional_df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """
    Subset the provisional migration data for the specified year and rename columns.

    Args:
        provisional_df (pd.DataFrame): The provisional migration DataFrame.
        config (dict): A dictionary configuration.

    Returns:
        subset_df (pd.DataFrame): A pandas DataFrame containing the subsetted and renamed data.
    """
    variables = config["datasets"]["provisional"]["variables"]

    subset_df = (
        provisional_df.groupby([variables["la_code"], variables["age"]])
        .agg(
            imm_prov=(variables["immigration"], "sum"),
            em_prov=(variables["emigration"], "sum"),
            net_prov=(variables["net"], "sum"),
        )
        .reset_index()
    )

    subset_df["year"] = config["global_parameters"]["year"]

    return subset_df[
        [
            "year",
            variables["la_code"],
            variables["age"],
            "imm_prov",
            "em_prov",
            "net_prov",
        ]
    ]


def provisional_scot_cartesian_merge(
    provisional_scot_df: pd.DataFrame, config: dict
) -> pd.DataFrame:
    """
    Create a cartesian product of unique values for the provisional Scotland data and merge it with the original DataFrame.

    Args:
        provisional_scot_df (pd.DataFrame): The provisional Scotland migration DataFrame.
        config (dict): A dictionary configuration.

    Returns:
        merged_df (pd.DataFrame): A pandas DataFrame containing the cartesian product merged with the original data, with missing values filled with 0.

    """
    variables = config["datasets"]["provisional_scot"]["variables"]

    unique_values = [
        provisional_scot_df[col].unique()
        for col in provisional_scot_df.columns
        if col != variables["count"]
    ]

    scot_column_select = [
        col for col in provisional_scot_df.columns if col != variables["count"]
    ]

    scot_cartesian = pd.DataFrame(
        set(product(*unique_values)), columns=scot_column_select
    )

    scot_merged_df = scot_cartesian.merge(
        provisional_scot_df, on=scot_column_select, how="left"
    ).fillna(0)

    return scot_merged_df


def provisional_scot_aggregate(
    provisional_scot_df: pd.DataFrame, config: dict
) -> pd.DataFrame:
    """
    Aggregate the provisional Scotland migration data by summing counts for each combination of local authority, year, direction, and age.

    Args:
        provisional_scot_df (pd.DataFrame): The provisional Scotland migration DataFrame.
        config (dict): A dictionary configuration.

    Returns:
        aggregate_df (pd.DataFrame): A pandas DataFrame containing the aggregated data.
    """
    variables = config["datasets"]["provisional_scot"]["variables"]
    directions = config["global_parameters"]["provisional_scot_direction"]

    aggregate_df = (
        provisional_scot_df.groupby(
            [
                variables["la_code"],
                variables["year"],
                variables["direction"],
                variables["age"],
            ]
        )
        .agg({variables["count"]: "sum"})
        .reset_index()
    )

    aggregate_df = (
        pd.pivot_table(
            aggregate_df,
            index=[variables["la_code"], variables["year"], variables["age"]],
            columns=variables["direction"],
            values=variables["count"],
        )
        .reset_index()
        .rename(columns={directions[0]: "imm_prov", directions[1]: "em_prov"})
    )

    aggregate_df["net_prov"] = aggregate_df["imm_prov"] - aggregate_df["em_prov"]

    aggregate_df = aggregate_df[
        aggregate_df[variables["year"]] == config["global_parameters"]["year"]
    ]

    return aggregate_df[
        [
            variables["year"],
            variables["la_code"],
            variables["age"],
            "imm_prov",
            "em_prov",
            "net_prov",
        ]
    ]


def squared_difference(
    df: pd.DataFrame, prefix: str, prov_col: str, fin_col: str
) -> pd.DataFrame:
    """
    Create squared difference estimates for migration data using provisional and final estimates.

    Args:
        df (pd.DataFrame): The input migration DataFrame.
        prefix (str): A string prefix used to name the computed squared difference column
        prov_col (str): The provisional estimate column name.
        fin_col (str): The final estimate column name.

    Returns:
        df (pd.DataFrame): A pandas DataFrame containing the difference
        and squared difference estiamtes.
    """

    df[f"diff_{prefix}"] = (df[fin_col] - df[prov_col]) - (
        (df[prov_col] * df[f"{fin_col}_T"] / df[f"{prov_col}_T"]) - (df[prov_col])
    )

    df[f"sqdiff_{prefix}"] = (df[f"diff_{prefix}"] ** 2).where(
        df[f"{prov_col}_T"] != 0, 0
    )

    return df


def regional_breakdown(
    df: pd.DataFrame,
    config: dict,
    nation: str = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Performs aggregations by Age and Local Authority on both a whole country (GB) profile and nation profile.

    Args:
        df (pd.DataFrame): The input migration DataFrame.
        config (dict): A dictionary configuration.
        nation (str, optional): A one letter code for nation, must be one of 'E', 'S', 'W'. Defaults to None for GB analysis.

    Returns:
        tuple:
            - age_agg (pd.DataFrame): Migration data aggregated by age.
            - la_agg (pd.DataFrame): Migration data aggregated by age and local authority.
    """
    imm_prefix = "imm"
    em_prefix = "em"
    net_prefix = "net"

    variables = config["datasets"]["final_immigration"]["variables"]

    if nation is None:
        age_agg = (
            df.groupby(variables["age"])
            .agg(
                {
                    "imm_prov": "sum",
                    "em_prov": "sum",
                    "net_prov": "sum",
                    "imm_fin": "sum",
                    "em_fin": "sum",
                    "net_fin": "sum",
                }
            )
            .reset_index()
        )

        age_agg = df.merge(
            age_agg,
            on=variables["age"],
            how="left",
            suffixes=("", "_T"),
        )
    else:
        if nation in ["W", "S", "E"]:
            age_agg = (
                df[df["nation"] == nation]
                .groupby(variables["age"])
                .agg(
                    {
                        "imm_prov": "sum",
                        "em_prov": "sum",
                        "net_prov": "sum",
                        "imm_fin": "sum",
                        "em_fin": "sum",
                        "net_fin": "sum",
                    }
                )
                .reset_index()
            )

            age_agg = df[df["nation"] == nation].merge(
                age_agg,
                on=variables["age"],
                how="left",
                suffixes=("", "_T"),
            )
        else:
            raise (ValueError("Nation must be one of 'E', 'S', 'W'"))

    age_agg = squared_difference(age_agg, imm_prefix, "imm_prov", "imm_fin")
    age_agg = squared_difference(age_agg, em_prefix, "em_prov", "em_fin")
    age_agg = squared_difference(age_agg, net_prefix, "net_prov", "net_fin")

    la_agg = (
        age_agg.groupby(variables["la_code"])
        .agg(
            {
                "imm_prov": "sum",
                "em_prov": "sum",
                "net_prov": "sum",
                f"sqdiff_{imm_prefix}": "sum",
                f"sqdiff_{em_prefix}": "sum",
                f"sqdiff_{net_prefix}": "sum",
            }
        )
        .reset_index()
    )

    # todo: check denominator for scaled squared differences
    for prefix in [imm_prefix, em_prefix, net_prefix]:
        if prefix == net_prefix:
            la_agg[f"sqdiff_{prefix}_sc"] = (
                la_agg[f"sqdiff_{prefix}"] / la_agg[f"{imm_prefix}_prov"]
            )
        else:
            la_agg[f"sqdiff_{prefix}_sc"] = (
                la_agg[f"sqdiff_{prefix}"] / la_agg[f"{prefix}_prov"]
            )

    for frame in [age_agg, la_agg]:
        frame["nation"] = frame[variables["la_code"]].str[0]

    return age_agg, la_agg
