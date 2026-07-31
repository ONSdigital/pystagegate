from pystagegate import prov_fin, functions
import pandas as pd
from itertools import product


def prov_fin_main(config):
    print("\n\n")
    # Configuration setup
    if type(config) is str:
        config = functions.load_config(config)["prov_fin"]
    else:
        config = config["prov_fin"]

    # Load datasets
    ltim_immigration = prov_fin.load_summary_data(config, "final_immigration")
    ltim_emigration = prov_fin.load_summary_data(config, "final_emigration")
    ltim_provisional = prov_fin.load_summary_data(config, "provisional")
    ltim_provisional_scot = prov_fin.load_summary_data(config, "provisional_scot")

    # todo: Data validation against schema

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

    print(
        "\n\n",
        ltim_merged.head(5),
        ltim_provisional_subset.head(5),
        ltim_provisional_scot_agg.head(5),
        ltim_provisional_all.head(5),
        ltim_final.head(5),
        ltim_final.columns,
        sep="\n\n",
    )

    # GB analysis
    gb_age, gb_la = prov_fin.regional_breakdown(ltim_final, config)

    # England analysis
    eng_age, eng_la = prov_fin.regional_breakdown(ltim_final, config, "E")

    # Wales analysis
    wal_age, wal_la = prov_fin.regional_breakdown(ltim_final, config, "W")

    # Scotland analysis
    scot_age, scot_la = prov_fin.regional_breakdown(ltim_final, config, "S")

    # Console print out
    print("\n\n******** GB Analysis ********", gb_age, gb_la, sep="\n\n")
    print("\n\n******** England Analysis ********", eng_age, eng_la, sep="\n\n")
    print("\n\n******** Wales Analysis ********", wal_age, wal_la, sep="\n\n")
    print("\n\n******** Scotland Analysis ********", scot_age, scot_la, sep="\n\n")
