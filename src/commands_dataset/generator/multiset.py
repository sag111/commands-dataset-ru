import json
import random
from pathlib import Path

from gen import Generator


class MultisetGenerator(Generator):

    def __init__(self, dictionary_path: Path, config_path: Path):
        super(MultisetGenerator, self).__init__(dictionary_path, config_path)

        nums = 0
        for v in self.dictionary.values():
            nums += len(v)

    def ner(self, sample: str) -> (str, str):
        """
        Adding entity markup for templates, the function is called in the create() method of the parent class Generator

        :return:
            template for declensions and template for substitution
        """
        sample_to_inflect = sample
        edited_sample = sample

        keys = self.key_pattern.findall(sample)

        addition = 0
        for key in keys:
            random_word = random.choice(self.dictionary[key])

            sample_to_inflect = sample_to_inflect.replace(key, random_word)

            entity, role = key.split('@')

            match entity:
                case "action":
                    random_word = f'[{random_word}]' + str(json.dumps({"entity": entity, "role": role}))
                case "direction":
                    random_word = f'[{random_word}]' + str(json.dumps({"entity": entity, "role": role}))
                case "object":
                    if addition == 0 and random_word != '_' and role != "gaze":
                        random_word = f'[{random_word}]' + str(json.dumps({"entity": "object", "role": role}))
                    elif addition > 0 and random_word != '_':
                        random_word = f'[{random_word}]' + str(json.dumps({"entity": "subject", "role": role}))
                    elif role == "gaze":
                        random_word = f'[{random_word}]' + str(json.dumps({"entity": role}))
                    else:
                        random_word = ''
                    addition += 1
                case "relation":
                    random_word = f'[{random_word}]' + str(json.dumps({"entity": entity, "role": role}))
                case "feature":
                    random_word = f'[{random_word}]' + str(json.dumps({"entity": role}))

            edited_sample = edited_sample.replace(key, random_word)

        return sample_to_inflect, edited_sample

    def patrol(self, amount: int) -> dict:
        """
        Creates patrol commands

        :param amount: number of commands per template
        :return:
            Command Dictionary
        """
        samples = [
            # патрулируй
            "|prep@robot|action@patrol|",
            # патрулируй по кругу радиуса 4 м
            "|prep@robot|action@patrol|aux@by|object@circle|aux@radius|$|distance@meters|",
            # патрулируй по кругу 4 м
            "|prep@robot|action@patrol|aux@by|object@circle|$|distance@meters|",
            # патрулируй по маршруту номер 2
            "|prep@robot|action@patrol|aux@by|object@route|aux@number|$|",
            # патрулируй по 2 маршруту
            "|prep@robot|action@patrol|aux@by|$|object@route|",
        ]

        print(f"Samples: {len(samples)}")

        commands = self.run(samples, amount=amount, numbers=[1, 2, 5, 7, 10])

        return commands

    def simple(self, amount: int) -> dict:
        """
        Creates simple commands

        :param amount: number of commands per template
        :return:
            Command Dictionary
        """
        samples = [
            # стоп
            "|prep@robot|action@stop|",
            # продолжай
            "|prep@robot|action@continue|",
            # пауза
            "|prep@robot|action@pause|"
        ]

        print(f"Samples: {len(samples)}")

        commands = self.run(samples, amount=amount)

        return commands

    def move_rotate_dir(self, amount: int) -> dict:
        """
        Generates commands to turn in a direction

        :param amount: number of commands per template
        :return:
            Command Dictionary
        """
        samples = []
        for direct in self.get_keys('direction'):
            # иди вперед
            sample = f"|prep@robot|action@move|{direct}|"
            samples.append(sample)
            # поворачивай направо
            sample = f"|prep@robot|action@rotate|{direct}|"
            samples.append(sample)

        print(f"Samples: {len(samples)}")

        commands = self.run(samples, amount=amount)

        return commands

    def move_on(self, amount: int) -> dict:
        """
        Creates movement commands for a specified number of meters

        :param amount: number of commands per template
        :return:
            Command Dictionary
        """
        samples = []
        for direct in self.get_keys('direction'):
            # иди вперед 4 м
            sample = f"|prep@robot|action@move|{direct}|$|distance@meters|"
            samples.append(sample)
            # иди 10 м вперед
            sample = f"|prep@robot|action@move|$|distance@meters|{direct}|"
            samples.append(sample)
            # иди вперед на 10м
            sample = f"|prep@robot|action@move|{direct}|aux@on|$|distance@meters|"
            samples.append(sample)
            # иди на 10м вперед
            sample = f"|prep@robot|action@move|aux@on|$|distance@meters|{direct}|"
            samples.append(sample)

        print(f"Samples: {len(samples)}")

        commands = self.run(samples, amount=amount, numbers=list(self.attr_config['meters'].keys()))

        return commands

    def rotate_on_degs(self, amount: int) -> dict:
        """
        Generates rotation commands by a specified number of degrees

        :param amount: number of commands per template
        :return:
            Command Dictionary
        """
        samples = []
        for direct in self.get_keys('direction'):
            # поверни направо 90°
            sample = f"|prep@robot|action@rotate|{direct}|$|distance@degs|"
            samples.append(sample)
            # поверни 90° направо
            sample = f"|prep@robot|action@rotate|$|distance@degs|{direct}|"
            samples.append(sample)
            # поверни направо на 90°
            sample = f"|prep@robot|action@rotate|{direct}|aux@on|$|distance@degs|"
            samples.append(sample)
            # поверни на 90° направо
            sample = f"|prep@robot|action@rotate|aux@on|$|distance@degs|{direct}|"
            samples.append(sample)

        print(f"Samples: {len(samples)}")

        commands = self.run(samples, amount=amount, numbers=list(self.attr_config['degs'].keys()))

        return commands

    def rotate_on_hours_fake(self, amount: int) -> dict:
        """
        Creates rotation commands for a specified number of hours in the "1:00" format

        :param amount: number of commands per template
        :return:
            Command Dictionary
        """
        samples = []
        for direct in self.get_keys('direction'):
            # поверни направо на 11:00
            sample = f"|prep@robot|action@rotate|{direct}|aux@on|$|distance@hours_fake|"
            samples.append(sample)
            # поверни на 11:00 направо
            sample = f"|prep@robot|action@rotate|aux@on|$|distance@hours_fake|{direct}|"
            samples.append(sample)

        print(f"Samples: {len(samples)}")

        commands = self.run(samples, amount=amount, numbers=['"1:00"', '"1:30"', '"2:00"', '"2:30"', '"3:00"', '"3:30"',
                                                             '"4:00"', '"4:30"', '"5:00"', '"5:30"', '"6:00"', '"6:30"',
                                                             '"7:00"', '"7:30"', '"8:00"', '"8:30"', '"9:00"', '"9:30"',
                                                             '"10:00"', '"10:30"', '"11:00"', '"11:30"', '"12:00"'])

        return commands

    def rotate_on_hours(self, amount: int) -> dict:
        """
        Creates rotation commands for a specified number of hours in the "1 hour" format

        :param amount: number of commands per template
        :return:
            Command Dictionary
        """
        samples = []
        for direct in self.get_keys('direction'):
            # поверни направо на 1.5 часа
            sample = f"prep@robot|action@rotate|{direct}|aux@on|$|distance@hours|"
            samples.append(sample)
            # поверни на 1.5 часа направо
            sample = f"prep@robot|action@rotate|aux@on|$|distance@hours|{direct}|"
            samples.append(sample)

        print(f"Samples: {len(samples)}")

        commands = self.run(samples, amount=amount, numbers=["0,5", "1", "1,5", "2", "2,5", "3", "3,5", "4", "4,5", "5",
                                                             "5,5", "6", "6,5", "7", "7,5", "8", "8,5", "9", "9,5", "10",
                                                             "10,5", "11", "11,5", "12"])

        return commands

    def objects(self, amount: int, states: int) -> dict:
        """
        Creates commands for interacting with objects

        :param amount: number of commands per template
        :param states: number of random searches of objects
        :return:
            Command Dictionary
        """
        actions = self.get_keys('action')
        actions.remove('action@patrol')
        actions.remove('action@stop')
        actions.remove('action@pause')
        actions.remove('action@continue')

        objects = self.get_keys('object')
        objects.remove('object@gaze')
        objects.remove('object@void')
        objects.remove('object@route')
        objects.remove('object@circle')

        relations = self.get_keys('relation')

        samples = []
        for action in actions:
            for _ in range(states):
                temp_objects = objects.copy()
                obj1 = random.choice(temp_objects)
                temp_objects.remove(obj1)
                obj2 = random.choice(temp_objects)
                temp_objects.remove(obj2)
                rel1 = random.choice(relations)
                obj3 = random.choice(temp_objects)
                rel2 = random.choice(relations)

                match action:
                    case "action@move" | "action@rotate":
                        # иди к дому
                        sample = f"|prep@robot|{action}|aux@to|{obj1}|"
                        samples.append(sample)
                        # иди к дому около дерева
                        sample = f"|prep@robot|{action}|aux@to|{obj1}|{rel1}|{obj2}|"
                        samples.append(sample)
                        # иди к дому около дерева рядом с камнем
                        sample = f"|prep@robot|{action}|aux@to|{obj1}|{rel1}|{obj2}|{rel2}|{obj3}|"
                        samples.append(sample)
                        # иди к ближайшему дереву
                        sample = f"|prep@robot|{action}|aux@to|feature@nearest {obj1}|"
                        samples.append(sample)
                        # иди к дереву ближайшему
                        sample = f"|prep@robot|{action}|aux@to|{obj1} feature@nearest|"
                        samples.append(sample)
                        # иди к этому дереву
                        sample = f"|prep@robot|{action}|aux@to|feature@gaze {obj1}|"
                        samples.append(sample)
                        # иди к дереву этому
                        sample = f"|prep@robot|{action}|aux@to|{obj1} feature@gaze|"
                        samples.append(sample)
                        # иди туда
                        sample = f"|prep@robot|{action}|object@gaze|"
                        samples.append(sample)
                        if rel1 != "relation@near":
                            # иди к дому слева от тебя
                            sample = f"|prep@robot|{action}|aux@to|{obj1}|{rel1}|aux@self|"
                            samples.append(sample)
                            # иди к дому слева
                            sample = f"|prep@robot|{action}|aux@to|{obj1}|{rel1}|"
                            samples.append(sample)
                    case "action@follow":
                        # следуй за машиной
                        sample = f"|prep@robot|{action}|aux@into|object@car|"
                        samples.append(sample)
                    case _:
                        # анализируй дом
                        sample = f"|prep@robot|{action}|{obj1}|"
                        samples.append(sample)
                        # анализируй дом около дерева
                        sample = f"|prep@robot|{action}|{obj1}|{rel1}|{obj2}|"
                        samples.append(sample)
                        # анализируй дом около дерева рядом с камнем
                        sample = f"|prep@robot|{action}|{obj1}|{rel1}|{obj2}|{rel2}|{obj3}|"
                        samples.append(sample)
                        # анализируй ближайшее дерево
                        sample = f"|prep@robot|{action}|feature@nearest {obj1}|"
                        samples.append(sample)
                        # анализируй дерево ближайшее
                        sample = f"|prep@robot|{action}|{obj1} feature@nearest|"
                        samples.append(sample)
                        # анализируй это дерево
                        sample = f"|prep@robot|{action}|feature@gaze {obj1}|"
                        samples.append(sample)
                        # анализируй дереву это
                        sample = f"|prep@robot|{action}|{obj1} feature@gaze|"
                        samples.append(sample)
                        if rel1 != "relation@near":
                            # анализируй дом слева от тебя
                            sample = f"|prep@robot|{action}|{obj1}|{rel1}|aux@self|"
                            samples.append(sample)
                            # анализируй дом слева
                            sample = f"|prep@robot|{action}|{obj1}|{rel1}|"
                            samples.append(sample)

        print(f"Samples: {len(samples)}")

        commands = self.run(samples, amount=amount)

        return commands
