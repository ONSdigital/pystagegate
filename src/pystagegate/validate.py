import pandas as pd
import pandera.pandas as pa


def validate(df: pd.DataFrame, df_key: str, config: dict) -> None:
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
