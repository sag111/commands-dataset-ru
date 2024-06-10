import time
import requests
import argparse

from pathlib import Path


project_path = Path(__file__).resolve().parents[2]
api_url = 'https://api.openai.com/v1/chat/completions'


def arguments_parser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="API for GPT-3.5"
    )

    parser.add_argument('-t', '--token',
                        default='secret-key',
                        type=str,
                        help='File with token')

    parser.add_argument('-m', '--model',
                        default="gpt-3.5-turbo",
                        type=str,
                        help='Model name')

    parser.add_argument('-p', '--prompt',
                        default="cmd_to_json_ru_en",
                        type=str,
                        help='Prompt')

    parser.add_argument('--text',
                        type=str,
                        help='TARGET field')

    return parser.parse_args()


def ask_gpt(token, model, content, sentence):
    """
    Sends a single request within the content prompt of the language model and returns its response,
    without dialog mode support,
    in the original seed "TARGET" is replaced by the value of the sentence variable

    :param token: token from OpenAI API
    :param model: model version used
    :param content: prompt
    :param sentence: expression for substitution into the prompt context
    :return:
        The language model's response to a given prompt
    """
    retries = 0

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(token)
    }

    data = {
        "model": model,
        "temperature": 0.3,
        # "top_p": 0.9,
        # "n": 5,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": content.replace('TARGET', sentence)}
        ]
    }

    # With frequent requests, a 503 code appears:
    # That model is currently overloaded with other requests.
    while retries <= 5:
        response = requests.post(api_url, headers=headers, json=data)

        if response.status_code == 503:
            retries += 1
            time.sleep(1)

        elif response.status_code == 200:
            retries = 10

    try:
        answer = {
            "status": "Code: {}, Status: {}".format(response.status_code, response.reason),
            "message": response.json()['choices'][0]['message']
        }
    except KeyError:
        answer = {
            "status": "Code: {}, Status: {}".format(response.status_code, response.reason),
            "message": response.json()
        }

    return answer


if __name__ == '__main__':
    args = arguments_parser()

    secret_path = project_path.joinpath(f"src/prompt_api/tokens/{args.token}")
    with open(secret_path, 'r') as file:
        tok = file.read()

    prompt_path = project_path.joinpath(f"src/prompt_api/textseeds/{args.prompt}")
    with open(prompt_path, 'r') as file:
        prompt = file.read()

    mes = ask_gpt(tok, args.model, prompt, args.text)

    print(mes)
