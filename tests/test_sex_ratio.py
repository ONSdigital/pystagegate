import pytest
import pandas as pd
from itertools import product
from pystagegate import sex_ratio


class TestYearAggMerge:
    def test_merge_preserves_net_migration(self, merged_df, sex_ratio_config):
        result = sex_ratio.year_agg_merge(merged_df, sex_ratio_config)
        for year in [
            sex_ratio_config["global_parameters"]["year"],
            sex_ratio_config["global_parameters"]["year2"],
        ]:
            assert (
                result[f"count_imm_{year}"] - result[f"count_em_{year}"]
                == result[f"count_net_{year}"]
            ).all()
            assert (
                result[f"total_count_imm_{year}"] - result[f"total_count_em_{year}"]
                == result[f"total_count_net_{year}"]
            ).all()

    def test_error_for_years(self, sex_ratio_config):
        merged_df = pd.DataFrame(
            {
                "Year": [2023, 2023, 2023, 2024, 2024, 2024, 2026],
            }
        )
        with pytest.raises(ValueError):
            sex_ratio.year_agg_merge(merged_df, sex_ratio_config)


class TestYearAggSqDiff:
    def test_non_zero_sqdiff(self, merged_df, sex_ratio_config):
        agg_df = sex_ratio.year_agg_merge(merged_df, sex_ratio_config)

        result, result_adjusted = sex_ratio.year_agg_sqdiff(agg_df, sex_ratio_config)

        for out_name in ["imm", "em", "net"]:
            assert (result[f"sqdiff_{out_name}"] >= 0).all()

        for out_name in ["imm", "em"]:
            assert (result_adjusted[f"{out_name}_adjusted_size_ssq"] >= 0).all()


class TestPivotSexRatioFrame:
    def test_return_is_multiindex(self, merged_sr_df, sex_ratio_config):
        result = sex_ratio.pivot_sex_ratio_frame(merged_sr_df, sex_ratio_config)
        assert type(result.index) is pd.core.indexes.multi.MultiIndex

    def test_multiindex_contains_all_columns(self, merged_sr_df, sex_ratio_config):
        result = sex_ratio.pivot_sex_ratio_frame(merged_sr_df, sex_ratio_config)

        for element in result.columns.to_flat_index():
            assert element[2] in [
                sex_ratio_config["global_parameters"]["year"],
                sex_ratio_config["global_parameters"]["year2"],
            ]
            assert element[1] in ["Male", "Female"]
            assert element[0] in ["imm_fin", "em_fin"]

    def test_multiindex_contains_all_index(self, merged_sr_df, sex_ratio_config):
        unique_values = [
            merged_sr_df[col].unique()
            for col in merged_sr_df[["Local Authority Code", "Age"]].columns
        ]

        result = sex_ratio.pivot_sex_ratio_frame(merged_sr_df, sex_ratio_config)

        assert set(product(*unique_values)) == set(result.index)


class TestCleanAndMask:
    pass


class TestComputeSexRatio:
    pass


class TestSexRatioHelper:
    pass


class TestSexRatioSsq:
    pass
