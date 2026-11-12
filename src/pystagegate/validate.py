"""Validate configured migration tables using dataset-specific Pandera schemas.

Notes:
    Checks cover column structure, coercible types and selected value constraints,
    not statistical fitness, complete coverage or formal quality compliance.
    Validation does not read or write files.
"""

import pandas as pd
import pandera.pandas as pa


def validate(df: pd.DataFrame, df_key: str, config: dict) -> None:
    """Check one supported migration table without returning its coerced copy.

    Args:
        df (pd.DataFrame): Table containing exactly the configured columns for
            its schema, with no null values. Final tables require string local
            authority, sex and nationality columns, integer age and year, and a
            float count. Provisional England/Wales tables require string local
            authority and sex, integer age, and float immigration, emigration
            and net. Scottish provisional tables require string local authority,
            sex and direction, integer age and year, and a float count. Types
            are checked after Pandera attempts coercion.
        df_key (str): Dataset name: ``final_immigration``, ``final_emigration``,
            ``provisional`` or ``provisional_scot``.
        config (dict): Requires ``datasets[df_key].variables`` mapping semantic
            names to column names. All schemas use ``la_code``, ``age`` and
            ``sex``; final schemas also use ``nationality``, ``year`` and
            ``count``; provisional uses ``immigration``, ``emigration`` and
            ``net``; Scottish provisional uses ``direction``, ``year`` and
            ``count``. ``global_parameters`` must contain ``age_min``,
            ``age_max``, ``year`` and ``year2`` (which may be None). Final
            schemas additionally require ``final_nationalities``; Scottish
            provisional requires ``provisional_scot_direction``.

    Returns:
        None: Successful validation returns no data. The coerced DataFrame
        returned by Pandera is discarded; this function does not request
        in-place validation or replace the caller's table.

    Raises:
        ValueError: If ``df_key`` is absent from ``config['datasets']``.
        KeyError: If a required configuration entry is absent.
        pandera.errors.SchemaError: If schema validation or coercion fails.
        UnboundLocalError: If a configured dataset name has no supported schema.

    Notes:
        Local authority strings need only start with E, S or W; actual codes
        are not verified. Ages must be within the inclusive configured bounds.
        Sex must have exactly two distinct values, with no label check. For
        year-bearing tables, the configured year and any non-None year2 must
        occur somewhere in the column; other years are not excluded and
        coverage within each authority or age is not checked. Counts and
        provisional immigration/emigration must lie in [0, 1000000]. Final
        nationalities must belong to the configured collection. Scottish
        directions must have exactly two distinct values, both in the configured
        collection. Provisional net must equal immigration minus emigration
        exactly, using the original input columns for that comparison.

        Schemas reject extra columns and do not enforce unique rows, balanced
        groups, integral counts or consistency between separate datasets.
        Checks normally fail at the first reported error, not as a full audit.
    """
    if df_key not in config["datasets"]:
        raise ValueError(f"Dataset key '{df_key}' not found in configuration.")

    params = config["global_parameters"]
    vars = config["datasets"][df_key]["variables"]

    # Reusable checks for Local Authority codes
    la_code_checks = [
        pa.Check.str_startswith(("W", "S", "E")),
    ]

    # Reusable checks for age
    age_checks = [
        pa.Check.between(params["age_min"], params["age_max"]),
    ]

    # Reusable checks for sex
    sex_checks = [
        pa.Check(lambda x: len(x.unique()) == 2),
    ]

    # Reusable checks for year
    year_checks = [
        pa.Check(lambda x: params["year"] in x.unique()),
    ]
    # Append check for optional year2
    if params["year2"] is not None:
        year_checks.append(pa.Check(lambda x: params["year2"] in x.unique()))

    # Reusable checks for immigration or emigration estimates
    migration_estimate_checks = [
        pa.Check.between(0, 1 * 10**6),
    ]

    if df_key in ["final_immigration", "final_emigration"]:
        schema = pa.DataFrameSchema(
            {
                vars["la_code"]: pa.Column(str, checks=la_code_checks),
                vars["age"]: pa.Column(int, checks=age_checks),
                vars["sex"]: pa.Column(str, checks=sex_checks),
                vars["nationality"]: pa.Column(
                    str,
                    checks=[
                        pa.Check.isin(params["final_nationalities"]),
                    ],
                ),
                vars["year"]: pa.Column(int, checks=year_checks),
                vars["count"]: pa.Column(float, checks=migration_estimate_checks),
            },
            strict=True,
            coerce=True,
        )

    if df_key in ["provisional"]:
        schema = pa.DataFrameSchema(
            {
                vars["la_code"]: pa.Column(str, checks=la_code_checks),
                vars["age"]: pa.Column(int, checks=age_checks),
                vars["sex"]: pa.Column(str, checks=sex_checks),
                vars["immigration"]: pa.Column(float, checks=migration_estimate_checks),
                vars["emigration"]: pa.Column(float, checks=migration_estimate_checks),
                vars["net"]: pa.Column(
                    float,
                    checks=[
                        pa.Check(
                            lambda x: (
                                x == df[vars["immigration"]] - df[vars["emigration"]]
                            )
                        )
                    ],
                ),
            },
            strict=True,
            coerce=True,
        )

    if df_key in ["provisional_scot"]:
        schema = pa.DataFrameSchema(
            {
                vars["la_code"]: pa.Column(str, checks=la_code_checks),
                vars["age"]: pa.Column(int, checks=age_checks),
                vars["sex"]: pa.Column(str, checks=sex_checks),
                vars["direction"]: pa.Column(
                    str,
                    checks=[
                        pa.Check(lambda x: len(x.unique()) == 2),
                        pa.Check.isin(params["provisional_scot_direction"]),
                    ],
                ),
                vars["year"]: pa.Column(int, checks=year_checks),
                vars["count"]: pa.Column(float, checks=migration_estimate_checks),
            },
            strict=True,
            coerce=True,
        )

    schema.validate(df)
