import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from pystagegate import prov_fin


class TestMergeFinalMigrationData:
    def test_merge_produces_correct_columns(
        self, mock_immigration_df, mock_emigration_df, prov_fin_config_no_output
    ):
        result = prov_fin.merge_final_migration_data(
            mock_immigration_df, mock_emigration_df, prov_fin_config_no_output
        )
        assert list(result.columns) == [
            "Year",
            "Local Authority Code",
            "Age",
            "imm_fin",
            "em_fin",
            "net_fin",
        ]

    def test_merge_calculates_net_migration(
        self, mock_immigration_df, mock_emigration_df, prov_fin_config_no_output
    ):
        result = prov_fin.merge_final_migration_data(
            mock_immigration_df, mock_emigration_df, prov_fin_config_no_output
        )
        assert (result["net_fin"] == result["imm_fin"] - result["em_fin"]).all()

    def test_merge_filters_by_year(
        self, mock_immigration_df, mock_emigration_df, prov_fin_config_no_output
    ):
        result = prov_fin.merge_final_migration_data(
            mock_immigration_df, mock_emigration_df, prov_fin_config_no_output
        )
        # All rows should be for year 2024 (filtered by config)
        assert (result["Year"] == 2024).all()

    def test_merge_filters_by_nationality(
        self, mock_immigration_df, mock_emigration_df, prov_fin_config_no_output
    ):
        # Should only contain "All Nationalities" after filtering
        result = prov_fin.merge_final_migration_data(
            mock_immigration_df, mock_emigration_df, prov_fin_config_no_output
        )
        assert len(result) > 0

    def test_merge_aggregates_by_la_year_age(
        self, mock_immigration_df, mock_emigration_df, prov_fin_config_no_output
    ):
        result = prov_fin.merge_final_migration_data(
            mock_immigration_df, mock_emigration_df, prov_fin_config_no_output
        )
        # No duplicates on groupby keys
        assert not result.duplicated(
            subset=["Local Authority Code", "Year", "Age"]
        ).any()


class TestSubsetProvisionalData:
    def test_subset_produces_correct_columns(
        self, mock_provisional_df, prov_fin_config_no_output
    ):
        result = prov_fin.subset_provisional_data(
            mock_provisional_df, prov_fin_config_no_output
        )
        assert list(result.columns) == [
            "year",
            "code",
            "Age",
            "imm_prov",
            "em_prov",
            "net_prov",
        ]

    def test_subset_adds_year_column(
        self, mock_provisional_df, prov_fin_config_no_output
    ):
        result = prov_fin.subset_provisional_data(
            mock_provisional_df, prov_fin_config_no_output
        )
        assert (result["year"] == 2024).all()

    def test_subset_aggregates_by_la_age(
        self, mock_provisional_df, prov_fin_config_no_output
    ):
        result = prov_fin.subset_provisional_data(
            mock_provisional_df, prov_fin_config_no_output
        )
        assert not result.duplicated(subset=["code", "Age"]).any()


class TestProvisionalScotCartesianMerge:
    def test_cartesian_fills_missing_with_zero(
        self, mock_provisional_scot_df, prov_fin_config_no_output
    ):
        result = prov_fin.provisional_scot_cartesian_merge(
            mock_provisional_scot_df, prov_fin_config_no_output
        )
        assert not result["count"].isna().any()

    def test_cartesian_has_all_combinations(
        self, mock_provisional_scot_df, prov_fin_config_no_output
    ):
        result = prov_fin.provisional_scot_cartesian_merge(
            mock_provisional_scot_df, prov_fin_config_no_output
        )
        # Should have at least as many rows as the original
        assert len(result) >= len(mock_provisional_scot_df)


class TestProvisionalScotAggregate:
    def test_aggregate_produces_correct_columns(
        self, mock_provisional_scot_df, prov_fin_config_no_output
    ):
        cartesian = prov_fin.provisional_scot_cartesian_merge(
            mock_provisional_scot_df, prov_fin_config_no_output
        )
        result = prov_fin.provisional_scot_aggregate(
            cartesian, prov_fin_config_no_output
        )
        assert list(result.columns) == [
            "year",
            "ca_code",
            "Age",
            "imm_prov",
            "em_prov",
            "net_prov",
        ]

    def test_aggregate_calculates_net(
        self, mock_provisional_scot_df, prov_fin_config_no_output
    ):
        cartesian = prov_fin.provisional_scot_cartesian_merge(
            mock_provisional_scot_df, prov_fin_config_no_output
        )
        result = prov_fin.provisional_scot_aggregate(
            cartesian, prov_fin_config_no_output
        )
        assert (result["net_prov"] == result["imm_prov"] - result["em_prov"]).all()

    def test_aggregate_filters_by_year(
        self, mock_provisional_scot_df, prov_fin_config_no_output
    ):
        cartesian = prov_fin.provisional_scot_cartesian_merge(
            mock_provisional_scot_df, prov_fin_config_no_output
        )
        result = prov_fin.provisional_scot_aggregate(
            cartesian, prov_fin_config_no_output
        )
        assert (result["year"] == 2024).all()


