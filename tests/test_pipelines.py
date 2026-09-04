import pandas as pd
import pytest
import os
from pystagegate.pipelines import (
    prov_fin_main,
    sex_ratio_national_profile,
    sex_ratio_main,
)


@pytest.mark.parametrize("config", ["test_config", "test_config_path"])
def test_prov_fin_dict(request, config, test_config):
    output = prov_fin_main(request.getfixturevalue(config))

    expected_output = pd.read_csv(
        os.path.join("tests/data/prov_fin/prov_fin_output.csv")
    )

    pd.testing.assert_frame_equal(output, expected_output)


@pytest.mark.parametrize("config", ["test_config", "test_config_path"])
def test_sex_ratio_national_profile_dict(request, config):
    sq_diff, year_agg, year_agg_adjusted = sex_ratio_national_profile(
        request.getfixturevalue(config)
    )

    expected_sq_diff = pd.read_csv("tests/data/sex_ratio/provisional_final_ssq.csv")
    expected_year_agg = pd.read_csv("tests/data/sex_ratio/year_agg_ssq.csv")
    expected_year_agg_adjusted = pd.read_csv(
        "tests/data/sex_ratio/year_agg_adjusted_ssq.csv"
    )

    pd.testing.assert_frame_equal(sq_diff, expected_sq_diff)
    pd.testing.assert_frame_equal(year_agg, expected_year_agg)
    pd.testing.assert_frame_equal(year_agg_adjusted, expected_year_agg_adjusted)


@pytest.mark.parametrize("config", ["test_config", "test_config_path"])
def test_sex_ratio_main(request, config):
    sr, sr_national, sr_merged_ssq = sex_ratio_main(request.getfixturevalue(config))

    expected_sr = pd.read_csv("tests/data/sex_ratio/sex_ratio_recoded.csv")
    expected_sr_national = pd.read_csv("tests/data/sex_ratio/sex_ratio_national.csv")
    expected_sr_merged_ssq = pd.read_csv("tests/data/sex_ratio/sex_ratio_ssq.csv")

    print("\n\n", sr, expected_sr, "\n\n")

    pd.testing.assert_frame_equal(sr, expected_sr)
    pd.testing.assert_frame_equal(sr_national, expected_sr_national)
    pd.testing.assert_frame_equal(sr_merged_ssq, expected_sr_merged_ssq)
