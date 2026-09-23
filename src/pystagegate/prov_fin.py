import pandas as pd
from itertools import product


def _filter_migration_data(migration_df: pd.DataFrame, key: str, config: dict):
    variables = config["datasets"][key]["variables"]
    migration_df = migration_df[
        migration_df[variables["nationality"]].isin(
            config["global_parameters"]["final_nationalities"]
        )
    ]
    migration_df = migration_df[
        migration_df[variables["year"]] == config["global_parameters"]["year"]
    ]

    return migration_df


def merge_final_migration_data(
    immigration_df: pd.DataFrame,
    emigration_df: pd.DataFrame,
    config: dict,
    sex_ratio: bool = False,
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

    if sex_ratio:
        # Alternative aggregation for sex_ratio calculations
        merged_df = (
            merged_df.groupby(
                [
                    left_vars["la_code"],
                    left_vars["year"],
                    left_vars["age"],
                    left_vars["sex"],
                ]
            )
            .agg(imm_fin=(immigration_col, "sum"), em_fin=(emigration_col, "sum"))
            .reset_index()
        )

        return merged_df[
            [
                left_vars["year"],
                left_vars["la_code"],
                left_vars["age"],
                left_vars["sex"],
                "imm_fin",
                "em_fin",
            ]
        ]

    else:
        # Default aggregation for combining with provisional data
        merged_df = (
            merged_df.groupby(
                [left_vars["la_code"], left_vars["year"], left_vars["age"]]
            )
            .agg(imm_fin=(immigration_col, "sum"), em_fin=(emigration_col, "sum"))
            .reset_index()
        )

        merged_df["net_fin"] = merged_df["imm_fin"] - merged_df["em_fin"]

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
        )
        .reset_index()
    )

    subset_df["year"] = config["global_parameters"]["year"]
    subset_df["net_prov"] = subset_df["imm_prov"] - subset_df["em_prov"]

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
    df: pd.DataFrame,
    type_1: str,
    type_2: str,
    type_1_total: str,
    type_2_total: str,
    output_name: str = "output",
) -> pd.DataFrame:
    """
    Create squared difference estimates for migration data using two estimate types and their totals.

    Args:
        df (pd.DataFrame): The input migration DataFrame.
        type_1 (str): The first estimate column name.
        type_2 (str): The second estimate column name.
        type_1_total (str): The first estimate total column name.
        type_2_total (str): The second estimate total column name.
        output_name (str): Substring to denote the outputted squared difference columns. Defaults to "output".

    Returns:
        df (pd.DataFrame): A pandas DataFrame containing the difference
        and squared difference estiamtes.
    """
    # Todo: Interrogate why we do not recode here in the case of prov_col_total = 0
    df[f"diff_{output_name}"] = df[type_2] - (
        df[type_1] * df[type_2_total] / df[type_1_total]
    )

    # Todo: Interrogate why we recode to zero in the case of prov_col_total = 0
    df[f"sqdiff_{output_name}"] = (df[f"diff_{output_name}"] ** 2).where(
        df[f"{type_1_total}"] != 0, 0
    )

    return df


def nation_breakdown_sqdiff(
    df: pd.DataFrame,
    config: dict,
    nation: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Performs aggregations and squared difference calculations by age and Local Authority on national profiles.

    Args:
        df (pd.DataFrame): The input migration DataFrame.
        config (dict): A dictionary configuration.
        nation (str): A one letter code for nation, must be one of 'E', 'S', 'W'.

    Returns:
        tuple:
            - age_agg (pd.DataFrame): Migration data aggregated by age.
            - la_agg (pd.DataFrame): Migration data aggregated by age and local authority.
    """

    variables = config["datasets"]["final_immigration"]["variables"]

    # Filter by nation, aggregate by age and merge these totals with original dataframe
    if nation in ["W", "S", "E"]:
        age_agg = (
            df[df[variables["la_code"]].str[0] == nation]
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

        if len(age_agg) == 0:
            raise ValueError(f"No matching records found for nation {nation}")

        age_agg = df[df[variables["la_code"]].str[0] == nation].merge(
            age_agg,
            on=variables["age"],
            how="left",
            suffixes=("", "_T"),
        )
    else:
        raise ValueError("Nation must be one of 'E', 'S', 'W'")

    # Compute the squared difference between the age totals and the age and local authority estimates
    for prefix in ["imm", "em", "net"]:
        age_agg = squared_difference(
            age_agg,
            type_1=f"{prefix}_prov",
            type_2=f"{prefix}_fin",
            type_1_total=f"{prefix}_prov_T",
            type_2_total=f"{prefix}_fin_T",
            output_name=f"{prefix}",
        )

    # Now aggregate by local authority
    la_agg = (
        age_agg.groupby(variables["la_code"])
        .agg(
            {
                "imm_prov": "sum",
                "em_prov": "sum",
                "net_prov": "sum",
                "sqdiff_imm": "sum",
                "sqdiff_em": "sum",
                "sqdiff_net": "sum",
            }
        )
        .reset_index()
    )

    # Scale squared differences by provisional totals
    # todo: Check denominator for scaled squared differences - why is net migration scaled by immigration??
    # todo: How to handle divide by zero?
    for prefix in ["imm", "em", "net"]:
        if prefix == "net":
            la_agg[f"sqdiff_{prefix}_sc"] = (
                la_agg[f"sqdiff_{prefix}"] / la_agg["imm_prov"]
            )
        else:
            la_agg[f"sqdiff_{prefix}_sc"] = (
                la_agg[f"sqdiff_{prefix}"] / la_agg[f"{prefix}_prov"]
            )

    la_agg["nation"] = la_agg[variables["la_code"]].str[0]

    return la_agg
