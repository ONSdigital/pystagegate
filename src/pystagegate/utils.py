import pandas as pd
import json
import os
import warnings
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

    validate(df, dataset_key, config)

    return df


def write_outputs(
    output_path: str,
    output_pairs: list[tuple[pd.DataFrame, str]] | tuple[pd.DataFrame, str],
) -> None:
    """
    Write output DataFrames to CSV files.

    Args:
        output_path (str): The directory path where the output files will be saved.
        output_pairs (list[tuple[pd.DataFrame, str]] | tuple[pd.DataFrame, str]): A list of tuples or a single tuple
        containing a DataFrame and the corresponding output file name.

    Returns:
        None

    """
    if output_path is not None:
        if not os.path.exists(output_path):
            warnings.warn(
                f"No directory found at {output_path}, writing in new directory {os.path.abspath(output_path)}",
                stacklevel=2,
            )
            os.makedirs(output_path)

        if type(output_pairs) is list:
            for pair in output_pairs:
                pair[0].to_csv(
                    os.path.join(output_path, pair[1]),
                    index=False,
                )
        elif type(output_pairs) is tuple:
            output_pairs[0].to_csv(
                os.path.join(output_path, output_pairs[1]), index=False
            )
        else:
            raise ValueError(
                "Invalid output_pairs. Must be tuple of (pd.DataFrame, str) or list of tuple of (pd.DataFrame, str)"
            )
