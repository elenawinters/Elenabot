"""
    This only implements a simple chatbot.

    Inherit from Session class to use.

    Copyright 2021-present ElenaWinters
    References:
        Twitch IRC Guide
        Rinbot by RingoMär
        TwitchDev samples

    Tested on Windows 10 and Ubuntu 22.04

"""

from typing import Any, Callable, Union
from dataclasses import make_dataclass, asdict
from sqlalchemy.types import LargeBinary
from datetime import datetime
from queue import Queue
import functools
import aiohttp
import asyncio
import logging
import dataset
import msgpack
import hints
import json
import math
import sys
import re


log = logging.getLogger(__name__)
SOH = chr(1)  # ASCII SOH (Start of Header) Control Character, used for ACTION events

# con = sqlite3.connect('log.sqlite')
# cur = con.cursor()

# con.execute('''CREATE TABLE IF NOT EXISTS msg_sent (channel text, message text)''')
# con.execute('''CREATE TABLE IF NOT EXISTS msg_denied (channel text, message text)''')
# con.execute('''CREATE TABLE IF NOT EXISTS msg_banned (channel text)''')
# con.execute('''CREATE TABLE IF NOT EXISTS outgoing (channel text, message text)''')


def event(name: str = 'any', *extras) -> Callable:  # listener/decorator for any event
    events = list(extras)
    events.append(name)
    # print(events)

    def wrapper(func: Callable) -> Callable:
        return add_listeners(func, events)
    return wrapper


events = event


def cooldown(time: int) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self: Session, ctx) -> Callable:
            if self.func_on_cooldown(func, time):
                # log.debug(f'{func.__name__} is on cooldown!')
                return asyncio.sleep(0)
            return func(self, ctx)
        return wrapper
    return decorator


def ignore_myself() -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self: Session, ctx: hints.Messageable) -> Callable:
            if ctx.user.lower() != self.nick:
                return func(self, ctx)
            return asyncio.sleep(0)
        return wrapper
    return decorator


def author(*names) -> Callable:  # check author
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self: Session, ctx: hints.Messageable) -> Callable:
            if any(ctx.user.lower() == name.lower() for name in list(names)):
                return func(self, ctx)
            return asyncio.sleep(0)
        return wrapper
    return decorator


authors = author


def channel(*names) -> Callable:  # check channel
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self: Session, ctx: hints.Messageable) -> Callable:
            def adapt(_name: str) -> str:
                return self.merge(_name)
            if any(ctx.channel == adapt(name) for name in list(names)):
                return func(self, ctx)
            return asyncio.sleep(0)
        return wrapper
    return decorator


channels = channel


# these need to be set to the same thing for a solo compare to check for mode, reference the message decorator below
def msg_compare(mode: str = 'eq', actual: str = 'test', compare: str = 'test') -> bool:
    match mode.lower():
        case 'eq' | 'equals':
            if actual == compare:
                return True
        case 'sw' | 'startswith':
            return actual.startswith(compare)
        case 'ew' | 'endswith':
            return actual.endswith(compare)
        case 'in' | 'contains':
            if compare in actual:
                return True


def message(*args: tuple, **kwargs: dict) -> Callable:
    def decorator(func: Callable) -> Callable:
        def wrapper(self: Session, ctx: hints.Messageable) -> Callable:
            mode = [pmode for pmode in args if msg_compare(pmode)]  # this is so bad lmfao
            if not mode:
                mode = kwargs.get('mode', kwargs.get('m', 'eq'))
            else: mode = mode[0]
            ignore_self = kwargs.get('ignore_self', True)

            possible = list(args)
            if mode in possible:
                possible.remove(mode)

            if any(msg_compare(mode, ctx.message.content, msg) for msg in possible):
                if ignore_self and ctx.user.lower() == self.nick:
                    return asyncio.sleep(0)
                return func(self, ctx)
            return asyncio.sleep(0)
        return wrapper
    return decorator


