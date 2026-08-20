from pystagegate import prov_fin, utils
import pandas as pd
import os


def prov_fin_main(config: dict | str) -> pd.DataFrame:
    # Configuration setup
    if type(config) is str:
        if os.path.exists(config):
            config = utils.load_config(config)["prov_fin"]
        else:
            raise FileNotFoundError(f"Config file not found: {config}")
    elif type(config) is dict:
        config = config["prov_fin"]
    else:
        raise ValueError("Invalid config type. Must be str or dict.")

    # Load and validate datasets
    ltim_immigration = utils.load_summary_data(config, "final_immigration")
    ltim_emigration = utils.load_summary_data(config, "final_emigration")
    ltim_provisional = utils.load_summary_data(config, "provisional")
    ltim_provisional_scot = utils.load_summary_data(config, "provisional_scot")

    print(config["datasets"]["final_immigration"]["variables"]["nationality"])

    # Filter final immigration and emmigration on nationality
    ltim_immigration = ltim_immigration[
        ltim_immigration[
            config["datasets"]["final_immigration"]["variables"]["nationality"]
        ] == config["global_parameters"]["final_nationalities"][0]
    ]

    ltim_emigration = ltim_emigration[
        ltim_emigration[
            config["datasets"]["final_emigration"]["variables"]["nationality"]
        ] == config["global_parameters"]["final_nationalities"][0]
    ]

    # Merge and aggregate final immigration and emmigration
    ltim_merged = prov_fin.merge_final_migration_data(
        ltim_immigration, ltim_emigration, config
    )

    # Filter provisional data for the specified year and aggregate
    ltim_provisional_subset = prov_fin.subset_provisional_data(ltim_provisional, config)

    # Create and merge cartesian product of unique values for the provisional Scotland data
    ltim_provisional_scot_cartesian = prov_fin.provisional_scot_cartesian_merge(
        ltim_provisional_scot, config
    )

    # Aggregate the merged Scotland data, summing count for sex
    ltim_provisional_scot_agg = prov_fin.provisional_scot_aggregate(
        ltim_provisional_scot_cartesian, config
    )

    # Concatenate all aggregated provisional data
    ltim_provisional_scot_agg.columns = ltim_provisional_subset.columns

    ltim_provisional_all = pd.concat(
        [ltim_provisional_subset, ltim_provisional_scot_agg]
    )

    # Final dataframe with provisional and merged data
    ltim_final = ltim_provisional_all.merge(
        ltim_merged,
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

    ltim_final["nation"] = ltim_final[
        config["datasets"]["final_immigration"]["variables"]["la_code"]
    ].str[0]

    # GB analysis
    gb_age, gb_la = prov_fin.regional_breakdown(ltim_final, config)

    # England analysis
    eng_age, eng_la = prov_fin.regional_breakdown(ltim_final, config, "E")

    # Wales analysis
    wal_age, wal_la = prov_fin.regional_breakdown(ltim_final, config, "W")

    # Scotland analysis
    scot_age, scot_la = prov_fin.regional_breakdown(ltim_final, config, "S")

    # Correlation matrices and outputs
    ltim_output = pd.concat([eng_la, wal_la, scot_la])

    # Handle output directory creation
    if config["output_path"] is not None:
        if not os.path.exists(config["output_path"]):
            os.makedirs(config["output_path"])

        ltim_output.to_csv(
            os.path.join(config["output_path"], "prov_fin_output.csv"), index=False
        )

    return ltim_output.reset_index(drop=True)
