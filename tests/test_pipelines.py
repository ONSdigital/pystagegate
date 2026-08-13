from pystagegate.pipelines import prov_fin_main


def test_prov_fin_dict(test_config):
    prov_fin_main(test_config)


def test_prov_fin_path():
    prov_fin_main("tests/data/testing_config.json")
