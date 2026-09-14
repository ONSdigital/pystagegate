import pytest
import pandas as pd
from pystagegate.utils import load_config, load_summary_data


@pytest.fixture
def test_config():
    config = load_config("tests/data/testing_config.json")
    return config


@pytest.fixture
def test_config_path():
    config = "tests/data/testing_config.json"
    return config


@pytest.fixture
def prov_fin_config_no_output():
    config = load_config("tests/data/testing_config.json")
    config["prov_fin"]["output_path"] = None
    return config["prov_fin"]


@pytest.fixture
def sex_ratio_config_no_output():
    config = load_config("tests/data/testing_config.json")
    config["sex_ratio"]["output_path"] = None
    return config["sex_ratio"]


@pytest.fixture
def prov_fin_immigration_df(prov_fin_config_no_output):
    return load_summary_data(prov_fin_config_no_output, "final_immigration")


@pytest.fixture
def prov_fin_emigration_df(prov_fin_config_no_output):
    return load_summary_data(prov_fin_config_no_output, "final_emigration")


@pytest.fixture
def prov_fin_prov_df(prov_fin_config_no_output):
    return load_summary_data(prov_fin_config_no_output, "provisional")


@pytest.fixture
def prov_fin_scot_df(prov_fin_config_no_output):
    return load_summary_data(prov_fin_config_no_output, "provisional_scot")


@pytest.fixture
def mock_merged_df():
    return pd.DataFrame(
        {
            "Local Authority Code": ["E001", "E001", "E002"],
            "Age": [25, 30, 25],
            "imm_prov": [120.0, 220.0, 160.0],
            "imm_fin": [100.0, 200.0, 150.0],
            "imm_prov_T": [500.0, 500.0, 500.0],
            "imm_fin_T": [450.0, 450.0, 450.0],
        }
    )


@pytest.fixture
def mock_final_merged_df():
    return pd.DataFrame(
        {
            "Local Authority Code": ["E001", "E001", "E002", "W001", "S001"],
            "Age": [25, 30, 25, 25, 25],
            "imm_prov": [120.0, 220.0, 160.0, 90.0, 110.0],
            "em_prov": [60.0, 110.0, 80.0, 45.0, 55.0],
            "net_prov": [60.0, 110.0, 80.0, 45.0, 55.0],
            "imm_fin": [100.0, 200.0, 150.0, 80.0, 100.0],
            "em_fin": [50.0, 100.0, 75.0, 40.0, 50.0],
            "net_fin": [50.0, 100.0, 75.0, 40.0, 50.0],
            "nation": ["E", "E", "E", "W", "S"],
        }
    )
