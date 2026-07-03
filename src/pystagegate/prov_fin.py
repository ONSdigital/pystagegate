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
