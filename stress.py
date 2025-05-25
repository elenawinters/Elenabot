from elenabotlib import Session, log
import configparser
import logging
import ast
import os

# This runs the bot with extra debug info, but no handlers.
# It's useful for testing the bot in chaotic situations

class Elenabot(Session):
    def __init__(self):
        super().__init__()  # unfortunately, this is a required call for elenabotlib implemented like this
        config = configparser.ConfigParser()
        config_file = 'config.ini'
        if not os.path.exists(config_file):
            config['twitch'] = {
                'oauth': 'anonymous'.encode('utf-8').hex(),
                'channels': ['tmiloadtesting2', 'twitchmedia_qs_10'],  # this is standard list format in the ini file. example: ['elenaberry']
                'nickname': 'justinfan69'
            }
            config['db'] = {
                'address': ''
            }
            with open(config_file, 'w') as configfile:
                config.write(configfile)
        else:
            config.read(config_file)

        channels = ast.literal_eval(config['twitch']['channels'])
        self.dbaddress = config['db']['address']  # overwrite DB Address with the one we want

        self.auto_reconnect = False
        # if __debug__:
            # self.flags.log_hint_differences = True
            # self.flags.send_in_debug = True

        self.start(config['twitch']['oauth'], config['twitch']['nickname'], channels)

if __name__ == '__main__':
    # log.setLevel(logging.INFO)
    Elenabot()