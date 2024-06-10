"""
Assessing the accuracy of RDF commands using text-based language model interaction (prompt)
This method uses two seeds:
1. Composes a JSON file for the source command
2. Maps object key values to object classes defined in the robotic environment
"""
import re
import json
import argparse
import pandas as pd

from pathlib import Path
from pyhocon import ConfigFactory

from translate import ask_gpt
from logger import logger

project_path = Path(__file__).resolve().parents[3]

# logger
log_path = project_path.joinpath('log/eval/prompt_api')
log_path.mkdir(parents=True, exist_ok=True)
log, _ = logger(log_path, stream_level="DEBUG")

# attribute dictionary
attr_path = project_path.joinpath("configs/attrs_inverse.conf")
attr = ConfigFactory.parse_file(attr_path)

action_classes = [
    "patrol", "stop", "move_dir", "rotate_dir", "move_on", "rotate_on", "move_to", "find", "go_around", "monitor",
    "rotate_to", "pause", "continue", "analyze", "follow"
]

object_classes = [
    "house", "tree", "broken_tree", "forest", "pit", "human", "hill", "fissure", "man_lay", "rock", "butte", "barrier",
    "lamp_post", "car", "route", "circle"
]

relation_classes = [
    "near", "behind_of", "in_front_of", "to_left_from", "to_right_from", "to_north_from", "to_south_from",
    "to_east_from", "to_west_from"
]


def arguments_parser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="Accuracy rating for prompting"
    )

    parser.add_argument('--test',
                        default='data/raw/test.csv',
                        type=str,
                        help='Path to test data')

    parser.add_argument('--sep',
                        default=',',
                        type=str,
                        help='Data separator')

    parser.add_argument('--token',
                        type=str,
                        help='File with token for openai api')

    parser.add_argument('--model',
                        default='gpt-3.5-turbo',
                        type=str,
                        help='Language model name')

    parser.add_argument('--prompts',
                        default='data/prompts',
                        type=str,
                        help='The path to the prompts')

    return parser.parse_args()


