from pystagegate import prov_fin, utils, validate
import great_expectations as gx
import pandas as pd
import os
import json


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

    # Load datasets
    ltim_immigration = prov_fin.load_summary_data(config, "final_immigration")
    ltim_emigration = prov_fin.load_summary_data(config, "final_emigration")
    ltim_provisional = prov_fin.load_summary_data(config, "provisional")
    ltim_provisional_scot = prov_fin.load_summary_data(config, "provisional_scot")

    # todo: Data validation with GX against (generated) schema
    validation = validate.generic_validate(
        ltim_immigration, "final_immigration", config
    )

    # Merge immigration and emmigration and aggregate
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

    ltim_final["Nation"] = ltim_final[
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

        with open(
            os.path.join(config["output_path"], "validation_results.json"), "w"
        ) as f:
            json.dump(validation.to_json_dict(), f, indent=4)

        ltim_output.to_csv(
            os.path.join(config["output_path"], "prov_fin_output.csv"), index=False
        )

        ltim_output.groupby("Nation")[["sqdiff_imm_sc", "imm_prov"]].corr().to_csv(
            os.path.join(config["output_path"], "prov_fin_corr_imm.csv"), index=False
        )

        ltim_output.groupby("Nation")[["sqdiff_em_sc", "em_prov"]].corr().to_csv(
            os.path.join(config["output_path"], "prov_fin_corr_em.csv"), index=False
        )

        ltim_output.groupby("Nation")[["sqdiff_net_sc", "imm_prov"]].corr().to_csv(
            os.path.join(config["output_path"], "prov_fin_corr_net.csv"), index=False
        )

    return ltim_output
