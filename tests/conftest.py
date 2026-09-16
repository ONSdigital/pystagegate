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


@pytest.fixture
def mock_year_agg_final_df():
    return pd.DataFrame(
        {
            "Local Authority Code": ["E001", "E002", "E001", "E002"],
            "Year": [2024, 2024, 2025, 2025],
            "Age": [25, 25, 25, 25],
            "imm_fin": [100.0, 300.0, 150.0, 250.0],
            "em_fin": [50.0, 150.0, 40.0, 160.0],
            "net_fin": [50.0, 150.0, 110.0, 90.0],
        }
    )


@pytest.fixture
def mock_sex_ratio_source_df():
    return pd.DataFrame(
        {
            "Local Authority Code": [
                "E001",
                "E001",
                "E001",
                "E001",
                "E001",
            ],
            "Age": [25, 25, 25, 25, 25],
            "Sex": ["Male", "Female", "Male", "Female", "Male"],
            "Year": [2024, 2024, 2025, 2025, 2023],
            "imm_fin": [10.0, 5.0, 12.0, 6.0, 99.0],
            "em_fin": [4.0, 2.0, 9.0, 3.0, 99.0],
        }
    )


@pytest.fixture
def mock_sex_ratio_pivot_with_quality():
    index = pd.MultiIndex.from_tuples(
        [("E001", 25), ("E002", 25), ("E003", 25), ("E004", 25)],
        names=["Local Authority Code", "Age"],
    )
    columns = pd.MultiIndex.from_tuples(
        [
            ("imm_fin", "Male", 2024),
            ("imm_fin", "Female", 2024),
            ("imm_fin", "Male", 2025),
            ("imm_fin", "Female", 2025),
            ("em_fin", "Male", 2024),
            ("em_fin", "Female", 2024),
            ("em_fin", "Male", 2025),
            ("em_fin", "Female", 2025),
            ("imm_fin_quality", "Male", 2024),
            ("imm_fin_quality", "Female", 2024),
            ("imm_fin_quality", "Male", 2025),
            ("imm_fin_quality", "Female", 2025),
            ("em_fin_quality", "Male", 2024),
            ("em_fin_quality", "Female", 2024),
            ("em_fin_quality", "Male", 2025),
            ("em_fin_quality", "Female", 2025),
        ]
    )
    return pd.DataFrame(
        [
            [
                10.0,
                5.0,
                12.0,
                6.0,
                4.0,
                2.0,
                90.0,
                3.0,
                "OK",
                "OK",
                "OK",
                "OK",
                "OK",
                "OK",
                "OK",
                "OK",
            ],
            [
                2.0,
                4.0,
                8.0,
                4.0,
                6.0,
                3.0,
                6.0,
                3.0,
                "Zero",
                "Low",
                "OK",
                "OK",
                "OK",
                "OK",
                "OK",
                "OK",
            ],
            [
                0.0,
                8.0,
                8.0,
                4.0,
                6.0,
                3.0,
                6.0,
                3.0,
                "Zero",
                "OK",
                "OK",
                "OK",
                "OK",
                "OK",
                "OK",
                "OK",
            ],
            [
                7.0,
                0.0,
                8.0,
                4.0,
                6.0,
                3.0,
                6.0,
                3.0,
                "OK",
                "Zero",
                "OK",
                "OK",
                "OK",
                "OK",
                "OK",
                "OK",
            ],
        ],
        index=index,
        columns=columns,
    )


@pytest.fixture
def mock_local_sex_ratio_df():
    return pd.DataFrame(
        {
            "Local Authority Code": ["E001", "E002"],
            "Age": [25, 25],
            "sex_ratio_imm_2024": [2.0, 1.0],
            "sex_ratio_imm_2025": [3.0, 1.5],
            "sex_ratio_em_2024": [1.0, 2.0],
            "sex_ratio_em_2025": [1.5, 4.0],
            "imm_weight": [100.0, 50.0],
            "em_weight": [80.0, 60.0],
        }
    ).set_index("Local Authority Code")


@pytest.fixture
def mock_national_sex_ratio_df():
    return pd.DataFrame(
        {
            "Age": [25],
            "sex_ratio_imm_2024": [1.5],
            "sex_ratio_imm_2025": [2.0],
            "sex_ratio_em_2024": [0.5],
            "sex_ratio_em_2025": [1.0],
            "imm_weight": [999.0],
            "em_weight": [999.0],
        }
    )
