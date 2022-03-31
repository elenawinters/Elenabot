"""
    This only implements a simple chatbot.

    Inherit from Session class to use.

    Copyright 2021-present ElenaWinters
    References:
        Twitch IRC Guide
        Rinbot by RingoMär
        TwitchDev samples

"""

from dataclasses import dataclass, field, make_dataclass
from typing import Any, Callable, Union
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
class Sendable:
    send: str = None


@dataclass
class Messageable(Sendable):
    message: Message = None


@dataclass
class CLEARCHAT(Messageable):  # the minimum data that would be provided would just be the channel
    tmi_sent_ts: str = None
    ban_duration: int = None


@dataclass
class CLEARMSG(Messageable):
    target_msg_id: str = None
    login: str = None


@dataclass
class ROOMSTATE(Sendable):
    channel: str = None
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
class HOSTTARGET(Sendable):
    channel: str = None
    target: str = None
    viewers: int = 0


@dataclass
class JOIN(Sendable):  # join and part are the same struct, but for readability, they are seperated
    channel: str = None
    user: str = None


@dataclass
class PART(Sendable):
    channel: str = None
    user: str = None


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


class Session(object):
    def __init__(self) -> None:
        self.host = 'ws://irc-ws.chat.twitch.tv'
        self.port = 80
        self.cooldowns = {}
        self.channels = []
        self.joinqueue = Queue()

        self.last = ''

    def start(self, token, nick, channels=None) -> None:
        self.token = token
        self.nick = nick

        # ws_timeout = aiohttp.ClientTimeout(total=86400)  # 1 day
        ws_timeout = aiohttp.ClientTimeout(total=21600)  # 6 hours
        # ws_timeout = aiohttp.ClientTimeout(total=60)  # 1 minute

        async def wsloop():
            async with aiohttp.ClientSession(timeout=ws_timeout).ws_connect(f'{self.host}:{self.port}') as self.sock:
                await self.connect()
                await self.join(channels)
                async for msg in self.sock:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        for line in msg.data.split("\r\n")[:-1]:  # ?!?
                            await self.parse(line)
                    else:
                        log.debug(f'Unknown WSMessage Type: {msg.type}')
                log.info('WebSocket has been closed!')
                if hasattr(self, 'jointask'):
                    self.jointask.cancel()
                    self.joinqueue = Queue()
                # await self.part(channels)
        # self.loop.run_until_complete(wsloop())

        while True:  # this loops over the aiohttp code
            try:
                # self.loop.run_until_complete(wsloop())
                asyncio.run(wsloop())
            except Exception as exc:
                log.exception(exc)

    async def socksend(self, sock_msg) -> None:  # removes the need to do the converting and stuff
        await self.sock.send_str(sock_msg)

    async def connect(self) -> None:
        log.debug(f'Attempting to connect to {self.host}:{self.port}')
        await self.socksend(f"PASS {self.token}")
        await self.socksend(f"NICK {self.nick}")
        await self.socksend("CAP REQ :twitch.tv/tags")
        await self.socksend("CAP REQ :twitch.tv/membership")
        await self.socksend("CAP REQ :twitch.tv/commands")

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
                await self.socksend(f"JOIN {c}")
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
            await self.socksend(f"PART {c}")
            log.info(f'Left {c}')

    def cast(self, dclass, data) -> dict:  # this populates nested dataclasses with default values
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
                self.attempt(setattr, prs, field.name, field.type(entry))

    def create_prs(self, dclass, line: str, base=True):  # 'prs' is short for 'parsed'
        dprs = self.cast(dclass, line)
        if base: dprs = self.parse_base(dprs)
        prs = dclass(**dprs)
        self.prs_conv(prs)
        return prs

    def parse_channel(self, chan: Union[str, dataclass], line: str):
        class_name = chan if isinstance(chan, str) else type(chan).__name__
        return re.search(f'{class_name} ' + r"(#[a-zA-Z0-9-_\w]+)", line).group(1)

    def proxy_send_obj(self, prs: dataclass, channel: str):
        async def _send_proxy(message: str):  # construct send function that can be called from ctx)
            await self.send(message, channel)
        prs.send = _send_proxy

    def parse_user(self, line):
        try:
            user = re.search(r":([a-zA-Z0-9-_\w]+)!([a-zA-Z0-9-_\w]+)@([a-zA-Z0-9-_\w]+)", line).group(1)
        except AttributeError:
            user = "Anon"
        return user

    def parse_msg(self, clname, channel: str, line: str):
        class_name = clname if isinstance(clname, str) else type(clname).__name__
        msg = re.search(f'{class_name} {channel}' + r'..(.*)', line)
        if msg: msg = msg.group(1)
        return msg

    def parse_privmsg(self, prs: Messageable, line: str, oprs: Messageable = None) -> None:  # user regex provided by RingoMär <3
        class_name = type(oprs).__name__ if oprs else type(prs).__name__  # basically only for the usernotice subcalls

        user = self.parse_user(line)

        channel = self.parse_channel(class_name, line)
        msg = self.parse_msg(class_name, channel, line)

        prs.message = Message(user, channel, msg)

        self.proxy_send_obj(prs, channel)

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

        # lol funny comment below
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

        await self.call_listeners(f'sub:{oprs.msg_id}', ctx=prs)  # this covers anysub, just use "sub" as the event

    async def parse_raid(self, oprs: USERNOTICE, line: str) -> None:
        prs = self.create_prs(RAID, line)
        self.parse_privmsg(prs, line, oprs)
        self.format_display_name(prs)

        prs.raider = oprs.msg_param_displayName if oprs.msg_param_displayName else oprs.msg_param_login
        prs.viewers = oprs.msg_param_viewerCount

        await self.call_listeners('raid', ctx=prs)

    def any_listeners(self, *events):  # this is in an attempt to not construct a event object unless there's an event registered
        for event in _listeners:
            if ':' in event:
                if event.split(':')[0] in events:
                    return True
            else:
                if event in events:
                    return True
        return False

    async def parse(self, line: str) -> None:  # use an elif chain or match case (maybeeee down the line)
        if line == 'PING :tmi.twitch.tv':
            await self.socksend("PONG :tmi.twitch.tv")
            if __debug__:
                log.info('Server sent PING. We sent PONG.')

        elif 'PRIVMSG' in line and line[0] == '@':
            if 'message' not in _listeners: return
            prs = self.create_prs(PRIVMSG, line)
            self.parse_privmsg(prs, line)
            self.format_display_name(prs)
            self.parse_action(prs)

            await self.call_listeners('message', ctx=prs)

        elif 'USERNOTICE' in line and line[0] == '@':
            # if not self.any_listeners('usernotice', 'sub', 'raid', 'unraid', 'ritual', 'bitsbadgetier', 'announcement'): return
            prs = self.create_prs(USERNOTICE, line)
            self.parse_privmsg(prs, line)
            self.format_display_name(prs)

            await self.call_listeners('usernotice', ctx=prs)

            # these are the valid msg_id's
            # sub, resub, subgift, anonsubgift, submysterygift, giftpaidupgrade, rewardgift, anongiftpaidupgrade, raid, unraid, ritual, bitsbadgetier
            # undocumented: extendsub, primepaidupgrade, communitypayforward, standardpayforward

            # I don't like having to put subs in multiple cases, but Python does not allow wraparound with Structural Pattern Matching (SPM).
            # Also, don't yell at me for using SPM. It's not the correct use case, but I don't care.

            match prs.msg_id:
                case 'sub' | 'resub' | 'extendsub' | 'primepaidupgrade' | 'communitypayforward' | 'standardpayforward':
                    await self.parse_subscription(prs, line)  # normal?
                case 'subgift' | 'anonsubgift' | 'submysterygift' | 'giftpaidupgrade' | 'anongiftpaidupgrade':
                    await self.parse_subscription(prs, line)  # gift?
                case 'unraid':  # called when a raid is cancelled. doesn't give a raid target
                    await self.call_listeners('unraid', ctx=prs)
                case 'raid':
                    await self.parse_raid(prs, line)
                case 'ritual':
                    await self.parse_ritual(prs, line)
                case 'bitsbadgetier':  # i documented this above but never looked into it
                    await self.call_listeners('bitsbadgetier', ctx=prs)  # i have a few examples, no idea how this works
                case 'announcement':  # This is super new. I'm going to watch this one for a bit.
                    await self.call_listeners('announcement', ctx=prs)
                    log.debug(line)
                    log.debug(prs)
                case _:  # other cases for testing
                    log.debug(line)
                    log.debug(prs)

        elif 'RECONNECT' in line:  # user influence shouldn't be possible. any user input is parsed above
            log.debug('Server sent RECONNECT.')
            await self.sock.close()

        elif 'ROOMSTATE' in line and line[0] == '@':
            if 'roomstate' not in _listeners: return
            prs = self.create_prs(ROOMSTATE, line)
            prs.channel = self.parse_channel(prs, line)
            self.proxy_send_obj(prs, prs.channel)
            await self.call_listeners('roomstate', ctx=prs)

        elif 'USERSTATE' in line and line[0] == '@':
            if 'userstate' not in _listeners: return
            prs = self.create_prs(USERSTATE, line)
            self.parse_privmsg(prs, line)
            self.format_display_name(prs)

            await self.call_listeners('userstate', ctx=prs)

        elif 'NOTICE' in line and line[0] == '@':
            if 'notice' not in _listeners: return
            prs = self.create_prs(NOTICE, line)
            self.parse_privmsg(prs, line)

            await self.call_listeners('notice', ctx=prs)

        elif 'CLEARCHAT' in line and line[0] == '@':
            if 'clearchat' not in _listeners: return
            prs = self.create_prs(CLEARCHAT, line)
            self.parse_privmsg(prs, line)
            self.swap_message_order(prs)

            await self.call_listeners('clearchat', ctx=prs)

        elif 'CLEARMSG' in line and line[0] == '@':
            if 'clearmsg' not in _listeners: return
            prs = self.create_prs(CLEARMSG, line)
            self.parse_privmsg(prs, line)
            self.format_display_name(prs)

            await self.call_listeners('clearmsg', ctx=prs)

        elif 'HOSTTARGET' in line and line[0] == ':':  # this is the only time imma make a proper seperate parsing
            if not self.any_listeners('host', 'hosttarget', 'unhost'): return
            prs = self.create_prs(HOSTTARGET, line, False)
            prs.channel = self.parse_channel(prs, line)
            prs.target, prs.viewers = self.parse_msg(prs, prs.channel, line).split(' ')
            self.proxy_send_obj(prs, prs.channel)
            # prs.target = f'#{prs.target}'

            if prs.target == '-':
                prs.target = None
                await self.call_listeners('unhost', ctx=prs)
                return

            await self.call_listeners('host', ctx=prs)
            await self.call_listeners('hosttarget', ctx=prs)

        elif re.search(r"[.:]tmi\.twitch\.tv [0-9]+ " + self.nick + r" [#:=]", line):
            await self.glhf_auth(line)

        elif ':tmi.twitch.tv CAP * ACK :twitch.tv/' in line:
            pass

        elif 'JOIN' in line and line[0] == ':':
            if not self.any_listeners('join'): return
            prs = self.create_prs(JOIN, line, False)
            prs.channel = self.parse_channel(prs, line)
            prs.user = self.parse_user(line)
            self.proxy_send_obj(prs, prs.channel)

            await self.call_listeners(f'join:{prs.user}', ctx=prs)
            if prs.user == self.nick:  # i dont like calling _lcall here, but we dont want to parse this
                await self._lcall('join:self', ctx=prs)

        elif 'PART' in line and line[0] == ':':
            if not self.any_listeners('part'): return
            prs = self.create_prs(PART, line, False)
            prs.channel = self.parse_channel(prs, line)
            prs.user = self.parse_user(line)
            self.proxy_send_obj(prs, prs.channel)

            await self.call_listeners(f'part:{prs.user}', ctx=prs)
            if prs.user == self.nick:  # i dont even know if this will ever trigger, but it's here just in case
                await self._lcall('part:self', ctx=prs)

        else:
            log.debug(f'THE FOLLOWING IS NOT BEING HANDLED:\n{line}')

    async def glhf_auth(self, line):
        ident = re.search(r"[.:]tmi\.twitch\.tv ([0-9]+) " + self.nick + r" [#:=]", line).group(1)
        match int(ident):
            case 1 | 2 | 3 | 4 | 372 | 376 | 366:  # Welcome, GLHF!
                pass
            case 353:  # Users in this chat! Sent on successful JOIN TODO: GET THIS DONE
                if not self.any_listeners('join'): return
                channel = self.parse_channel(f'{self.nick} =', line)  # haha string compat go brrrrr
                users = re.search(r' :(.*)', line).group(1).split(' ')  # JOIN(channel, user)
                for user in users:
                    prs = self.create_prs(JOIN, line, False)
                    prs.channel = channel
                    prs.user = user
                    # prs = JOIN(channel, user)
                    self.proxy_send_obj(prs, channel)

                    await self.call_listeners(f'join:{prs.user}', ctx=prs)
                    if prs.user == self.nick: continue

            case 375:  # this is the connected response
                log.info(f"Connected! Environment is {'DEBUG' if __debug__ else 'PRODUCTION'}.")

                loop = asyncio.get_running_loop()
                self.jointask = loop.create_task(self._join())
            case _:  # unhandled ident
                log.debug(f'ID {ident} is not being handled!\n{line}')

    async def _lcall(self, event: str, **kwargs):
        if event not in _listeners: return
        for func in _listeners[event]:
            # log.debug(type(func))
            # log.debug(func.__name__)
            await func(self, **kwargs)

    async def call_listeners(self, event: str, **kwargs) -> None:
        if ':' in event: await self._lcall(event.split(':')[0], **kwargs)  # we call the base event here. simplifies coding subevents
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
        if not __debug__:
            await self.socksend(f'PRIVMSG {channel} :{message}')  # placement of the : is important :zaqPbt:

    def maximize_msg(self, content: str, offset: int = 0) -> str:
        return content * math.trunc((500 - offset) / len(content))  # need to trunc cuz we always round down

    def fill_msg(self, content: str, length: int = 500) -> str:
        return content * math.trunc((length) / len(content))  # need to trunc cuz we always round down


async def cancelCall():  # decorators expect a function return. This is called instead of the function being decorated.
    return


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
                return cancelCall()
            return func(self, ctx)
        return wrapper
    return decorator


def ignore_myself() -> Callable:
    def decorator(func: Callable) -> Callable:
        def wrapper(self: Session, ctx: Messageable) -> Callable:
            if ctx.message.author.lower() != self.nick:
                return func(self, ctx)
            return cancelCall()
        return wrapper
    return decorator


def author(names: Union[str, list[str]]) -> Callable:  # check author
    def decorator(func: Callable) -> Callable:
        def wrapper(self: Session, ctx: Messageable) -> Callable:
            if any(ctx.message.author.lower() == name.lower() for name in listify(names)):
                return func(self, ctx)
            return cancelCall()
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
            return cancelCall()
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
            if mode in possible:
                possible.remove(mode)

            if any(msg_compare(mode, ctx.message.content, msg) for msg in possible):
                if ignore_self and ctx.message.author.lower() == self.nick:
                    return cancelCall()
                return func(self, ctx)
            return cancelCall()
        return wrapper
    return decorator
