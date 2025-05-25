from elenabotlib import Session, log, event
from elenabotapi import API
from twitchAPI.helper import limit
import configparser
import asyncio
import logging
import ast
import os

# This runs the bot with extra debug info, but no handlers.
# It's useful for testing the bot in chaotic situations

class Elenabot(Session):
    def __init__(self):
        self.api = API()
        super().__init__()  # unfortunately, this is a required call for elenabotlib implemented like this
        self.config = configparser.ConfigParser()
        self.config_file = 'config.ini'
        if not os.path.exists(self.config_file):
            self.config['twitch'] = {
                'oauth': 'anonymous'.encode('utf-8').hex(),
                'channels': ['tmiloadtesting2', 'twitchmedia_qs_10'],  # this is standard list format in the ini file. example: ['elenaberry']
                'nickname': 'justinfan69'
            }
            self.config['db'] = {
                'address': ''
            }
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)
        else:
            self.config.read(self.config_file)

        self.api.client_secret = self.config['twitch']['api_client_secret']
        self.api.client_id = self.config['twitch']['api_client_id']

        # channels = ast.literal_eval(config['twitch']['channels'])
        self.dbaddress = self.config['db']['address']  # overwrite DB Address with the one we want

        self.auto_reconnect = False
        # if __debug__:
            # self.flags.log_hint_differences = True
            # self.flags.send_in_debug = True
        asyncio.run(self.api.auth_flow(self.config, self.config_file))
        self.start(self.config['twitch']['oauth'], self.config['twitch']['nickname'], [])

    @event('376')
    async def setup_stress_test(self, ctx):
        # log.info('Stream list', context=ctx, data=t)
        stream_list = []
        viewer_count = 0
        async for stream in limit(self.api.twitch.get_streams(first=100), 300):
            stream_list.append(stream.user_login)
            viewer_count += stream.viewer_count
            # log.info('Stream', data=stream)
        stream_list = list(set(stream_list))
        log.info(f'~{viewer_count} viewers in {len(stream_list)} streams')
        self.joindelay = 0.05
        await self.join(stream_list)

if __name__ == '__main__':
    log.setLevel(logging.INFO)
    Elenabot()
