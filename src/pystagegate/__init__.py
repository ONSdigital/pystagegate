import argparse
from pystagegate.pipelines import prov_fin_main, sex_ratio_main, national_profile


def run_prov_fin() -> None:
    parser = argparse.ArgumentParser(
        description="Run provisional-final migration quality assurance pipeline"
    )
    parser.add_argument("config", type=str, help="Path to the config file")
    args = parser.parse_args()

    prov_fin_main(args.config)


def run_sex_ratio() -> None:
    parser = argparse.ArgumentParser(
        description="Run sex-ratio migration quality assurance pipeline"
    )
    parser.add_argument("config", type=str, help="Path to the config file")
    args = parser.parse_args()

    sex_ratio_main(args.config)


def run_national_profile() -> None:
    parser = argparse.ArgumentParser(
        description="Run national profile migration quality assurance pipeline"
    )
    parser.add_argument("config", type=str, help="Path to the config file")
    args = parser.parse_args()

    national_profile(args.config)
