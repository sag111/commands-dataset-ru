import argparse
import pandas as pd

from pathlib import Path
from pyhocon import ConfigFactory
from sklearn.model_selection import train_test_split

from multiset import MultisetGenerator


pp = Path(__file__).parents[3]


def argument_parser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="Generator for robot commands"
    )

    parser.add_argument('-d', '--data',
                        type=str,
                        default="data/raw/test.csv",
                        help='Path to the file with the generated data')

    return parser.parse_args()


def to_df(commands: dict) -> pd.DataFrame:
    """
    Creates a data set in the form of a Dataframe from a dictionary of generated commands
    :param commands: dictionary of generated commands
    :return:
        Dataframe
    """
    df_values = []
    for i in range(len(commands['text'])):
        txt = commands['text'][i]
        ner = commands['ner'][i]
        vec = commands['vector'][i]

        at_dict = {}
        for key, value in vec.items():
            at_dict[key] = attrs[key][str(value)]

        df_values.append([txt, ner, *list(vec.values())])

    df = pd.DataFrame(df_values, columns=df_columns)
    df = df.drop_duplicates()

    print(df)

    return df


if __name__ == '__main__':
    df_columns = ["x", "ner", "action", "direction", "meters", "degs", "hours", "object1",
                  "nearest", "relation1", "object2", "relation2", "object3", "self", "gaze"]

    args = argument_parser()
    assert args.data

    dp = pp.joinpath('data/dictionary')
    cp = pp.joinpath('configs')

    attrs = ConfigFactory.parse_file(cp.joinpath("attrs.conf"))

    gen = MultisetGenerator(dictionary_path=dp, config_path=cp)

    # patrol commands
    cmds = gen.patrol(amount=4000)
    patrol = to_df(cmds)

    # simple commands - stop, pause, continue
    cmds = gen.simple(amount=500)
    simple = to_df(cmds)

    # turn/move direction commands
    cmds = gen.move_rotate_dir(amount=500)
    move_rotate_dir = to_df(cmds)

    # commands to move in the direction of a given number of meters
    cmds = gen.move_on(amount=200)
    move_on = to_df(cmds)

    # commands to rotate by a given number of degrees
    cmds = gen.rotate_on_degs(amount=50)
    rotate_on_degs = to_df(cmds)

    # clock rotation commands v1
    cmds = gen.rotate_on_hours_fake(amount=50)
    rotate_on_hours_fake = to_df(cmds)

    # clock rotation commands v2
    cmds = gen.rotate_on_hours(amount=50)
    rotate_on_hours = to_df(cmds)

    # commands for interacting with objects - movement, turn, search, detour, etc.
    cmds = gen.objects(amount=35, states=30)
    objects = to_df(cmds)

    final_df = pd.concat((
        patrol,
        simple,
        move_rotate_dir,
        move_on,
        rotate_on_degs,
        rotate_on_hours_fake,
        rotate_on_hours,
        objects
    ))

    # markup on train/valid by action
    train_df = pd.DataFrame()
    valid_df = pd.DataFrame()
    for act in sorted(final_df['action'].unique()):
        train_set, valid_set = train_test_split(final_df[final_df['action'] == act], test_size=0.15, random_state=42)
        train_df = pd.concat((train_df, train_set), axis=0)
        valid_df = pd.concat((valid_df, valid_set), axis=0)

    train_df['fold'] = -1
    train_df['subset'] = 'train'

    valid_df['fold'] = -1
    valid_df['subset'] = 'valid'

    final_df = pd.concat((train_df, valid_df), axis=0)
    final_df = final_df.sample(frac=1, random_state=42)

    save_path = pp.joinpath(args.data)
    final_df.to_csv(save_path, sep=',', index=False)
