import pytest
import pandas as pd
from itertools import product
from pystagegate import prov_fin


class TestMergeFinalMigrationData:
    def test_correct_columns(self, immigration_df, emigration_df, prov_fin_config):
        result = prov_fin.merge_final_migration_data(
            immigration_df, emigration_df, prov_fin_config
        )
        assert list(result.columns) == [
            "Year",
            "Local Authority Code",
            "Age",
            "imm_fin",
            "em_fin",
            "net_fin",
        ]

    def test_correct_columns_sex_ratio(
        self, immigration_df, emigration_df, prov_fin_config
    ):
        result = prov_fin.merge_final_migration_data(
            immigration_df,
            emigration_df,
            prov_fin_config,
            sex_ratio=True,
        )

        assert list(result.columns) == [
            "Year",
            "Local Authority Code",
            "Age",
            "Sex",
            "imm_fin",
            "em_fin",
        ]

    def test_merge_net_migration(self, immigration_df, emigration_df, prov_fin_config):
        result = prov_fin.merge_final_migration_data(
            immigration_df, emigration_df, prov_fin_config
        )
        assert (result["net_fin"] == result["imm_fin"] - result["em_fin"]).all()

    def test_merge_aggregates(self, immigration_df, emigration_df, prov_fin_config):
        result = prov_fin.merge_final_migration_data(
            immigration_df, emigration_df, prov_fin_config
        )
        # No duplicates on groupby keys
        assert not result.duplicated(
            subset=["Local Authority Code", "Year", "Age"]
        ).any()

    def test_merge_aggregates_sex_ratio(
        self, immigration_df, emigration_df, prov_fin_config
    ):
        result = prov_fin.merge_final_migration_data(
            immigration_df, emigration_df, prov_fin_config, sex_ratio=True
        )
        # No duplicates on groupby keys
        assert not result.duplicated(
            subset=["Local Authority Code", "Year", "Age", "Sex"]
        ).any()

    def test_different_count_column_names(
        self, immigration_df, emigration_df, prov_fin_config
    ):
        result = prov_fin.merge_final_migration_data(
            immigration_df, emigration_df, prov_fin_config
        )

        # Rename count immigration in config and in frames
        prov_fin_config["datasets"]["final_immigration"]["variables"]["count"] = (
            "immigration"
        )
        prov_fin_config["datasets"]["final_emigration"]["variables"]["count"] = (
            "emigration"
        )

        result_nename = prov_fin.merge_final_migration_data(
            immigration_df.rename(columns={"Count": "immigration"}),
            emigration_df.rename(columns={"Count": "emigration"}),
            prov_fin_config,
        )

        pd.testing.assert_frame_equal(result, result_nename)


class TestSubsetProvisionalData:
    def test_subset_produces_correct_columns(self, provisional_df, prov_fin_config):
        result = prov_fin.subset_provisional_data(provisional_df, prov_fin_config)
        assert list(result.columns) == [
            "year",
            "code",
            "Age",
            "imm_prov",
            "em_prov",
            "net_prov",
        ]

    def test_subset_adds_year_column(self, provisional_df, prov_fin_config):
        result = prov_fin.subset_provisional_data(provisional_df, prov_fin_config)
        assert (result["year"] == 2024).all()

    def test_subset_aggregates_by_la_age(self, provisional_df, prov_fin_config):
        result = prov_fin.subset_provisional_data(provisional_df, prov_fin_config)
        # No duplicates on groupby keys
        assert not result.duplicated(subset=["code", "Age"]).any()


class TestProvisionalScotCartesianMerge:
    def test_cartesian_has_all_combinations(self, provisional_scot_df, prov_fin_config):
        result = prov_fin.provisional_scot_cartesian_merge(
            provisional_scot_df, prov_fin_config
        )

        unique_values = [
            provisional_scot_df[col].unique()
            for col in provisional_scot_df.columns
            if col != "count"
        ]

        # Len of merged result should equal len of unique combinations
        assert len(result) == len(list(product(*unique_values)))

    def test_cartesian_has_no_duplicates(self, provisional_scot_df, prov_fin_config):
        result = prov_fin.provisional_scot_cartesian_merge(
            provisional_scot_df, prov_fin_config
        )

        assert not result.duplicated().any()


