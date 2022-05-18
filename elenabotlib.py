"""
    This only implements a simple chatbot.

    Inherit from Session class to use.

    Copyright 2021-present ElenaWinters
    References:
        Twitch IRC Guide
        Rinbot by RingoMär
        TwitchDev samples

"""

from typing import Any, Callable, Union
from dataclasses import make_dataclass
from hints import USERSTATE, Badge, Message, Messageable, PRIVMSG
from queue import Queue
import traceback
import datetime
import aiohttp
import asyncio
import inspect
import logging
import struct
import time
import math
import sys
import re


log = logging.getLogger(__name__)


async def cancelCall():  # i need to return an async function and i cant do an async lambda. i hate it. if i find a way, i'll get rid of this
    return


def event(name: str = 'any', *extras) -> Callable:  # listener/decorator for any event
    events = list(extras)
    events.append(name)

    def wrapper(func: Callable) -> Callable:
        for event in events:
            add_listener(func, event)
        return func
    return wrapper


events = event


def cooldown(time: int) -> Callable:
    def decorator(func: Callable) -> Callable:
        def wrapper(self: Session, ctx) -> Callable:
            if self.func_on_cooldown(func, time):
                # log.debug(f'{func.__name__} is on cooldown!')
                return cancelCall()
            return func(self, ctx)
        return wrapper
    return decorator


def ignore_myself() -> Callable:
    def decorator(func: Callable) -> Callable:
        def wrapper(self: Session, ctx: Messageable) -> Callable:
            if ctx.user.lower() != self.nick:
                return func(self, ctx)
            return cancelCall()
        return wrapper
    return decorator


def author(*names) -> Callable:  # check author
    def decorator(func: Callable) -> Callable:
        def wrapper(self: Session, ctx: Messageable) -> Callable:
            if any(ctx.user.lower() == name.lower() for name in list(names)):
                return func(self, ctx)
            return cancelCall()
        return wrapper
    return decorator


authors = author


def channel(*names) -> Callable:  # check channel
    def decorator(func: Callable) -> Callable:
        def wrapper(self: Session, ctx: Messageable) -> Callable:
            def adapt(_name: str) -> str:
                return _name if _name[0] == '#' else f'#{_name}'
            if any(ctx.channel == adapt(name) for name in list(names)):
                return func(self, ctx)
            return cancelCall()
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
        def wrapper(self: Session, ctx: Messageable) -> Callable:
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
                    return cancelCall()
                return func(self, ctx)
            return cancelCall()
        return wrapper
    return decorator


class DebugFilter(logging.Filter):
    def filter(self, record):
        if record.levelno >= 40:
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


def add_listener(func, name='any') -> None:
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

    """
        There used to be a logger here, but it's rather finicky.
        If this program is wrapped, the logs would appear.
        If the program isn't, the log messages would NOT appear.
        The botUI.py would log, but the bot.py would not.

        The listeners appended also reference the function right after the event is registered.
        So, an @event followed by an @message would show the wrapper function inside the message decorator function.
        But, a single @event would show the actual function.

        The log call has been removed because of these reasons.
        You can call `len(_listeners)` to get the number of registered events.
    """


rx_ampersat = re.compile(r'([-\w]+)=(.*?)(;| :)')
rx_positive = re.compile(r'^\d+$')
rx_353 = re.compile(r'\w+')


