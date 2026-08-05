from sdv.single_table import GaussianCopulaSynthesizer
from sdv.metadata import Metadata
import pandas as pd
import numpy as np
import json
import os


def load_config(path: str) -> dict:
    """
    Load a JSON configuration file.

    Args:
        path (str): The file path to the JSON file.

    Returns:
        config (dict): The loaded JSON configuration as a dictionary.
    """
    with open(path, "r") as f:
        config = json.load(f)
    return config


def join_paths(root: str, paths: dict) -> dict:
    """
    Join the folder root from the config to a dict of paths from the config

    Args:
        root (str): The root value from the config.
        paths (dict): A paths value from the config.

    Returns:
        joined_paths (dict): A new dict with the joined root and path values.
    """
    joined_paths = {}

    for key in paths:
        joined_path = os.path.join(root, paths[key])
        joined_paths.update({key: joined_path})

    return joined_paths


def _generate_synth_df(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """
    Return a synthetic DataFrame produced from a DataFrame reference.

    Args:
        df (pd.DataFrame): The input DataFrame.
        n (int): Number of rows to return.

    Returns:
        synth_df (pd.DataFrame): A synthetic DataFrame modelled from df
    """

    metadata = Metadata.detect_from_dataframes(data={"real data": df})

    synthesizer = GaussianCopulaSynthesizer(metadata, default_distribution="norm")
    synthesizer.fit(data=df)

    synth_data = synthesizer.sample(num_rows=n)

    if "Local Authority Code" in synth_data.columns:
        synth_data["Local Authority Code"] = np.random.choice(
            a=["E1", "E2", "E3", "E4", "S1", "S2", "S3", "W1", "W2"],
            size=len(synth_data),
        )

        print(synth_data["Local Authority Code"])

    if "code" in synth_data.columns:
        synth_data["code"] = np.random.choice(
            a=["E1", "E2", "E3", "E4", "W1", "W2"], size=len(synth_data)
        )

        print(synth_data["code"])

    if "ca_code" in synth_data.columns:
        synth_data["ca_code"] = np.random.choice(
            a=["S1", "S2", "S3"], size=len(synth_data)
        )

    if "Age" in synth_data.columns:
        synth_data["Age"] = np.random.choice(
            a=[20, 30, 40, 50, 60], size=len(synth_data), p=[0.2, 0.4, 0.2, 0.1, 0.1]
        )

    return synth_data
