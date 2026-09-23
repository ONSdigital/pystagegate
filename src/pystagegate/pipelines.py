from pystagegate import prov_fin, sex_ratio, utils
import pandas as pd


def prov_fin_main(config: dict | str) -> pd.DataFrame:
    # Configuration setup
    config = utils.load_config(config)["prov_fin"]

    # Load and validate datasets
    immigration = utils.load_summary_data(config, "final_immigration")
    emigration = utils.load_summary_data(config, "final_emigration")
    provisional = utils.load_summary_data(config, "provisional")
    provisional_scot = utils.load_summary_data(config, "provisional_scot")

    # Filter final immigration and emmigration
    immigration = prov_fin._filter_migration_data(
        immigration, "final_immigration", config
    )
    emigration = prov_fin._filter_migration_data(
        emigration, "final_immigration", config
    )

    # Merge and aggregate final immigration and emmigration
    final = prov_fin.merge_final_migration_data(immigration, emigration, config)

    # Aggregate provisional data
    provisional_agg = prov_fin.subset_provisional_data(provisional, config)

    # Create and merge cartesian product of unique values for the provisional Scotland data
    provisional_scot_cartesian = prov_fin.provisional_scot_cartesian_merge(
        provisional_scot, config
    )

    # Aggregate the merged Scotland data, summing count for sex
    provisional_scot_agg = prov_fin.provisional_scot_aggregate(
        provisional_scot_cartesian, config
    )

    # Concatenate all aggregated provisional data
    provisional_scot_agg.columns = provisional_agg.columns

    provisional_all = pd.concat([provisional_agg, provisional_scot_agg])

    # Final dataframe with provisional and merged data
    prov_vars = config["datasets"]["provisional"]["variables"]
    fin_imm_vars = config["datasets"]["final_immigration"]["variables"]

    all = provisional_all.merge(
        final,
        left_on=[
            prov_vars["la_code"],
            prov_vars["age"],
            "year",
        ],
        right_on=[
            fin_imm_vars["la_code"],
            fin_imm_vars["age"],
            fin_imm_vars["year"],
        ],
        how="left",
    )

    # Todo: delete
    all.to_csv("tests/data/provisional_final_merged.csv")

    # England analysis
    eng_la = prov_fin.nation_breakdown_sqdiff(all, config, "E")

    # Wales analysis
    wal_la = prov_fin.nation_breakdown_sqdiff(all, config, "W")

    # Scotland analysis
    scot_la = prov_fin.nation_breakdown_sqdiff(all, config, "S")

    # Concatenate for output
    output = pd.concat([eng_la, wal_la, scot_la])

    # Write outputs
    utils.write_outputs(config["output_path"], (output, "prov_fin_output.csv"))

    return output


def sex_ratio_national_profile(config: dict | str) -> tuple[pd.DataFrame, pd.DataFrame]:
    # Configuration setup
    config = utils.load_config(config)["sex_ratio"]

    # Load and validate datasets
    immigration = utils.load_summary_data(config, "final_immigration")
    emigration = utils.load_summary_data(config, "final_emigration")

    # Merge and aggregate final immigration and emmigration data
    final = prov_fin.merge_final_migration_data(immigration, emigration, config)

    # Year on year comparison squared difference for national vs local authority
    year_on_year_merged = sex_ratio.year_agg_merge(final, config)

    year_agg, year_agg_adjusted = sex_ratio.year_agg_sqdiff(year_on_year_merged, config)

    # Write outputs
    utils.write_outputs(
        config["output_path"],
        [
            (year_agg, "year_on_year_sqdiff.csv"),
            (year_agg_adjusted, "year_on_year_adjusted_sqdiff.csv"),
        ],
    )

    return (year_agg, year_agg_adjusted)


def sex_ratio_main(
    config: dict | str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    # Configuration setup
    config = utils.load_config(config)["sex_ratio"]

    # Load and validate datasets
    immigration = utils.load_summary_data(config, "final_immigration")
    emigration = utils.load_summary_data(config, "final_emigration")

    # Sex Ratio analysis
    sr = prov_fin.merge_final_migration_data(
        immigration, emigration, config, sex_ratio=True
    )

    sr_pivot = sex_ratio.pivot_sex_ratio_frame(sr, config)

    # Data cleaning for sex ratio calculation
    sr_recode = sex_ratio.clean_and_mask(sr_pivot, config)

    # Calculate sex ratios:
    sr_recode = sex_ratio.compute_sex_ratio(
        sr_recode, config, caps=(0.1, 10.0), male_sex="Male", female_sex="Female"
    )

    # Aggregate by age to get national-level data and recalculate sex ratios (use uncleaned data)
    sr_national = sex_ratio.compute_sex_ratio(
        sr_pivot.groupby("Age").agg("sum")[["em_fin", "imm_fin"]],
        config,
        mask=False,
        male_sex="Male",
        female_sex="Female",
    )

    # Year on year comparison squared difference for national vs local authority
    sr_merged = sex_ratio.sex_ratio_ssq(sr_recode, sr_national, config)

    # Drop columns not needed for output
    sr_recode.drop(columns=["em_fin_quality", "imm_fin_quality"], level=0, inplace=True)
    sr_merged.drop(columns=["em_fin_quality", "imm_fin_quality"], level=0, inplace=True)

    # Write outputs
    utils.write_outputs(
        config["output_path"],
        [
            (sr_recode, "sex_ratios.csv"),
            (sr_national, "national_sex_ratios.csv"),
            (sr_merged, "sex_ratios_ssq.csv"),
        ],
    )

    return (
        sr_recode,
        sr_national,
        sr_merged,
    )
