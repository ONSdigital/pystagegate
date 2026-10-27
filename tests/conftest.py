import pytest
import pandas as pd
from pystagegate.prov_fin import merge_final_migration_data
from pystagegate.sex_ratio import (
    pivot_sex_ratio_frame,
    clean_and_mask,
    compute_sex_ratio,
)
from pystagegate.utils import load_config, load_summary_data


# Fixtures for all test modules
@pytest.fixture(scope="module")
def test_config():
    config = load_config("tests/data/testing_config.json")
    return config


@pytest.fixture(scope="module")
def test_config_path():
    config = "tests/data/testing_config.json"
    return config


@pytest.fixture(scope="module")
def test_config_no_output():
    config = load_config("tests/data/testing_config.json")
    config["output_path"] = None
    return config


@pytest.fixture(scope="module")
def immigration_df(test_config_no_output):
    return load_summary_data(test_config_no_output, "final_immigration")


@pytest.fixture(scope="module")
def emigration_df(test_config_no_output):
    return load_summary_data(test_config_no_output, "final_emigration")


@pytest.fixture(scope="module")
def provisional_df(test_config_no_output):
    return load_summary_data(test_config_no_output, "provisional")


@pytest.fixture(scope="module")
def provisional_scot_df(test_config_no_output):
    return load_summary_data(test_config_no_output, "provisional_scot")


# test_prov_fin fixtures
@pytest.fixture(scope="class")
def nation_breakdown_df():
    df = pd.read_csv("tests/data/provisional_final_merged.csv")

    return df


# test_sex_ratio fixtures
@pytest.fixture(scope="class")
def merged_df(test_config_no_output, immigration_df, emigration_df):
    return merge_final_migration_data(
        immigration_df, emigration_df, test_config_no_output
    )


@pytest.fixture(scope="class")
def merged_sr_df(test_config_no_output, immigration_df, emigration_df):
    return merge_final_migration_data(
        immigration_df, emigration_df, test_config_no_output, sex_ratio=True
    )


@pytest.fixture(scope="class")
def fake_merged_df():
    return pd.DataFrame(
        {
            "Year": [2024, 2024, 2024, 2025, 2025, 2025],
            "Local Authority Code": ["E1", "E1", "E1", "E1", "E1", "E1"],
            "Age": [30, 40, 50, 30, 40, 50],
            "Sex": ["M", "M", "M", "M", "M", "M"],
            "imm_fin": [0.3, 0.6, 1.1, 0, -100, 10],
            "em_fin": [-1, 5, 0.3, 1.1, 0.5, 0.2],
        }
    )


@pytest.fixture(scope="class")
def local_sr_df(merged_sr_df, test_config_no_output):
    pivot_df = pivot_sex_ratio_frame(merged_sr_df, test_config_no_output)
    mask_df = clean_and_mask(pivot_df, test_config_no_output)

    return compute_sex_ratio(mask_df, test_config_no_output)


@pytest.fixture(scope="class")
def national_sr_df(merged_sr_df, test_config_no_output):
    pivot_df = pivot_sex_ratio_frame(merged_sr_df, test_config_no_output)

    return compute_sex_ratio(
        pivot_df.groupby("Age").agg("sum")[["em_fin", "imm_fin"]],
        test_config_no_output,
        mask=False,
    )


@pytest.fixture
def valid_validation_dfs():
    return {
        "final_immigration": pd.DataFrame(
            {
                "Local Authority Code": ["E1", "W1", "S1", "E2"],
                "Age": [0, 30, 40, 200],
                "Sex": ["M", "F", "M", "F"],
                "Nationality Group": [
                    "British",
                    "Non-British",
                    "British",
                    "Non-British",
                ],
                "Year": [2024, 2025, 2024, 2025],
                "Count": [0.0, 1.0, 10.0, 1_000_000.0],
            }
        ),
        "final_emigration": pd.DataFrame(
            {
                "Local Authority Code": ["E1", "W1", "S1", "E2"],
                "Age": [0, 30, 40, 200],
                "Sex": ["M", "F", "M", "F"],
                "Nationality Group": [
                    "British",
                    "Non-British",
                    "British",
                    "Non-British",
                ],
                "Year": [2024, 2025, 2024, 2025],
                "Count": [0.0, 1.0, 10.0, 1_000_000.0],
            }
        ),
        "provisional": pd.DataFrame(
            {
                "code": ["E1", "W1", "S1", "E2"],
                "Age": [0, 30, 40, 200],
                "sex": ["M", "F", "M", "F"],
                "international_in_2024": [10.0, 20.0, 30.0, 40.0],
                "international_out_2024": [1.0, 2.0, 3.0, 4.0],
                "international_net_2024": [9.0, 18.0, 27.0, 36.0],
            }
        ),
        "provisional_scot": pd.DataFrame(
            {
                "ca_code": ["E1", "W1", "S1", "E2"],
                "Age": [0, 30, 40, 200],
                "sex": ["M", "F", "M", "F"],
                "dir": ["in", "out", "in", "out"],
                "year": [2024, 2025, 2024, 2025],
                "count": [0.0, 1.0, 10.0, 1_000_000.0],
            }
        ),
    }
