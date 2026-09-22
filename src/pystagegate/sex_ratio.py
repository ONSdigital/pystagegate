import pandas as pd
import numpy as np
from pystagegate import prov_fin


def year_agg_merge(merged_df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """
    Aggregates year totals for specified years and merges them for comparison.

    Args:
        merged_df (pd.DataFrame): The merged DataFrame containing immigration and emigration data.
        config (dict): Configuration dictionary containing dataset variable mappings and global parameters.

    Returns:
        pd.DataFrame: A DataFrame containing the squared differences for immigration, emigration, and net migration counts between the two specified years.
    """
    variables = config["datasets"]["final_immigration"]["variables"]

    year_1 = config["global_parameters"]["year"]
    year_2 = config["global_parameters"]["year2"]

    if (
        merged_df[merged_df[variables["year"]] == year_1].empty
        | merged_df[merged_df[variables["year"]] == year_2].empty
    ):
        raise ValueError(f"Cannot find both {year_1} and {year_2} in data")

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

    # DataFrame with merged totals for year_1 and year_2
    return pd.merge(
        df_dict[year_1],
        df_dict[year_2],
        on=[variables["la_code"], variables["age"]],
        how="left",
        suffixes=(f"_{year_1}", f"_{year_2}"),
    )


def year_agg_sqdiff(
    merged_df: pd.DataFrame, config: dict
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Computes the squared differences for immigration, emigration, and net migration counts
    between two specified years and aggregates the results.

    Args:
        merged (pd.DataFrame): The merged DataFrame containing immigration and emigration data.
        config (dict): Configuration dictionary containing dataset variable mappings and global parameters.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: A tuple containing the merged DataFrame with squared differences
        and the aggregated DataFrame with scaled sums of squared differences.
    """
    variables = config["datasets"]["final_immigration"]["variables"]
    year_1 = config["global_parameters"]["year"]
    year_2 = config["global_parameters"]["year2"]

    for output_name in ["imm", "em", "net"]:
        count_year_1 = f"count_{output_name}_{year_1}"
        total_count_year_1 = f"total_count_{output_name}_{year_1}"

        count_year_2 = f"count_{output_name}_{year_2}"
        total_count_year_2 = f"total_count_{output_name}_{year_2}"

        merged_df = prov_fin.squared_difference(
            merged_df,
            type_1=count_year_1,
            type_2=count_year_2,
            type_1_total=total_count_year_1,
            type_2_total=total_count_year_2,
            output_name=output_name,
        )

    # Aggregated DataFrame for scaled sums of squared differences
    adjusted_ssq = merged_df.groupby(variables["la_code"]).agg(
        imm_ssq_total=("sqdiff_imm", "sum"),
        em_ssq_total=("sqdiff_em", "sum"),
        net_ssq_total=("sqdiff_net", "sum"),
        imm_la_total=(f"count_imm_{year_1}", "sum"),
        em_la_total=(f"count_em_{year_1}", "sum"),
        net_la_total=(f"count_net_{year_1}", "sum"),
    )

    for out_name in ["imm", "em", "net"]:
        adjusted_ssq[f"{out_name}_adjusted_size_ssq"] = (
            adjusted_ssq[f"{out_name}_ssq_total"] / adjusted_ssq[f"{out_name}_la_total"]
        )

    return merged_df, adjusted_ssq.reset_index()


def pivot_sex_ratio_frame(sex_ratio_df: pd.DataFrame, config: dict):
    """
    Pivot the sex ratio DataFrame over sex and year.

    Args:
        sex_ratio_df (pd.DataFrame): The DataFrame containing sex ratio data.
        config (dict): Configuration dictionary.

    Returns:
        pd.DataFrame: A pivoted DataFrame
    """
    variables = config["datasets"]["final_immigration"]["variables"]
    year_1 = config["global_parameters"]["year"]
    year_2 = config["global_parameters"]["year2"]

    if (
        sex_ratio_df[sex_ratio_df[variables["year"]] == year_1].empty
        | sex_ratio_df[sex_ratio_df[variables["year"]] == year_2].empty
    ):
        raise ValueError(f"Cannot find both {year_1} and {year_2} in data")

    # Filter on years
    sex_ratio_df = sex_ratio_df[sex_ratio_df[variables["year"]].isin([year_1, year_2])]

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


def clean_and_mask(
    sex_ratio_df: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    """
    Clean and mask the sex ratio DataFrame.

    Args:
        sex_ratio_df (pd.DataFrame): The DataFrame containing sex ratio data.
        config (dict): Configuration dictionary.

    Returns:
        pd.DataFrame: The cleaned and masked DataFrame.
    """
    # Recode values
    sex_ratio_df = sex_ratio_df.where(sex_ratio_df >= 1, 1).where(
        sex_ratio_df >= 0.5, 0
    )

    # Add flags
    masked_df = (
        sex_ratio_df.mask(sex_ratio_df == 0, "Zero")
        .mask(sex_ratio_df >= 1, "Low")
        .mask(sex_ratio_df >= 5, "OK")
    )

    fin_imm_vars = config["datasets"]["final_immigration"]["variables"]

    sex_ratio_df = sex_ratio_df.merge(
        masked_df,
        on=[
            fin_imm_vars["la_code"],
            fin_imm_vars["age"],
        ],
        how="left",
        suffixes=("", "_quality"),
    )
    return sex_ratio_df


def compute_sex_ratio(
    sex_ratio_df: pd.DataFrame,
    config: dict,
    caps: tuple[float, float] = None,
    mask: bool = True,
    male_sex: str = "Male",
    female_sex: str = "Female",
) -> pd.DataFrame:
    """
    Compute sex ratios for immigration and emigration across both configured years.

    Args:
        sex_ratio_df (pd.DataFrame): Pivoted DataFrame with (measure, sex, year) columns.
        config (dict): Configuration dictionary containing global parameters.
        caps (tuple[float, float], optional): Lower and upper caps for sex ratio. Defaults to None.
        mask (bool, optional): Whether to apply quality masking to the sex ratio calculations. Defaults to True.

    Returns:
        pd.DataFrame: The DataFrame with added sex ratio columns for each migration type and year.
    """
    year_1 = config["global_parameters"]["year"]
    year_2 = config["global_parameters"]["year2"]

    # Call sex ratio calculation helper func for each year of data
    for year in [year_1, year_2]:
        sex_ratio_df = sex_ratio_helper(
            sex_ratio_df, "imm", year, caps, mask, male_sex, female_sex
        )
        sex_ratio_df = sex_ratio_helper(
            sex_ratio_df, "em", year, caps, mask, male_sex, female_sex
        )

    # Calculate weights
    sex_ratio_df["imm_weight"] = sex_ratio_df["imm_fin"].sum(axis=1)
    sex_ratio_df["em_weight"] = sex_ratio_df["em_fin"].sum(axis=1)

    return sex_ratio_df


def sex_ratio_helper(
    sex_ratio_df: pd.DataFrame,
    migration: str,
    year: int,
    caps: tuple[float, float] = None,
    mask: bool = True,
    male_sex: str = "Male",
    female_sex: str = "Female",
) -> pd.DataFrame:
    """
    Helper function to compute sex ratio for a given migration type and year.

    Args:
        sex_ratio_df (pd.DataFrame): Pivoted DataFrame with (measure, sex, year) columns.
        migration (str): Migration type, either 'imm' or 'em'.
        year (int): Year for which to compute the sex ratio.
        caps (tuple[float, float], optional): Lower and upper caps for sex ratio. Defaults to None.
        mask (bool, optional): Whether to apply quality masking to the sex ratio calculations. Defaults to True.

    Returns:
        pd.DataFrame: The DataFrame with the added sex ratio column for the specified migration type and year.
    """
    if migration not in ["imm", "em"]:
        raise ValueError("migration must be one of 'imm', 'em'")

    # Sex ratio calculation
    male_count = sex_ratio_df[(f"{migration}_fin", male_sex, year)]
    female_count = sex_ratio_df[(f"{migration}_fin", female_sex, year)]
    ratio = male_count / female_count

    # Default recode sex ratios based on quality metrics
    if mask:
        male_quality = sex_ratio_df[(f"{migration}_fin_quality", male_sex, year)]
        female_quality = sex_ratio_df[(f"{migration}_fin_quality", female_sex, year)]

        # Recode sex ratios based on quality metrics
        conditions = [
            # Zero/Zero, Zero/Low or Low/Zero are invalid
            (male_quality == "Zero") & (female_quality.isin(["Zero", "Low"])),
            (male_quality == "Low") & (female_quality == "Zero"),
            # OK/Zero or Zero/OK take the value of the OK estimate
            (male_quality == "Zero") & (female_quality == "OK"),
            (male_quality == "OK") & (female_quality == "Zero"),
        ]
        choices = [np.nan, np.nan, female_count, male_count]

        sex_ratio_df[f"sex_ratio_{migration}_{year}"] = np.select(
            conditions, choices, default=ratio
        )
    else:
        sex_ratio_df[f"sex_ratio_{migration}_{year}"] = ratio

    if caps:
        sex_ratio_df[f"sex_ratio_{migration}_{year}"] = sex_ratio_df[
            f"sex_ratio_{migration}_{year}"
        ].clip(caps[0], caps[1])

    return sex_ratio_df


def sex_ratio_ssq(
    la_df: pd.DataFrame, national_df: pd.DataFrame, config: dict
) -> pd.DataFrame:
    """
    Compute the squared sex ratio for local authorities compared to the national average.

    Args:
        la_df (pd.DataFrame): DataFrame containing local authority sex ratio data.
        national_df (pd.DataFrame): DataFrame containing national sex ratio data.

    Returns:
        pd.DataFrame: A DataFrame containing the squared sex ratio for local authorities compared to the national average.
    """

    variables = config["datasets"]["final_immigration"]["variables"]
    year_1 = config["global_parameters"]["year"]
    year_2 = config["global_parameters"]["year2"]

    # Merge national data onto local authority data
    sr_merged = (
        la_df.reset_index()
        .merge(
            national_df,
            on=variables["age"],
            how="left",
            suffixes=("_local", "_national"),
        )
        .set_index(variables["la_code"])
    )

    # Compute sum of squared differences in sex ratios for national vs local authority data
    for migration in ["imm", "em"]:
        sr_merged[f"ssq_{migration}"] = (
            (
                (
                    sr_merged[f"sex_ratio_{migration}_{year_2}_local"]
                    - sr_merged[f"sex_ratio_{migration}_{year_1}_local"]
                )
                - (
                    sr_merged[f"sex_ratio_{migration}_{year_2}_national"]
                    - sr_merged[f"sex_ratio_{migration}_{year_1}_national"]
                )
            )
            ** 2
        ) * sr_merged[f"{migration}_weight_local"]

    return sr_merged
