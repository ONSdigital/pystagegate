# Configuration Guidance

A valid configuration file is an essential component of pystagegate. It is the only way for the package to connect to data sources and select the correct variable names from those data sources.

A template of the configuration file is always on GitHub. You download it [here.](https://github.com/ONSdigital/pystagegate/blob/main/configuration/pipeline_config.json)

The JSON is shown below:

::: {admonition} Click here to see the JSON configuration file
:class: dropdown
:name: json-config

```json
{
    "prov_fin": {
        "root_path": "",
        "output_path": null,
        "global_parameters": {
            "age_min": 0,
            "age_max": 200,
            "year": 2024,
            "final_nationalities": ["", "", ""],
            "provisional_scot_direction": ["", ""]
        },
        "datasets": {
            "final_immigration": {
                "path": "",
                "variables": {
                    "la_code": "",
                    "age": "",
                    "sex": "",
                    "nationality": "",
                    "year": "",
                    "count": ""
                }
            },
            "final_emigration": {
                "path": "",
                "variables": {
                    "la_code": "",
                    "age": "",
                    "sex": "",
                    "nationality": "",
                    "year": "",
                    "count": ""
                }
            },
            "provisional": {
                "path": "",
                "variables": {
                    "la_code": "",
                    "age": "",
                    "sex": "",
                    "immigration": "",
                    "emigration": "",
                    "net": ""
                }
            },
            "provisional_scot": {
                "path": "",
                "variables": {
                    "la_code": "",
                    "age": "",
                    "sex": "",
                    "direction": "",
                    "year": "",
                    "count": ""
                }
            }
        }
    }
}
```
:::

## Provisional-Final Configuration

The provisional final configuration is accessed using the `prov-fin` key.

Within `prov-fin` we can access:

| Key | Value |
|-----|-------|
| `root_path` | An optional directory that is appended to all other file paths to simplify the configuration |
| `output_path` | An optional directory used to write output files, can be set to `null` to disable writing outputs |
| `global_parameters` | A dictionary for setting parameters for the entire pipeline |
| `datasets` | A dictionary containing configuration specific to individual datasets |

### Global Parameters

Within `global_parameters` we can access:

| Key | Value |
|-----|-------|
| `age_min` | The lower bound of age to perform the analysis on. Must be an integer |
| `age_max` | The upper bound of age to perform the analysis on. Must be an integer |
| `year` | The year to perform the analysis on. Must be an integer |
| `final_nationalities` | String array stating the nationality categories contained in both final migration datasets. Must be ordered such that the 'all nationalities' category takes position 0. E.g., `["All Nationality", "British", "Non-British"]` |
| `provisional_scot_direction` | String array stating the direction categories from the provisional Scottish migration data. Must be ordered so that the immigration category takes position 0 and the emigration category takes position 1. E.g., `["in", "out"]` |


### Datasets

Within `datasets` we can access:

| Key | Value |
|-----|-------|
| `final_immigration` | A dictionary for configuration specific to the final immigration dataset |
| `final_emigration` | A dictionary for configuration specific to the final emigration dataset |
| `provisional` | A dictionary for configuration specific to the provisional migration dataset |
| `provisional_scot` | A dictionary for configuration specific to the Scottish additional provisional migration data |

### Dataset-Specific Configuration

Within each dataset-specific configuration we have the two keys:

- `path`: The path to the dataset. This can be either a shortened path appended to `root_path` or the entire path if `root_path` is left empty.
- `variables`: The list of variable names required from the dataset to run the pipeline.

#### Final Immigration / Final Emigration (`final_immigration`/`final_emigration`)

Final migration estimates by Local Authority geography, age, sex, nationality status and year.

The final migration data is ingested seperately as two datasets for immigration and emigration and joined during the pipeline.

The final migration datasets `final_immigration` and `final_migration` share the same set of required variable names, but they can be named differently between the two datasets.

| Key | Value | Column Description |
|-----|-------|-------------|
| `la_code` | String value to index the geography column for the Local Authority Code | This column must be recognised in Pandas as a string |
| `age` | String value to index the column for age | This column must be recognised in Pandas as an integer |
| `sex` | String value to index the column for sex | This column must take the values `"Male"` or `"Female"` |
| `nationality` | String value to index the column for migrant nationality | This column must take the values given in Global Parameters - `final_nationalities` |
| `year` | String value to index the column for year data was collected | This column must be recognised in Pandas as an integer |
| `count` | String value to index the column for the final estimate of migration at a given geography, age, sex and nationality | This column must be recognised in Pandas as an integer or floating point |

#### Provisional Migration (`provisional`)

Provisional migration estimates by Local Authority geography, age, sex, nationality status and year.

| Key | Value | Column Description |
|-----|-------|-------------|
| `la_code` | String value to index the geography column for the Local Authority Code | This column must be recognised in Pandas as a string |
| `age` | String value to index the column for age | This column must be recognised in Pandas as an integer |
| `sex` | String value to index the column for sex | This column must be recognised in Pandas as a string |
| `immigration` | String value to index the column for the provisional estimate of immigration at a given geography, age, sex and nationality | This column must be recognised in Pandas as an integer or floating point |
| `emigration` | String value to index the column for the provisional estimate of emigration at a given geography, age, sex and nationality | This column must be recognised in Pandas as an integer or floating point |
| `net` | `immigration` - `emigration` | This column must be recognised in Pandas as an integer or floating point |

#### Scottish Provisional Migration (`provisional_scot`)

Additional provisional migration estimates for Local Authority geographies in Scotland only.

| Key | Value | Description |
|-----|-------|-------------|
| `la_code` | String value to index the geography column for the Local Authority Code | This column must be recognised in Pandas as a string |
| `age` | String value to index the column for age | This column must be recognised in Pandas as an integer |
| `sex` | String value to index the column for sex | This column must be recognised in Pandas as a string |
| `direction` | String value to index the column that states if the row refers to immigration or emigration | This column must take the values given in Global Parameters - `provisional_scot_direction` |
| `year` | String value to index the column for year data was collected | This column must be recognised in Pandas as an integer |
| `count` | String value to index the column for the provisional estimate migration at a given geography, age, sex and nationality | This column must be recognised in Pandas as an integer or floating point |