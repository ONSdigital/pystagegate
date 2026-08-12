import pytest
from pystagegate.utils import load_config


@pytest.fixture
def test_pipeline_config():
    config = load_config("tests/data/testing_config.json")
    return config
