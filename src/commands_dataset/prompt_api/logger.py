import sys
import logging

from faker import Faker
from datetime import datetime


fake = Faker("en_US")


def logger(path=None, stream_level="INFO", file_level="DEBUG"):
    form = logging.Formatter(fmt='[%(asctime)s] - [%(name)s] - [%(levelname)s] - %(message)s')

    name = fake.user_name()
    log = logging.getLogger(name)
    log.setLevel(stream_level)

    handler_stream = logging.StreamHandler(stream=sys.stdout)
    handler_stream.setFormatter(form)
    handler_stream.setLevel(stream_level)
    log.addHandler(handler_stream)

    if path:
        log_path = str(path) + '/' + datetime.now().strftime("%d-%m-%Y_%H:%M") + '_' + name
        handler_file = logging.FileHandler(log_path, mode='w')
        handler_file.setFormatter(form)
        handler_file.setLevel(file_level)
        log.addHandler(handler_file)
    else:
        log_path = None

    return log, log_path
