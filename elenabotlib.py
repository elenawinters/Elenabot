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

# @badge-info=subscriber/13;badges=subscriber/12,bits/1000;color=#D2691E;display-name=ElenaBerry;emotes=;flags=;id=a8ebbea8-8bcf-4fa6-955f-a9820946e4fe;mod=0;room-id=89766478;subscriber=1;tmi-sent-ts=1619431746466;turbo=0;user-id=41057644;user-type= :elenaberry!elenaberry@elenaberry.tmi.twitch.tv PRIVMSG #zaquelle :zaqLurkie 󠀀
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
class PRIVMSG:  # unfortunately, defining fields is necessary
    badge_info: Badge = field(default_factory=str)
    badges: list[Badge] = field(default_factory=list)
    bits: str = field(default_factory=str)
    color: int = field(default_factory=list)
    display_name: str = field(default_factory=str)
    emotes: list = field(default_factory=list)
    flags: list = field(default_factory=list)
    id: str = field(default_factory=str)
    mod: bool = field(default_factory=bool)
    room_id: int = field(default_factory=int)
    subscriber: bool = field(default_factory=bool)
    tmi_sent_ts: int = field(default_factory=int)
    turbo: bool = field(default_factory=bool)
    user_id: int = field(default_factory=list)
    user_type: str = field(default_factory=str)
    message: Message = field(default_factory=str)
    send: str = field(default_factory=str)
    

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
        pong_msg = "PONG :tmi.twitch.tv"
        self.socksend(pong_msg)
        log.debug(pong_msg)

    def ping(self, line):
        if line == "PING :tmi.twitch.tv":
            self.pong()

    def cast(self, dclass, data):
        items = {}
        for k in dclass.__annotations__:
            item = re.search(k.replace('_', '-') + r'=([a-zA-Z0-9-/_,#\w]+)', data)
            if item:
                items[k] = item.group(1)
        return items

    def parse(self, line):  # https://stackoverflow.com/a/9868665/14125122
        # if next((i for i in line.split(' ') if i == 'PRIVMSG'), False) and line[0] == '@': # potentially useful?
        if 'PRIVMSG' in line and line[0] == '@': # some of the regex provided by RingoMär <3
            casted = self.cast(PRIVMSG, line)
            if 'badge_info' in casted:
                casted['badge_info'] = Badge(*casted['badge_info'].split('/'))

            if 'badges' in casted:
                casted['badges'] = [Badge(*badge.split('/')) for badge in casted['badges'].split(',')]
            
            try:
                user = re.search(r":([a-zA-Z0-9-_\w]+)!([a-zA-Z0-9-_\w]+)@([a-zA-Z0-9-_\w]+)", line).group(1)
            except AttributeError:
                user = "Anon"

            channel = re.search(r"(#[a-zA-Z0-9-_\w]+) :", line).group(1)
            msg = line.split(f"PRIVMSG {channel} :")[1]  # this can be broken and abused. conv to regex

            def _new_send(message):  # construct send function that can be called from ctx
                self.send(message, channel)

            uncast = PRIVMSG(**casted, message=Message(user, channel, msg), send=_new_send)
            self.call_listeners('message', ctx=uncast)

    def receive(self):
        buffer = ""
        buffer += self.sock.recv(2048).decode('utf-8')  # again, only used once, no need for wrapper
        temp = buffer.split("\r\n")
        buffer = temp.pop()
        # self.ping(line)
        for line in temp:
            log.debug(line)
            self.ping(line)
            self.parse(line)
            # if line[0] == '@':
            #     self.parse(line)

        pass

    # def privmsg(self, ctx, message):
    #     self.socksend(f'PRIVMSG {channel}: {message}')
    #     pass

    def call_listeners(self, event, **kwargs):        
        if event not in listeners:
            log.critical('NO LISTENERS FOUND')
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
    def decorator(func):
        def wrapper(self, ctx):
            if ctx.message.author == name.lower():
                return func(self, ctx)
            return False
        return wrapper
    return decorator

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
