from pystagegate import prov_fin, sex_ratio, utils
import pandas as pd
import os


def prov_fin_main(config: dict | str) -> pd.DataFrame:
    # Configuration setup
    config = utils.load_config(config)["prov_fin"]

    # Load and validate datasets
    immigration = utils.load_summary_data(config, "final_immigration")
    emigration = utils.load_summary_data(config, "final_emigration")
    provisional = utils.load_summary_data(config, "provisional")
    provisional_scot = utils.load_summary_data(config, "provisional_scot")

    # Filter final immigration and emmigration
    immigration = prov_fin.filter_migration_data(
        immigration, "final_immigration", config
    )
    emigration = prov_fin.filter_migration_data(emigration, "final_immigration", config)

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
    all = provisional_all.merge(
        final,
        left_on=[
            config["datasets"]["provisional"]["variables"]["la_code"],
            config["datasets"]["provisional"]["variables"]["age"],
            "year",
        ],
        right_on=[
            config["datasets"]["final_immigration"]["variables"]["la_code"],
            config["datasets"]["final_immigration"]["variables"]["age"],
            config["datasets"]["final_immigration"]["variables"]["year"],
        ],
        how="left",
    )

    all["nation"] = all[
        config["datasets"]["final_immigration"]["variables"]["la_code"]
    ].str[0]

    # England analysis
    _, eng_la = prov_fin.regional_breakdown_sqdiff(all, config, "E")

    # Wales analysis
    _, wal_la = prov_fin.regional_breakdown_sqdiff(all, config, "W")

    # Scotland analysis
    _, scot_la = prov_fin.regional_breakdown_sqdiff(all, config, "S")

    # Correlation matrices and outputs
    output = pd.concat([eng_la, wal_la, scot_la])

    # Handle output directory creation
    if config["output_path"] is not None:
        if not os.path.exists(config["output_path"]):
            os.makedirs(config["output_path"])

        output.to_csv(
            os.path.join(config["output_path"], "prov_fin_output.csv"), index=False
        )

    return output.reset_index(drop=True)


def national_profile_main(config: dict | str) -> list:
    # Configuration setup
    config = utils.load_config(config)["sex_ratio"]

    # Load and validate datasets
    immigration = utils.load_summary_data(config, "final_immigration")
    emigration = utils.load_summary_data(config, "final_emigration")
    provisional = utils.load_summary_data(config, "provisional")

    # Merge and aggregate final immigration and emmigration data
    final = prov_fin.merge_final_migration_data(immigration, emigration, config)

    # Aggregate provisional data
    provisional_agg = prov_fin.subset_provisional_data(provisional, config)

    # Create merged provisional and final with added aggregated national profile
    merged = sex_ratio.merged_national_profile(provisional_agg, final, config)

    # Calculate squared difference from national profile
    merged = prov_fin.squared_difference(merged, "imm", "imm_prov", "imm_fin")
    merged = prov_fin.squared_difference(merged, "em", "em_prov", "em_fin")
    merged = prov_fin.squared_difference(merged, "net", "net_prov", "net_fin")

    # Aggregate squared difference
    sq_diff_output = merged.groupby(
        config["datasets"]["final_immigration"]["variables"]["la_code"]
    ).agg(
        {
            "imm_prov": "sum",
            "em_prov": "sum",
            "net_prov": "sum",
            "sqdiff_imm": "sum",
            "sqdiff_em": "sum",
            "sqdiff_net": "sum",
        }
    )

    # Year on year comparison squared difference
    year_agg, year_agg_adjusted = sex_ratio.year_agg_sqdiff(final, config)

    return [sq_diff_output, year_agg, year_agg_adjusted]


def sex_ratio_main(config: dict | str) -> pd.DataFrame:
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

    print("\n\n", sr_pivot, sr_pivot.columns, sep="\n\n")

    # Data cleaning sex ratio
