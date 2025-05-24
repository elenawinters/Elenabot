"""
    This only implements a simple chatbot.

    Inherit from Session class to use.

    Copyright 2021-2025 ElenaWinters
    References:
        Twitch IRC Guide
        Rinbot by RingoMär
        TwitchDev samples

    Tested on Windows 11 and Ubuntu 22.04

"""

from typing import Any, Callable, Union
from dataclasses import make_dataclass, asdict, dataclass
from sqlalchemy.types import LargeBinary
from datetime import datetime
from queue import Queue
import configlib
import functools
import structlog
import traceback
import logging
import inspect
import aiohttp
import asyncio
import dataset
import msgpack
import hints
import math
import sys
import re

"""

    For anyone wondering why this lib uses websockets instead of sockets, it's pretty simple.

    The Twitch chat socket implementation has data loss. Whether or not that's a Python issue or a twitch issue is beyond me.
    The websocket implementation has no data loss. It's simply more reliable.

    If you want an old, outdated socket implementation, check out the `socket` branch.

"""

# This doesn't need to be ordered the way it is, but I like it this way.
# This contains type conversions for all the included tags.
# @dataclass
# class GENERIC_TYPES():
#     msg_param_cumulative_months: int
#     msg_param_displayName: str
#     msg_param_viewerCount: int
#     msg_param_login: str
#     msg_param_months: int
#     msg_param_promo_gift_total: str
#     msg_param_promo_name: str
#     msg_param_recipient_display_name: str
#     msg_param_recipient_id: str
#     msg_param_recipient_user_name: str
#     msg_param_sender_login: str
#     msg_param_sender_name: str
#     msg_param_multimonth_tenure: int
#     msg_param_should_share_streak: int
#     msg_param_streak_months: int
#     msg_param_sub_plan_name: str
#     msg_param_sub_plan: str
#     msg_param_was_gifted: bool
#     msg_param_ritual_name: str
#     msg_param_threshold: int
#     msg_param_gift_months: int
#     pinned_chat_paid_amount: int
#     pinned_chat_paid_canonical_amount: int
#     pinned_chat_paid_currency: str
#     pinned_chat_paid_exponent: int
#     pinned_chat_paid_is_system_messag: bool
#     pinned_chat_paid_level: str
#     mod: bool
#     subscriber: bool
#     followers_only: int
#     target_msg_id: str
#     display_name: str
#     emote_only: bool
#     subs_only: bool
#     channel: str
#     user_id: int
#     msg_id: str
#     turbo: bool
#     login: str
#     color: str
#     vip: bool
#     r9k: bool
#     slow: int
#     bits: str
#     emotes: list
#     flags: list
#     id: str
#     room_id: int
#     tmi_sent_ts: int
#     action: bool

# def convert_to_typeset(ctx: dict) -> dict:
#     typeset = GENERIC_TYPES
#     # print(ctx)
#     # print(ctx.__dict__)
#     # print(GENERIC_TYPES.__annotations__)
#     # print(GENERIC_TYPES.__dict__)
#     # print(ctx.__class__.__name__)
#     # print(GENERIC_TYPES.__name__)
#     # print (typeset.__annotations__)


#     # results = {}
#     # if 'tags' in ctx:
#     #     for k, v in ctx['tags'].items():
#     #         results[k] = v
#     #         print(k, v)
#     #         print(k, type(k))
#     #         if k in typeset.__annotations__:
#     #             results[k] = typeset.__annotations__[k](v)
#     #             print(k, type(typeset.__annotations__[k](v)), typeset.__annotations__[k](v))
#     #             print('present')
#     # for k, v in ctx.items():
#     #     results[k] = v
#     #     print(k, v)
#     #     print(k, type(k))
#     #     if k in typeset.__annotations__:
            
#     #         results[k] = typeset.__annotations__[k](v)
#     #         print(k, type(typeset.__annotations__[k](v)), typeset.__annotations__[k](v))
#     #         print('present')

