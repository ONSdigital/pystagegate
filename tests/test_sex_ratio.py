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
        df = pd.DataFrame(
            {
                "Year": [2023, 2023, 2023, 2024, 2024, 2024, 2026],
            }
        )
        with pytest.raises(ValueError):
            sex_ratio.year_agg_merge(df, sex_ratio_config)


class TestYearAggSqDiff:
    def test_non_zero_sqdiff(self, merged_df, sex_ratio_config):
        agg_df = sex_ratio.year_agg_merge(merged_df, sex_ratio_config)

        result, result_adjusted = sex_ratio.year_agg_sqdiff(agg_df, sex_ratio_config)

        for out_name in ["imm", "em", "net"]:
            assert (result[f"sqdiff_{out_name}"] >= 0).all()

        for out_name in ["imm", "em"]:
            assert (result_adjusted[f"{out_name}_adjusted_size_ssq"] >= 0).all()


class TestPivotSexRatioFrame:
    def test_error_for_years(self, sex_ratio_config):
        df = pd.DataFrame(
            {
                "Year": [2023, 2023, 2023, 2024, 2024, 2024, 2026],
            }
        )
        with pytest.raises(ValueError):
            sex_ratio.year_agg_merge(df, sex_ratio_config)

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
    def test_recoding(self, fake_merged_df, sex_ratio_config):
        fake_sr_df = sex_ratio.pivot_sex_ratio_frame(fake_merged_df, sex_ratio_config)

        result = sex_ratio.clean_and_mask(fake_sr_df, sex_ratio_config).drop(
            columns=["imm_fin_quality", "em_fin_quality"], level=0
        )

        # Check mulltiindex
        assert list(result.loc[("E1", 30)]) == [0, 1.1, 0, 0]
        assert list(result.loc[("E1", 40)]) == [5.0, 1.0, 1.0, 0]
        assert list(result.loc[("E1", 50)]) == [0, 0, 1.1, 10]

    def test_masking(self, fake_merged_df, sex_ratio_config):
        fake_sr_df = sex_ratio.pivot_sex_ratio_frame(fake_merged_df, sex_ratio_config)

        result = sex_ratio.clean_and_mask(fake_sr_df, sex_ratio_config).drop(
            columns=["imm_fin", "em_fin"], level=0
        )

        # Check multiindex
        assert list(result.loc[("E1", 30)]) == ["Zero", "Low", "Zero", "Zero"]
        assert list(result.loc[("E1", 40)]) == ["OK", "Low", "Low", "Zero"]
        assert list(result.loc[("E1", 50)]) == ["Zero", "Zero", "Low", "OK"]

    def test_no_small_numbers(self, merged_sr_df, sex_ratio_config):
        # Artifically make counts very small, so that many counts are between 0 and 1
        fact = 0.05
        merged_sr_df["imm_fin"] = merged_sr_df["imm_fin"] * fact
        merged_sr_df["em_fin"] = merged_sr_df["em_fin"] * fact

        sr_df = sex_ratio.pivot_sex_ratio_frame(merged_sr_df, sex_ratio_config)
        result = sex_ratio.clean_and_mask(sr_df, sex_ratio_config).drop(
            columns=["imm_fin_quality", "em_fin_quality"], level=0
        )

        # Ensure that there is nothing between 0 and 1 after masking
        assert result[(result < 1) & (result > 0)].isna().all().all()