class Session(object):
    def __init__(self) -> None:
        self.host = 'ws://irc-ws.chat.twitch.tv'
        self.port = 80
        self.cooldowns = {}
        self.channels = []
        self.joinqueue = Queue()

        self.last = ''

    # Refactor this function to reduce its Cognitive Complexity from 36 to the 15 allowed. Note: I'm not gonna try to reduce the complexity.
    def TwitchIRCFormatter(self, original: str = '@badge-info=gay/4;badges=lesbian/3,premium/1;user-type=awesome :tmi.twitch.tv GAYMSG #zaquelle :This is kinda gay'):  # tested with every @ based message. parses correctly.
        array = original[1:].split(' ')  # Indexes | 0 = Server, 1 = Notice, 2 = Channel, 3+ = Message (Broken up, use Regex)
        offset = 0
        info = {}
        if original.startswith('@'):
            offset = 1
            for k, v, _ in rx_ampersat.findall(original):
                k = k.replace('-', '_')
                if k in ('badge_info', 'badges'):  # converts for specific fields
                    badges = []
                    for entry in v.split(','):
                        if badge := re.search(r'(.+?)/(.+)', entry):
                            version = badge.group(2).replace('\\s', ' ')
                            if rx_positive.match(version):
                                version = int(version)
                            badges.append(Badge(name=badge.group(1), version=version))
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
                        v = int(v)
                    elif v == 'false':
                        v = False
                    elif v == 'true':
                        v = True
                    info[k] = v

        if len(array) - 1 >= 2 + offset:  # this is so sketch but it works. basically, check if a channel is provided
            info['channel'] = array[2 + offset]  # force channel
            message = re.search(f"{array[1 + offset]} {info['channel']}" + r'..(.*)', original)
            if message: info['message'] = message.group(1)

        user = re.search(r"([a-zA-Z0-9-_\w]+)!([a-zA-Z0-9-_\w]+)@([a-zA-Z0-9-_\w]+)", array[0 + offset])
        if user and f'{user.group(1)}!{user.group(1)}@{user.group(1)}' in array[0 + offset]:
            info['user'] = user.group(1)  # we verify the user

        if __debug__:  # include server if in debug mode. this isn't useful for most cases.
            info['server'] = array[0 + offset]
        prs = make_dataclass(array[1 + offset], [tuple([k, v]) for k, v in info.items()])
        return prs(**info)

    def proxy_send_obj(self, channel: str):
        async def _send_proxy(message: str):  # construct send function that can be called from ctx)
            await self.send(message, channel)
        return _send_proxy

    @dispatch(1, 2, 3, 4, 372, 376, 366)
    async def sinkhole(self, ctx):  # I'm not currently parsing these as I don't need to.
        await self.call_listeners(type(ctx).__name__, ctx=ctx)

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
        users = rx_353.findall(ctx.message)
        channel = users.pop(0)

        for user in users:
            if user == self.nick: continue
            prs = make_dataclass('JOIN', [tuple(['user', str]), tuple(['channel', str])])
            await self.call_listeners(f'join:{user}', ctx=prs(user=user, channel=f'#{channel}'))

    @dispatch(375)
    async def handle_375(self, ctx):
        log.info(f"Connected! Environment is {'DEBUG' if __debug__ else 'PRODUCTION'}.")
        loop = asyncio.get_running_loop()
        self.jointask = loop.create_task(self._join())

    @dispatch(421)  # UNKNOWN IRC COMMAND
    async def unknown_command_irc(self, ctx):
        log.debug(f"An IRC command was sent to the server, and they didn't recognize it. Here is what the server told us:\n{ctx}")

    @dispatch('cap')
    async def handle_cap(self, ctx):
        pass  # ENSURE CAP
        # dprs = ctx.__dict__
        # if hasattr(ctx, 'channel'): del dprs['channel']
        # prs = make_dataclass(type(ctx).__name__, [tuple([k, v]) for k, v in dprs.items()])
        # await self.call_listeners(type(ctx).__name__.lower(), ctx=prs(**dprs))

    @dispatch('globaluserstate')  # I usually format display_name to user but I don't want to do that with GUS
    async def handle_globaluserstate(self, ctx):  # ALWAYS SET THIS
        dprs = ctx.__dict__
        dprs['user'] = ctx.display_name
        del dprs['display_name']
        prs = make_dataclass(type(ctx).__name__, [tuple([k, v]) for k, v in dprs.items()])(**dprs)
        await self.call_listeners(type(ctx).__name__.lower(), ctx=prs)
        self.gsu = ctx  # i know that this isn't the right acronym but i dont care

    @dispatch('privmsg', 'userstate')
    async def handle_messageable(self, ctx: Union[PRIVMSG, USERSTATE]):
        if not self.any_listeners('message', 'userstate'): return
        dprs = ctx.__dict__
        if hasattr(ctx, 'display_name'):
            dprs['user'] = ctx.display_name
            del dprs['display_name']
        dprs['send'] = self.proxy_send_obj(ctx.channel)
        prs = make_dataclass(type(ctx).__name__, [tuple([k, v]) for k, v in dprs.items()])(**dprs)
        if bool(type(ctx).__name__ == 'PRIVMSG'):
            prs.message = Message(dprs['user'], ctx.channel, ctx.message)
            await self.call_listeners('message', ctx=prs)
        await self.call_listeners(type(ctx).__name__.lower(), ctx=prs)

    @dispatch('roomstate', 'notice', 'clearmsg')
    async def handle_generic(self, ctx):
        if not self.any_listeners('roomstate', 'notice', 'clearmsg'): return
        dprs = ctx.__dict__
        dprs['send'] = self.proxy_send_obj(ctx.channel)
        prs = make_dataclass(type(ctx).__name__, [tuple([k, v]) for k, v in dprs.items()])(**dprs)
        await self.call_listeners(type(ctx).__name__.lower(), ctx=prs)

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
            dprs['message'] = Message(dprs['user'], ctx.channel, ctx.message if hasattr(ctx, 'message') else None)
            prs = make_dataclass('SUBSCRIPTION', [tuple([k, v]) for k, v in dprs.items()])(**dprs)
            await self.call_listeners(f'sub:{prs.msg_id}', ctx=prs)  # this covers anysub, just use "sub" as the event

        elif ctx.msg_id == 'raid':
            dprs['raider'] = dprs['msg_param_displayName'] if dprs['msg_param_displayName'] else dprs['msg_param_login']
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

    # Refactor this function to reduce its Cognitive Complexity from 53 to the 15 allowed. Note: I'm not gonna try to reduce the complexity.
    def start(self, token, nick, channels=None) -> None:
        self.token = token
        self.nick = nick

        ws_timeout = aiohttp.ClientTimeout()

        async def wsloop():
            async with aiohttp.ClientSession(timeout=ws_timeout).ws_connect(f'{self.host}:{self.port}') as self.sock:
                log.debug(f'Attempting to connect to {self.host}:{self.port}')
                await self.sock.send_str("CAP REQ :twitch.tv/membership twitch.tv/tags twitch.tv/commands")
                await self.sock.send_str(f"PASS {self.token}")
                await self.sock.send_str(f"NICK {self.nick}")
                await self.join(channels)
                async for msg in self.sock:
                    if msg.type != aiohttp.WSMsgType.TEXT:  # guard clause? cleaner code overall
                        log.debug(f'Unknown WSMessage Type: {msg.type}')
                        continue
                    for line in msg.data.split("\r\n")[:-1]:  # ?!?
                        if line == 'PING :tmi.twitch.tv':
                            await self.sock.send_str('PONG :tmi.twitch.tv')
                            if __debug__:
                                log.info('Server sent PING. We sent PONG.')
                            continue
                        if 'RECONNECT' in line:
                            log.debug(line)
                            log.debug(notice)
                        try:
                            notice = self.TwitchIRCFormatter(line)
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
                    self.jointask.cancel()
                    self.joinqueue = Queue()

        def run_loop():
            try:
                asyncio.run(wsloop())
            except Exception as exc:
                log.exception(exc)

        if not __debug__:
            while True: run_loop()
        else:  # if debug, don't loop
            run_loop()

    async def join(self, channels: Union[list, str]):
        chans = []
        if isinstance(channels, str):
            chans.append(channels)
        if chans: channels = chans

        channels = [chan for chan in channels if chan not in self.channels]
        if not channels:
            if hasattr(self, 'jointask') and self.jointask.done():
                for chan in self.channels:
                    self.joinqueue.put(chan)
            return
        for chan in channels:
            self.channels.append(chan)
            self.joinqueue.put(chan)
        return

    async def _join(self) -> None:  # i dont like this, but there's no other way to really do this
        while True:
            if not self.joinqueue.empty():
                channel = self.joinqueue.get()
                c = channel.lower() if channel[0] == '#' else f'#{channel.lower()}'
                await self.sock.send_str(f"JOIN {c}")
                log.info(f'Joined {c}')

            await asyncio.sleep(0.5)  # 20 times per 10 seconds

    async def part(self, channels: Union[list, str]) -> None:  # this is currently untested
        chans = []
        if isinstance(channels, str):
            chans.append(channels)
        if chans: channels = chans
        channels = [chan for chan in channels if chan in self.channels]
        if not channels: return
        for chan in channels:
            self.channels.remove(chan)
        for x in channels:
            c = x.lower() if x[0] == '#' else f'#{x.lower()}'
            await self.sock.send_str(f"PART {c}")
            log.info(f'Left {c}')

    @event('message', 'sub')
    async def log_messageable(self, ctx: Messageable) -> None:
        log.info(f'{type(ctx).__name__} {ctx.message.channel} >>> {ctx.message.author}: {ctx.message.content}')

    def attempt(self, func, *args, **kwargs) -> Any:
        output = kwargs.get('output', True)
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            if not output: return
            log.exception(exc)

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
            # log.debug(type(func))
            # log.debug(func.__name__)
            await func(self, **kwargs)

    async def call_listeners(self, event: str, **kwargs) -> None:  # this is all overcomplicated
        # log.debug(kwargs.get('ctx', None))
        if ':' in event: await self._lcall(event.split(':')[0], **kwargs)  # we call the base event here. simplifies coding subevents
        await self._lcall(event, **kwargs)
        if 'any' not in event:
            await self._lcall('any', **kwargs)
            # if ctx := kwargs.get('ctx', None):
            #     self.log_to_console(ctx)

    def func_on_cooldown(self, func: Callable, time: int) -> bool:
        time_now = datetime.datetime.utcnow()
        if func in self.cooldowns:
            if (time_now - self.cooldowns[func]).seconds >= time:
                self.cooldowns[func] = time_now
                return False
        else:
            self.cooldowns[func] = time_now
            return False
        return True

    async def send(self, message: str, channel: str) -> None:
        if not __debug__:
            await self.sock.send_str(f'PRIVMSG {channel} :{message}')  # placement of the : is important :zaqPbt:

    def maximize_msg(self, content: str, offset: int = 0) -> str:  # max length is variable and this is static
        return content * math.trunc((500 - offset) / len(content))  # need to trunc cuz we always round down

    def fill_msg(self, content: str, length: int = 500) -> str:
        return content * math.trunc((length) / len(content))  # need to trunc cuz we always round down
