import pandas as pd


def merged_national_profile(
    provisional_df: pd.DataFrame, final_df: pd.DataFrame, config: dict
) -> pd.DataFrame:
    left_vars = config["datasets"]["provisional"]["variables"]
    right_vars = config["datasets"]["final_immigration"]["variables"]

    merged_df = provisional_df.merge(
        final_df,
        left_on=[
            "year",
            left_vars["la_code"],
            left_vars["age"],
        ],
        right_on=[right_vars["year"], right_vars["la_code"], right_vars["age"]],
        how="left",
    )

    merged_df = merged_df[
        [
            right_vars["year"],
            right_vars["la_code"],
            right_vars["age"],
            "imm_prov",
            "em_prov",
            "net_prov",
            "imm_fin",
            "em_fin",
            "net_fin",
        ]
    ]

    national_profile = (
        merged_df.groupby(right_vars["age"])
        .agg(
            imm_prov_T=("imm_prov", "sum"),
            em_prov_T=("em_prov", "sum"),
            net_prov_T=("net_prov", "sum"),
            imm_fin_T=("imm_fin", "sum"),
            em_fin_T=("em_fin", "sum"),
            net_fin_T=("net_fin", "sum"),
        )
        .reset_index()
    )

    return merged_df.merge(national_profile, on=right_vars["age"], how="left")
