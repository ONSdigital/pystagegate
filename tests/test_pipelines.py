import pandas as pd
import os
from pystagegate.pipelines import prov_fin_main


def test_prov_fin_dict(test_config):
    output = prov_fin_main(test_config)

    expected_output = pd.read_csv(os.path.join(test_config["prov_fin"]["root_path"], "prov_fin_output.csv"))

    pd.testing.assert_frame_equal(output, expected_output)


def test_prov_fin_path(test_config):
    output = prov_fin_main("tests/data/testing_config.json")

    expected_output = pd.read_csv(os.path.join(test_config["prov_fin"]["root_path"], "prov_fin_output.csv"))

    pd.testing.assert_frame_equal(output, expected_output)