class TestComputeSexRatio:
    def test_no_match_for_ratios(self, fake_merged_df, sex_ratio_config):
        fake_sr_df = sex_ratio.pivot_sex_ratio_frame(fake_merged_df, sex_ratio_config)

        fake_mask_df = sex_ratio.clean_and_mask(fake_sr_df, sex_ratio_config)

        # Check that we get a KeyError when there is no match for ratios
        with pytest.raises(KeyError):
            sex_ratio.compute_sex_ratio(
                fake_mask_df, sex_ratio_config, male_sex="M", female_sex="F"
            )

    def test_low_zero_computes(self, sex_ratio_config):
        low_zero_df = pd.DataFrame(
            {
                "Year": [2024, 2025, 2024, 2025],
                "Local Authority Code": ["E1", "E1", "E1", "E1"],
                "Age": [30, 30, 30, 30],
                "Sex": ["M", "M", "F", "F"],
                "imm_fin": [0.5, 0.6, 0.1, 2],
                "em_fin": [-1, 0.3, 0.3, 1.1],
            }
        )
        low_zero_sr_df = sex_ratio.pivot_sex_ratio_frame(low_zero_df, sex_ratio_config)
        low_zero_mask_df = sex_ratio.clean_and_mask(low_zero_sr_df, sex_ratio_config)

        result = sex_ratio.compute_sex_ratio(
            low_zero_mask_df, sex_ratio_config, male_sex="M", female_sex="F"
        )

        # Prove Zero/Zero quality mask gives NA sex ratio
        assert (result[("em_fin_quality", "M", 2024)] == "Zero").all()  # Numerator
        assert (result[("em_fin_quality", "F", 2024)] == "Zero").all()  # Denominator
        assert (result["sex_ratio_em_2024"].isna()).all()  # Ratio

        # Prove Zero/Low quality mask gives NA sex ratio
        assert (result[("em_fin_quality", "M", 2025)] == "Zero").all()  # Numerator
        assert (result[("em_fin_quality", "F", 2025)] == "Low").all()  # Denominator
        assert (result["sex_ratio_em_2025"].isna()).all()  # Ratio

        # Prove Low/Zero quality mask gives NA sex ratio
        assert (result[("imm_fin_quality", "M", 2024)] == "Low").all()  # Numerator
        assert (result[("imm_fin_quality", "F", 2024)] == "Zero").all()  # Denominator
        assert (result["sex_ratio_imm_2024"].isna()).all()  # Ratio

        # Prove Low/Low quality mask computes valid sex ratio
        assert (result[("imm_fin_quality", "M", 2025)] == "Low").all()  # Numerator
        assert (result[("imm_fin_quality", "F", 2025)] == "Low").all()  # Denominator
        assert (
            result["sex_ratio_imm_2025"]
            == result[("imm_fin", "M", 2025)] / result[("imm_fin", "F", 2025)]
        ).all()  # Ratio

    def test_ok_zero_computes(self, sex_ratio_config):
        ok_zero_df = pd.DataFrame(
            {
                "Year": [2024, 2025, 2024, 2025],
                "Local Authority Code": ["E1", "E1", "E1", "E1"],
                "Age": [30, 30, 30, 30],
                "Sex": ["M", "M", "F", "F"],
                "imm_fin": [5, 0.3, 0.49, 8],
                "em_fin": [4, 2, 1, 0.9],
            }
        )
        ok_zero_sr_df = sex_ratio.pivot_sex_ratio_frame(ok_zero_df, sex_ratio_config)
        ok_zero_mask_df = sex_ratio.clean_and_mask(ok_zero_sr_df, sex_ratio_config)

        result = sex_ratio.compute_sex_ratio(
            ok_zero_mask_df, sex_ratio_config, male_sex="M", female_sex="F"
        )

        # Prove OK/Zero quality mask skips computation and returns value of OK
        assert (result[("imm_fin_quality", "M", 2024)] == "OK").all()  # Numerator
        assert (result[("imm_fin_quality", "F", 2024)] == "Zero").all()  # Denominator
        assert (
            result["sex_ratio_imm_2024"] == result[("imm_fin", "M", 2024)]
        ).all()  # Ratio = Numerator

        # Prove Zero/OK quality mask skips computation and returns value of OK
        assert (result[("imm_fin_quality", "M", 2025)] == "Zero").all()  # Numerator
        assert (result[("imm_fin_quality", "F", 2025)] == "OK").all()  # Denominator
        assert (
            result["sex_ratio_imm_2025"] == result[("imm_fin", "F", 2025)]
        ).all()  # Ratio = Denominator


class TestSexRatioHelper:
    @pytest.mark.parametrize("caps", [[0, 1], [-10, 100], [0.25, 0.26], [1, 2]])
    def test_valid_caps_are_applied(self, merged_sr_df, sex_ratio_config, caps):
        pivot_df = sex_ratio.pivot_sex_ratio_frame(merged_sr_df, sex_ratio_config)
        result = sex_ratio.sex_ratio_helper(
            pivot_df, "imm", 2025, caps=caps, mask=False
        )

        assert result["sex_ratio_imm_2025"].min() >= caps[0]
        assert result["sex_ratio_imm_2025"].max() <= caps[1]

    def test_invalid_caps(self, merged_sr_df, sex_ratio_config):
        pivot_df = sex_ratio.pivot_sex_ratio_frame(merged_sr_df, sex_ratio_config)

        with pytest.raises(ValueError):
            sex_ratio.sex_ratio_helper(pivot_df, "imm", 2025, caps=[2, 1], mask=False)

    def test_invalid_migration_type(self):
        with pytest.raises(ValueError):
            sex_ratio.sex_ratio_helper(pd.DataFrame(), "Imm", 2025)

    def test_divide_by_zero_no_mask(self, merged_sr_df, sex_ratio_config):
        pivot_df = sex_ratio.pivot_sex_ratio_frame(merged_sr_df, sex_ratio_config)

        # Set denominators in sex ratio computation to zero
        pivot_df[("imm_fin", "Female", 2025)] = 0

        result = sex_ratio.sex_ratio_helper(pivot_df, "imm", 2025, mask=False)

        assert (result["sex_ratio_imm_2025"] == result[("imm_fin", "Male", 2025)]).all()


class TestSexRatioSsq:
    def test_non_zero_ssq(self, local_sr_df, national_sr_df, sex_ratio_config):
        result = sex_ratio.sex_ratio_ssq(local_sr_df, national_sr_df, sex_ratio_config)
        for output in ["ssq_imm", "ssq_em"]:
            assert (result[output] >= 0).all()
