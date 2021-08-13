"""
    This only implements a simple chatbot.

    Inherit from Session class to use.

    Copyright 2021-present ElenaWinters
    References:
        Twitch IRC Guide
        Rinbot by RingoMär
        TwitchDev samples

"""

from dataclasses import dataclass, field
from typing import Any, Callable, Union
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


@dataclass
class Badge:
    name: str
    version: int


@dataclass
class Message:
    author: str = None
    channel: str = None
    content: str = None


@dataclass
class Messageable:
    message: Message = None
    send: str = None


@dataclass
class CLEARCHAT(Messageable):  # the minimum data that would be provided would just be the channel
    tmi_sent_ts: str = None
    ban_duration: int = None


@dataclass
class CLEARMSG(Messageable):
    target_msg_id: str = None
    login: str = None


@dataclass
class ROOMSTATE:
    channel: str = None
    emote_only: bool = False
    followers_only: int = -1
    r9k: bool = False
    slow: int = 0
    subs_only: bool = False
    send: str = None


@dataclass
class NOTICE(Messageable):
    msg_id: str = None


@dataclass
class GLOBALUSERSTATE:  # in this codebase, this is considered the base struct for most actions
    badge_info: list[Badge] = None  # prediction info goes here as well, for some reason
    badges: list[Badge] = None
    color: str = None
    display_name: str = None
    emote_sets: list[int] = None
    turbo: bool = False
    user_id: int = 0
    user_type: str = None


@dataclass
class USERSTATE(GLOBALUSERSTATE, Messageable):
    mod: bool = False
    subscriber: bool = False


@dataclass
class PRIVMSG(USERSTATE):
    bits: str = None
    emotes: list = None
    flags: list = None
    id: str = None
    room_id: int = 0
    tmi_sent_ts: int = 0
    action: bool = False


@dataclass
class USERNOTICEBASE(PRIVMSG):  # this is the baseclass for USERNOTICE. used by the subclasses
    system_msg: str = None
    msg_id: str = None
    login: str = None


@dataclass
class USERNOTICE(USERNOTICEBASE):  # there are a ton of params
    msg_param_cumulative_months: int = 0
    msg_param_displayName: str = None  # display name of raider
    msg_param_viewerCount: int = 0  # number of viewers raiding
    msg_param_login: str = None  # login name of raider
    msg_param_months: int = 0
    msg_param_promo_gift_total: str = None
    msg_param_promo_name: str = None
    msg_param_recipient_display_name: str = None
    msg_param_recipient_id: str = None
    msg_param_recipient_user_name: str = None
    msg_param_sender_login: str = None
    msg_param_sender_name: str = None
    msg_param_multimonth_tenure: int = 0  # not sure what this is. it's not in the spec, but found it in sub messages. always 0?
    msg_param_should_share_streak: int = 0
    msg_param_streak_months: int = 0
    msg_param_sub_plan_name: str = None
    msg_param_sub_plan: str = None  # this can be a string or number
    msg_param_was_gifted: bool = False
    msg_param_ritual_name: str = None  # lol what? this is in the spec
    msg_param_threshold: int = 0
    msg_param_gift_months: int = 0


# Here we implement some custom ones for the bot dev to use
# USERNOTICE subclasses
@dataclass
class SUBSCRIPTION(USERNOTICEBASE):  # This should be complete
    promo_total: int = 0
    promo_name: str = None
    cumulative: int = 0
    months: int = 0
    recipient: str = None
    recipient_id: str = None
    sender: str = None
    share_streak: bool = False
    streak: int = 0
    plan: str = None
    plan_name: str = None
    gifted_months: int = 0


@dataclass
class RITUAL(USERNOTICEBASE):  # yes this is a thing lol
    name: str = None


@dataclass
class RAID(USERNOTICEBASE):
    raider: str = None
    viewers: int = 0


class ReconnectReceived(Exception):
    pass


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


# _dataclasses = Union[Messageable, CLEARCHAT, ROOMSTATE, NOTICE, GLOBALUSERSTATE, USERSTATE,
#                      PRIVMSG, USERNOTICEBASE, USERNOTICE, SUBSCRIPTION, RITUAL, RAID]
_listeners = {}


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

    log.debug(f'Added {func.__name__} to {name} handler.')


