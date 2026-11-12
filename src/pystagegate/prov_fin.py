"""Prepare migration estimates and compare provisional and final profiles.

Functions use column names from ``config["datasets"][dataset]["variables"]``
and selections from ``config["global_parameters"]``. Preparation helpers
filter final data, join immigration to emigration, aggregate provisional
estimates, and reshape Scottish direction counts. Comparison helpers rescale
provisional estimates to final totals and aggregate squared residuals.

Notes:
    Inputs must already have compatible count types, dimension labels, and
    geographic codes. Configuration and schemas are not validated here.
    Most helpers construct new DataFrames; ``squared_difference`` instead
    modifies and returns its input. Pandas grouping normally drops missing
    group keys, and sums skip missing counts, returning zero for all-missing
    groups. No weights, uncertainty estimates, significance tests, or
    independence assumptions are implemented. The squared differences are
    descriptive discrepancies, not calibrated inferential statistics.
"""

import pandas as pd
from itertools import product


def _filter_migration_data(migration_df: pd.DataFrame, key: str, config: dict):
    """Select final migration records by configured nationality and year.

    Args:
        migration_df (pd.DataFrame): Records with the nationality and year
            columns named by the selected dataset's variable mapping.
        key (str): Dataset key under ``config["datasets"]``, typically
            ``"final_immigration"`` or ``"final_emigration"``.
        config (dict): The selected dataset's ``variables`` must define
            ``nationality`` and ``year``. ``global_parameters`` must define
            ``final_nationalities`` (values accepted by ``Series.isin``) and
            ``year`` (the value to match exactly).

    Returns:
        pd.DataFrame: Matching rows with their original columns and index;
        no aggregation, renaming, or index reset is performed.

    Raises:
        KeyError: If a required configuration key or input column is absent.
        TypeError: If ``final_nationalities`` is not a suitable list-like
            argument for ``Series.isin``.

    Notes:
        Both selections must match; values are not coerced between types.
        Missing values follow pandas membership and equality semantics.
        No matches produce an empty DataFrame. The input is not modified;
        no explicit deep copy of the selected data is requested.
    """
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
    """Left-join final flows and sum them over the retained dimensions.

    Args:
        immigration_df (pd.DataFrame): Final immigration records with the
            configured ``age``, ``la_code``, ``year``, ``sex``, ``nationality``,
            and numeric ``count`` columns.
        emigration_df (pd.DataFrame): Final emigration records with the same
            logical dimensions and count, using its own column mapping.
        config (dict): ``datasets.final_immigration.variables`` and
            ``datasets.final_emigration.variables`` must each map ``age``,
            ``la_code``, ``year``, ``sex``, ``nationality``, and ``count`` to
            input column names. No global selection keys are read here.
        sex_ratio (bool): If True, retain sex when aggregating and omit net
            migration. If False, sum over sex as well. Defaults to False.

    Returns:
        pd.DataFrame: With ``sex_ratio=False``, columns in order are the
        immigration mapping's year, local-authority, and age column names,
        followed by ``imm_fin``, ``em_fin``, and ``net_fin``. Each row is a
        local-authority/year/age group and ``net_fin = imm_fin - em_fin``.
        With ``sex_ratio=True``, columns are year, local authority, age, sex
        (using the immigration mapping), ``imm_fin``, and ``em_fin``.

    Raises:
        KeyError: If required configuration keys or columns are absent, or
            merge suffixes make an expected column name unavailable.
        ValueError: If pandas cannot merge incompatible join-key types.
        TypeError: If count values do not support the requested arithmetic.

    Notes:
        The left join uses age, local authority, year, sex, and nationality,
        with ``_imm``/``_em`` suffixes for overlapping non-key names. Equal
        configured count names are read with these suffixes; different count
        names are read unchanged. Inputs are not filtered by year or
        nationality and are not modified. Nationality is always summed out.

        Emigration-only keys are discarded. Unmatched immigration rows have
        missing emigration counts, which group sums skip; an all-missing
        emigration group sums to zero. Missing retained group keys are
        dropped by grouping. Pandas can match missing join keys. Duplicate
        join keys can multiply rows and counts; uniqueness is not checked,
        so callers must ensure the join represents their intended totals.
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
    """Sum provisional flows by local authority and age, then assign a year.

    Args:
        provisional_df (pd.DataFrame): Records with local-authority and age
            dimensions and numeric immigration and emigration columns. Any
            additional dimensions, including any input year, are summed out.
        config (dict): ``datasets.provisional.variables`` must map ``la_code``,
            ``age``, ``immigration``, and ``emigration`` to input columns.
            ``global_parameters.year`` supplies the output year label.

    Returns:
        pd.DataFrame: One row per local-authority/age group, with columns
        ``year``, the configured local-authority and age names, ``imm_prov``,
        ``em_prov``, and ``net_prov``, in that order. Immigration and emigration
        are group sums; ``net_prov = imm_prov - em_prov``.

    Raises:
        KeyError: If required configuration keys or input columns are absent.
        TypeError: If aggregated counts do not support subtraction.

    Notes:
        Despite its name, this function does not filter records by year.
        It sums all supplied rows first and assigns the configured year
        afterwards. Callers must prefilter when a single-year total is
        intended. Missing group keys are dropped; sums skip missing values
        and all-missing flow groups sum to zero. The input is not modified.
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
    """Complete the Scottish data's observed dimension combinations with zeros.

    Args:
        provisional_scot_df (pd.DataFrame): Scottish provisional records.
            Every column except the configured count is treated as a
            dimension, including any extra metadata columns.
        config (dict): ``datasets.provisional_scot.variables.count`` names
            the count column to exclude from the Cartesian dimensions.

    Returns:
        pd.DataFrame: The Cartesian product of observed unique values in
        every non-count column, left-joined to the original records on all
        those columns. Dimension columns precede the count column when
        present. All missing cells in the merged result are filled with zero.

    Raises:
        KeyError: If the required configuration keys are absent.
        TypeError: If dimension values are unhashable or a column dtype
            cannot accept zero during missing-value filling.
        ValueError: If pandas cannot merge the derived dimension keys.

    Notes:
        This adds combinations only from values already observed, not from
        an external geography, age, year, or direction domain. Duplicate
        source dimension combinations remain duplicate rows after merging;
        counts are not aggregated. The set used for the product gives no
        guaranteed row order and can be large for many dimensions.

        Missing dimension values participate in the product and can match
        missing source keys under pandas merge semantics. ``fillna(0)``
        replaces both original missing values and newly introduced ones,
        including missing dimension labels, not just missing counts. The
        input is not modified. The count column's existence is not checked.
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
    """Aggregate Scottish direction counts, pivot flows, and select the year.

    Args:
        provisional_scot_df (pd.DataFrame): Records with the configured
            local-authority, year, direction, age, and numeric count columns.
        config (dict): ``datasets.provisional_scot.variables`` must map
            ``la_code``, ``year``, ``direction``, ``age``, and ``count``.
            ``global_parameters.provisional_scot_direction`` supplies
            immigration and emigration labels at positions 0 and 1,
            respectively; ``global_parameters.year`` is matched exactly.

    Returns:
        pd.DataFrame: One row per retained local-authority/year/age
        combination. Columns are the configured year, local-authority, and
        age names, followed by ``imm_prov``, ``em_prov``, and ``net_prov``.
        Flows are summed counts; ``net_prov = imm_prov - em_prov``.

    Raises:
        KeyError: If a required configuration key or input column is absent,
            or a configured direction does not produce a required flow column.
        IndexError: If the direction configuration has fewer than two items.
        TypeError: If count values cannot be aggregated or subtracted.

    Notes:
        Counts are first summed by local authority, year, direction, and age;
        other dimensions are discarded. The pivot uses pandas' default mean
        aggregation, but its cells already have at most one aggregated value.
        Only after pivoting and computing net migration are rows selected
        for the configured year. Additional directions are omitted from the
        returned columns; input data is not modified.

        Grouping drops missing dimension keys and sums skip missing counts,
        with all-missing count groups summing to zero. Absent direction
        combinations become missing pivot cells, not zeros, so net migration
        can be missing. No Cartesian completion or explicit filling occurs
        here; ``provisional_scot_cartesian_merge`` can be called beforehand
        when zero-filled combinations are intended.
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
    """Add rescaled residuals and squared residuals to the input in place.

    Args:
        df (pd.DataFrame): Numeric estimate and total columns, with each
            total already aligned to the corresponding row's comparison
            group. Totals are supplied, not calculated or checked here.
        type_1 (str): Column containing the estimate to rescale.
        type_2 (str): Column containing the comparison estimate.
        type_1_total (str): Column containing the first estimate's group total.
        type_2_total (str): Column containing the comparison group total.
        output_name (str): Suffix for ``diff_`` and ``sqdiff_`` output column
            names. Defaults to ``"output"``.

    Returns:
        pd.DataFrame: The same object as ``df``, with ``diff_{output_name}``
        and ``sqdiff_{output_name}`` added or overwritten. Existing rows,
        index, and other columns are retained.

    Raises:
        KeyError: If any named input column is absent.
        TypeError: If the input columns do not support numeric arithmetic.

    Notes:
        The raw residual is ``type_2 - type_1 * type_2_total / type_1_total``.
        Its square is stored unless ``type_1_total == 0``, in which case
        only the squared residual is replaced by zero. The raw residual is
        not repaired and may remain NaN or infinite after division by zero.
        Other missing or non-finite arithmetic results are not explicitly
        replaced; pandas dtype and missing-value semantics apply.

        Rescaling compares the first profile at the second profile's total,
        assuming the supplied totals represent comparable groups. Negative
        estimates and totals are not rejected. These are descriptive squared
        residuals, not variance-standardized statistics or significance tests.
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
    """Compare a nation's age profiles and return local-authority discrepancies.

    Args:
        df (pd.DataFrame): Records with the configured local-authority and
            age columns and numeric ``imm_prov``, ``em_prov``, ``net_prov``,
            ``imm_fin``, ``em_fin``, and ``net_fin`` columns. Authority codes
            must support pandas string operations and start with a nation
            letter. Rows are expected to represent comparable age cells.
        config (dict): ``datasets.final_immigration.variables`` supplies
            ``la_code`` and ``age`` column names. No year selection is read.
        nation (str): Exact prefix ``"E"``, ``"S"``, or ``"W"`` for England,
            Scotland, or Wales, respectively.

    Returns:
        pd.DataFrame: A single DataFrame, despite the tuple return annotation,
        with one row per local authority. Columns are the configured
        authority name; ``imm_prov``, ``em_prov``, ``net_prov``;
        ``sqdiff_imm``, ``sqdiff_em``, ``sqdiff_net``;
        ``sqdiff_imm_sc``, ``sqdiff_em_sc``, ``sqdiff_net_sc``; and ``nation``.
        Final totals, age totals, and raw residuals are not returned.

    Raises:
        ValueError: If ``nation`` is not one of the three accepted prefixes,
            or the selected nation's age aggregation has no records.
        KeyError: If required configuration keys or columns are absent, or
            existing ``_T`` columns interfere with merged total names.
        AttributeError: If authority codes do not support string access.
        TypeError: If estimates do not support numeric arithmetic.

    Notes:
        Select rows by the first character of the authority code. Sum all
        six flow columns by age within that nation, then left-join those
        totals to the selected rows on age, adding ``_T`` to total names.
        No year filter or grouping is applied: multiple supplied years and
        any other dimensions are pooled. Net columns are used as supplied,
        not recomputed from immigration and emigration.

        For each of ``imm``, ``em``, and ``net``, compute the row residual
        ``prefix_fin - prefix_prov * prefix_fin_T / prefix_prov_T`` and its
        square through ``squared_difference``. Sum squared residuals and
        provisional flows by local authority. Divide ``sqdiff_imm`` by
        authority ``imm_prov`` and ``sqdiff_em`` by ``em_prov``. Net squared
        discrepancy is also divided by ``imm_prov``, not by ``net_prov``.
        The nation column is the first character of the authority code.

        Zero provisional age totals force only their squared residuals to
        zero; raw residuals can be NaN or infinite. Group sums skip missing
        values and all-missing groups sum to zero. Missing age keys are
        excluded from age totals. Final scaling has no zero-denominator
        guard and can yield NaN or infinity; negative denominators are not
        rejected. The input DataFrame is not modified: residuals are added
        to the newly merged intermediate frame.

        The calculation treats national age totals as the rescaling
        reference and assumes compatible age definitions and cell coverage.
        Duplicate input cells are included without validation. No sampling
        variance, covariance, degrees of freedom, or reference distribution
        is estimated; the scaled sums are descriptive, not formal tests.
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
