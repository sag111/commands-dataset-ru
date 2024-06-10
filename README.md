# commands-dataset-ru
Dataset for parsing texts of robot control commands in russian language

## Dataset

Dataset size 59973 rows and 18 columns.

Train / Valid / Test examples are 49365 / 8719 / 1889.
 
Dataset locates in [data/raw/dataset.csv](data/raw/dataset.csv). It consists of following columns:

| Columns      | About                                        |
|--------------|----------------------------------------------|
| x            | input text on Russian                        |
| output_text  | output text for text-to-text                 |
| ner          | output text for ner                          |
| fold         | fold numbers, -1 is training                 |
| subset       | possible values are `train`, `valid`, `test` |
| action, etc. | output values for classification             |

File [data/raw/attributes.csv](data/raw/attributes.conf) consist of numerical and text values of formalized attributes.

## Prompts

Directory [data/prompts](data/prompts) includes different prompts for Few-Shot prompting approach.

| File                     | About                                    |
|--------------------------|------------------------------------------|
| cmd_to_json_general      | file for generate classes and attributes |
| action, object, relation | files for incorrect attributes           |

## Code

Requirements: Python 3.10

#### Installation
```shell
pip install -r requirements.txt
```

#### Converter from vector to output text sequences

```shell
python src/commands_dataset/data/text2text_converter.py --data path_to_dataset.csv
```

#### Generator

```shell
python src/commands_dataset/generator/main.py
```

#### Few-Shot Prompting

```shell
python src/commands_dataset/prompt_api/promp_eval.py --token token_file
```