class Session(object):
    def __init__(self) -> None:
        self.host = 'ws://irc-ws.chat.twitch.tv'
        self.port = 80
        self.cooldowns = {}
        self.channels = []

        self.last = ''

    def start(self, token, nick, channels=None) -> None:
        self.token = token
        self.nick = nick

        self.loop = asyncio.get_event_loop()

        async def wsloop():
            async with aiohttp.ClientSession().ws_connect(f'{self.host}:{self.port}') as ws:
                self.sock = ws
                await self.connect()
                await self.join(channels)
                async for msg in self.sock:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        await self.parse(msg.data)
                        await self.ping(msg.data)
                    else:
                        log.debug(f'Unknown WSMessage Type: {msg.type}')

        self.loop.run_until_complete(wsloop())
        # await self.recv()

        # self.loop = asyncio.get_event_loop()
        # while True:
        #     # self.connect()
        #     if channels:
        #         self.join(channels)
        #     self.loop()

    async def recv(self) -> None:
        while True:
            try:
                self.receive()
            except (ConnectionResetError, ConnectionAbortedError, ReconnectReceived) as exc:
                # TODO: CLOSE CONNECTION? THIS SHOULD BE AUTOMATICALLY DONE
                # self.sock.shutdown(socket.SHUT_RDWR)
                # self.sock.close()
                log.error(f'Reconnecting: {type(exc).__name__}: {exc}')
                # log.exception(exc)
                return
            except Exception as e:
                log.exception(e)

    # def shutdown(self) -> None:
    #     self.sock.shutdown(socket.SHUT_RDWR)
    #     self.sock.close()
    #     sys.exit(0)

    async def socksend(self, sock_msg) -> None:  # removes the need to do the converting and stuff
        await self.sock.send_str(sock_msg)
        # self.sock.post(f"{sock_msg}\r\n".encode("utf-8"))

    async def connect(self) -> None:
        log.debug(f'Attempting to connect to {self.host}:{self.port}')
        try:
            # self.sock.connect((self.host, self.port))  # only called once, not worth writing seperate wrapper
            await self.socksend(f"PASS {self.token}")
            await self.socksend(f"NICK {self.nick}")
            await self.socksend("CAP REQ :twitch.tv/tags")
            await self.socksend("CAP REQ :twitch.tv/membership")
            await self.socksend("CAP REQ :twitch.tv/commands")
        except Exception as exc:
            log.exception(f'Error occured while connecting to WebSocket: ', exc_info=exc)
        else:
            log.info('Connected')

    async def join(self, channels: Union[list, str]) -> None:
        channels = channels if type(list) else list(channels)
        self.channels.append(channels)
        for x in channels:
            c = x.lower() if x[0] == '#' else f'#{x.lower()}'
            await self.socksend(f"JOIN {c}")
            log.info(f'Joined {c}')
            await self.call_listeners('join_self', channel=c)

    async def part(self, channels: Union[list, str]) -> None:  # this is currently untested
        channels = channels if type(list) else list(channels)
        self.channels.remove(channels)
        for x in channels:
            c = x.lower() if x[0] == '#' else f'#{x.lower()}'
            self.socksend(f"PART {c}")
            log.info(f'Left {c}')
            await self.call_listeners('part_self', channel=c)

    async def pong(self) -> None:
        await self.socksend("PONG :tmi.twitch.tv")
        # log.debug('Server sent PING. We sent PONG.')

    async def ping(self, line: str) -> None:
        if line == "PING :tmi.twitch.tv":
            await self.pong()

    def cast(self, dclass, data) -> dict:
        items = {}
        if not hasattr(dclass, '__annotations__'):
            return {}  # return if not dataclass
        for k in dclass.__annotations__:
            item = re.search(k.replace('_', '-') + r'=([a-zA-Z0-9-/_,#\w]+)', data)
            if item:
                items[k] = item.group(1)

        # next step is to go through base classes and run the same thing on them
        for bclass in dclass.__bases__:
            items.update(self.cast(bclass, data))

        return items

    def log_to_console(self, ctx: Messageable) -> None:
        if hasattr(ctx, 'message') and hasattr(ctx.message, 'content') and ctx.message.content:
            log.info(f'{type(ctx).__name__} {ctx.message.channel} >>> {ctx.message.author}: {ctx.message.content}')

    def attempt(self, func, *args, **kwargs) -> Any:
        output = kwargs.get('output', True)
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            if not output: return
            log.exception(exc)

    def parse_base(self, dprs: dict) -> dict:  # this needs to be done with dictionaries unfortunately
        for badge_type in ('badge_info', 'badges'):
            if badge_type in dprs:
                dprs[badge_type] = [Badge(*badge.split('/')) for badge in dprs[badge_type].split(',')]
        for emote_type in ('emote_sets', 'emotes'):
            if emote_type in dprs:
                dprs[emote_type] = [x for x in dprs[emote_type].split(',')]
        return dprs

    def prs_conv(self, prs: GLOBALUSERSTATE):  # i hate this already but what you gonna do
        for field in prs.__dataclass_fields__.values():
            entry = getattr(prs, field.name)
            if not isinstance(entry, type(None)) and type(field.type) == type and not isinstance(entry, field.type):
                if field.type == bool:
                    entry = self.attempt(int, entry, output=False)
                # log.debug(f'{type(entry)}: {field.type}: {type(field.type)}: {type}')
                self.attempt(setattr, prs, field.name, field.type(entry))

    def create_prs(self, dclass, line: str):  # 'prs' is short for 'parsed'
        dprs = self.cast(dclass, line)
        dprs = self.parse_base(dprs)
        prs = dclass(**dprs)
        self.prs_conv(prs)
        return prs

    def parse_channel(self, chan: str, line: str):
        class_name = chan if isinstance(chan, str) else type(chan).__name__
        return re.search(f'{class_name} ' + r"(#[a-zA-Z0-9-_\w]+)", line).group(1)

    def proxy_send_obj(self, prs: Messageable, channel: str):
        async def _send_proxy(message: str):  # construct send function that can be called from ctx
            await self.send(message, channel)
        prs.send = _send_proxy

    def parse_privmsg(self, prs: Messageable, line: str, oprs: Messageable = None) -> None:  # user regex provided by RingoMär <3
        class_name = type(oprs).__name__ if oprs else type(prs).__name__  # basically only for the usernotice subcalls
        try:
            user = re.search(r":([a-zA-Z0-9-_\w]+)!([a-zA-Z0-9-_\w]+)@([a-zA-Z0-9-_\w]+)", line).group(1)
        except AttributeError:
            user = "Anon"

        channel = self.parse_channel(class_name, line)
        msg = re.search(f'{class_name} {channel}' + r'..(.*)', line)
        if msg: msg = msg.group(1)

        prs.message = Message(user, channel, msg)

        self.proxy_send_obj(prs, channel)
        # def _send_proxy(message: str):  # construct send function that can be called from ctx
        #     self.send(message, channel)
        # prs.send = _send_proxy

    def parse_action(self, prs: PRIVMSG) -> None:
        SOH = chr(1)  # ASCII SOH (Start of Header) Control Character
        if hasattr(prs, 'message') and 'ACTION' in prs.message.content and SOH in prs.message.content:
            prs.message.content = prs.message.content[len(SOH + 'ACTION '):-len(SOH)]
            prs.action = True

    def swap_message_order(self, prs: Messageable) -> None:  # sometimes the author and content order is incorrect. we can call this to swap them around
        author = prs.message.content
        content = prs.message.author

        prs.message.content = content if content != 'Anon' else None
        prs.message.author = author

    def format_display_name(self, prs: USERNOTICEBASE) -> None:
        if hasattr(prs, 'login') and prs.login:
            prs.message.author = prs.login
        if not hasattr(prs, 'display_name'): return
        if not prs.display_name:
            prs.display_name = prs.message.author
        else:
            prs.message.author = prs.display_name

    async def parse_ritual(self, oprs: USERNOTICE, line: str) -> None:
        prs = self.create_prs(RITUAL, line)
        self.parse_privmsg(prs, line, oprs)
        self.format_display_name(prs)

        prs.name = oprs.msg_param_ritual_name
        await self.call_listeners(f'ritual:{prs.name}', ctx=prs)  # this will be new new catergory format "listener:sub_type"
        if prs.name != 'new_chatter':
            log.debug(prs)  # just incase new rituals are added

    async def parse_subscription(self, oprs: USERNOTICE, line: str) -> None:
        prs = self.create_prs(SUBSCRIPTION, line)
        self.parse_privmsg(prs, line, oprs)
        self.format_display_name(prs)

        # this will be revisited to dataclass some of these things together
        prs.promo_total = oprs.msg_param_promo_gift_total
        prs.promo_name = oprs.msg_param_promo_name
        prs.cumulative = oprs.msg_param_cumulative_months
        prs.months = oprs.msg_param_months
        prs.recipient = oprs.msg_param_recipient_display_name if oprs.msg_param_recipient_display_name else oprs.msg_param_recipient_user_name
        prs.recipient_id = oprs.msg_param_recipient_id
        prs.sender = oprs.msg_param_sender_name if oprs.msg_param_sender_name else oprs.msg_param_sender_login
        prs.share_streak = oprs.msg_param_should_share_streak
        prs.streak = oprs.msg_param_streak_months
        prs.plan = oprs.msg_param_sub_plan
        prs.plan_name = oprs.msg_param_sub_plan_name
        prs.gifted_months = oprs.msg_param_gift_months

        # self.call_listeners(f'subscription:{oprs.msg_id}', ctx=prs)
        await self.call_listeners(f'sub:{oprs.msg_id}', ctx=prs)
        await self.call_listeners('anysub', ctx=prs)

    async def parse_raid(self, oprs: USERNOTICE, line: str) -> None:
        prs = self.create_prs(RAID, line)
        self.parse_privmsg(prs, line, oprs)
        self.format_display_name(prs)

        prs.raider = oprs.msg_param_displayName if oprs.msg_param_displayName else oprs.msg_param_login
        prs.viewers = oprs.msg_param_viewerCount

        await self.call_listeners('raid', ctx=prs)

    async def parse(self, line: str) -> None:  # use an elif chain or match case (maybeeee down the line)
        if 'PRIVMSG' in line and line[0] == '@':
            prs = self.create_prs(PRIVMSG, line)
            self.parse_privmsg(prs, line)
            self.format_display_name(prs)
            self.parse_action(prs)

            # log.debug(f'{prs.display_name} and {prs.message.author}')

            await self.call_listeners('message', ctx=prs)

        elif 'USERNOTICE' in line and line[0] == '@':
            prs = self.create_prs(USERNOTICE, line)
            self.parse_privmsg(prs, line)
            self.format_display_name(prs)

            await self.call_listeners('usernotice', ctx=prs)

            # these are the valid msg_id's
            # sub, resub, subgift, anonsubgift, submysterygift, giftpaidupgrade, rewardgift, anongiftpaidupgrade, raid, unraid, ritual, bitsbadgetier
            # undocumented: extendsub, primepaidupgrade

            # I don't like having to put subs in multiple cases, but Python does not allow wraparound with SPM.

            match prs.msg_id:
                case 'sub' | 'resub' | 'extendsub' | 'primepaidupgrade':
                    await self.parse_subscription(prs, line)
                case 'subgift' | 'anonsubgift' | 'submysterygift' | 'giftpaidupgrade' | 'anongiftpaidupgrade':
                    await self.parse_subscription(prs, line)
                case 'unraid':
                    await self.call_listeners('unraid', ctx=prs)
                case 'raid':
                    await self.parse_raid(prs, line)
                case 'ritual':
                    await self.parse_ritual(prs, line)
                case _:  # other cases for testing
                    log.debug(line)
                    log.debug(prs)

        elif 'RECONNECT' in line:  # user influence shouldn't be possible
            raise ReconnectReceived('Server sent RECONNECT.')

        elif 'ROOMSTATE' in line and line[0] == '@':
            prs = self.create_prs(ROOMSTATE, line)
            prs.channel = self.parse_channel(prs, line)
            self.proxy_send_obj(prs, prs.channel)
            await self.call_listeners('roomstate', ctx=prs)
            log.info(prs)

        elif 'USERSTATE' in line and line[0] == '@':
            prs = self.create_prs(USERSTATE, line)
            self.parse_privmsg(prs, line)
            self.format_display_name(prs)

            await self.call_listeners('userstate', ctx=prs)

        elif 'NOTICE' in line and line[0] == '@':
            prs = self.create_prs(NOTICE, line)
            self.parse_privmsg(prs, line)

            await self.call_listeners('notice', ctx=prs)

        elif 'CLEARCHAT' in line and line[0] == '@':
            prs = self.create_prs(CLEARCHAT, line)
            self.parse_privmsg(prs, line)
            self.swap_message_order(prs)

            await self.call_listeners('clearchat', ctx=prs)

        elif 'CLEARMSG' in line and line[0] == '@':
            prs = self.create_prs(CLEARMSG, line)
            self.parse_privmsg(prs, line)
            self.format_display_name(prs)

            await self.call_listeners('clearmsg', ctx=prs)

        # else:
        #     log.debug(line)
            # log.debug(f'THE FOLLOWING IS NOT BEING HANDLED:\n{line}')

    def receive(self) -> None:  # I've compressed the shit outta this code
        for line in self.sock.recv(16384).decode('utf-8', 'replace').split("\r\n")[:-1]:
            self.parse(line)
            self.ping(line)
        # data = self.sock.recv(16384).decode('utf-8', 'replace').split("\r\n")[:-1]
        # data = self.sock.recv(2**14).decode('utf-8', 'replace').split("\r\n")[:-1]
        # iter_log = True
        # for line in data:
        #     self.parse(line)
        #     if not line.startswith('@') and iter_log:
        #         iter_log = False
        #         log.debug(line)
        #         log.debug(self.last)
        #     self.ping(line)
        # self.last = data

    async def _lcall(self, event: str, **kwargs):
        if event not in _listeners:
            return
        for func in _listeners[event]:
            await func(self, **kwargs)

    async def call_listeners(self, event: str, **kwargs) -> None:
        if ':' in event: await self._lcall(event.split(':')[0], **kwargs)
        await self._lcall(event, **kwargs)
        if 'any' not in event:
            if ctx := kwargs.get('ctx', None):
                self.log_to_console(ctx)
            await self._lcall('any', **kwargs)

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
        await self.socksend(f'PRIVMSG {channel} :{message}')  # placement of the : is important :zaqPbt:

    def maximize_msg(self, content: str, offset: int = 0) -> str:
        return content * math.trunc((500 - offset) / len(content))  # need to trunc cuz we always round down

    def fill_msg(self, content: str, length: int = 500) -> str:
        return content * math.trunc((length) / len(content))  # need to trunc cuz we always round down


