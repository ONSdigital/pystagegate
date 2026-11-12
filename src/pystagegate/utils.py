"""Load pipeline configuration and CSV inputs, and optionally export results.

Notes:
    Configuration is not validated on loading. CSV loading selects configured
    columns before invoking :func:`pystagegate.validate.validate`; that check
    does not return coerced data to this module. Exports omit DataFrame indexes
    and are neither transactional nor protected against overwriting files.
"""

import pandas as pd
import json
import os
import warnings
from pystagegate.validate import validate


def load_config(conf_id: str | dict) -> dict:
    """Return a supplied dictionary or decode a JSON file without schema checks.

    Args:
        conf_id (str | dict): An exact built-in ``str`` containing a file path,
            or an exact built-in ``dict``. Subclasses and path-like objects are
            not accepted by the type checks. Relative paths use the current
            working directory.

    Returns:
        dict: The same dictionary object when given a dict, without copying or
        mutation. For a path, returns the decoded JSON value; despite the return
        annotation, its type and required keys are not checked.

    Raises:
        FileNotFoundError: If the supplied string path does not exist.
        ValueError: If the argument is neither an exact str nor an exact dict.
        json.JSONDecodeError: If the file contains invalid JSON.
        OSError: If an existing path cannot be opened or read, including a
            directory path or insufficient permissions.
        UnicodeError: If the file cannot be decoded using the default encoding.

    Notes:
        This function only reads files. It does not resolve data paths relative
        to the configuration file or validate pipeline parameters.
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
    """Read configured CSV columns and validate them as a migration dataset.

    Args:
        config (dict): Requires ``root_path`` and a ``datasets[dataset_key]``
            mapping containing ``path`` and ``variables``. The latter maps
            semantic field names to CSV column names. Also requires the
            dataset-specific variable mappings and ``global_parameters`` keys
            documented by :func:`pystagegate.validate.validate`.
        dataset_key (str): Supported validation dataset name:
            ``final_immigration``, ``final_emigration``, ``provisional`` or
            ``provisional_scot``. A missing dataset entry fails during lookup.

    Returns:
        pd.DataFrame: Newly read table with columns selected in the order of
        ``variables.values()`` and types inferred by ``pandas.read_csv``. The
        validator's coerced copy is discarded, so successful validation does
        not guarantee that the returned table has the schema's target dtypes.

    Raises:
        KeyError: If configuration keys or selected CSV columns are missing.
        OSError: If the CSV cannot be opened or read.
        pandas.errors.ParserError: If CSV parsing fails.
        pandas.errors.EmptyDataError: If the CSV has no columns to parse.
        pandera.errors.SchemaError: If the selected table fails validation.
        UnboundLocalError: If a configured dataset has no supported schema.

    Notes:
        Reads ``os.path.join(root_path, datasets[dataset_key]['path'])`` using
        pandas defaults; relative paths use the current working directory, not
        the config file's directory. Extra CSV columns are discarded before
        strict validation, so they are not rejected. No input object is mutated
        and no files are written. Validation is limited to the documented
        schema checks, not completeness or statistical suitability.
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
    """Optionally write one or more DataFrames as index-free CSV files.

    Args:
        output_path (str): Destination directory. Despite the annotation, None
            disables all work, including validation of ``output_pairs``.
            Relative paths use the current working directory.
        output_pairs (list[tuple[pd.DataFrame, str]] | tuple[pd.DataFrame, str]):
            An exact built-in list of (DataFrame, filename) pairs, or an exact
            built-in tuple holding one such pair. Pair contents and lengths are
            not checked before indexing and calling ``to_csv``. Filenames are
            joined to ``output_path`` without sanitisation or containment checks.

    Returns:
        None: Tables are written for their filesystem effects, not returned.

    Raises:
        ValueError: If output is enabled and ``output_pairs`` is neither an
            exact built-in list nor an exact built-in tuple.
        OSError: If directory creation or CSV writing fails. Parent directories
            inside individual filenames are not created separately.
        IndexError: If a pair has too few elements.
        TypeError: If a supplied path or pair cannot be used as required.
        AttributeError: If a pair's first element has no ``to_csv`` method.

    Notes:
        A missing output directory causes a UserWarning and recursive directory
        creation, even before the pair container is checked. Existing files at
        target paths are overwritten. Files are written sequentially with no
        rollback: earlier files may remain if a later write fails. The supplied
        DataFrames are not modified. ``index=False`` drops all index identifiers;
        MultiIndex columns retain pandas' multi-row CSV header representation.
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
