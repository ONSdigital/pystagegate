from sdv.single_table import GaussianCopulaSynthesizer
from sdv.metadata import Metadata
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


def _generate_synth_df(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """
    Return a synthetic DataFrame produced from a DataFrame reference.

    Args:
        df (pd.DataFrame): The input DataFrame.
        n (int): Number of rows to return.

    Returns:
        synth_df (pd.DataFrame)
    """

    metadata = Metadata.detect_from_dataframes(data={"real data": df})

    synthesizer = GaussianCopulaSynthesizer(metadata)
    synthesizer.fit(data=df)

    return synthesizer.sample(num_rows=n)
