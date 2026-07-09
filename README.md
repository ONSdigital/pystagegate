# pystagegate
Automated quality assurance methods for demographic outputs

## Instuctions

This package uses [uv](https://docs.astral.sh/uv/) for virtual environments and dependency management.

- [Installation](https://docs.astral.sh/uv/getting-started/installation/)
- [Getting started with uv](https://pydevtools.com/handbook/tutorial/getting-started-with-uv/)

### Running the pipeline

1. Install uv `pipx install uv`
2. `cd` to project directory
3. Ensure you have a `testing_config.json` file located at the top level of the directory
4. `uv run pystagegate` to run all available pipelines

## Contributing

- `uv sync` to read dependencies
- `uv run pytest` for testing
- `uv run ruff check .` and `uv run ruff format .` for linting