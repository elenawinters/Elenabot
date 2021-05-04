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
import logging
import socket
import types
import sys
import re

log = logging.getLogger(__name__)

@dataclass
class Message:
    author: str
    channel: str
    content: str

@dataclass
class Badge:
    name: str
    version: int

# @dataclass
# class Bits:

@dataclass
class CLEARCHAT: # the minimum data that would be provided would just be the channel
    ban_duration: int = None
    channel: str = None
    user: str = None

@dataclass
class CLEARMSG:
    login: str = None
    message: str = None
    channel : str = None
    target_msg_id: str = None

@dataclass
class ROOMSTATE:
    emote_only: bool = False
    followers_only: int = -1
    r9k: bool = False
    slow: int = 0
    subs_only: bool = False

@dataclass
class GLOBALUSERSTATE: # in this codebase, this is considered the base struct for most actions
    badge_info: list[Badge] = None  # prediction info goes here as well, for some reason
    badges: list[Badge] = None
    color: str = None
    display_name: str = None
    emote_sets: str = None
    turbo: bool = False
    user_id: int = 0
    user_type: str = None

@dataclass
class USERSTATE(GLOBALUSERSTATE):
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
    message: Message = None
    send: str = None

@dataclass
class USERNOTICE(PRIVMSG):  # there are a ton of params
    login: str = None
    msg_id: str = None
    msg_param_cumulative_months: int = 0
    msg_param_displayName: str = None # sent only on raid
    msg_param_viewerCount: int = 0
    msg_param_login: str = None
    msg_param_months: int = 0
    msg_param_promo_gift_total: str = None
    msg_param_promo_name: str = None
    msg_param_recipient_display_name: str = None
    msg_param_recipient_id: str = None
    msg_param_recipient_user_name: str = None
    msg_param_sender_login: str = None
    msg_param_multimonth_tenure: int = 0  # not sure what this is. it's not in the spec, but found it in sub messages. always 0?
    msg_param_should_share_streak: int = 0
    msg_param_streak_months: int = 0
    msg_param_sub_plan_name: str = None
    msg_param_sub_plan: str = None  # this can be a string or number
    msg_param_was_gifted: bool = False
    msg_param_ritual_name: str = None # lol what? this is in the spec
    msg_param_threshold: int = 0
    system_msg: str = None


# Here we implement some custom ones for the bot dev to use
# USERNOTICE subclasses
@dataclass
class RAID:
    pass

@dataclass
class SUBSCRIPTION:
    pass

@dataclass
class RITUAL:  # yes this is a thing
    pass