#     test = {k: typeset.__annotations__[k](v) if k in typeset.__annotations__ else v for k, v in ctx.items()}
#     if 'tags' in ctx:
#         log.debug(test)
#         test['tags'] = {k: typeset.__annotations__[k](v) if k in typeset.__annotations__ else v for k, v in ctx.get('tags', {}).items()}
#     # print(test)
#     return test
#     # result = {k: typeset.__annotations__[k](v) if k in typeset.__annotations__ else v for k, v in ctx.items() if k in typeset.__annotations__}

#     # print(ctx.items())
#     # result = {k: typeset.__annotations__[k](v) if k in typeset.__annotations__ else v for k, v in ctx.items() if k in typeset.__annotations__}
#     # print(result)
#     # return result
#     # return None

#     # return {k: v for k, v in ctx.items() if k in typeset.__dict__.keys()}

LOG_LEVEL = logging.DEBUG if __debug__ else logging.INFO
log: logging = configlib.LoggerConfig(name='elenabotlib', level=LOG_LEVEL).get_logger()
log.info('ElenabotLib has been loaded.')
if __debug__: log.debug('Debugging is enabled. If this emoji ⭐️ appears, the logger is working correctly.')
# log = structlog.get_logger('elenabotlib')
SOH = chr(1)  # ASCII SOH (Start of Header) Control Character, used for ACTION events

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

            possible = list(args)
            if mode in possible:
                possible.remove(mode)

            if any(msg_compare(mode, ctx.message.content, msg) for msg in possible):
                if kwargs.get('ignore_self', True) and ctx.user.lower() == self.nick:
                    return asyncio.sleep(0)
                return func(self, ctx)
            return asyncio.sleep(0)
        return wrapper
    return decorator

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
            events=['midnightsquid'])  # i don't know if this will ever be depr'd or if it already has
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
            _listeners[name] = []
        _listeners[name].append(func)


rx_positive = re.compile(r'^\d+$')


@dataclass
class SessionFlags:
    log_hint_differences: bool = False
    extra_debug_logging: bool = False
    send_in_debug: bool = False

    def __setattr__(self, prop, val):
        if (old_val := getattr(self, prop)) != val:
            log.warn(f'WARNING: Flag {prop.upper()} was changed from {old_val} to {val}! This may put the program into an invalid state!')
        super().__setattr__(prop, val)


