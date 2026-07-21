import pytest


@pytest.fixture
def test_config():
    return {
        "parameters": {"age_min": 0, "age_max": 200, "year": 2024},
        "root": "tests/data/",
        "lookup_tables": {"ltim_lookup": "", "las_lookup": ""},
        "prov_fin_paths": {
            "spring_immigration": "final_immigration.csv",
            "spring_emigration": "final_emigration.csv",
            "provisional_mye": "provisional.csv",
            "provisional_scot": "provisional_added.csv",
        },
        "sex_ratio_paths": {
            "winter_immigration": "",
            "winter_emigration": "",
            "provisional_mye": "",
        },
        "yoy_paths": {"spring_immigration": "", "spring_emigration": ""},
        "scatter_paths": {"winter_immigration": ""},
    }
