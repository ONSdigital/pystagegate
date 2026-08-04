from pystagegate import pipelines


def test_prov_fin(test_pipeline_config):
    pipelines.prov_fin_main(test_pipeline_config)