class Session(object):
    def __init__(self) -> None:
        self.auto_reconnect = True
        self.host = 'wss://irc-ws.chat.twitch.tv'
        self.port = 443
        self.__cooldowns = {}
        self.__channels = []
        self.__joinqueue = Queue()
        self.__outgoing = {}

        self.__proxies = {}

        self.dbaddress = None

        self.flags = SessionFlags()
        self.flag_storage = {}

    # This is a direct port of the IRC parser from my JavaScript implementation.
    # it is a better implementation than the legacy verson, and I hope it is more expandable.
    def parseIRC(self, data: str = '@badge-info=gay/4;badges=lesbian/3,premium/1;user-type=awesome :tmi.twitch.tv GAYMSG #zaquelle :This is kinda gay'):
        RAW = data 
        RESULT = {}
        match = None

        if match := re.match(r'^@([^ ]+) ', data):
            tags = match[1].split(';')
            RESULT['tags'] = {}
            for tag in tags:
                try:
                    key, value = tag.split('=', maxsplit=1)
                except Exception as e:
                    log.warning(f'Failed to parse tag: {tag}', data=data, tags=tags)
                    log.exception(e)
                    continue
                if key == 'badges' or key == 'badge-info' or key == 'source-badges':
                    RESULT['tags'][key] = {}
                    if value == '': continue
                    badges = value.split(',')
                    for badge in badges:
                        badgeKey, badgeValue = badge.split('/')
                        RESULT['tags'][key][badgeKey] = badgeValue
                    continue
                elif key == 'emotes':
                    RESULT['tags'][key] = []
                    if value == '': continue
                    emotes = value.split('/')
                    for emote in emotes:
                        emoteKey, emoteValue = emote.split(':')
                        RESULT['tags'][key].append({ 'id': emoteKey, 'positions': emoteValue.split(',') })
                    continue
                RESULT['tags'][key] = value or None
            # log.debug(data)
            data = data[len(match[0]):]
            # log.debug(data)
        
        if match := re.match(r'^:([^ ]+) ([^ ]+) ?([^ ]+)?(.*)$', data):
            # print('here2')
            # print(match.groups())
            # print(match)
            SERVER, COMMAND, TARGET, _MESSAGE = match.groups()
            MESSAGE = _MESSAGE[1:]  # :)
            # print(SERVER)
            # print(COMMAND)
            # print(TARGET)
            # print(MESSAGE)
            ADD_TARGET = True

            RESULT['command'] = COMMAND
            RESULT['channel'] = TARGET
            match COMMAND:
                case 'CAP':
                    cap: list = MESSAGE[len('ACK') + 2:].split(' ')
                    RESULT['ACK'] = cap
                    ADD_TARGET = False
                case '353':
                    users: list = MESSAGE.split(' ')
                    users.pop()
                    RESULT['channel'] = users.pop()
                    users[0] = users[0][1:]
                    RESULT['users'] = users
                case '366':
                    RESULT['channel'] = MESSAGE.split(' ')[0]
                    RESULT['message'] = MESSAGE[len(RESULT['channel']) + 2:]
                case 'JOIN' | 'PART':
                    RESULT['user'] = SERVER.split('!')[0]
                case 'PRIVMSG':
                    RESULT['sender'] = SERVER.split('!')[0]
                    RESULT['message'] = MESSAGE[1:] if MESSAGE.startswith(':') else MESSAGE
                    RESULT['action'] = False
                    if SOH in RESULT['message']:
                        RESULT['message'] = RESULT['message'].replace(SOH + 'ACTION', '').replace(SOH, '')
                        RESULT['action'] = True
                case 'USERNOTICE':
                    RESULT['user'] = MESSAGE[1:] if MESSAGE.startswith(':') else MESSAGE
                    RESULT['sender'] = RESULT['tags']['login']
                    RESULT['message'] = MESSAGE[1:] if MESSAGE.startswith(':') else MESSAGE
                    RESULT['type'] = RESULT['tags']['msg-id']
                    if SOH in RESULT['message']:
                        log.warning("ACTION DETECTED IN USERNOTICE?! NANI?!")
                case 'CLEARMSG':
                    RESULT['user'] = RESULT['tags']['login']
                    RESULT['message'] = MESSAGE[1:] if MESSAGE.startswith(':') else MESSAGE
                case 'CLEARCHAT':
                    RESULT['user'] = MESSAGE[1:] if MESSAGE.startswith(':') else MESSAGE
                case _:
                    if re.match(r'^\d+$', COMMAND):
                        RESULT['message'] = MESSAGE[1:] if MESSAGE.startswith(':') else MESSAGE
                        ADD_TARGET = False
                    else:
                        if MESSAGE != '': RESULT['message'] = MESSAGE[1:] if MESSAGE.startswith(':') else MESSAGE
                        if COMMAND not in {'ROOMSTATE', 'USERSTATE', 'GLOBALUSERSTATE', 'NOTICE'}:
                            log.warning(f'{COMMAND} is not handled in a special way.')
                            RESULT['server'] = SERVER
                    pass

            
            if ADD_TARGET and RESULT['channel'] is not None:
                RESULT['send'] = self.proxy_send_obj(RESULT['channel'])

        RESULT['raw'] = RAW
        return RESULT

    def proxy_send_obj(self, channel: str):
        if channel not in self.__proxies:
            async def _send_proxy(message: str):  # construct send function that can be called from ctx)
                await self.send(message, channel)

            self.__proxies[channel] = _send_proxy
        return self.__proxies[channel]

    # @dispatch(1, 2, 3, 4, 372, 376, 366)
    # async def sinkhole(self, ctx):  # I'm not currently parsing these as I don't need to.
    #     print(ctx)
    #     pass

    @event('376')
    async def handle_376(self, ctx):
        log.debug(f"Connected! Environment is {'DEBUG' if __debug__ else 'PRODUCTION'}.")
        loop = asyncio.get_running_loop()
        self.jointask = loop.create_task(self._join())

    async def __wsloop(self, channels):
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
                for line in msg.data.split("\r\n")[:-1]:
                    if line == '': continue
                    if line == 'PING :tmi.twitch.tv':
                        log.info(line)
                        await self.sock.send_str('PONG :tmi.twitch.tv')
                        log.info('PONG :tmi.twitch.tv')
                        continue
                    ctx = self.parseIRC(line)
                    # log.debug(ctx)
                    # ctx = convert_to_typeset(ctx)
                    # log.debug(comp)
                    # dprs = comp.__dict__  # dprs and ctx are linked. changing one changes the other.
                    prs = make_dataclass(ctx['command'], [tuple([k, v]) for k, v in ctx.items()])(**ctx)
                    await self.call_listeners(type(prs).__name__.lower(), ctx=prs)

                    if ctx['command'] in ['NOTICE']:
                        log.info(ctx['command'], ctx=ctx)
                    else:
                        log.debug(ctx['command'], ctx=ctx)


            log.info('WebSocket has been closed!')
            if hasattr(self, 'jointask'):
                self.jointask.cancel()
                self.__joinqueue = Queue()

    def start(self, token, nick, channels=None) -> None:
        self.token = token
        self.nick = nick

        if self.nick.startswith('justinfan'):
            self.token = 'anonymous'
        log.debug(self.token)
        if self.flags.log_hint_differences:
            self.flag_storage['hint_classes'] = []
            for _, obj in inspect.getmembers(sys.modules['hints']):
                if inspect.isclass(obj):
                    self.flag_storage['hint_classes'].append(obj)

        if not self.dbaddress:
            self.dbaddress = 'sqlite:///elenabot.sqlite'  # default

        self.database = dataset.connect(self.dbaddress, engine_kwargs={'pool_recycle': 3600})

        tab = self.database.create_table('incoming')
        # tab.create_column('timestamp', self.database.types.datetime(6))
        tab.create_column_by_example('timestamp', datetime.utcnow())
        # tab.create_column('channel', self.database.types.text())
        tab.create_column_by_example('channel', self.nick) # fails
        tab.create_column_by_example('event', self.nick) # fails
        tab.create_column('data', LargeBinary()) # fails
        # tab.create_column_by_example('event', b'')
        try:  # we want this but things like SQLite don't do this so yeah
            self.database.query("ALTER TABLE `incoming` COLLATE='utf8mb4_unicode_ci', CHANGE COLUMN `timestamp` `timestamp` DATETIME(6) NULL DEFAULT NULL AFTER `id`;")
        except Exception:
            pass

        def attempt_connection():
            success, ret = self.attempt(asyncio.run, self.__wsloop(channels))
            if success is not None:
                log.critical('An error has occured and the program has exited prematurely.', exc_info=ret)

            # con.commit()
            self.attempt(asyncio.run, asyncio.sleep(1))

        if not self.auto_reconnect:
            attempt_connection()
            log.info('Auto Reconnect has been disabled, and the program has stopped.')
            return

        while self.auto_reconnect:
            attempt_connection()
            log.info('Attempting to reconnect...')


    async def join(self, channels: Union[list, str]):
        # print('here')
        channels = [channels] if isinstance(channels, str) else channels

        channels = [chan for chan in channels if chan not in self.__channels]
        if not channels:
            if hasattr(self, 'jointask') and self.jointask.done():
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

    # @event('any')
    # async def log_incoming(self, ctx):
    #     if type(ctx).__name__ in ['JOIN', 'PART']:
    #         return
    #     channel = None
    #     if hasattr(ctx, 'channel'):
    #         channel = ctx.channel
    #     event_data = asdict(ctx)
    #     if 'send' in event_data: 
    #         del event_data['send']
    #     try: 
    #         self.database['incoming'].insert(dict(
    #             timestamp=datetime.utcnow(),
    #             channel=channel,
    #             event=str(ctx),
    #             data=msgpack.packb({type(ctx).__name__: event_data})
    #         ))
    #     except Exception as esc:
    #         log.debug(f'Failed to save to database: {str(ctx)}')
    #         log.exception(esc)

    # @event('message', 'sub', 'raid')
    # async def log_messageable(self, ctx: hints.Messageable) -> None:
    #     if type(ctx).__name__ == 'RAID':
    #         log.info(f'RAID {ctx.channel} >>> {ctx.raider}: {ctx.viewers}')
    #         return
    #     if type(ctx).__name__ == 'PRIVMSG' and ctx.action:
    #         log.info(f'ACTION {ctx.message.channel} >>> {ctx.message.author}: {ctx.message.content}')
    #         return
    #     log.info(f'{type(ctx).__name__} {ctx.message.channel} >>> {ctx.message.author}: {ctx.message.content}')

    # @event('userstate')
    # async def verify_outgoing_approve(self, ctx):
    #     if not self.__outgoing[ctx.channel]: return
    #     msg = self.__outgoing[ctx.channel].pop(0)
    #     log.info(f'SENT {ctx.channel} >>> {ctx.user}: {msg}')
    #     # cur.execute('insert into msg_sent values (?, ?)', (ctx.channel, msg,))
    #     # con.commit()

    # @event('notice')
    # async def verify_outgoing_deny(self, ctx):
    #     if not ctx.msg_id.startswith('msg'): return
    #     if ctx.msg_id == 'msg_banned':  # ban me bitches, im tired of this throwing errors cuz im on a bot list
    #         # cur.execute('insert into msg_banned values (?)', (ctx.channel,))
    #         # con.commit()
    #         return
    #     msg = self.__outgoing[ctx.channel].pop(0)
    #     log.info(f'FAIL {ctx.channel} >>> {self.nick}: {msg}')
    #     # cur.execute('insert into msg_denied values (?, ?)', (ctx.channel, msg,))
    #     # con.commit()

    # @event('notice')
    # async def log_notices(self, ctx: hints.NOTICE):
    #     func = log.info if __debug__ else log.debug
    #     func(f'NOTICE({ctx.msg_id}): {ctx.channel} >>> {ctx.message}')

    # @event('cap')
    # async def get_cap(self, ctx):
    #     log.info(ctx)

    def attempt(self, func, *args, **kwargs) -> Any:
        try:
            return True, func(*args, **kwargs)
        except Exception as exc:
            return False, exc

    def any_listeners(self, *events):  # this is in an attempt to not construct a event object unless there's an event registered
        if __debug__ and not self.flags.log_hint_differences: return True
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
        if 'any' not in event: # I might add some logging here to compare the event to the hints file. Will only be enabled if a flag is set
            await self._lcall('any', **kwargs)
            if self.flags.log_hint_differences and 'ctx' in kwargs:
                if hint_class := [x for x in self.flag_storage['hint_classes'] if type(kwargs['ctx']).__name__ == x.__name__]:
                    if hint_class == []: return
                    c1 = hint_class[0].__annotations__
                    # log.info(asdict(hint_class[0]()))
                    c2 = type(kwargs['ctx']).__annotations__
                    # log.info(set(hint_class[0].__annotations__) ^ set(type(kwargs['ctx']).__annotations__))
                    difference = set(c2) - set(c1) - set(['server'])
                    # print(difference)
                    # print(type(difference))
                    # print(set([]))
                    # if difference == set(['server']): return
                    # print(difference == set(['']))
                    if difference == set(): return
                    self.database['log_hint_differences'].insert(dict(
                        classname=hint_class[0].__name__,
                        difference=difference,
                        c1=c1,
                        c2=c2
                    ))
                    # difference=set(c1) ^ set(c2),
                # log.info(type(kwargs['ctx']).__name__)

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
        return
        if __debug__ and not self.flags.send_in_debug:
            log.debug(f'ATTEMPTED SENDING MESSAGE IN DEBUG MODE! MESSAGE HAS BEEN SUPPRESSED! ({channel}: {message})' )
            return  # since i do a lot of debugging, i dont want to accidentally send something in a chat
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
