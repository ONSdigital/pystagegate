import great_expectations as gx
import os
import pandas as pd


def create_gx_context(df: pd.DataFrame, df_key: str):
    """
    Create a Great Expectations context for the given DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to validate.
        df_key (str): The key for the DataFrame in the configuration.

    Returns:
        tuple: A tuple containing the Great Expectations context, expectation suite, and batch definition.
    """
    context = gx.get_context()

    # Disable progress bars for metric calculations
    context.variables.progress_bars = {
        "globally": False,
        "metric_calculations": False,
    }

    data_source = context.data_sources.add_pandas("pandas")
    data_asset = data_source.add_dataframe_asset(name=f"{df_key} pd dataframe asset")

    batch_definition = data_asset.add_batch_definition_whole_dataframe(
        "batch definition"
    )

    suite = context.suites.add(
        gx.core.expectation_suite.ExpectationSuite(name=f"{df_key}_expectations")
    )

    return context, suite, batch_definition


def _load_validation_dataset(config: dict, df_key: str) -> pd.DataFrame:
    """
    Load a configured validation dataset from disk.

    This is used by cross-dataset checks where one dataset must be compared
    against another after the current DataFrame has passed its own GX suite.

    Args:
        config (dict): The prov_fin configuration dictionary.
        df_key (str): The dataset key to load from the configuration.

    Returns:
        pd.DataFrame: The configured dataset limited to its validation columns.
    """
    path = os.path.join(config["root_path"], config["datasets"][df_key]["path"])
    variables = config["datasets"][df_key]["variables"]
    return pd.read_csv(path)[variables.values()]


def _validate_final_dataset_consistency(df: pd.DataFrame, df_key: str, config: dict):
    """
    Validate that the two final migration datasets cover the same domains.

    The final immigration and final emigration inputs are validated separately
    by Great Expectations, but some rules only make sense when comparing one
    dataset against the other. This helper checks that both datasets share the
    same unique local authority code set and the same unique age set.

    Args:
        df (pd.DataFrame): The current final migration DataFrame under validation.
        df_key (str): The dataset key for the current DataFrame.
        config (dict): The prov_fin configuration dictionary.

    Raises:
        ValueError: If the counterpart dataset does not match on LA codes or ages.
    """
    counterpart_key = (
        "final_emigration" if df_key == "final_immigration" else "final_immigration"
    )
    variables = config["datasets"][df_key]["variables"]
    counterpart_variables = config["datasets"][counterpart_key]["variables"]
    counterpart_df = _load_validation_dataset(config, counterpart_key)

    current_la_codes = set(df[variables["la_code"]].dropna().unique())
    counterpart_la_codes = set(
        counterpart_df[counterpart_variables["la_code"]].dropna().unique()
    )

    if current_la_codes != counterpart_la_codes:
        raise ValueError(
            f"{df_key} local authority codes do not match {counterpart_key}"
        )

    current_ages = set(df[variables["age"]].dropna().unique())
    counterpart_ages = set(
        counterpart_df[counterpart_variables["age"]].dropna().unique()
    )

    if current_ages != counterpart_ages:
        raise ValueError(f"{df_key} ages do not match {counterpart_key}")


def _validate_provisional_scot_directions(
    df: pd.DataFrame, variables: dict, config: dict
):
    """
    Validate Scotland provisional direction coverage for the configured year.

    Great Expectations already restricts direction values to the configured set.
    This helper adds the stronger pipeline rule that, for the configured year,
    every configured direction must actually be present in the data.

    Args:
        df (pd.DataFrame): The provisional Scotland dataset under validation.
        variables (dict): Column mapping for the provisional Scotland dataset.
        config (dict): The prov_fin configuration dictionary.

    Raises:
        ValueError: If the configured year does not contain the full configured
            set of direction values.
    """
    target_year = config["global_parameters"]["year"]
    expected_directions = set(config["global_parameters"]["provisional_scot_direction"])
    year_mask = df[variables["year"]] == target_year
    direction_values = df.loc[year_mask, [variables["direction"]]][
        variables["direction"]
    ]
    actual_directions = set(direction_values.dropna().unique())

    if actual_directions != expected_directions:
        raise ValueError(
            "provisional_scot must contain both configured directions for the configured year"
        )


