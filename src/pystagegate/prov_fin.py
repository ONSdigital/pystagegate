import pandas as pd


def load_summary_data(
    path: str,
    age_var: str,
    age_min: int,
    age_max: int,
    lan_var: str = None,
    date_var: str = None,
) -> pd.DataFrame:
    """
    Load and preprocess summary data from a CSV file.

    Args:
        path (str): The file path to the CSV file.
        age_var (str): The name of the age variable column.
        age_min (int): The minimum age for filtering the data.
        age_max (int): The maximum age for filtering the data.
        lan_var (str, optional): The name of the language variable column to drop. Defaults to None.
        date_var (str, optional): The name of the date variable column to drop. Defaults to None.

    Returns:
        df (pd.DataFrame): A pandas DataFrame containing the filtered and preprocessed data.
    """
    df = pd.read_csv(path)
    df = df[df[age_var].between(age_min, age_max)]

    if lan_var:
        if lan_var in df.columns:
            df = df.drop(columns=[lan_var])

    if date_var:
        if date_var in df.columns:
            df = df.drop(columns=[date_var])

    return df


def squared_difference(
    df: pd.DataFrame, prefix: str, prov_col: str, fin_col: str
) -> pd.DataFrame:
    """
    Create squared difference estimates for migration data using provisional and final estimates.

    Args:
        df (pd.DataFrame): The input migration DataFrame.
        prov_col (str): The provisional estimate column name.
        fin_col (str): The final estimate column name.

    Returns:
        df (pd.DataFrame): A pandas DataFrame containing the difference
        and squared difference estiamtes.
    """

    df[f"diff_{prefix}"] = (df[fin_col] - df[prov_col]) - (
        (df[prov_col] * df[f"{fin_col}_T"] / df[f"{prov_col}_T"]) - (df[prov_col])
    )

    df[f"sqdiff_{prefix}"] = (df[f"diff_{prefix}"] ** 2).where(
        df[f"{prov_col}_T"] != 0, 0
    )

    return df


def check_prefix(prov: str, fin: str) -> str:
    """
    Checks if prefixes of supplied provisional and final column names match and returns the prefix.

    Args:
        prov (str): The provisional column name.
        fin (str): The final column name.

    Returns:
        prefix (str): The common prefix of the two column names.
    """
    if prov.split("_", 1)[0] == fin.split("_", 1)[0]:
        prefix = prov.split("_", 1)[0]

        return prefix
    else:
        raise (
            ValueError(
                f"Provisional and final columns do not match for {prov} and {fin}"
            )
        )


def regional_breakdown(
    df: pd.DataFrame,
    imm_prov: str,
    imm_fin: str,
    em_prov: str,
    em_fin: str,
    net_prov: str,
    net_fin: str,
    nation: str = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Performs aggregations by Age and Local Authority on both a whole country (GB) profile and nation profile.

    Args:
        df (pd.DataFrame): The input migration DataFrame.
        imm_prov (str): The provisional immigration estimate column name.
        imm_fin (str): The final immigration estimate column name.
        em_prov (str): The provisional emigration estimate column name.
        em_fin (str): The final emigration estimate column name.
        net_prov (str): The provisional net migration estimate column name.
        net_fin (str): The final net migration estimate column name.
        nation (str, optional): A one letter code for nation, must be one of 'E', 'S', 'W'. Defaults to None for GB analysis.

    Returns:
        tuple:
            - age_agg (pd.DataFrame): Migration data aggregated by age.
            - la_agg (pd.DataFrame): Migration data aggregated by age and local authority.
    """
    imm_prefix = check_prefix(imm_prov, imm_fin)
    em_prefix = check_prefix(em_prov, em_fin)
    net_prefix = check_prefix(net_prov, net_fin)

    if nation is None:
        age_agg = (
            df.groupby("Age")
            .agg(
                {
                    imm_prov: "sum",
                    em_prov: "sum",
                    net_prov: "sum",
                    imm_fin: "sum",
                    em_fin: "sum",
                    net_fin: "sum",
                }
            )
            .reset_index()
        )

        age_agg = df.merge(
            age_agg,
            on="Age",
            how="left",
            suffixes=("", "_T"),
        )
    else:
        if nation in ["W", "S", "E"]:
            age_agg = (
                df[df["Nation"] == nation]
                .groupby("Age")
                .agg(
                    {
                        imm_prov: "sum",
                        em_prov: "sum",
                        net_prov: "sum",
                        imm_fin: "sum",
                        em_fin: "sum",
                        net_fin: "sum",
                    }
                )
                .reset_index()
            )

            age_agg = df[df["Nation"] == nation].merge(
                age_agg,
                on="Age",
                how="left",
                suffixes=("", "_T"),
            )
        else:
            raise (ValueError("Nation must be one of 'E', 'S', 'W'"))

    age_agg = squared_difference(age_agg, imm_prefix, imm_prov, imm_fin)
    age_agg = squared_difference(age_agg, em_prefix, em_prov, em_fin)
    age_agg = squared_difference(age_agg, net_prefix, net_prov, net_fin)

    la_agg = (
        age_agg.groupby("Local Authority Code")
        .agg(
            {
                imm_prov: "sum",
                em_prov: "sum",
                net_prov: "sum",
                f"sqdiff_{imm_prefix}": "sum",
                f"sqdiff_{em_prefix}": "sum",
                f"sqdiff_{net_prefix}": "sum",
            }
        )
        .reset_index()
    )

    for prefix in [imm_prefix, em_prefix, net_prefix]:
        la_agg[f"sqdiff_{prefix}_sc"] = (
            la_agg[f"sqdiff_{prefix}"] / la_agg[f"{prefix}_Prov"]
        )

    for frame in [age_agg, la_agg]:
        frame["Nation"] = frame["Local Authority Code"].str[0]

    return age_agg, la_agg
