import pandas as pd


def merged_national_profile(
    provisional_df: pd.DataFrame, final_df: pd.DataFrame, config: dict
) -> pd.DataFrame:
    """
    Merges final immigration data onto the provisional data and computes national profiles.

    Args:
        provisional_df (pd.DataFrame): The provisional immigration dataset.
        final_df (pd.DataFrame): The final immigration dataset.
        config (dict): Configuration dictionary containing dataset variable mappings.

    Returns:
        pd.DataFrame: A DataFrame containing the merged data along with national profiles.
    """
    left_vars = config["datasets"]["provisional"]["variables"]
    right_vars = config["datasets"]["final_immigration"]["variables"]

    merged_df = provisional_df.merge(
        final_df,
        left_on=[
            "year",
            left_vars["la_code"],
            left_vars["age"],
        ],
        right_on=[right_vars["year"], right_vars["la_code"], right_vars["age"]],
        how="left",
    )

    merged_df = merged_df[
        [
            right_vars["year"],
            right_vars["la_code"],
            right_vars["age"],
            "imm_prov",
            "em_prov",
            "net_prov",
            "imm_fin",
            "em_fin",
            "net_fin",
        ]
    ]

    national_profile = (
        merged_df.groupby(right_vars["age"])
        .agg(
            imm_prov_T=("imm_prov", "sum"),
            em_prov_T=("em_prov", "sum"),
            net_prov_T=("net_prov", "sum"),
            imm_fin_T=("imm_fin", "sum"),
            em_fin_T=("em_fin", "sum"),
            net_fin_T=("net_fin", "sum"),
        )
        .reset_index()
    )

    return merged_df.merge(national_profile, on=right_vars["age"], how="left")


def year_agg_sqdiff(merged_df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """
    Computes the squared differences of immigration, emigration, and net migration counts
    between two specified years.

    Args:
        merged_df (pd.DataFrame): The merged DataFrame containing immigration and emigration data.
        config (dict): Configuration dictionary containing dataset variable mappings and global parameters.

    Returns:
        pd.DataFrame: A DataFrame containing the squared differences for immigration, emigration, and net migration counts between the two specified years.
    """
    variables = config["datasets"]["final_immigration"]["variables"]

    year_1 = config["global_parameters"]["year"]
    year_2 = config["global_parameters"]["year2"]
    df_dict = {}

    for year in [year_1, year_2]:
        df = (
            merged_df[merged_df[variables["year"]] == year]
            .groupby([variables["la_code"], variables["year"], variables["age"]])
            .agg(
                count_imm=("imm_fin", "sum"),
                count_em=("em_fin", "sum"),
                count_net=("net_fin", "sum"),
            )
        ).reset_index()

        df_total = (
            merged_df[merged_df[variables["year"]] == year]
            .groupby([variables["year"], variables["age"]])
            .agg(
                total_count_imm=("imm_fin", "sum"),
                total_count_em=("em_fin", "sum"),
                total_count_net=("net_fin", "sum"),
            )
        ).reset_index()

        df = df.merge(df_total, on=[variables["year"], variables["age"]], how="left")

        df_dict.update({year: df.drop(columns=[variables["year"]])})

    # DataFrame containing squared differences
    merged = pd.merge(
        df_dict[year_1],
        df_dict[year_2],
        on=[variables["la_code"], variables["age"]],
        how="left",
        suffixes=(year_1, year_2),
    )

    for out_name in ["imm", "em", "net"]:
        merged = year_squared_difference(merged, out_name, year_1, year_2)

    # Aggregated DataFrame for scaled sums of squared differences
    adjusted_ssq = merged.groupby(variables["la_code"]).agg(
        imm_ssq_total=("sqdiff_imm", "sum"),
        em_ssq_total=("sqdiff_em", "sum"),
        net_ssq_total=("sqdiff_net", "sum"),
        imm_la_total=(f"count_imm{year_1}", "sum"),
        em_la_total=(f"count_em{year_1}", "sum"),
        net_la_total=(f"count_net{year_1}", "sum"),
    )

    for out_name in ["imm", "em", "net"]:
        adjusted_ssq[f"{out_name}_adjusted_size_ssq"] = (
            adjusted_ssq[f"{out_name}_ssq_total"] / adjusted_ssq[f"{out_name}_la_total"]
        )

    return merged, adjusted_ssq.reset_index()


def year_squared_difference(
    yc_df: pd.DataFrame,
    output_name: str,
    year_1: int,
    year_2: int,
) -> pd.DataFrame:
    """
    Computes the squared differences for a specific migration type between two years.

    Args:
        yc_df (pd.DataFrame): The DataFrame containing migration counts for two years.
        output_name (str): The migration type to compute squared differences for. Must be one of 'imm', 'em', or 'net'.
        year_1 (int): The first year for comparison.
        year_2 (int): The second year for comparison.

    Returns:
        pd.DataFrame: The DataFrame with added columns for the difference and squared difference of the specified migration type between the two years.
    """
    if output_name not in ["imm", "em", "net"]:
        raise ValueError("output_name must be one of 'imm', 'em', 'net'")

    count_year_1 = f"count_{output_name}{year_1}"
    total_count_year_1 = f"total_count_{output_name}{year_1}"

    count_year_2 = f"count_{output_name}{year_2}"
    total_count_year_2 = f"total_count_{output_name}{year_2}"

    yc_df[f"diff_{output_name}"] = (yc_df[count_year_2]) - (
        yc_df[count_year_1] * yc_df[total_count_year_2] / yc_df[total_count_year_1]
    )

    yc_df[f"sqdiff_{output_name}"] = yc_df[f"diff_{output_name}"] ** 2

    return yc_df


def pivot_sex_ratio_frame(sex_ratio_df: pd.DataFrame, config: dict):
    variables = config["datasets"]["final_immigration"]["variables"]

    # Filter on years
    sex_ratio_df = sex_ratio_df[
        sex_ratio_df[variables["year"]].isin(
            [config["global_parameters"]["year"], config["global_parameters"]["year2"]]
        )
    ]

    # First pivot on gender and year
    sr_pivot = sex_ratio_df.pivot_table(
        index=[
            variables["la_code"],
            variables["age"],
        ],
        columns=[variables["sex"], variables["year"]],
        values=["imm_fin", "em_fin"],
    )

    return sr_pivot