class TestProvisionalScotAggregate:
    def test_provscot_agg_columns(self, provisional_scot_df, prov_fin_config):
        cartesian = prov_fin.provisional_scot_cartesian_merge(
            provisional_scot_df, prov_fin_config
        )
        result = prov_fin.provisional_scot_aggregate(cartesian, prov_fin_config)
        assert list(result.columns) == [
            "year",
            "ca_code",
            "Age",
            "imm_prov",
            "em_prov",
            "net_prov",
        ]

    def test_provscot_agg_calculates_net(self, provisional_scot_df, prov_fin_config):
        cartesian = prov_fin.provisional_scot_cartesian_merge(
            provisional_scot_df, prov_fin_config
        )
        result = prov_fin.provisional_scot_aggregate(cartesian, prov_fin_config)
        assert (result["net_prov"] == result["imm_prov"] - result["em_prov"]).all()

    def test_provscot_agg_filters_year(self, provisional_scot_df, prov_fin_config):
        cartesian = prov_fin.provisional_scot_cartesian_merge(
            provisional_scot_df, prov_fin_config
        )
        result = prov_fin.provisional_scot_aggregate(cartesian, prov_fin_config)
        assert (result["year"] == 2024).all()

    def test_provscot_agg_aggregates(self, provisional_scot_df, prov_fin_config):
        cartesian = prov_fin.provisional_scot_cartesian_merge(
            provisional_scot_df, prov_fin_config
        )
        result = prov_fin.provisional_scot_aggregate(cartesian, prov_fin_config)
        assert not result.duplicated(subset=["ca_code", "year", "Age"]).any()

    def test_provsot_agg_pivots(self, provisional_scot_df, prov_fin_config):
        cartesian = prov_fin.provisional_scot_cartesian_merge(
            provisional_scot_df, prov_fin_config
        )
        result = prov_fin.provisional_scot_aggregate(cartesian, prov_fin_config)
        assert list(result.columns) == [
            "year",
            "ca_code",
            "Age",
            "imm_prov",
            "em_prov",
            "net_prov",
        ]


class TestSquaredDifference:
    def test_sqdiff_calculates_expected(self):
        df = pd.DataFrame(
            {
                "final": [10],
                "provisional": [11],
                "final_total": [20],
                "provisional_total": [25],
            }
        )

        expected_df = pd.DataFrame(
            {
                "final": [10],
                "provisional": [11],
                "final_total": [20],
                "provisional_total": [25],
                "diff_output": [1.2],
                "sqdiff_output": [1.44],
            }
        )

        result = prov_fin.squared_difference(
            df,
            prov_col="provisional",
            fin_col="final",
            prov_col_total="provisional_total",
            fin_col_total="final_total",
        )

        pd.testing.assert_frame_equal(result, expected_df)

    def test_zero_sqdiff(self):
        df = pd.DataFrame(
            {
                "final": [10, 15, 35],
                "provisional": [10, 15, 35],
                "final_total": [60, 60, 60],
                "provisional_total": [60, 60, 60],
            }
        )

        result = prov_fin.squared_difference(
            df,
            prov_col="provisional",
            fin_col="final",
            prov_col_total="provisional_total",
            fin_col_total="final_total",
        )

        # Squared difference calculation should equal zero
        assert (result["diff_output"] == 0).all()
        assert (result["sqdiff_output"] == 0).all()

    def test_divide_by_zero_sqdiff(self):
        df = pd.DataFrame(
            {
                "final": [-6],
                "provisional": [-8],
                "final_total": [0],
                "provisional_total": [0],
            }
        )
        result = prov_fin.squared_difference(
            df,
            prov_col="provisional",
            fin_col="final",
            prov_col_total="provisional_total",
            fin_col_total="final_total",
        )

        assert result["diff_output"].isna().all()
        assert (result["sqdiff_output"] == 0).all()


@pytest.mark.parametrize("nation_param", ["E", "S", "W"])
class TestNationBreakdownSqDiff:
    def test_invalid_region(self, prov_fin_config, nation_param):
        nation_param = "X"
        with pytest.raises(ValueError, match="Nation must be one of 'E', 'S', 'W'"):
            prov_fin.nation_breakdown_sqdiff(
                pd.DataFrame(), prov_fin_config, nation=nation_param
            )

    def test_filter_nation(self, prov_fin_config, nation_param, nation_breakdown_df):
        result = prov_fin.nation_breakdown_sqdiff(
            nation_breakdown_df, prov_fin_config, nation=nation_param
        )
        assert (result["nation"] == nation_param).all()

    def test_nation_breakdown_aggregates(
        self, prov_fin_config, nation_param, nation_breakdown_df
    ):
        result = prov_fin.nation_breakdown_sqdiff(
            nation_breakdown_df, prov_fin_config, nation=nation_param
        )
        assert not result.duplicated(subset=["Local Authority Code"]).any()

    def test_valid_output_exists(
        self, prov_fin_config, nation_param, nation_breakdown_df
    ):
        result = prov_fin.nation_breakdown_sqdiff(
            nation_breakdown_df, prov_fin_config, nation=nation_param
        )

        # squared difference and scaled squared difference columns should be > 0 as all inputs > 0
        for prefix in ["imm", "em", "net"]:
            assert (result[f"sqdiff_{prefix}"] > 0).all()
            assert (result[f"sqdiff_{prefix}_sc"] > 0).all()

    def test_invalid_nation(self, prov_fin_config, nation_param):
        df = pd.DataFrame(
            {
                "Local Authority Code": ["X001"],
                "Age": [25],
                "imm_prov": [0],
                "em_prov": [5],
                "net_prov": [-5],
                "imm_fin": [1],
                "em_fin": [5],
                "net_fin": [-4],
            }
        )

        with pytest.raises(ValueError):
            prov_fin.nation_breakdown_sqdiff(df, prov_fin_config, nation=nation_param)
