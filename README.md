# pystagegate
Automated quality assurance methods for demographic outputs. Work in progress.

Contact: Christoffer.Soderberg@ons.gov.uk

## Instuctions

This package uses [uv](https://docs.astral.sh/uv/) for virtual environments and dependency management.

- [Installation](https://docs.astral.sh/uv/getting-started/installation/)
- [Getting started with uv](https://pydevtools.com/handbook/tutorial/getting-started-with-uv/)

### Running the pipeline

Install the package into your Python environment of choice: 
  
  `pip install git+https://github.com/ONSdigital/pystagegate.git`

Download a copy of the [configuration](https://github.com/ONSdigital/pystagegate/blob/main/configuration/pipeline_config.json) and save it to your working directory.

#### Running from the command line

Open your Python environment of choice and in your working directory use the console command `provfin` to run the provisional-final migration data quality assurance pipeline:

```{bash}
provfin pipeline_config.json
```

#### Running in Jupyter Notebooks

Import the `prov_fin_main` function from the `pipelines` module:

```{python}
from pystagegate.pipelines import prov_fin_main
```

Call the function with the filepath to the configuration JSON file as an argument (or pass a Python dictionary):

```{python}
prov_fin_main("pipeline_config.json")
```

See the [demo](https://onsdigital.github.io/pystagegate/demos.html) for more detail.

Pure synthetic data for testing is available in `tests/data`

### Contributing

- `uv sync` to read dependencies
- `uv run pytest` for testing
- `uv run ruff check` and `uv run ruff format` for linting