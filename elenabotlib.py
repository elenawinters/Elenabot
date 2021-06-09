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
from typing import Callable, Union
import traceback
import datetime
import logging
import socket
import math
import sys
import re

log = logging.getLogger(__name__)
debug = False  # global debug flag. set this to true to show tons of info. seperate from log.debug


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


@dataclass  # NO CLEAR EXAMPLES AT THE MOMENT
class CLEARMSG(Messageable):
    target_msg_id: str = None
    login: str = None


@dataclass
class ROOMSTATE:
    emote_only: bool = False
    followers_only: int = -1
    r9k: bool = False
    slow: int = 0
    subs_only: bool = False


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


# you can write your own configuration if you want to, not here though. do it in your own class
def configure_logger(_level=logging.INFO) -> None:
    log.setLevel(_level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(_level)
    log.addHandler(handler)


_dataclasses = Union[Messageable, CLEARCHAT, ROOMSTATE, NOTICE, GLOBALUSERSTATE, USERSTATE,
                     PRIVMSG, USERNOTICEBASE, USERNOTICE, SUBSCRIPTION, RITUAL, RAID]
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
        self.host = 'irc.twitch.tv'
        self.port = 6667
        self.sock = socket.socket()
        self.cooldowns = {}
        self.channels = []

    def start(self, token, nick, channels=None) -> None:
        self.token = token
        self.nick = nick

        while True:
            self.connect()
            if channels:
                self.join(channels)
            self.loop()

    def loop(self) -> None:
        while True:
            try:
                self.receive()
            except (ConnectionResetError, ConnectionAbortedError, ReconnectReceived) as exc:
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
                self.sock = socket.socket()
                log.error(f'Reconnecting: {type(exc).__name__}: {exc}')
                # log.exception(exc)
                return
            except Exception as e:
                log.exception(e)

    def socksend(self, sock_msg) -> None:  # removes the need to do the converting and stuff
        self.sock.send(f"{sock_msg}\r\n".encode("utf-8"))

    def connect(self) -> None:
        log.info(f'Attemptng to connect to {self.host}:{self.port}')
        try:
            self.sock.connect((self.host, self.port))  # only called once, not worth writing seperate wrapper
            self.socksend(f"PASS {self.token}")
            self.socksend(f"NICK {self.nick}")
            self.socksend("CAP REQ :twitch.tv/tags")
            self.socksend("CAP REQ :twitch.tv/membership")
            self.socksend("CAP REQ :twitch.tv/commands")
        except Exception as exc:
            log.exception(f'Error occured while connecting to IRC: ', exc_info=exc)
        else:
            log.info('Connected')

    def join(self, channels: Union[list, str]) -> None:
        channels = channels if type(list) else list(channels)
        self.channels.append(channels)
        for x in channels:
            c = x.lower() if x[0] == '#' else f'#{x.lower()}'
            self.socksend(f"JOIN {c}")
            log.info(f'Joined {c}')
            self.call_listeners('join_self', channel=c)

    def part(self, channels: Union[list, str]) -> None:  # this is currently untested
        channels = channels if type(list) else list(channels)
        self.channels.remove(channels)
        for x in channels:
            c = x.lower() if x[0] == '#' else f'#{x.lower()}'
            self.socksend(f"PART {c}")
            log.info(f'Left {c}')
            self.call_listeners('part_self', channel=c)

    def pong(self) -> None:
        self.socksend("PONG :tmi.twitch.tv")

    def ping(self, line: str) -> None:
        if line == "PING :tmi.twitch.tv":
            self.pong()

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

    def parse_base(self, dprs: dict) -> dict:  # this needs to be done with dictionaries unfortunately
        badge_tuple = ('badge_info', 'badges')
        for badge_type in badge_tuple:
            if badge_type in dprs:
                dprs[badge_type] = [Badge(*badge.split('/')) for badge in dprs[badge_type].split(',')]
        emote_tuple = ('emote_sets', 'emotes')
        for emote_type in emote_tuple:
            if emote_type in dprs:
                dprs[emote_type] = [x for x in dprs[emote_type].split(',')]

        return dprs

    def create_prs(self, dclass, line: str):  # 'prs' is short for 'parsed'
        dprs = self.cast(dclass, line)
        dprs = self.parse_base(dprs)
        return dclass(**dprs)

    def parse_privmsg(self, prs: Messageable, line: str, oprs: Messageable = None) -> None:  # user regex provided by RingoMär <3
        class_name = type(oprs).__name__ if oprs else type(prs).__name__  # basically only for the usernotice subcalls
        try:
            user = re.search(r":([a-zA-Z0-9-_\w]+)!([a-zA-Z0-9-_\w]+)@([a-zA-Z0-9-_\w]+)", line).group(1)
        except AttributeError:
            user = "Anon"

        channel = re.search(f'{class_name} ' + r"(#[a-zA-Z0-9-_\w]+)", line).group(1)
        msg = re.search(f'{class_name} {channel}' + r'..(.*)', line)
        if msg: msg = msg.group(1)

        prs.message = Message(user, channel, msg)

        def _send_proxy(message: str):  # construct send function that can be called from ctx
            self.send(message, channel)
        prs.send = _send_proxy

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

    def parse_ritual(self, oprs: USERNOTICE, line: str) -> None:
        prs = self.create_prs(RITUAL, line)
        self.parse_privmsg(prs, line, oprs)
        self.format_display_name(prs)

        prs.name = oprs.msg_param_ritual_name
        self.call_listeners('ritual', ctx=prs)
        log.debug(prs)  # i haven't actually seen this so i wanna log it

    def parse_subscription(self, oprs: USERNOTICE, line: str) -> None:
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

        self.call_listeners(oprs.msg_id, ctx=prs)
        self.call_listeners('anysub', ctx=prs)

    def parse_raid(self, oprs: USERNOTICE, line: str) -> None:
        prs = self.create_prs(RAID, line)
        self.parse_privmsg(prs, line, oprs)
        self.format_display_name(prs)

        prs.raider = oprs.msg_param_displayName if oprs.msg_param_displayName else oprs.msg_param_login
        prs.viewers = oprs.msg_param_viewerCount

        self.call_listeners('raid', ctx=prs)

    def parse(self, line: str) -> None:  # use an elif chain or match case (maybeeee down the line)
        if 'PRIVMSG' in line and line[0] == '@':
            prs = self.create_prs(PRIVMSG, line)
            self.parse_privmsg(prs, line)
            self.format_display_name(prs)
            self.parse_action(prs)

            # log.debug(f'{prs.display_name} and {prs.message.author}')

            self.call_listeners('message', ctx=prs)

        elif 'USERNOTICE' in line and line[0] == '@':
            prs = self.create_prs(USERNOTICE, line)
            self.parse_privmsg(prs, line)
            self.format_display_name(prs)

            self.call_listeners('usernotice', ctx=prs)

            # these are the valid msg_id's
            # sub, resub, subgift, anonsubgift, submysterygift, giftpaidupgrade, rewardgift, anongiftpaidupgrade, raid, unraid, ritual, bitsbadgetier

            match prs.msg_id:
                case 'sub' | 'resub' | 'subgift' | 'anonsubgift' | 'submysterygift' | 'giftpaidupgrade' | 'rewardgift' | 'anongiftpaidupgrade':
                    self.parse_subscription(prs, line)
                case 'unraid':
                    self.call_listeners('unraid', ctx=prs)
                case 'raid':
                    self.parse_raid(prs, line)
                case 'bitsbadgetier':  # I need to do more research on this one
                    log.debug(prs)
                case 'ritual':
                    self.parse_ritual(prs, line)

        elif 'RECONNECT' in line:  # user influence shouldn't be possible
            raise ReconnectReceived('Server sent RECONNECT.')

        elif 'USERSTATE' in line and line[0] == '@':
            prs = self.create_prs(USERSTATE, line)
            self.parse_privmsg(prs, line)
            self.format_display_name(prs)

            self.call_listeners('userstate', ctx=prs)

        elif 'NOTICE' in line and line[0] == '@':
            prs = self.create_prs(NOTICE, line)
            self.parse_privmsg(prs, line)

            self.call_listeners('notice', ctx=prs)

        elif 'CLEARCHAT' in line and line[0] == '@':
            prs = self.create_prs(CLEARCHAT, line)
            self.parse_privmsg(prs, line)
            self.swap_message_order(prs)

            self.call_listeners('clearchat', ctx=prs)

        elif 'CLEARMSG' in line and line[0] == '@':
            prs = self.create_prs(CLEARMSG, line)
            self.parse_privmsg(prs, line)
            self.format_display_name(prs)

            self.call_listeners('clearmsg', ctx=prs)

        # else:
        #     log.debug(f'THE FOLLOWING IS NOT BEING HANDLED:\n{line}')

    def receive(self) -> None:  # I've compressed the shit outta this code
        for line in self.sock.recv(16384).decode('utf-8', 'replace').split("\r\n")[:-1]:
            # log.debug(line)
            self.ping(line)
            self.parse(line)

    def call_listeners(self, event: str, **kwargs) -> None:
        if event != 'any':
            if ctx := kwargs.get('ctx', None):  # walrus zaqV
                self.log_to_console(ctx)
            self.call_listeners('any', **kwargs)
        if event not in _listeners:
            return
        for func in _listeners[event]:
            func(self, **kwargs)

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

    def send(self, message: str, channel: str) -> None:
        self.socksend(f'PRIVMSG {channel} :{message}')  # placement of the : is important :zaqPbt:

    def maximize_msg(self, content: str, offset: int = 0) -> str:
        return content * math.trunc((500 - offset) / len(content))  # need to trunc cuz we always round down

    def fill_msg(self, content: str, length: int = 500) -> str:
        return content * math.trunc((length) / len(content))  # need to trunc cuz we always round down


def event(event: str = None) -> Callable:  # listener/decorator for on_message
    def wrapper(func: Callable) -> Callable:
        add_listener(func, event)
        return func
    return wrapper


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
    def decorator(func: Callable) -> Callable:  # TODO: Add list support
        def wrapper(self: Session, ctx: Messageable) -> Callable:
            if ctx.message.author.lower() != self.nick:
                return func(self, ctx)
            return False
        return wrapper
    return decorator


def author(name: str) -> Callable:  # check author
    def decorator(func: Callable) -> Callable:  # TODO: Add list support
        def wrapper(self: Session, ctx: Messageable) -> Callable:
            if ctx.message.author.lower() == name.lower():
                return func(self, ctx)
            return False
        return wrapper
    return decorator


authors = author


def channel(name: str) -> Callable:  # check channel
    def decorator(func: Callable) -> Callable:
        def wrapper(self: Session, ctx: Messageable) -> Callable:
            def adapt(_name) -> str:
                return _name if _name[0] == '#' else f'#{_name}'
            if ctx.message.channel == adapt(name):
                return func(self, ctx)
            return False
        return wrapper
    return decorator


def message(content: str, mode='eq') -> Callable:  # check message
    def decorator(func: Callable) -> Callable:
        def wrapper(self: Session, ctx: Messageable) -> Callable:
            def advance() -> bool:
                match mode:
                    case 'eq' | 'equals':
                        if ctx.message.content == content:
                            return True
                    case 'sw' | 'startswith':
                        return ctx.message.content.startswith(content)
                    case 'ew' | 'endswith':
                        return ctx.message.content.endswith(content)
                    case 'in' | 'contains':
                        if content in ctx.message.content:
                            return True
            if advance():
                return func(self, ctx)
            return False
        return wrapper
    return decorator
