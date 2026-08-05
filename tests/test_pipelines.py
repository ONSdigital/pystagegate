from pystagegate import pipelines


def test_prov_fin_dict(test_pipeline_config):
    pipelines.prov_fin_main(test_pipeline_config)


def test_prov_fin_path():
    pipelines.prov_fin_main("tests/data/testing_config.json")
