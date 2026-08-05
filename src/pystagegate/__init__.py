import argparse
from pystagegate.pipelines import prov_fin_main


def run_prov_fin() -> None:
    parser = argparse.ArgumentParser(
        description="Run provisional-final migration quality assurance pipeline"
    )
    parser.add_argument("config", type=str, help="Path to the config file")
    args = parser.parse_args()

    prov_fin_main(args.config)
