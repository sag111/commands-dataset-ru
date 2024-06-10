import json
import argparse
import pandas as pd

from tqdm import tqdm
from pathlib import Path
from pyhocon import ConfigFactory


project_path = Path(__file__).resolve().parents[3]


def argument_parser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="Preparing data in csv format for text2text models"
    )

    parser.add_argument("-d", "--data",
                        type=str,
                        help="Data set")

    parser.add_argument("-s", "--sep",
                        type=str,
                        default=",",
                        help="Separator in data set")

    parser.add_argument('-v', '--version',
                        type=str,
                        choices=["json", "flat"],
                        help="Markup version")

    return parser.parse_args()


def get_version_flat(data: pd.DataFrame, save_path: Path = None) -> pd.DataFrame:
    """
    Creates a text2text dataset in the following format

    осмотри камень что неподалеку от холма ->
    action monitor. object1 rock. relation1 near. object2 hill

    :param data: Dataframe
    :param save_path: saving path
    :return:
        Dataframe with columns input_text, output_text, subset, fold
    """
    config_path = project_path.joinpath("configs/attrs.conf")
    config = ConfigFactory.parse_file(config_path)

    columns = ["x", "fold", "subset", "action", "direction", "meters", "degs", "hours", "object1", "nearest",
               "relation1", "object2", "relation2", "object3", "self", "gaze"]

    data = data[columns]

    vector = data.columns[3:]

    input_text = []
    output_text = []
    for row in tqdm(data.values):
        flat_like = []
        vector_dict = dict(zip(vector, row[3:]))
        for key, val in vector_dict.items():
            config_value = config[key][str(val)]
            if config_value:
                flat_like.append("{} {}".format(key, config_value))

        input_text.append(row[0])
        output_text.append(". ".join(flat_like))

    data_df_json = pd.DataFrame({
        "input_text": input_text,
        "output_text": output_text,
        "subset": data["subset"],
        "fold": data["fold"]
    })

    if save_path:
        save_to = project_path.joinpath(save_path)
        data_df_json.to_csv(save_to, sep=',', index=False)

    return data_df_json


def get_version_json(data: pd.DataFrame, save_path: Path = None) -> pd.DataFrame:
    """
    Creates a text2text dataset in json format

    осмотри камень что неподалеку от холма ->
    {"action": "monitor", "object1": "rock", "relation1": "near", "object2": "hill"}

    :param data: Dataframe
    :param save_path: saving path
    :return:
        Dataframe with columns input_text, output_text, subset, fold
    """
    config_path = project_path.joinpath("configs/attrs.conf")
    config = ConfigFactory.parse_file(config_path)

    columns = ["x", "fold", "subset", "action", "direction", "meters", "degs", "hours", "object1", "nearest",
               "relation1", "object2", "relation2", "object3", "self", "gaze"]

    data = data[columns]

    vector = data.columns[3:]

    input_text = []
    output_text = []
    for row in tqdm(data.values):
        json_like = {}
        vector_dict = dict(zip(vector, row[3:]))
        for key, val in vector_dict.items():
            config_value = config[key][str(val)]
            if config_value:
                json_like[key] = config_value

        input_text.append(row[0])
        output_text.append(json.dumps(json_like))

    data_df_json = pd.DataFrame({
        "input_text": input_text,
        "output_text": output_text,
        "subset": data["subset"],
        "fold": data["fold"]
    })

    if save_path:
        save_to = project_path.joinpath(save_path)
        data_df_json.to_csv(save_to, sep=',', index=False)

    return data_df_json


if __name__ == '__main__':
    args = argument_parser()

    data_path = project_path.joinpath(args.data)
    df = pd.read_csv(data_path, sep=args.sep)

    interim_path = project_path.joinpath("data/interim")
    interim_path.mkdir(parents=True, exist_ok=True)

    if args.version == "json":
        save = interim_path.joinpath(data_path.stem + "_json.csv")
        get_version_json(df, save)
    elif args.version == "flat":
        save = interim_path.joinpath(data_path.stem + "_flat.csv")
        get_version_flat(df, save)
