import pandas as pd
import json


def filler(df: pd.DataFrame) -> pd.DataFrame:
    """Filler function for testing autodoc

    Args:
        df: A pandas DataFrame.

    Returns:
        A pandas DataFrame.
    """

    return df


def load_config(path: str) -> dict:
    """Load a JSON configuration file.

    Args:
        path (str): The file path to the JSON file.

    Returns:
        dict: The loaded JSON configuration as a dictionary.
    """
    with open(path, "r") as f:
        config = json.load(f)
    return config