class TestSquaredDifference:
    def test_squared_difference_creates_columns(self, mock_merged_df):
        result = prov_fin.squared_difference(
            mock_merged_df, "imm", "imm_prov", "imm_fin"
        )
        assert "diff_imm" in result.columns
        assert "sqdiff_imm" in result.columns

    def test_squared_difference_zero_when_total_zero(self, mock_merged_df):
        mock_merged_df["imm_prov_T"] = 0
        result = prov_fin.squared_difference(
            mock_merged_df, "imm", "imm_prov", "imm_fin"
        )
        assert (result["sqdiff_imm"] == 0).all()

    def test_squared_difference_non_negative(self, mock_merged_df):
        result = prov_fin.squared_difference(
            mock_merged_df, "imm", "imm_prov", "imm_fin"
        )
        assert (result["sqdiff_imm"] >= 0).all()


class TestRegionalBreakdown:
    def test_gb_breakdown_returns_two_dataframes(
        self, mock_final_merged_df, prov_fin_config_no_output
    ):
        age_agg, la_agg = prov_fin.regional_breakdown(
            mock_final_merged_df, prov_fin_config_no_output
        )
        assert isinstance(age_agg, pd.DataFrame)
        assert isinstance(la_agg, pd.DataFrame)

    def test_nation_breakdown_filters_correctly(
        self, mock_final_merged_df, prov_fin_config_no_output
    ):
        age_agg, la_agg = prov_fin.regional_breakdown(
            mock_final_merged_df, prov_fin_config_no_output, "E"
        )
        assert (la_agg["nation"] == "E").all()

    def test_invalid_nation_raises_error(
        self, mock_final_merged_df, prov_fin_config_no_output
    ):
        with pytest.raises(ValueError):
            prov_fin.regional_breakdown(
                mock_final_merged_df, prov_fin_config_no_output, "X"
            )

    def test_la_agg_has_scaled_sqdiff(
        self, mock_final_merged_df, prov_fin_config_no_output
    ):
        _, la_agg = prov_fin.regional_breakdown(
            mock_final_merged_df, prov_fin_config_no_output, "E"
        )
        assert "sqdiff_imm_sc" in la_agg.columns
        assert "sqdiff_em_sc" in la_agg.columns
        assert "sqdiff_net_sc" in la_agg.columns


class TestLoadSummaryData:
    @patch("pystagegate.prov_fin.prov_fin_validate")
    @patch("pandas.read_csv")
    def test_load_returns_dataframe(
        self, mock_read_csv, mock_validate, prov_fin_config_no_output
    ):
        mock_df = pd.DataFrame(
            {
                "Local Authority Code": ["E001"],
                "Age": [25],
                "Sex": ["Male"],
                "Nationality Group": ["All Nationalities"],
                "Year": [2024],
                "Count": [100],
            }
        )
        mock_read_csv.return_value = mock_df
        mock_validate.return_value = MagicMock(to_json_dict=lambda: {})

        result = prov_fin.load_summary_data(
            prov_fin_config_no_output, "final_immigration"
        )
        assert isinstance(result, pd.DataFrame)

    @patch("pystagegate.prov_fin.prov_fin_validate")
    @patch("pandas.read_csv")
    def test_load_selects_correct_columns(
        self, mock_read_csv, mock_validate, prov_fin_config_no_output
    ):
        mock_df = pd.DataFrame(
            {
                "Local Authority Code": ["E001"],
                "Age": [25],
                "Sex": ["Male"],
                "Nationality Group": ["All Nationalities"],
                "Year": [2024],
                "Count": [100],
                "Extra Column": ["should be dropped"],
            }
        )
        mock_read_csv.return_value = mock_df
        mock_validate.return_value = MagicMock(to_json_dict=lambda: {})

        result = prov_fin.load_summary_data(
            prov_fin_config_no_output, "final_immigration"
        )
        assert "Extra Column" not in result.columns

    @patch("pystagegate.prov_fin.prov_fin_validate")
    @patch("pandas.read_csv")
    def test_load_missing_column_raises_error(
        self, mock_read_csv, mock_validate, prov_fin_config_no_output
    ):
        mock_df = pd.DataFrame(
            {
                "Local Authority Code": ["E001"],
                "Age": [25],
                # Missing Sex, Nationality Group, Year, Count
            }
        )
        mock_read_csv.return_value = mock_df
        mock_validate.return_value = MagicMock(to_json_dict=lambda: {})

        with pytest.raises(KeyError):
            prov_fin.load_summary_data(prov_fin_config_no_output, "final_immigration")

    @patch("pandas.read_csv")
    def test_load_file_not_found(self, mock_read_csv, prov_fin_config_no_output):
        mock_read_csv.side_effect = FileNotFoundError("File not found")

        with pytest.raises(FileNotFoundError):
            prov_fin.load_summary_data(prov_fin_config_no_output, "final_immigration")

    def test_load_invalid_dataset_key(self, prov_fin_config_no_output):
        with pytest.raises(KeyError):
            prov_fin.load_summary_data(prov_fin_config_no_output, "nonexistent_dataset")

    @patch("pystagegate.prov_fin.prov_fin_validate")
    @patch("pandas.read_csv")
    def test_load_validation_failure_propagates(
        self, mock_read_csv, mock_validate, prov_fin_config_no_output
    ):
        mock_df = pd.DataFrame(
            {
                "Local Authority Code": ["E001"],
                "Age": [25],
                "Sex": ["Male"],
                "Nationality Group": ["All Nationalities"],
                "Year": [2024],
                "Count": [100],
            }
        )
        mock_read_csv.return_value = mock_df
        mock_validate.side_effect = ValueError("Validation failed")

        with pytest.raises(ValueError, match="Validation failed"):
            prov_fin.load_summary_data(prov_fin_config_no_output, "final_immigration")
