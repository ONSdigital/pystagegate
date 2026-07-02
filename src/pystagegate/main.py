from pystagegate import prov_fin, functions
import pandas as pd

# Params
age_min = 0
age_max = 200
year = 2024

def main():
    # Load config
    config = functions.load_config("testing_config.json")
    
    # Load datasets
    ltim_lookup = pd.read_csv(config["lookup_tables"]["ltim_lookup"])

    las_lookup = pd.read_csv(config["lookup_tables"]["las_lookup"])

    ltim_immigration = prov_fin.load_summary_data(
        path=config["prov_fin_paths"]["spring_immigration"],
        age_var="Age",
        age_min=age_min,
        age_max=age_max,
        lan_var="Local Authority Name",
        date_var="Date Updated"
    )

    ltim_emigration = prov_fin.load_summary_data(
        path=config["prov_fin_paths"]["spring_emigration"],
        age_var="Age",
        age_min=age_min,
        age_max=age_max,
        lan_var="Local Authority Name",
        date_var="Date Updated"
    )

    ltim_provisional = prov_fin.load_summary_data(
        path=config["prov_fin_paths"]["provisional_mye"],
        age_var="Age",
        age_min=age_min,
        age_max=age_max,
    )

    ltim_provisional_scot = prov_fin.load_summary_data(
        path=config["prov_fin_paths"]["provisional_scot"],
        age_var="Age",
        age_min=age_min,
        age_max=age_max,
    )

    # Merge immigration and emmigration
    ltim_merged = pd.merge(
        ltim_immigration,
        ltim_emigration,
        on=["Age","Local Authority Code", "Year","Sex","Nationality Group"],
        how="left",
        suffixes=("_imm", "_em")
    )

    ltim_merged["Net_Cell"] = ltim_merged["Count_imm"] - ltim_merged["Count_em"]

    # Filter provisional data for the specified year
    ltim_provisional_subset = pd.concat(
        [
            ltim_provisional.iloc[:, 0:3],
            ltim_provisional.loc[:, [
                f"international_in_{year}", 
                f"international_out_{year}", 
                f"international_net_{year}"
            ]]
        ],
        axis=1
    )

    ltim_provisional_subset = ltim_provisional_subset.rename(columns={
        f"international_in_{year}": "international_in",
        f"international_out_{year}": "international_out",
        f"international_net_{year}": "international_net"
    })

    ltim_provisional_subset["Year"] = year

    print(ltim_provisional_subset.head())

if __name__ == "__main__":
    main()