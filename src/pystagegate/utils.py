from sdv.single_table import GaussianCopulaSynthesizer
from sdv.metadata import Metadata
import pandas as pd
import numpy as np
import json
import os
from pystagegate.validate import validate


def load_config(conf_id: str | dict) -> dict:
    """
    Load a JSON configuration file.

    Args:
        conf_id (str | dict): The file path to a JSON file or a dict object

    Returns:
        config (dict): Configuration dictionary.
    """
    if type(conf_id) is str:
        if os.path.exists(conf_id):
            with open(conf_id, "r") as f:
                config = json.load(f)
            return config
        else:
            raise FileNotFoundError(f"Config file not found: {conf_id}")
    elif type(conf_id) is dict:
        return conf_id
    else:
        raise ValueError("Invalid config type. Must be str or dict.")


def load_summary_data(config: dict, dataset_key: str) -> pd.DataFrame:
    """
    Load and validate summary data from a CSV file.

    Args:
        config (dict): A dictionary configuration.
        dataset (str): A string key value for the dataset to load.

    Returns:
        df (pd.DataFrame): A pandas DataFrame containing the selected data.
    """
    path = os.path.join(config["root_path"], config["datasets"][dataset_key]["path"])
    variables = config["datasets"][dataset_key]["variables"]

    df = pd.read_csv(path)[variables.values()]

    validation_results = validate(df, dataset_key, config)

    if config["output_path"] is not None:
        if not os.path.exists(config["output_path"]):
            os.makedirs(config["output_path"])

        with open(
            os.path.join(config["output_path"], f"{dataset_key}_validate.json"), "w"
        ) as f:
            json.dump(validation_results.to_json_dict(), f, indent=4)

    return df


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
