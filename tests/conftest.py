import pytest


@pytest.fixture
def test_pipeline_config():
    return {
        "prov_fin": {
            "root_path": "tests/data/",
            "global_parameters": {
                "age_min": 0,
                "age_max": 200,
                "year": 2024,
                "all_nationalities": "All Nationalities",
            },
            "datasets": {
                "final_immigration": {
                    "path": "final_immigration.csv",
                    "variables": {
                        "la_code": "Local Authority Code",
                        "age": "Age",
                        "sex": "Sex",
                        "nationality": "Nationality Group",
                        "year": "Year",
                        "count": "Count",
                    },
                },
                "final_emigration": {
                    "path": "final_emigration.csv",
                    "variables": {
                        "la_code": "Local Authority Code",
                        "age": "Age",
                        "sex": "Sex",
                        "nationality": "Nationality Group",
                        "year": "Year",
                        "count": "Count",
                    },
                },
                "provisional": {
                    "path": "provisional.csv",
                    "variables": {
                        "la_code": "code",
                        "age": "Age",
                        "sex": "sex",
                        "immigration_prefix": "international_in_",
                        "emigration_prefix": "international_out_",
                        "net_prefix": "international_net_",
                    },
                },
                "provisional_scot": {
                    "path": "provisional_added.csv",
                    "variables": {
                        "la_code": "ca_code",
                        "age": "Age",
                        "sex": "sex",
                        "direction": "dir",
                        "year": "year",
                        "count": "count",
                    },
                },
            },
        }
    }
