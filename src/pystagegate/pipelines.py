from pystagegate import prov_fin, utils
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

    # Filter final immigration and emmigration on nationality
    immigration = immigration[
        immigration[config["datasets"]["final_immigration"]["variables"]["nationality"]]
        == config["global_parameters"]["final_nationalities"][0]
    ]

    emigration = emigration[
        emigration[config["datasets"]["final_emigration"]["variables"]["nationality"]]
        == config["global_parameters"]["final_nationalities"][0]
    ]

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
    _, eng_la = prov_fin.regional_breakdown(all, config, "E")

    # Wales analysis
    _, wal_la = prov_fin.regional_breakdown(all, config, "W")

    # Scotland analysis
    _, scot_la = prov_fin.regional_breakdown(all, config, "S")

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


def sex_ratio_main(config: dict | str) -> pd.DataFrame:
    # Configuration setup
    config = utils.load_config(config)["sex_ratio"]

    # Load and validate datasets
    immigration = utils.load_summary_data(config, "final_immigration")
    emigration = utils.load_summary_data(config, "final_emigration")
    provisional = utils.load_summary_data(config, "provisional")

    # Merge and aggregate final immigration and emmigration data
    merged = prov_fin.merge_final_migration_data(
        immigration, emigration, config
    )

    print(
        "\n\n",
        immigration.head(),
        emigration.head(),
        provisional.head(),
        merged,
        sep="\n\n",
    )
