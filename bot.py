from twitchAPI.type import AuthScope
from elenabotlib import Session, event, channel, cooldown, message, author, configure_logger, log
from elenabotapi import API
import configparser
import asyncio
import logging
import random
import httpx
import hints
import ast
import os


class Elenabot(Session):
    def __init__(self):
        self.api = API()
        super().__init__()  # unfortunately, this is a required call for elenabotlib implemented like this
        self.config = configparser.ConfigParser()
        self.config_file = 'config.ini'
        if not os.path.exists(self.config_file):
            self.config['twitch'] = {
                'oauth': 'oauth'.encode('utf-8').hex(),
                'channels': ['tmiloadtesting2', 'twitchmedia_qs_10'],  # this is standard list format in the ini file. example: ['elenaberry']
                'nickname': 'your_lowercase_username'
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
        self.api.scopes.append(AuthScope.MODERATOR_MANAGE_BANNED_USERS)

        # if __debug__:
        #     # channels = ['zaquelle']
        #     import gen_stream_list
        #     channels = gen_stream_list.ActiveHasroot('gtarp')
        #     # if 'zaquelle' in channels:
        #     #     channels.remove('zaquelle')
        #     # self.dbaddress = config['db']['address'] + '_dev'
        #     # self.kekchannels = []
        # else:

        channels = ast.literal_eval(self.config['twitch']['channels'])
        self.dbaddress = self.config['db']['address']  # overwrite DB Address with the one we want
        self.allowed_bots = ['elenaberry', 'elenaberry_senpai', 'streamlabs', 'streamelements', 'sery_bot', 'moobot', 'nightbot', 'soundalerts']
        self.bot_threshold = 200
        self.chatters = {}
        self.botlist = {}

        if __debug__:
            self.flags.log_hint_differences = True
            # self.flags.send_in_debug = True
        asyncio.run(self.api.auth_flow(self.config, self.config_file))
        self.start(self.config['twitch']['oauth'], self.config['twitch']['nickname'], channels)

    async def update_botlist(self):
        async with httpx.AsyncClient() as client:
            response = await client.get('https://api.twitchinsights.net/v1/bots/online')
            self.botlist = {}
            for x in response.json()['bots']:
                self.botlist[x[0]] = x[1]

    async def check_and_ban_user(self, user, channel):
        if user in self.allowed_bots: return
        if user in self.botlist:
            await self.api.ban_user(channel, user, f'User is currently in {self.botlist[user]} chat rooms at the time of this ban')
            # await ctx.send(f"/ban {ctx.user} User is currently in {self.botlist[ctx.user]} chat rooms at the time of this ban.")
            print(f'{user} is a bot')
            pass

    # @event('any')
    # async def test(self, ctx):
    #     print(ctx)

    @event('001')
    async def elenabot_first_start_update(self, ctx):
        # https://api.twitchinsights.net/v1/bots/online
        await self.update_botlist()
        await self.api.botlist_to_lookup(self.botlist)
        await self.api.define_moderator_id(self.nick)
        print(self.botlist)
        # print('Updating local active botlist')
    
    @event('ping')
    async def elenabot_get_botlist(self, ctx):
        # https://api.twitchinsights.net/v1/bots/online
        await self.update_botlist()
        for channel in list(self.chatters.keys()):
            for user in self.chatters[channel]:
                await self.check_and_ban_user(user, channel)
        # print('Updating local active botlist')

    @event('join')
    async def elenabot_ban_online_bots(self, ctx: hints.JOIN):
        await self.api.add_channel_to_lookup(ctx.channel)
        await self.check_and_ban_user(ctx.user, ctx.channel)
        if self.chatters.get(ctx.channel, None) == None:
            self.chatters[ctx.channel] = []
        if ctx.user not in self.chatters[ctx.channel]:
            self.chatters[ctx.channel].append(ctx.user)
        # print(self.chatters.get(ctx.channel, None))
        # if type(self.chatters[ctx.channel])
        # self.chatters[ctx.channel]
        # print(self.chatters[ctx.channel])

    @event('part')
    async def elenabot_remove_parted_chatters(self, ctx: hints.PART):
        self.chatters[ctx.channel].remove(ctx.user)


if __name__ == '__main__':
    configure_logger(logging.DEBUG)

    Elenabot()