def listify(text: Union[list, str]):
    return text if isinstance(text, list) else [text]


def event(events: Union[str, list[str]] = 'any') -> Callable:  # listener/decorator for any event
    events = events if isinstance(events, list) else [events]

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
                return False
            return func(self, ctx)
        return wrapper
    return decorator


def ignore_myself() -> Callable:
    def decorator(func: Callable) -> Callable:
        def wrapper(self: Session, ctx: Messageable) -> Callable:
            if ctx.message.author.lower() != self.nick:
                return func(self, ctx)
            return False
        return wrapper
    return decorator


def author(names: Union[str, list[str]]) -> Callable:  # check author
    def decorator(func: Callable) -> Callable:
        def wrapper(self: Session, ctx: Messageable) -> Callable:
            if any(ctx.message.author.lower() == name.lower() for name in listify(names)):
                return func(self, ctx)
            return False
        return wrapper
    return decorator


authors = author


def channel(names: Union[str, list[str]]) -> Callable:  # check channel
    def decorator(func: Callable) -> Callable:
        def wrapper(self: Session, ctx: Messageable) -> Callable:
            def adapt(_name: str) -> str:
                return _name if _name[0] == '#' else f'#{_name}'
            if any(ctx.message.channel == adapt(name) for name in listify(names)):
                return func(self, ctx)
            return False
        return wrapper
    return decorator


channels = channel


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


# this new code is slow cuz of the msg_compare check for mode
def message(*args: tuple, **kwargs: dict) -> Callable:
    def decorator(func: Callable) -> Callable:
        def wrapper(self: Session, ctx: Messageable) -> Callable:
            mode = [pmode for pmode in args if msg_compare(pmode)]
            if not mode:
                mode = kwargs.get('mode', kwargs.get('m', 'eq'))
            else: mode = mode[0]
            ignore_self = kwargs.get('ignore_self', True)

            possible = list(args)
            possible.remove(mode)

            if any(msg_compare(mode, ctx.message.content, msg) for msg in possible):
                if ignore_self and ctx.message.author.lower() == self.nick:
                    return False
                return func(self, ctx)
            return False
        return wrapper
    return decorator
