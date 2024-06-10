import random
import re

import pymorphy2

from pathlib import Path
from pyhocon import ConfigFactory


class Generator:
    def __init__(self, dictionary_path: Path, config_path: Path):
        self.attr_config = ConfigFactory.parse_file(config_path.joinpath("attrs_inverse.conf"))
        self.hours_config = ConfigFactory.parse_file(config_path.joinpath("hours.conf"))
        self.dictionary_path = dictionary_path
        self.dictionary_files = self.dictionary_path.glob("**/*/*")
        self.dictionary = self.create_dictionary()
        self.morph = pymorphy2.MorphAnalyzer()
        self.key_pattern = re.compile(r'\w+@[^| ]+')
        self.word_pattern = re.compile(r'([\w\s-]+)')

    def create_dictionary(self) -> dict:
        """
        Creates a dictionary
        The key is the path to the file with words, example action:move, object:house
        Value - contents of a file with words in the form of a list
        :return
            {
                "action:move": ["идти", "двигаться", "направляться"],
                "object:house": ["дом", "изба", "строение"],
                ...
            }
        """
        dictionary = {}
        for path_to_file in self.dictionary_files:
            key = '@'.join(path_to_file.parts[-2:])
            with open(path_to_file, 'r') as values_file:
                value = values_file.read()
                value = value.strip()
                value = value.split('\n')

            dictionary[key] = value

        return dictionary

    def get_keys(self, dictionary_name: str) -> list:
        """
        Creates a list of all keys for a specific dictionary

        :param dictionary_name: Name of the directory with dictionary files inside
        :return:
            ['action:move', 'action:rotate', ... ]
        """
        pattern = f'**/{dictionary_name}/*'
        key_path = list(self.dictionary_path.glob(pattern))
        keys = list(map(lambda x: '@'.join(x.parts[-2:]), key_path))

        return keys

    def inflect(self, words: str, grammes: set) -> str:
        """
        Converts a word according to grammes (http://opencorpora.org/dict.php?act=gram)

        :param words: word/words in normal form, example: "идти"
        :param grammes: the set of grammes, example: {'excl'}
        :return:
            Inflected word: "идти", {'excl'} -> "иди"
        """
        morphed = []
        words = words.split(" ")

        # If there are several words, then all words are declined into the gender of the noun
        if len(words) > 1:
            idx = list(map(lambda x: self.morph.parse(x)[0].tag.POS, words)).index('NOUN')
            noun_parsed = self.morph.parse(words[idx])[0]
            gender = noun_parsed.tag.gender
            animacy = noun_parsed.tag.animacy

            # Sometimes coordination depends on animation
            try:
                words = list(map(lambda x: self.morph.parse(x)[0].inflect({gender, animacy}).word, words))
            except AttributeError:
                words = list(map(lambda x: self.morph.parse(x)[0].inflect({gender}).word, words))

        for word in words:
            try:
                morph = self.morph.parse(word)[0]
                inflected = morph.inflect(grammes)
                new_word = inflected.word
            except AttributeError:
                new_word = word

            morphed.append(new_word)

        return ' '.join(morphed)

    def ner(self, sample: str) -> (str, str):
        """
        Adding entity markup for templates

        :return:
            template for declensions and template for substitution
        """
        sample_to_inflect, edited_sample = sample, sample

        keys = self.key_pattern.findall(sample)
        for key in keys:
            random_word = random.choice(self.dictionary[key])

            # highlight entities
            # ...

            sample_to_inflect = sample_to_inflect.replace(key, random_word)
            edited_sample = edited_sample.replace(key, random_word)

        return sample_to_inflect, edited_sample

    def create(self, sample: str) -> (str, str):
        """
        Substitutes random words from the dictionary into the template, applies word transformation

        :param sample: "prep:robot action:patrol"
            {
                "prep:robot": ["-excl", "-excl-plur"],
                "action:patrol" ["патрулировать", "разведывать", "охранять"],
                ...
            }
            P.S.: for word conversion to work, you must specify the required grammes in the dictionary files,
            example for file prep:robot: "-excl" means that
            the transformation will be applied to the next word in the pattern
        :return:
            modified string according to selected dictionary values
        """
        sample_to_inflect, edited_sample = self.ner(sample)

        # Extracting words for declension using a pattern
        words = self.word_pattern.findall(sample_to_inflect)

        case = None
        for stuff in words:
            word_and_case = stuff.split('-')

            word = word_and_case[0]

            if case:
                new_word = self.inflect(word, set(case))
            else:
                new_word = word

            case = word_and_case[1:]
            edited_sample = edited_sample.replace('-'.join(case), '')
            sample_to_inflect = sample_to_inflect.replace('-'.join(case), '')

            if new_word:
                # Correct replacement of words in the template taking into account entities
                for new, old in zip(new_word.split(" "), word.split(" ")):
                    edited_sample = edited_sample.replace(old, new)
                    sample_to_inflect = sample_to_inflect.replace(old, new)

        sample_to_inflect = sample_to_inflect.replace('-', '')
        sample_to_inflect = sample_to_inflect.replace('|', ' ')
        sample_to_inflect = sample_to_inflect.strip()

        edited_sample = edited_sample.replace('-', '')
        edited_sample = edited_sample.replace('|', ' ')
        edited_sample = edited_sample.strip()

        return sample_to_inflect, edited_sample

    def run(self, samples: list, amount: int, numbers=None) -> (list, list):
        """
        Using templates, generates amount of commands per template

        If a range of numbers is specified start, end - substitutes a random number from the range into the command

        :param amount: number of examples per template
        :param numbers: list of numbers to substitute
        :return:
            List of generated commands by templates
        """
        cmd_list = []
        cmd_ner_list = []
        cmd_vector_list = []
        for sample in samples:

            for i in range(amount):

                sample_for_vector = sample

                example, example_ner = self.create(sample)
                if numbers:
                    n = random.choice(numbers)
                    sample_for_vector = sample_for_vector.replace("$", f"value@{n}")

                    example = example.replace("$", str(n))
                    example_ner = example_ner.replace("$", str(n))

                vector = self.to_vector(sample_for_vector)

                cmd_list.append(example)
                cmd_ner_list.append(example_ner)
                cmd_vector_list.append(vector)

        return {
            "text": cmd_list,
            "ner": cmd_ner_list,
            "vector": cmd_vector_list
        }

    def to_vector(self, sample: str) -> dict:
        """
        Creating a vector from command attributes

        :return:
            dictionary with numeric values of the attribute vector
        """
        true_keys = self.attr_config.keys()
        true_dict = dict(zip(true_keys, [0 for _ in true_keys]))

        keys = self.key_pattern.findall(sample)
        vector_keys = [k.split('@')[0] for k in keys]
        vector_values = [v.split('@')[1] for v in keys]
        vector_dict = dict(zip(vector_keys, vector_values))

        object_count = 1
        relation_count = 1
        for key in keys:

            k, v = key.split('@')

            if k == 'action':
                if v in ['move', 'rotate']:
                    if 'direction' in vector_keys and 'value' not in vector_keys:
                        v = v + '_dir'
                    elif 'value' in vector_keys:
                        v = v + '_on'
                    elif 'object' in vector_keys:
                        v = v + '_to'

                true_dict[k] = self.attr_config[k][v]

            if k == 'direction':
                true_dict[k] = self.attr_config[k][v]

            if k == 'distance':
                if v == 'meters':
                    true_dict[v] = self.attr_config[v][vector_dict['value']]
                elif v == 'degs':
                    true_dict[v] = self.attr_config[v][vector_dict['value']]
                elif v in ['hours', 'hours_fake']:
                    true_dict['hours'] = self.hours_config[f'{vector_dict["value"]}']

            if k == 'object':
                if v == 'gaze':
                    true_dict['gaze'] = 1
                elif v == 'route':
                    true_dict['meters'] = self.attr_config['meters'][vector_dict["value"]]
                    k1 = k + str(object_count)
                    true_dict[k1] = self.attr_config[k1][v]
                else:
                    k1 = k + str(object_count)
                    true_dict[k1] = self.attr_config[k1][v]
                    object_count += 1

            if k == 'relation':
                objects = vector_keys.count('object')

                if objects == 1:
                    true_dict['self'] = self.attr_config['self'][v]
                else:
                    k1 = k + str(relation_count)
                    true_dict[k1] = self.attr_config[k1][v]
                    relation_count += 1

            if k == 'feature':
                true_dict[v] = 1

        return true_dict

    @staticmethod
    def save(data: dict, path: Path) -> None:
        """
        Saves generated data in RASA NLU format
        Rasa NLU data header:
        --------------
        version: "3.1"

        nlu:
        - intent: intent_name
          examples: |
        --------------

        :param data: dictionary of generated data key - action type, value - list of commands
        :param path: path to rasa nlu data
        """
        for key, values in data.items():
            # compiling a list of unique commands and random shuffling
            uniq = list(set(values))
            random.shuffle(uniq)

            filename = f"intent_{key}.yml"
            save_path = path.joinpath(filename)
            head = f'version: "3.1"\n\nnlu:\n- intent: {key}\n  examples: |\n'
            with open(save_path, 'w') as file:
                file.write(head)

                for val in uniq:
                    text = f'    - {val}\n'
                    file.write(text)
