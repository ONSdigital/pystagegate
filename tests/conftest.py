import pytest
import pandas as pd
from pystagegate.prov_fin import merge_final_migration_data
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
def test_config_with_no_output():
    config = load_config("tests/data/testing_config.json")
    config["prov_fin"]["output_path"] = None
    config["sex_ratio"]["output_path"] = None
    return config


@pytest.fixture(scope="module")
def prov_fin_config():
    config = load_config("tests/data/testing_config.json")
    config["prov_fin"]["output_path"] = None
    return config["prov_fin"]


@pytest.fixture(scope="module")
def sex_ratio_config():
    config = load_config("tests/data/testing_config.json")
    config["sex_ratio"]["output_path"] = None
    return config["sex_ratio"]


@pytest.fixture(scope="module")
def immigration_df(prov_fin_config):
    return load_summary_data(prov_fin_config, "final_immigration")


@pytest.fixture(scope="module")
def emigration_df(prov_fin_config):
    return load_summary_data(prov_fin_config, "final_emigration")


@pytest.fixture(scope="module")
def provisional_df(prov_fin_config):
    return load_summary_data(prov_fin_config, "provisional")


@pytest.fixture(scope="module")
def provisional_scot_df(prov_fin_config):
    return load_summary_data(prov_fin_config, "provisional_scot")


# test_prov_fin fixtures
@pytest.fixture(scope="class")
def nation_breakdown_df():
    df = pd.read_csv("tests/data/provisional_final_merged.csv")

    return df


# test_sex_ratio fixtures
@pytest.fixture(scope="class")
def merged_df(sex_ratio_config, immigration_df, emigration_df):
    return merge_final_migration_data(immigration_df, emigration_df, sex_ratio_config)


@pytest.fixture(scope="class")
def merged_sr_df(sex_ratio_config, immigration_df, emigration_df):
    return merge_final_migration_data(
        immigration_df, emigration_df, sex_ratio_config, sex_ratio=True
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
