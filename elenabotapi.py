"""
    This is a helper class.

    Inherit from API class to use.

    Copyright 2021-2024 ElenaWinters
    References:
        Twitch IRC Guide
        Rinbot by RingoMär
        TwitchDev samples

    Tested on Windows 11 and Ubuntu 22.04

"""

from twitchAPI.oauth import UserAuthenticator, refresh_access_token
from twitchAPI.twitch import Twitch
from twitchAPI.helper import first
import logging


log = logging.getLogger(__name__)

class API(object):
    def __init__(self) -> None:
        self.client_secret = None
        self.client_id = None
        self.scopes = []
        self.refresh = None
        self.token = None
        self.lookup = {}

    async def auth_flow(self, config, config_file) -> None:
        # with open(config_file, 'w') as configfile:
        #     config.write(configfile)
        self.token = config['api']['token']
        self.refresh = config['api']['refresh']
        self.twitch = await Twitch(self.client_id, self.client_secret)
        if self.token == '' or self.refresh == '' :
            auth = UserAuthenticator(self.twitch, self.scopes, force_verify=False)
            self.token, self.refresh = await auth.authenticate()
        else:
            self.token, self.refresh = await refresh_access_token(self.refresh, self.client_id, self.client_secret)

        config['api']['token'] = self.token
        config['api']['refresh'] = self.refresh
        with open(config_file, 'w') as configfile:
            config.write(configfile)
        
        # self.twitch = await Twitch(self.client_id, self.client_secret)
        # auth = UserAuthenticator(self.twitch, self.scopes, force_verify=False)
        # self.token, self.refresh = await auth.authenticate()

        await self.twitch.set_user_authentication(self.token, self.scopes, self.refresh)
        
        # config['api']['token'] = self.token
        # config['api']['refresh'] = self.refresh
        # with open(config_file, 'w') as configfile:
        #     config.write(configfile)

    async def botlist_to_lookup(self, botlist):
        async for i in self.twitch.get_users(logins=list(botlist.keys())):
            self.lookup[i.login] = i.id

    async def add_channel_to_lookup(self, channel):
        if channel[1:] in self.lookup: return
        async for i in self.twitch.get_users(logins=channel[1:]):
            self.lookup[i.login] = i.id

    async def define_moderator_id(self, nickname):
        user = await first(self.twitch.get_users(logins=nickname))
        self.moderator_id = user.id
        # self.lookup[user.login] = user.id

    async def ban_user(self, broadcaster, username, ban_msg) -> None:
        if broadcaster[1:] not in self.lookup or username not in self.lookup:
            async for i in self.twitch.get_users(logins=[broadcaster[1:], username]):
                self.lookup[i.login] = i.id
        # print(broadcaster[1:])
        # print(username)
        try:
            await self.twitch.ban_user(self.lookup[broadcaster[1:]], self.moderator_id, self.lookup[username], ban_msg)
        except Exception as e:
            pass
        # print(self.lookup)
        # async for i in user:

        pass



