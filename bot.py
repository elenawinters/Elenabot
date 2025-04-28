from elenabotlib import Session, event, channel, cooldown, message, author, configure_logger, log
import configparser
import logging
import random
import hints
import ast
import os


class Elenabot(Session):
    def __init__(self):
        super().__init__()  # unfortunately, this is a required call for elenabotlib implemented like this
        config = configparser.ConfigParser()
        config_file = 'config.ini'
        if not os.path.exists(config_file):
            config['twitch'] = {
                'oauth': 'oauth'.encode('utf-8').hex(),
                'channels': ['tmiloadtesting2', 'twitchmedia_qs_10'],  # this is standard list format in the ini file. example: ['elenaberry']
                'nickname': 'your_lowercase_username'
            }
            config['db'] = {
                'address': ''
            }
            with open(config_file, 'w') as configfile:
                config.write(configfile)
        else:
            config.read(config_file)

        # if __debug__:
        #     # channels = ['zaquelle']
        #     import gen_stream_list
        #     channels = gen_stream_list.ActiveHasroot('gtarp')
        #     # if 'zaquelle' in channels:
        #     #     channels.remove('zaquelle')
        #     # self.dbaddress = config['db']['address'] + '_dev'
        #     # self.kekchannels = []
        # else:

        channels = ast.literal_eval(config['twitch']['channels'])
        self.dbaddress = config['db']['address']  # overwrite DB Address with the one we want

        if __debug__:
            self.flags.log_hint_differences = True
            self.flags.send_in_debug = False

        self.start(config['twitch']['oauth'], config['twitch']['nickname'], channels)


if __name__ == '__main__':
    configure_logger(logging.DEBUG)

    Elenabot()
