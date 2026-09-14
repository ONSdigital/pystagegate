import pandas as pd
import pytest
from pystagegate.pipelines import (
    prov_fin_main,
    sex_ratio_national_profile,
    sex_ratio_main,
)


@pytest.mark.parametrize("config", ["test_config", "test_config_path"])
class TestPipelines:
    def test_prov_fin_dict(self, request, config):
        output = prov_fin_main(request.getfixturevalue(config))

        pd.testing.assert_frame_equal(
            output, pd.read_pickle("tests/data/prov_fin/prov_fin_sqdiff.pkl")
        )

    def test_sex_ratio_national_profile_dict(self, request, config):
        year_agg, year_agg_adjusted = sex_ratio_national_profile(
            request.getfixturevalue(config)
        )

        pd.testing.assert_frame_equal(
            year_agg, pd.read_pickle("tests/data/sex_ratio/year_on_year_sqdiff.pkl")
        )
        pd.testing.assert_frame_equal(
            year_agg_adjusted,
            pd.read_pickle("tests/data/sex_ratio/year_on_year_adjusted_sqdiff.pkl"),
        )

    def test_sex_ratio_main(self, request, config):
        sr, sr_national, sr_merged_ssq = sex_ratio_main(request.getfixturevalue(config))

        pd.testing.assert_frame_equal(
            sr, pd.read_pickle("tests/data/sex_ratio/sex_ratios.pkl")
        )
        pd.testing.assert_frame_equal(
            sr_national, pd.read_pickle("tests/data/sex_ratio/national_sex_ratios.pkl")
        )
        pd.testing.assert_frame_equal(
            sr_merged_ssq,
            pd.read_pickle("tests/data/sex_ratio/sex_ratios_ssq_comparison.pkl"),
        )
