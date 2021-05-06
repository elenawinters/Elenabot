from elenabotlib import *
import sys, os, ast
import configparser
import random

class Elenabot(Session):
    def __init__(self):

        super().__init__()  # unfortunately, this is a required call for elenabotlib implemented like this
        config = configparser.ConfigParser()
        config_file = 'config.ini'
        if not os.path.exists(config_file):
            config['twitch'] = {
                'oauth': 'oauth'.encode('utf-8').hex(),
                'channels': ['channel_to_be_in'],  # this is standard list format in the ini file. example: ['elenaberry']
                'nickname': 'your_lowercase_username'
            }
            with open(config_file, 'w') as configfile:
                config.write(configfile)
        else:
            config.read(config_file)

        channels = ast.literal_eval(config['twitch']['channels'])
        self.start(config['twitch']['oauth'], config['twitch']['nickname'], channels)

if __name__ == '__main__':
    configure_logger(logging.DEBUG)

    Elenabot()
