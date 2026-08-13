import pytest
import pandas as pd
from pystagegate.utils import load_config


@pytest.fixture
def test_config():
    config = load_config("tests/data/testing_config.json")
    return config


@pytest.fixture
def prov_fin_config_no_output():
    config = load_config("tests/data/testing_config.json")
    config["prov_fin"]["output_path"] = None
    return config["prov_fin"]


@pytest.fixture
def mock_immigration_df():
    return pd.DataFrame(
        {
            "Local Authority Code": ["E001", "E001", "E002", "E002", "E001"],
            "Age": [25, 30, 25, 30, 25],
            "Sex": ["Male", "Female", "Male", "Female", "Male"],
            "Nationality Group": [
                "All Nationalities",
                "All Nationalities",
                "All Nationalities",
                "All Nationalities",
                "British",
            ],
            "Year": [2024, 2024, 2024, 2024, 2024],
            "Count": [100, 200, 150, 250, 50],
        }
    )


@pytest.fixture
def mock_emigration_df():
    return pd.DataFrame(
        {
            "Local Authority Code": ["E001", "E001", "E002", "E002", "E001"],
            "Age": [25, 30, 25, 30, 25],
            "Sex": ["Male", "Female", "Male", "Female", "Male"],
            "Nationality Group": [
                "All Nationalities",
                "All Nationalities",
                "All Nationalities",
                "All Nationalities",
                "British",
            ],
            "Year": [2024, 2024, 2024, 2024, 2024],
            "Count": [50, 100, 75, 125, 25],
        }
    )


@pytest.fixture
def mock_provisional_df():
    return pd.DataFrame(
        {
            "code": ["E001", "E001", "E002", "E002"],
            "Age": [25, 30, 25, 30],
            "sex": ["Male", "Female", "Male", "Female"],
            "international_in_2024": [120, 220, 160, 260],
            "international_out_2024": [60, 110, 80, 130],
            "international_net_2024": [60, 110, 80, 130],
        }
    )


@pytest.fixture
def mock_provisional_scot_df():
    return pd.DataFrame(
        {
            "ca_code": ["S001", "S001", "S001", "S001", "S002", "S002"],
            "Age": [25, 25, 30, 30, 25, 25],
            "sex": ["Male", "Male", "Female", "Female", "Male", "Male"],
            "dir": ["in", "out", "in", "out", "in", "out"],
            "year": [2024, 2024, 2024, 2024, 2024, 2024],
            "count": [100, 50, 80, 40, 120, 60],
        }
    )


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