class DebugFilter(logging.Filter):
    def filter(self, record):
        if record.levelno >= 30:
            return True
        elif record.levelno > 10:
            return False
        return True


# you can write your own configuration if you want to, not here though. do it in your own class
def configure_logger(_level=logging.INFO) -> None:
    log.setLevel(_level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(_level)
    log.addHandler(handler)
    d_log = logging.FileHandler('debug.log')
    d_log.addFilter(DebugFilter())
    d_log.setLevel(_level)
    log.addHandler(d_log)


_listeners = {}
_handlers = {}  # for internal dispatch


def dispatch(*args) -> Callable:  # listener/decorator for any event
    '''
        This function is used for notice dispatches to internal functions.
        While it can be used in a import case, it will most likely do nothing.
        A notice can only be registered once.
    '''
    def wrapper(func: Callable) -> Callable:
        for event in args:
            if event in _handlers: continue  # skip if already found, no need to error
            _handlers[event] = func
        return func
    return wrapper


# Adding this make me realize that I may need to split the bot into multiple files.
# I've prided myself on keeping the lib portable in a single file.
# But with the removal of hosts, I need to implement the Twitch API eventually.
def depr_event(date: datetime, before: str, after: str, events: list) -> Callable:
    '''
        Warn the user that the event they are registering is or is about to be depreciated.
    '''
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Callable:
            if event := set(args[1]).intersection(events):
                pretty = {'date': f'{date.strftime("%B %d, %Y")}', 'event': event.pop()}
                prefix = 'DEPRECIATION({event}): '
                if date > datetime.now():
                    log.warning(str(prefix + before).format(**pretty))
                else:
                    log.warning(str(prefix + after).format(**pretty))
            return func(*args, **kwargs)
        return wrapper
    return decorator


def expr_event(message: str, events: list, date: datetime = datetime.now()) -> Callable:
    '''
        Alert the user that the event they are using is considered experiemental and may be removed at any time.
    '''
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Callable:
            if event := set(args[1]).intersection(events):
                pretty = {'date': f'{date.strftime("%B %d, %Y")}', 'event': event.pop()}
                log.warning(str('EXPERIMENT({event}): ' + message).format(**pretty))
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ORDER OF THESE DECORATORS SHOULD BE IN ORDER OF HAPPENINGS
@expr_event(message='https://help.twitch.tv/s/article/cheering-experiment-2022',
            events=['midnightsquid'])
@depr_event(date=datetime(2022, 10, 3),
            before='Event \'{event}\' will be depreciated by Twitch on {date}. You will no longer receive this event after that date.',
            after='Event \'{event}\' has been depreciated by Twitch as of {date}. You can still listen for the event, but you will never receive it.',
            events=['host', 'hosttarget', 'unhost', 'notice:autohost_receive', 'notice:bad_host_error', 'notice:bad_host_hosting',
                    'notice:bad_host_rate_exceeded', 'notice:bad_host_rejected', 'notice:bad_host_self', 'notice:bad_unhost_error',
                    'notice:host_off', 'notice:host_on', 'notice:host_receive', 'notice:host_receive_no_count', 'notice:host_target_went_offline',
                    'notice:hosts_remaining', 'notice:not_hosting', 'notice:usage_host', 'notice:usage_unhost'])
def add_listeners(func, names=['any']) -> None:
    # print(names)
    for name in names:
        match name:
            case 'all' | '*':
                name = 'any'
            case 'resubscribe' | 'resubscription':
                name = 'resub'
            case 'subscribe' | 'subscription':
                name = 'sub'
            case 'msg':
                name = 'message'

        if name not in _listeners:
            _listeners[name] = [func]
        else:
            _listeners[name].append(func)


rx_positive = re.compile(r'^\d+$')


class Session(object):
    def __init__(self) -> None:
        self.auto_reconnect = True
        self.host = 'ws://irc-ws.chat.twitch.tv'
        self.port = 80
        self.__cooldowns = {}
        self.__channels = []
        self.__joinqueue = Queue()
        self.__outgoing = {}

        self.__proxies = {}

        self.dbaddress = None

    # This is a complex function, and it has a high "Cognitive Complexity", beyond the limit of 15.
    def twitch_irc_formatter(self, original: str = '@badge-info=gay/4;badges=lesbian/3,premium/1;user-type=awesome :tmi.twitch.tv GAYMSG #zaquelle :This is kinda gay'):  # tested with every @ based message. parses correctly.
        array = original[1:].split(' ')  # Indexes | 0 = Server, 1 = Notice, 2 = Channel, 3+ = Message (Broken up, use Regex)
        # ChatGPT says that re.split should be used over a string split for the above. TODO: Test with re.split
        offset = 0
        info = {}
        if original.startswith('@'):
            offset = 1
            for k, v, _ in re.findall(r'([-\w]+)=(.*?)(;| :)', re.split(r'tmi\.twitch\.tv', original)[0]):
                k = k.replace('-', '_')
                if k in ('badge_info', 'badges'):  # converts for specific fields
                    badges = []
                    for entry in v.split(','):
                        if badge := re.search(r'(.+?)/(.+)', entry):
                            version = badge.group(2).replace('\\s', ' ')
                            if rx_positive.match(version):
                                version = int(version)
                            badges.append(hints.Badge(name=badge.group(1), version=version))
                    info[k] = badges
                elif k in ('emote_sets', 'emotes'):
                    info[k] = [e for e in v.split(',') if e]  # E
                elif k in ('system_msg', 'reply_parent_msg_body'):
                    info[k] = v.replace('\\s', ' ')
                elif k in ('emote_only', 'subscriber', 'first_msg', 'subs_only', 'rituals',
                           'turbo', 'mod', 'r9k'):
                    info[k] = bool(int(v))
                else:
                    if v == '':
                        v = None
                    elif rx_positive.match(v) or re.match(r'^-\d+$', v):  # there is a positive and negative version cuz regex
                        v = int(v)  # ^\d+$|^-\d+$
                    elif v == 'false':
                        v = False
                    elif v == 'true':
                        v = True
                    info[k] = v

        if len(array) >= 3 + offset:  # this is so sketch but it works. basically, check if a channel is provided
            info['channel'] = array[2 + offset]  # force channel
            if message := re.search(f"{array[1 + offset]} {info['channel']}" + r'..(.*)', original):
                info['message'] = message.group(1)

        if user := re.search(r"(?P<name>[\w]+)!(?P=name)@(?P=name)", array[0 + offset]):
            info['user'] = user.group(1)

        if __debug__:  # include server if in debug mode. this isn't useful for most cases.
            info['server'] = array[0 + offset]
        prs = make_dataclass(array[1 + offset], [tuple([k, v]) for k, v in info.items()])
        return prs(**info)

    def proxy_send_obj(self, channel: str):
        if channel not in self.__proxies:
            async def _send_proxy(message: str):  # construct send function that can be called from ctx)
                await self.send(message, channel)

            self.__proxies[channel] = _send_proxy
        return self.__proxies[channel]

    @dispatch(1, 2, 3, 4, 372, 376, 366)
    async def sinkhole(self, ctx):  # I'm not currently parsing these as I don't need to.
        pass

    @dispatch('join', 'part')
    async def handle_join_part(self, ctx):
        if not self.any_listeners('join', 'part'): return
        dprs = ctx.__dict__
        prs = make_dataclass(type(ctx).__name__, [tuple([k, v]) for k, v in dprs.items()])(**dprs)
        if ctx.user == self.nick:
            await self._lcall(f'{type(ctx).__name__.lower()}:self', ctx=prs)
        await self.call_listeners(f'{type(ctx).__name__.lower()}:{ctx.user}', ctx=prs)

    @dispatch(353)
    async def handle_353(self, ctx):
        if not self.any_listeners('join'): return
        users = re.findall(r'\w+', ctx.message)
        channel = users.pop(0)

        for user in users:
            if user == self.nick: continue
            prs = make_dataclass('JOIN', [tuple(['user', str]), tuple(['channel', str])])
            await self.call_listeners(f'join:{user}', ctx=prs(user=user, channel=f'#{channel}'))

    @dispatch(375)
    async def handle_375(self, ctx):
        log.debug(f"Connected! Environment is {'DEBUG' if __debug__ else 'PRODUCTION'}.")
        loop = asyncio.get_running_loop()
        self.__jointask = loop.create_task(self._join())

    @dispatch(421)  # UNKNOWN IRC COMMAND
    async def unknown_command_irc(self, ctx):
        log.debug(f"An IRC command was sent to the server, and they didn't recognize it. Here is what the server told us:\n{ctx}")

    @dispatch('cap')
    async def handle_cap(self, ctx):
        dprs = ctx.__dict__  # dprs and ctx are linked
        dprs['capabilities'] = re.findall(r'twitch\.tv\/(\w+)', ctx.message)
        dprs['response'] = re.search(r'(\w+) :twitch\.tv\/\w+', ctx.message).group(1)
        del dprs['channel']
        del dprs['message']
        prs = make_dataclass(type(ctx).__name__, [tuple([k, v]) for k, v in dprs.items()])
        await self.call_listeners(type(ctx).__name__.lower(), ctx=prs(**dprs))

    @dispatch('globaluserstate')  # I usually format display_name to user but I don't want to do that with GUS
    async def handle_globaluserstate(self, ctx: hints.GLOBALUSERSTATE):  # ALWAYS SET THIS
        dprs = ctx.__dict__
        dprs['user'] = ctx.display_name
        del dprs['display_name']
        prs = make_dataclass(type(ctx).__name__, [tuple([k, v]) for k, v in dprs.items()])(**dprs)
        await self.call_listeners(type(ctx).__name__.lower(), ctx=prs)
        self.state = ctx

    @dispatch('privmsg')
    async def handle_privmsg(self, ctx: Union[hints.PRIVMSG, hints.USERSTATE]):
        if not self.any_listeners('message'): return
        dprs = ctx.__dict__
        if hasattr(ctx, 'display_name'):
            dprs['user'] = ctx.display_name
            del dprs['display_name']
        dprs['send'] = self.proxy_send_obj(ctx.channel)
        dprs['action'] = True if 'ACTION' in ctx.message and SOH in ctx.message else False
        dprs['message'] = hints.Message(dprs['user'], ctx.channel, ctx.message[len(SOH + 'ACTION '):-len(SOH)] if dprs['action'] else ctx.message)
        prs = make_dataclass(type(ctx).__name__, [tuple([k, v]) for k, v in dprs.items()])(**dprs)
        if prs.action:
            await self.call_listeners('message:action', ctx=prs)
            return
        await self.call_listeners('message', ctx=prs)

    @dispatch('userstate')
    async def handle_userstate(self, ctx: Union[hints.PRIVMSG, hints.USERSTATE]):
        if not self.any_listeners('userstate'): return
        dprs = ctx.__dict__
        if hasattr(ctx, 'display_name'):
            dprs['user'] = ctx.display_name
            del dprs['display_name']
        dprs['send'] = self.proxy_send_obj(ctx.channel)
        prs = make_dataclass(type(ctx).__name__, [tuple([k, v]) for k, v in dprs.items()])(**dprs)
        await self.call_listeners(type(ctx).__name__.lower(), ctx=prs)

    @dispatch('roomstate', 'clearmsg')
    async def handle_generic(self, ctx):
        if not self.any_listeners('roomstate', 'clearmsg'): return
        dprs = ctx.__dict__
        dprs['send'] = self.proxy_send_obj(ctx.channel)
        prs = make_dataclass(type(ctx).__name__, [tuple([k, v]) for k, v in dprs.items()])(**dprs)
        await self.call_listeners(type(ctx).__name__.lower(), ctx=prs)

    @dispatch('notice')
    async def handle_notice(self, ctx):
        if not self.any_listeners('notice'): return
        dprs = ctx.__dict__
        dprs['send'] = self.proxy_send_obj(ctx.channel)
        prs = make_dataclass(type(ctx).__name__, [tuple([k, v]) for k, v in dprs.items()])(**dprs)
        await self.call_listeners(f'notice:{ctx.msg_id}', ctx=prs)

    @dispatch('usernotice')  # i dont know if i'll add individual listener checks yet. unsure on speed of any_listeners
    async def handle_usernotice(self, ctx):
        dprs = ctx.__dict__
        dprs['send'] = self.proxy_send_obj(ctx.channel)

        if hasattr(ctx, 'display_name'):
            dprs['user'] = ctx.display_name
            del dprs['display_name']
        else:
            dprs['user'] = ctx.login
        del dprs['login']

        prs = None

        if ctx.msg_id in ('sub', 'resub', 'extendsub', 'primepaidupgrade', 'communitypayforward', 'standardpayforward',
                          'subgift', 'anonsubgift', 'submysterygift', 'giftpaidupgrade', 'anongiftpaidupgrade'):
            dprs['message'] = hints.Message(dprs['user'], ctx.channel, ctx.message if hasattr(ctx, 'message') else None)
            prs = make_dataclass('SUBSCRIPTION', [tuple([k, v]) for k, v in dprs.items()])(**dprs)
            await self.call_listeners(f'sub:{prs.msg_id}', ctx=prs)  # this covers anysub, just use "sub" as the event

        elif ctx.msg_id == 'raid':
            dprs['raider'] = dprs['msg_param_displayName'] if 'msg_param_displayName' in dprs else dprs['msg_param_login']
            dprs['viewers'] = dprs['msg_param_viewerCount']

            prs = make_dataclass(ctx.msg_id.upper(), [tuple([k, v]) for k, v in dprs.items()])(**dprs)
            await self.call_listeners(f'{ctx.msg_id}:{prs.channel}', ctx=prs)

        elif ctx.msg_id == 'ritual':
            dprs['name'] = dprs['msg_param_ritual_name']
            prs = make_dataclass(ctx.msg_id.upper(), [tuple([k, v]) for k, v in dprs.items()])(**dprs)
            await self.call_listeners(f'{ctx.msg_id}:{prs.name}', ctx=prs)  # this will be new new catergory format "listener:sub_type"
            if prs.name != 'new_chatter':
                log.debug(prs)  # just incase new rituals are added

        # This is for generic items that don't need to be processed.
        elif ctx.msg_id in ('unraid',  # called when a raid is cancelled. doesn't give a raid target
                            'bitsbadgetier',  # i documented this above but never looked into it. only a few examples, no idea what it does
                            'announcement',  # This is super new.
                            'midnightsquid'):  # Midnightsquid is a 2022 cheering experiment with actual currency.
            prs = make_dataclass(ctx.msg_id.upper(), [tuple([k, v]) for k, v in dprs.items()])(**dprs)
            await self.call_listeners(ctx.msg_id, ctx=prs)

        else:
            log.debug('THE FOLLOWING MSG_ID IS NOT BEING HANDLED PROPERLY.')
            log.debug(ctx)
            if hasattr(ctx, 'msg_id'):
                prs = make_dataclass(ctx.msg_id.upper(), [tuple([k, v]) for k, v in dprs.items()])(**dprs)
                await self.call_listeners(prs.msg_id, ctx=prs)
                log.debug(prs)
            log.debug("WE'VE TRIED TO MAKE IT WORK FOR YOU THIS TIME.\nPLEASE CONTACT THE DEVELOPER.")

        prs = make_dataclass(type(ctx).__name__, [tuple([k, v]) for k, v in dprs.items()])(**dprs)
        await self.call_listeners(type(ctx).__name__.lower(), ctx=prs)

    @dispatch('clearchat')  # CLEARCHAT(ban_duration=60, room_id=22484632, target_user_id=42935983, tmi_sent_ts=1652203009894, message='narehawk', server=':tmi.twitch.tv', channel='#forsen')
    async def handle_clearchat(self, ctx):
        if not self.any_listeners('clearchat'): return
        dprs = ctx.__dict__
        dprs['target'] = dprs.get('message')
        if hasattr(ctx, 'message'): del dprs['message']
        prs = make_dataclass(type(ctx).__name__, [tuple([k, v]) for k, v in dprs.items()])(**dprs)
        await self.call_listeners(type(ctx).__name__.lower(), ctx=prs)
        if prs.target is None:
            log.debug(prs)

    @dispatch('hosttarget')  # HOSTTARGET(message='froggirlgaming 6', server='tmi.twitch.tv', channel='#xcup_of_joe')
    async def handle_hosttarget(self, ctx):
        if not self.any_listeners('host', 'unhost', 'hosttarget'): return
        dprs = ctx.__dict__
        target, dprs['viewers'] = ctx.message.split(' ')
        del dprs['message']
        if dprs['viewers'] == '-':
            dprs['viewers'] = 0
        focus = 'unhost'
        if target != '-':
            dprs['target'] = target
            focus = 'host'
        dprs['viewers'] = int(dprs['viewers'])
        prs = make_dataclass(focus.upper(), [tuple([k, v]) for k, v in dprs.items()])(**dprs)
        await self.call_listeners('hosttarget', ctx=prs)  # this is sent regardless of focus
        await self.call_listeners(focus, ctx=prs)

    @dispatch('whisper')
    async def handle_whisper(self, ctx):  # you cannot send a whisper from irc so i'm not gonna include a send object
        if not self.any_listeners('whisper'): return
        dprs = ctx.__dict__
        if hasattr(ctx, 'display_name'):
            dprs['user'] = ctx.display_name
            del dprs['display_name']
        dprs['message'] = hints.Message(dprs['user'], ctx.channel, ctx.message if hasattr(ctx, 'message') else None)
        prs = make_dataclass(type(ctx).__name__, [tuple([k, v]) for k, v in dprs.items()])(**dprs)
        await self.call_listeners(type(ctx).__name__.lower(), ctx=prs)

    # This is a complex function, and it has a high "Cognitive Complexity", beyond the limit of 15.
    def start(self, token, nick, channels=None) -> None:
        self.token = token
        self.nick = nick

        if not self.dbaddress:
            self.dbaddress = 'sqlite:///elenabot.sqlite'  # default

        self.database = dataset.connect(self.dbaddress, engine_kwargs={'pool_recycle': 3600})

        tab = self.database.create_table('incoming')
        # tab.create_column('timestamp', self.database.types.datetime(6))
        tab.create_column_by_example('timestamp', datetime.utcnow())
        tab.create_column_by_example('channel', self.nick)
        tab.create_column_by_example('event', self.nick)
        tab.create_column('data', LargeBinary())
        # tab.create_column_by_example('event', b'')
        try:  # we want this but things like SQLite don't do this so yeah
            self.database.query("ALTER TABLE `incoming` COLLATE='utf8mb4_unicode_ci', CHANGE COLUMN `timestamp` `timestamp` DATETIME(6) NULL DEFAULT NULL AFTER `id`;")
        except Exception:
            pass

        async def wsloop():
            async with aiohttp.ClientSession().ws_connect(f'{self.host}:{self.port}', heartbeat=10) as self.sock:
                log.debug(f'Attempting to connect to {self.host}:{self.port}')
                await self.sock.send_str("CAP REQ :twitch.tv/membership twitch.tv/tags twitch.tv/commands")
                await self.sock.send_str(f"PASS {self.token}")
                await self.sock.send_str(f"NICK {self.nick}")
                await self.join(channels)
                async for msg in self.sock:
                    if msg.type != aiohttp.WSMsgType.TEXT:
                        log.debug(f'Unknown WSMessage Type: {msg.type}')
                        continue
                    for line in msg.data.split("\r\n")[:-1]:  # ?!?
                        if line == 'PING :tmi.twitch.tv':
                            await self.sock.send_str('PONG :tmi.twitch.tv')
                            if __debug__:
                                log.info('Server sent PING. We sent PONG.')
                            continue
                        elif line == ':tmi.twitch.tv RECONNECT':  # the parser will parse this, but i want it to be very explicitly handled
                            await self.sock.close()
                            continue
                        try:
                            notice = self.twitch_irc_formatter(line)
                        except Exception as exc:
                            log.exception(exc)
                            log.debug(line)
                            continue
                        name = type(notice).__name__.lower()
                        if rx_positive.match(name):
                            name = int(name)
                        if name in _handlers:
                            try:
                                await _handlers[name](self, ctx=notice)
                            except Exception as exc:
                                log.exception(exc)
                                log.debug(notice)
                        else:  # NOTICE NOT HANDLED, LOG AND NOTIFY
                            log.debug('THE FOLLOWING NOTICE IS NOT BEING HANDLED PROPERLY.')
                            log.debug(notice)
                            await self.call_listeners(type(notice).__name__.lower(), ctx=notice)
                            log.debug("WE'VE TRIED TO MAKE IT WORK FOR YOU THIS TIME.\nPLEASE CONTACT THE DEVELOPER.")

                log.info('WebSocket has been closed!')
                if hasattr(self, 'jointask'):
                    self.__jointask.cancel()
                    self.__joinqueue = Queue()

        def attempt_connection():
            success, ret = self.attempt(asyncio.run, wsloop())
            if success is not None:
                log.debug(ret)

            # con.commit()
            self.attempt(asyncio.run, asyncio.sleep(1))

        if not self.auto_reconnect:
            attempt_connection()
            return

        while self.auto_reconnect:
            attempt_connection()

        log.info('Auto Reconnect has been disabled, and the program has stopped.')

    async def join(self, channels: Union[list, str]):
        channels = [channels] if isinstance(channels, str) else channels

        channels = [chan for chan in channels if chan not in self.__channels]
        if not channels:
            if hasattr(self, 'jointask') and self.__jointask.done():
                for chan in self.__channels:
                    self.__joinqueue.put(chan)
            return
        for chan in channels:
            self.__channels.append(chan)
            self.__joinqueue.put(chan)

    async def _join(self) -> None:  # i dont like this, but there's no other way to really do this
        while True:
            if not self.__joinqueue.empty():
                channel = self.__joinqueue.get()
                c = self.merge(channel)
                await self.sock.send_str(f"JOIN {c}")
                log.info(f'Joined {c}')
                self.__outgoing[c] = []

            await asyncio.sleep(0.5)  # 20 times per 10 seconds, 2 times a second

    async def part(self, channels: Union[list, str]) -> None:  # i made it work
        channels = [channels] if isinstance(channels, str) else channels
        channels = [self.split(x) for x in channels]
        channels = [chan for chan in channels if chan in self.__channels]
        if not channels: return

        for chan in channels:
            c = self.merge(chan)
            await self.sock.send_str(f"PART {c}")
            log.info(f'Left {c}')

            self.__channels.remove(chan)

    @event('any')
    async def log_incoming(self, ctx):
        if type(ctx).__name__ in ['JOIN', 'PART']:
            return
        channel = None
        if hasattr(ctx, 'channel'):
            channel = ctx.channel
        event_data = asdict(ctx)
        if 'send' in event_data: 
            del event_data['send']
        self.database['incoming'].insert(dict(
            timestamp=datetime.utcnow(),
            channel=channel,
            event=str(ctx),
            data=msgpack.packb({type(ctx).__name__: event_data})
        ))

    @event('message', 'sub')
    async def log_messageable(self, ctx: hints.Messageable) -> None:
        if type(ctx).__name__ == 'PRIVMSG' and ctx.action:
            log.info(f'ACTION {ctx.message.channel} >>> {ctx.message.author}: {ctx.message.content}')
            return
        log.info(f'{type(ctx).__name__} {ctx.message.channel} >>> {ctx.message.author}: {ctx.message.content}')

    @event('userstate')
    async def verify_outgoing_approve(self, ctx):
        if not self.__outgoing[ctx.channel]: return
        msg = self.__outgoing[ctx.channel].pop(0)
        log.info(f'SENT {ctx.channel} >>> {ctx.user}: {msg}')
        # cur.execute('insert into msg_sent values (?, ?)', (ctx.channel, msg,))
        # con.commit()

    @event('notice')
    async def verify_outgoing_deny(self, ctx):
        if not ctx.msg_id.startswith('msg'): return
        if ctx.msg_id == 'msg_banned':  # ban me bitches, im tired of this throwing errors cuz im on a bot list
            # cur.execute('insert into msg_banned values (?)', (ctx.channel,))
            # con.commit()
            return
        msg = self.__outgoing[ctx.channel].pop(0)
        log.info(f'FAIL {ctx.channel} >>> {self.nick}: {msg}')
        # cur.execute('insert into msg_denied values (?, ?)', (ctx.channel, msg,))
        # con.commit()

    @event('notice')
    async def log_notices(self, ctx: hints.NOTICE):
        func = log.info if __debug__ else log.debug
        func(f'NOTICE({ctx.msg_id}): {ctx.channel} >>> {ctx.message}')

    @event('cap')
    async def get_cap(self, ctx):
        log.info(ctx)

    def attempt(self, func, *args, **kwargs) -> Any:
        try:
            return True, func(*args, **kwargs)
        except Exception as exc:
            return False, exc

    def any_listeners(self, *events):  # this is in an attempt to not construct a event object unless there's an event registered
        if __debug__: return True
        for event in _listeners:
            if ':' in event:
                if event.split(':')[0] in events:
                    return True
            else:
                if event in events:
                    return True
        return False

    async def _lcall(self, event: str, **kwargs):
        if event not in _listeners: return
        for func in _listeners[event]:
            await func(self, **kwargs)

    async def call_listeners(self, event: str, **kwargs) -> None:  # this is all overcomplicated
        if ':' in event: await self._lcall(event.split(':')[0], **kwargs)  # we call the base event here. simplifies coding subevents
        await self._lcall(event, **kwargs)
        if 'any' not in event:
            await self._lcall('any', **kwargs)

    def func_on_cooldown(self, func: Callable, time: int) -> bool:
        time_now = datetime.utcnow()
        if func in self.__cooldowns:
            if (time_now - self.__cooldowns[func]).seconds >= time:
                self.__cooldowns[func] = time_now
                return False
        else:
            self.__cooldowns[func] = time_now
            return False
        return True

    async def send(self, message: str, channel: str) -> None:
        if __debug__: return  # since i do a lot of debugging, i dont want to accidentally send something in a chat
        await self.sock.send_str(f'PRIVMSG {channel} :{message}')  # placement of the : is important :zaqPbt:
        self.__outgoing[channel].append(message)
        # cur.execute('insert into outgoing values (?, ?)', (channel, message,))

    def maximize_msg(self, content: str, offset: int = 0) -> str:
        return self.fill_msg(content, 500 - offset)

    def fill_msg(self, content: str, length: int = 500) -> str:
        return content * math.trunc(length / len(content))  # need to trunc cuz we always round down

    def merge(self, channel: str):  # name isn't appropriate for use-case
        return channel.lower() if channel[0] == '#' else '#' + channel.lower()

    def split(self, channel: str):  # name isn't appropriate for use-case
        return channel[1:].lower() if channel[0] == '#' else channel.lower()
