import great_expectations as gx
import pandas as pd


def create_gx_context(df: pd.DataFrame, df_key: str):
    context = gx.get_context()

    data_source = context.data_sources.add_pandas("pandas")
    data_asset = data_source.add_dataframe_asset(name=f"{df_key} pd dataframe asset")

    batch_definition = data_asset.add_batch_definition_whole_dataframe(
        "batch definition"
    )
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})

    suite = context.suites.add(
        gx.core.expectation_suite.ExpectationSuite(name=f"{df_key}_expectations")
    )

    return context, suite, batch_definition, batch


def generic_validate(df: pd.DataFrame, df_key: str, config: dict):
    variables = config["datasets"][df_key]["variables"]


    context, suite, batch_definition, batch = create_gx_context(df, df_key)

    for v in variables.values():
        suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column=v))

    validation_definition = context.validation_definitions.add(
        gx.core.validation_definition.ValidationDefinition(
            name=f"{df_key} validation definition",
            data=batch_definition,
            suite=suite,
        )
    )

    validation_results = validation_definition.run(
        batch_parameters={"dataframe": df}
    )

    return validation_results