# you can write your own configuration if you want to, not here though. do it in your own class
def configure_logger(_level=logging.INFO):
    log.setLevel(_level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(_level)
    log.addHandler(handler)

listeners = {}

def add_listener(func, name='message'):
    if name not in listeners:
        listeners[name] = [func]
    else:
        listeners[name].append(func)

class Session(object):
    def __init__(self):
        self.host = 'irc.twitch.tv'
        self.port = 6667
        self.sock = socket.socket()
        self.channels = []

    def start(self, token, nick, channels=None):
        self.token = token
        self.nick = nick

        self.connect()
        if channels:
            self.join(channels)
        while True:
            try:
                self.receive()
            except Exception as e:
                log.exception(e)

    def socksend(self, sock_msg):  # removes the need to do the converting and stuff
        self.sock.send(f"{sock_msg}\r\n".encode("utf-8"))

    def connect(self):
        log.debug(f'Attemptng to connect to {self.host}:{self.port}')
        try:
            self.sock.connect((self.host, self.port))  # only called once, not worth writing seperate wrapper
            self.socksend(f"PASS {self.token}")
            self.socksend(f"NICK {self.nick}")
            self.socksend("CAP REQ :twitch.tv/tags")
            self.socksend("CAP REQ :twitch.tv/membership")
            self.socksend("CAP REQ :twitch.tv/commands")
        except Exception as exc:
            log.exception(f'Error occured while connecting to IRC: ', exc)
        else:
            log.debug('Connected')

    def join(self, channels):
        channels = channels if type(list) else list(channels)
        # if len(channels) > 1: # they work i guess
        #     log.warn('Multiple channels are not guarenteed to work!')
        self.channels.append(channels)
        for x in channels:
            c = x.lower() if x[0] == '#' else f'#{x.lower()}'
            self.socksend(f"JOIN {c}")
            log.debug(f'Joined {c}')

    def pong(self):
        self.socksend("PONG :tmi.twitch.tv")

    def ping(self, line):
        if line == "PING :tmi.twitch.tv":
            self.pong()

    def cast(self, dclass, data):
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
    
    def log_to_console(self, ctx):
        if hasattr(ctx, 'message'):
            log.debug(f'{type(ctx).__name__} {ctx.message.channel} >>> {ctx.display_name}: {ctx.message.content}')

    def parse_base(self, casted):
        if 'badge_info' in casted:
            casted['badge_info'] = [Badge(*badge.split('/')) for badge in casted['badge_info'].split(',')]

        if 'badges' in casted:
            casted['badges'] = [Badge(*badge.split('/')) for badge in casted['badges'].split(',')]
        return casted

    # this can also parse 
    def parse_privmsg(self, dclass, line): # some of the regex provided by RingoMär <3
        casted = self.cast(dclass, line)
        self.parse_base(casted)
        # casted = self.parse_base(casted)

        try:
            user = re.search(r":([a-zA-Z0-9-_\w]+)!([a-zA-Z0-9-_\w]+)@([a-zA-Z0-9-_\w]+)", line).group(1)
        except AttributeError:
            user = "Anon"

        channel = re.search(f'{dclass.__name__} ' + r"(#[a-zA-Z0-9-_\w]+)", line).group(1)
        msg = re.search(f'{dclass.__name__} {channel}' + r'..(.*)', line)
        if msg:
            msg = msg.group(1)

        def _send_proxy(message):  # construct send function that can be called from ctx
            self.send(message, channel)

        return dclass(**casted, message=Message(user, channel, msg), send=_send_proxy)

    def parse(self, line):  # use an elif chain or match case (maybee down the line)
        if 'PRIVMSG' in line and line[0] == '@':
            prs = self.parse_privmsg(PRIVMSG, line)
            if not prs.display_name:
                prs.display_name = prs.message.author
            self.call_listeners('message', ctx=prs)
        elif 'USERNOTICE' in line and line[0] == '@':  # this uses practically same structure as PRIVMSG, so we can parse the same
            prs = self.parse_privmsg(USERNOTICE, line)  # all we gotta do is correct the user in the message struct
            if prs.login:
                prs.message.author = prs.login
            if not prs.display_name:  # TODO: Find a better way to do this
                prs.display_name = prs.message.author
            self.call_listeners('usernotice', ctx=prs)  # this will be seperated into the different msg-id's later on

    def receive(self):
        buffer = ""
        buffer += self.sock.recv(2048).decode('utf-8')  # again, only used once, no need for wrapper
        temp = buffer.split("\r\n")
        buffer = temp.pop()
        # self.ping(line)
        for line in temp:
            # log.debug(line)
            self.ping(line)
            self.parse(line)
            # if line[0] == '@':
            #     self.parse(line)

        pass

    # def privmsg(self, ctx, message):
    #     self.socksend(f'PRIVMSG {channel}: {message}')
    #     pass

    def call_listeners(self, event, **kwargs):
        self.log_to_console(kwargs.get('ctx'))
        # log.debug(kwargs.get('ctx'))
        if event not in listeners:
            # log.critical('NO LISTENERS FOUND')
            return
        for func in listeners[event]:
            func(self, **kwargs)  # this should

    def send(self, message, channel):
        self.socksend(f'PRIVMSG {channel} :{message}')  # placement of the : is important :zaqPbt:

# @room-id=41057644;tmi-sent-ts=1619279551899 :tmi.twitch.tv CLEARCHAT #elenaberry

def event(event=None): # listener/decorator for on_message
    def wrapper(func):
        add_listener(func, event)
        return func
    return wrapper

def author(name): # check author
    def decorator(func): # TODO: Add list support
        def wrapper(self, ctx):
            if ctx.message.author == name.lower():
                return func(self, ctx)
            return False
        return wrapper
    return decorator

authors = author

def channel(name): # check channel
    def decorator(func):
        def wrapper(self, ctx):
            def adapt(_name):
                return _name if _name[0] == '#' else f'#{_name}'
            if ctx.message.channel == adapt(name):
                return func(self, ctx)
            return False
        return wrapper
    return decorator

def message(content, mode='eq'): # check message
    def decorator(func):
        def wrapper(self, ctx):
            def advance():
                match mode:  # this will show an error because we using 3.10.0a7 and VSC doesn't know that. it works tho
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
