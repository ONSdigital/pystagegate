import great_expectations as gx
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


def validate(df: pd.DataFrame, df_key: str, config: dict):
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

    if df_key in ["final_immigration", "final_emigration"]:
        suite.add_expectation(
            gx.expectations.ExpectColumnDistinctValuesToBeInSet(
                column=variables["nationality"],
                value_set=config["global_parameters"]["final_nationalities"],
            )
        )
        suite.add_expectation(
            gx.expectations.ExpectColumnDistinctValuesToBeInSet(
                column=variables["sex"], value_set=["Male", "Female"]
            )
        )
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToBeInTypeList(
                column=variables["count"], type_list=["int64", "float64"]
            )
        )

    if df_key == "provisional_scot":
        suite.add_expectation(
            gx.expectations.ExpectColumnDistinctValuesToBeInSet(
                column=variables["direction"],
                value_set=config["global_parameters"]["provisional_scot_direction"],
            )
        )
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToBeInTypeList(
                column=variables["count"], type_list=["int64", "float64"]
            )
        )

    if df_key == "provisional":
        for v in [variables["immigration"], variables["emigration"], variables["net"]]:
            gx.expectations.ExpectColumnValuesToBeInTypeList(
                column=v, type_list=["int64", "float64"]
            )

        suite.add_expectation(
            gx.expectations.ExpectColumnDistinctValuesToBeInSet(
                column=variables["sex"], value_set=[1, 2]
            )
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

    return validation_results
