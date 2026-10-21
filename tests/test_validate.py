import pandera.errors as pa_errors
import pytest

from pystagegate.validate import validate


@pytest.mark.parametrize(
    "df_key",
    [
        "final_immigration",
        "final_emigration",
        "provisional",
        "provisional_scot",
    ],
)
def test_validate_accepts_valid_dataset(df_key, valid_validation_dfs, test_config):
    validate(valid_validation_dfs[df_key], df_key, test_config)


@pytest.mark.parametrize(
    ("df_key", "column", "values"),
    [
        ("final_immigration", "Local Authority Code", ["X1", "W1", "S1", "E2"]),
        ("final_immigration", "Age", [0, 30, 201, 200]),
        ("final_immigration", "Sex", ["M", "M", "M", "M"]),
        (
            "final_emigration",
            "Nationality Group",
            ["British", "Unknown", "British", "Non-British"],
        ),
        ("final_emigration", "Year", [2025, 2025, 2025, 2025]),
        ("final_emigration", "Count", [0.0, 1.0, -1.0, 10.0]),
        ("provisional", "international_in_2024", [10.0, 20.0, 30.0, 1_000_001.0]),
        ("provisional", "international_net_2024", [8.0, 18.0, 27.0, 36.0]),
        ("provisional_scot", "dir", ["bad", "out", "in", "out"]),
        ("provisional_scot", "year", [2024, 2024, 2024, 2024]),
        ("provisional_scot", "count", [0.0, 1.0, 10.0, -1.0]),
    ],
)
def test_validate_rejects_invalid_values(
    df_key, column, values, valid_validation_dfs, test_config
):
    df = valid_validation_dfs[df_key].copy()
    df[column] = values

    with pytest.raises(pa_errors.SchemaError):
        validate(df, df_key, test_config)


@pytest.mark.parametrize("df_key", ["final_immigration", "provisional_scot"])
def test_validate_requires_configured_year2(df_key, valid_validation_dfs, test_config):
    df = valid_validation_dfs[df_key].copy()
    variables = test_config["datasets"][df_key]["variables"]
    df[variables["year"]] = [2024, 2024, 2024, 2024]

    with pytest.raises(pa_errors.SchemaError):
        validate(df, df_key, test_config)


def test_validate_rejects_unexpected_columns(valid_validation_dfs, test_config):
    df = valid_validation_dfs["final_immigration"].copy()
    df["unexpected"] = 1

    with pytest.raises(pa_errors.SchemaErrors):
        validate(df, "final_immigration", test_config)


def test_validate_rejects_missing_columns(valid_validation_dfs, test_config):
    df = valid_validation_dfs["final_immigration"].drop(columns="Count")

    with pytest.raises(pa_errors.SchemaError):
        validate(df, "final_immigration", test_config)


def test_validate_coerces_column_types(valid_validation_dfs, test_config):
    df = valid_validation_dfs["final_immigration"].copy()
    df["Age"] = df["Age"].astype(str)
    df["Year"] = df["Year"].astype(str)
    df["Count"] = df["Count"].astype(str)

    validate(df, "final_immigration", test_config)


def test_validate_rejects_unknown_dataset_key(test_config):
    with pytest.raises(
        ValueError,
        match="Dataset key 'unknown' not found in configuration\\.",
    ):
        validate(None, "unknown", test_config)