def prov_fin_validate(df: pd.DataFrame, df_key: str, config: dict):
    """
    Validate the given DataFrame against the configuration.

    Args:
        df (pd.DataFrame): The DataFrame to validate.
        df_key (str): The key for the DataFrame in the configuration.
        config (dict): The configuration dictionary containing validation rules.

    Returns:
        validation_results: Validation result object.

    """
    variables = config["datasets"][df_key]["variables"]

    context, suite, batch_definition = create_gx_context(df, df_key)

    suite.add_expectation(gx.expectations.ExpectTableRowCountToBeBetween(min_value=0))

    for v in variables.values():
        suite.add_expectation(gx.expectations.ExpectColumnToExist(column=v))
        suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column=v))

    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeOfType(
            column=variables["la_code"], type_="str"
        )
    )
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeOfType(
            column=variables["age"], type_="int64"
        )
    )
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column=variables["age"],
            min_value=config["global_parameters"]["age_min"],
            max_value=config["global_parameters"]["age_max"],
        )
    )

    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToMatchRegex(
            column=variables["la_code"], regex=r".*\S.*"
        )
    )

    if df_key in ["final_immigration", "final_emigration"]:
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToBeOfType(
                column=variables["year"], type_="int64"
            )
        )
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToBeBetween(
                column=variables["year"], min_value=1900, max_value=2100
            )
        )
        suite.add_expectation(
            gx.expectations.ExpectColumnDistinctValuesToBeInSet(
                column=variables["nationality"],
                value_set=config["global_parameters"]["final_nationalities"],
            )
        )
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToMatchRegex(
                column=variables["nationality"], regex=r".*\S.*"
            )
        )
        suite.add_expectation(
            gx.expectations.ExpectColumnDistinctValuesToBeInSet(
                column=variables["sex"], value_set=["Male", "Female"]
            )
        )
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToMatchRegex(
                column=variables["sex"], regex=r".*\S.*"
            )
        )
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToBeInTypeList(
                column=variables["count"], type_list=["int64", "float64"]
            )
        )
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToBeBetween(
                column=variables["count"], min_value=0
            )
        )

    if df_key == "provisional_scot":
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToBeOfType(
                column=variables["year"], type_="int64"
            )
        )
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToBeBetween(
                column=variables["year"], min_value=1900, max_value=2100
            )
        )
        suite.add_expectation(
            gx.expectations.ExpectColumnDistinctValuesToBeInSet(
                column=variables["sex"], value_set=["F", "M"]
            )
        )
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToMatchRegex(
                column=variables["sex"], regex=r".*\S.*"
            )
        )
        suite.add_expectation(
            gx.expectations.ExpectColumnDistinctValuesToBeInSet(
                column=variables["direction"],
                value_set=config["global_parameters"]["provisional_scot_direction"],
            )
        )
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToMatchRegex(
                column=variables["direction"], regex=r".*\S.*"
            )
        )
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToBeInTypeList(
                column=variables["count"], type_list=["int64", "float64"]
            )
        )
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToBeBetween(
                column=variables["count"], min_value=0
            )
        )

    if df_key == "provisional":
        suite.add_expectation(
            gx.expectations.ExpectColumnDistinctValuesToBeInSet(
                column=variables["sex"], value_set=[1, 2]
            )
        )
        for v in [variables["immigration"], variables["emigration"], variables["net"]]:
            suite.add_expectation(
                gx.expectations.ExpectColumnValuesToBeInTypeList(
                    column=v, type_list=["int64", "float64"]
                )
            )

        for v in [variables["immigration"], variables["emigration"]]:
            suite.add_expectation(
                gx.expectations.ExpectColumnValuesToBeBetween(column=v, min_value=0)
            )

    validation_definition = context.validation_definitions.add(
        gx.core.validation_definition.ValidationDefinition(
            name=f"{df_key} validation definition",
            data=batch_definition,
            suite=suite,
        )
    )

    validation_results = validation_definition.run(batch_parameters={"dataframe": df})

    if validation_results.statistics["success_percent"] < 100:
        raise ValueError(validation_results.get_failed_validation_results())

    if df_key in ["final_immigration", "final_emigration"]:
        _validate_final_dataset_consistency(df, df_key, config)

    if df_key == "provisional_scot":
        _validate_provisional_scot_directions(df, variables, config)

    return validation_results
