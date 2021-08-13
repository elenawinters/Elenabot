from dataclasses import dataclass
from elenabotlib import *
import sys, os, ast
import configparser
import random


@dataclass
class LangFilterResult:
    words: list
    exceptions: list
    count: int


class LangFilter:
    def __init__(self, message):
        self.message = message

    def process(self):
        ematches = []
        matches = []
        ecount = 0
        count = 0

        with open('words.txt', 'r') as file:
            wdat = file.read().split(',')

        for word in wdat:
            _c = self.message.count(word)
            # print(_c)
            if _c > 0:
                matches.append(word)
                count += _c

        with open('exceptions.txt', 'r') as file:
            edat = file.read().split(',')

        for exc in edat:
            _c = self.message.count(exc)
            if _c > 0:
                ematches.append(exc)
                ecount += _c

        print(matches)
        print(ematches)
        # # TODO: Filter out matches if an exception was found
        # _rem = []
        # for ematc in ematches:
        #     for matc in matches:
        #         if matc in ematc:
        #             _rem.append(matc)

        # print(_rem)

        _rem = [tuple((matc, ematc)) for matc in matches for ematc in ematches if matc in ematc]  # see what matched to what
        # _rem = [x for x in _rem if _rem[x][1] == ]
        print(_rem)

        # _rem = [tuple(matc, ematc) for matc in matches for ematc in ematches if matc in ematc]
        # if _rem:
        #     print(_rem)
        # else:
        #     print('rem is empty')

        # for phrase in fury.execute("SELECT phrase FROM swear WHERE serverid = ?", (serverid, )):
        #     offenceTime += msg.count('{}'.format(phrase[0]))
        #     if msg.count('{}'.format(phrase[0])) > 0:
        #         swears += '{}, '.format(phrase[0])
        # return offenceTime, swears


class Elenabot(Session):
    def __init__(self):
        # LangFilter('assassins are trying to fuck me in the asswhore').process()
        # return
        super().__init__()  # unfortunately, this is a required call for elenabotlib implemented like this
        config = configparser.ConfigParser()
        config_file = 'config.ini'
        if not os.path.exists(config_file):
            config['twitch'] = {
                'oauth': 'oauth'.encode('utf-8').hex(),
                'channels': ['channel_to_be_in'],  # this is standard list format in the ini file. example: ['elenaberry']
                'nickname': 'your_lowercase_username'
            }
            with open(config_file, 'w') as configfile:
                config.write(configfile)
        else:
            config.read(config_file)

        channels = ast.literal_eval(config['twitch']['channels'])

        self.start(config['twitch']['oauth'], config['twitch']['nickname'], channels)

    # @event('message')

    # @event('roomstate')
    # def test_roomstate_stuff(self, ctx: ROOMSTATE):
    #     print(ctx)

    # @event('join_self')
    # def test_sub_stuff(self, channel):
    #     log.debug('JOINING CHANNEL')

    # @event('anysub')
    # def test_sub_stuff(self, ctx):
    #     log.debug(ctx)

    # @event('ritual')
    # def test_ritual_stuff(self, ctx):
    #     log.debug(ctx)

    # @event('ritual:new_chatter')
    # def test_new_chatter_ritual_stuff(self, ctx):
    #     log.debug(f'NEW CHATTER: {ctx}')

    # @event('message')
    # @message('zaqHeart', 'zaqLurkie', 'zaqCool', 'zaqHayes', 'zaqClap', 'in')
    # def test_new_msg_deco(self, ctx):
    #     log.debug(ctx)

    # @event('raid')
    # def test_raid_stuff(self, ctx):
    #     log.debug(ctx)

    # @event('userstate')
    # @channel('elenaberry')
    # @cooldown(60)
    # def test_message_length(self, ctx):
    #     ctx.send(self.maximize_msg('jessiLurk '))

    # @event('message')
    # @message('Sadge 👑 🐘')
    # @cooldown(60)
    # def queen_cutie(self, ctx):
    #     ctx.send('Sadge 👑 🐘')

    # @event('message')
    # @message('COPIUM')
    # @cooldown(60)
    # def copium(self, ctx):
    #     ctx.send('COPIUM')

    # @event('message')
    # @message('AYAYA', 'in')
    # @cooldown(60)
    # def ayaya(self, ctx):
    #     ctx.send('AYAYA')

    # @event('message')
    # @message('pepeSmoke', 'in')
    # @cooldown(120)
    # def smoke_hayes_smoke(self, ctx):
    #     ctx.send('pepeSmoke')

    # @event('message')
    # @message('zaqHayes', 'in')
    # @cooldown(60)
    # def good_shit_hayes(self, ctx):
    #     ctx.send('zaqHayes')

    # @event('message')
    # @message('cowDance', 'in')
    # @cooldown(120)
    # def cow_dance(self, ctx):
    #     ctx.send('cowDance')

    # @event('message')
    # @message('MLADY')
    # @cooldown(60)
    # def mlady(self, ctx):
    #     ctx.send('MLADY')

    # @event('message')
    # @author('richardharrow_')
    # @message('ppHopAround')
    # def ppHopAround(self, ctx):
    #     ctx.send('ppHopAround')

    # @event('message')
    # @message('!ping', 'sw')
    # def lol_you_thought(self, ctx):
    #     pick = ["I may be a bot but you can't just ping me like that GooseKnife", 'Gimme your fingers GooseKnife',
    #             f"c'mere {ctx.display_name} GooseKnife", 'ping me daddy zaqLewd', "i've been pinged AYAYA"]
    #     ctx.send(random.choice(pick))

    # @event('message')
    # @author('nightbot')
    # @message('Zaquelle has summoned her inner Wookie', 'sw')
    # def wookie(self, ctx):
    #     ctx.send('zaqWookie')

    # @event('message')
    # @author('oythebrave')
    # @message('brb gotta pee')
    # def oys_gotta_pee(self, ctx):
    #     ctx.send('ok')

    # @event('message')
    # @author('nightbot')
    # @message('zaqT THIS IS YOUR REMINDER TO DRINK WATER OR SOME SORT OF LIQUID BECAUSE YOUR BODY NEEDS IT AND SHIT zaqT')
    # def drink_water_zaq(self, ctx):
    #     ctx.send('zaqT')

    # @event('message')
    # @author('oythebrave')
    # @message('This zaq is good')
    # def zaq_is_good(self, ctx):
    #     ctx.send('NODDERS')

    # @event('message')
    # @author('oythebrave')
    # @message('zaqNOM')
    # def zaq_nom(self, ctx):
    #     ctx.send('zaqPop')


if __name__ == '__main__':
    configure_logger(logging.DEBUG)

    Elenabot()