if __name__ == '__main__':
    args = arguments_parser()

    # read token
    token_path = project_path.joinpath(args.token)
    with open(token_path, 'r') as file:
        token = file.read()

    log.debug("Token loaded")

    prompt_path = project_path.joinpath(args.prompts)

    # prompt for generating json
    prompt = 'cmd_to_json_ru_general'
    json_prompt_path = prompt_path.joinpath(prompt)
    with open(json_prompt_path, 'r') as file:
        json_prompt = file.read()

    log.debug("Json prompt loaded")

    # prompt for forming object classes
    object_prompt_path = prompt_path.joinpath('object')
    with open(object_prompt_path, 'r') as file:
        object_prompt = file.read()

    log.debug("Prompt object loaded")

    # prompt for forming relationship classes
    relation_prompt_path = prompt_path.joinpath('relation')
    with open(relation_prompt_path, 'r') as file:
        relation_prompt = file.read()

    log.debug("Prompt relation loaded")

    # prompt for forming action classes
    action_prompt_path = prompt_path.joinpath('action')
    with open(action_prompt_path, 'r') as file:
        action_prompt = file.read()

    log.debug("Prompt action loaded")

    # loading test
    test_path = project_path.joinpath(args.test)
    data = pd.read_csv(test_path, sep=args.sep)
    # data = data.sample(frac=1)

    log.debug("Test data set loaded")

    # extract json from language model response
    translation_pattern = re.compile(r'Translation: (.*)')
    json_pattern = pat2 = re.compile(r'JSON: (.*)')

    # Class highlighting and explanation
    class_pattern = re.compile(r'Class: (.*)')
    explanation_pattern = re.compile(r'Explanation: (.*)')

    save_path = project_path.joinpath('data/processed/gpt-3.5')
    save_path.mkdir(parents=True, exist_ok=True)

    out_data = pd.DataFrame(columns=['sentence', 'mes1', 'mes2', 'mes3', 'mes4', 'translation', 'json', 'action',
                                     'a_explain', 'object1', 'o_explain1', 'object2', 'o_explain2', 'object3',
                                     'o_explain3', 'relation1', 'r_explain1', 'relation2', 'r_explain2'],
                            index=range(len(data['x'])))

    for i, text in enumerate(data['x']):
        log.info("Sentence {}: {}".format(i, text))
        # request the command in json form
        res1 = ask_gpt(token, args.model, json_prompt, text)
        log.debug(res1['status'])

        mes1 = res1['message']
        out_data['mes1'].loc[i] = mes1
        log.debug(mes1)

        # Translation into English
        translation = translation_pattern.findall(mes1['content'])[0]
        translation = re.sub(r'[.,"\'-?:!;]', '', translation)
        log.info("Translation: {}".format(translation))

        # json command form
        cmd_json = json_pattern.findall(mes1['content'])[0]

        log.info("JSON: {}".format(cmd_json))

        out_data['sentence'].loc[i] = text
        out_data['translation'].loc[i] = translation
        # out_data['json'].loc[i] = json.dumps(cmd_json)

        try:
            cmd_json = json.loads(cmd_json)
        except json.decoder.JSONDecodeError as e:
            log.error(e)
            continue

        for k, v in cmd_json.items():

            if v is None:
                continue

            # if object values are not contained in the class list
            if "object" in k and k in ["object1", "object2", "object3"] and v not in object_classes:
                res2 = ask_gpt(token, args.model, object_prompt, v)
                log.debug(res2['status'])

                mes2 = res2['message']
                out_data['mes2'].loc[i] = mes2
                log.debug(mes2)

                # object class
                object_cls = class_pattern.findall(mes2['content'])[0]
                log.info('{} {} class: {}'.format(k, v, object_cls))

                # explanation of class selection
                object_explain = explanation_pattern.findall(mes2['content'])[0]
                log.info('Explanation: {}'.format(object_explain))

                out_data[k].loc[i] = "{}.{}".format(cmd_json[k], object_cls)
                out_data[f"o_explain{k[-1]}"].loc[i] = object_explain

                # update json according to classes
                cmd_json[k] = object_cls

            # if relation values are not contained in the class list
            elif "relation" in k and k in ["relation1", "relation2"] and v not in relation_classes:
                res3 = ask_gpt(token, args.model, relation_prompt, v)
                log.debug(res3['status'])

                mes3 = res3['message']
                out_data['mes3'].loc[i] = mes3
                log.debug(mes3)

                # relation class
                relation_cls = class_pattern.findall(mes3['content'])[0]
                log.info('{} {} class: {}'.format(k, v, relation_cls))

                # explanation of class selection
                relation_explain = explanation_pattern.findall(mes3['content'])[0]
                log.info('Explanation: {}'.format(relation_explain))

                out_data[k].loc[i] = "{}.{}".format(cmd_json[k], relation_cls)
                out_data[f"r_explain{k[-1]}"].loc[i] = relation_explain

                cmd_json[k] = relation_cls

            # if action values are not contained in the class list
            elif "action" in k and k in ["action"] and v not in action_classes:
                res4 = ask_gpt(token, args.model, action_prompt, v)
                log.debug(res4['status'])

                mes4 = res4['message']
                out_data['mes4'].loc[i] = mes4
                log.debug(mes4)

                # action class
                action_cls = class_pattern.findall(mes4['content'])[0]
                log.info('{} {} class: {}'.format(k, v, action_cls))

                # explanation of class selection
                action_explain = explanation_pattern.findall(mes4['content'])[0]
                log.info('Explanation: {}'.format(action_explain))

                out_data[k].loc[i] = '{}.{}'.format(cmd_json[k], action_cls)
                out_data['a_explain'].loc[i] = action_explain

                cmd_json[k] = action_cls

        out_data['json'].loc[i] = json.dumps(cmd_json)
        log.debug(out_data.loc[i].values)

        out_data.to_csv(save_path.joinpath(f"{prompt}_out.csv"), sep=',', index=False)
