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
        pd.DataFrame: A pandas DataFrame containing the filtered and preprocessed data.
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
    Create squared difference estimates for immigration or emigration
    data using provisional and final estimates.

    Args:
        df (pd.DataFrame): The input DataFrame.
        prov_col (str): The provisional estimate column name.
        fin_col (str): The final estimate column name.

    Returns:
        pd.DataFrame: A pandas DataFrame containing the difference
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
    Docstrings here
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
    region: str = None,
) -> pd.DataFrame:
    """
    Docstrings here
    """
    imm_prefix = check_prefix(imm_prov, imm_fin)
    em_prefix = check_prefix(em_prov, em_fin)
    net_prefix = check_prefix(net_prov, net_fin)

    if region is None:
        aggr = (
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

        aggr = df.merge(
            aggr,
            on="Age",
            how="left",
            suffixes=("", "_T"),
        )
    else:
        if region in ["W", "S", "E"]:
            aggr = (
                df[df["Nation"] == region]
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

            aggr = df[df["Nation"] == region].merge(
                aggr,
                on="Age",
                how="left",
                suffixes=("", "_T"),
            )
        else:
            raise (ValueError("Region must be one of 'E', 'S', 'W'"))

    aggr = squared_difference(aggr, imm_prefix, imm_prov, imm_fin)
    aggr = squared_difference(aggr, em_prefix, em_prov, em_fin)
    aggr = squared_difference(aggr, net_prefix, net_prov, net_fin)

    aggr = (
        aggr.groupby("Local Authority Code")
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

    return aggr
