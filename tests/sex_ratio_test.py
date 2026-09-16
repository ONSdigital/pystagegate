import pytest
import pandas as pd
from pystagegate import sex_ratio


def _series(frame: pd.DataFrame, column: str) -> pd.Series:
    selected = frame[column]
    if isinstance(selected, pd.DataFrame):
        return selected.iloc[:, 0]
    return selected


class TestYearAggSqDiff:
    def test_returns_year_level_and_adjusted_summaries(
        self, mock_year_agg_final_df, sex_ratio_config_no_output
    ):
        year_agg, adjusted = sex_ratio.year_agg_sqdiff(
            mock_year_agg_final_df, sex_ratio_config_no_output
        )

        e001 = year_agg[year_agg["Local Authority Code"] == "E001"].iloc[0]
        assert e001["diff_imm"] == 50.0
        assert e001["sqdiff_imm"] == 2500.0
        assert e001["diff_em"] == -10.0
        assert e001["sqdiff_em"] == 100.0
        assert e001["diff_net"] == 60.0
        assert e001["sqdiff_net"] == 3600.0

        e001_adjusted = adjusted[adjusted["Local Authority Code"] == "E001"].iloc[0]
        assert e001_adjusted["imm_adjusted_size_ssq"] == 25.0
        assert e001_adjusted["em_adjusted_size_ssq"] == 2.0
        assert e001_adjusted["net_adjusted_size_ssq"] == 72.0

    def test_year_squared_difference_rejects_invalid_output_name(self):
        with pytest.raises(ValueError, match="output_name must be one of"):
            sex_ratio.year_squared_difference(pd.DataFrame(), "invalid", 2024, 2025)


class TestPivotSexRatioFrame:
    def test_pivots_over_sex_and_year(
        self, mock_sex_ratio_source_df, sex_ratio_config_no_output
    ):
        result = sex_ratio.pivot_sex_ratio_frame(
            mock_sex_ratio_source_df, sex_ratio_config_no_output
        )

        assert isinstance(result.columns, pd.MultiIndex)
        assert result.loc[("E001", 25), ("imm_fin", "Male", 2024)] == 10.0
        assert result.loc[("E001", 25), ("imm_fin", "Female", 2025)] == 6.0
        assert result.loc[("E001", 25), ("em_fin", "Male", 2025)] == 9.0
        assert 2023 not in result.columns.get_level_values(2)


class TestComputeSexRatio:
    def test_computes_masked_ratios_caps_and_weights(
        self, mock_sex_ratio_pivot_with_quality, sex_ratio_config_no_output
    ):
        result = sex_ratio.compute_sex_ratio(
            mock_sex_ratio_pivot_with_quality.copy(),
            sex_ratio_config_no_output,
            caps=(0.1, 10.0),
        )

        imm_2024 = _series(result, "sex_ratio_imm_2024")
        em_2025 = _series(result, "sex_ratio_em_2025")
        imm_weight = _series(result, "imm_weight")
        em_weight = _series(result, "em_weight")

        assert imm_2024.loc[("E001", 25)] == 2.0
        assert pd.isna(imm_2024.loc[("E002", 25)])
        assert imm_2024.loc[("E003", 25)] == 8.0
        assert imm_2024.loc[("E004", 25)] == 7.0
        assert em_2025.loc[("E001", 25)] == 10.0
        assert imm_weight.loc[("E001", 25)] == 33.0
        assert em_weight.loc[("E001", 25)] == 99.0

    def test_can_compute_ratios_without_quality_masking(
        self, mock_sex_ratio_pivot_with_quality, sex_ratio_config_no_output
    ):
        result = sex_ratio.compute_sex_ratio(
            mock_sex_ratio_pivot_with_quality.copy(),
            sex_ratio_config_no_output,
            mask=False,
        )

        imm_2024 = _series(result, "sex_ratio_imm_2024")
        assert imm_2024.loc[("E003", 25)] == 0.0

    def test_sex_ratio_helper_rejects_invalid_migration(
        self, mock_sex_ratio_pivot_with_quality
    ):
        with pytest.raises(ValueError, match="migration must be one of"):
            sex_ratio._sex_ratio_helper(mock_sex_ratio_pivot_with_quality, "net", 2024)


class TestSexRatioSsq:
    def test_calculates_weighted_difference_from_national_change(
        self,
        mock_local_sex_ratio_df,
        mock_national_sex_ratio_df,
        sex_ratio_config_no_output,
    ):
        result = sex_ratio.sex_ratio_ssq(
            mock_local_sex_ratio_df,
            mock_national_sex_ratio_df,
            sex_ratio_config_no_output,
        )

        assert result.loc["E001", "ssq_imm"] == 25.0
        assert result.loc["E002", "ssq_imm"] == 0.0
        assert result.loc["E001", "ssq_em"] == 0.0
        assert result.loc["E002", "ssq_em"] == 135.0
