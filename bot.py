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
    # @message('!quit', 'sw', False)
    # async def bot_suicide_pill(self, ctx: Messageable):
    #     ctx.send('Elenabot is shutting down')
    #     log.debug(ctx)
    #     self.shutdown()

    @event('ritual:new_chatter')
    async def new_zaqpaq_chatter(self, ctx: RITUAL):
        await ctx.send(f"raccPog raccPog raccPog Welcome {ctx.message.author} to the ZaqPaq! raccPog raccPog raccPog")

    @event('anysub')
    @cooldown(5)  # 5 second cooldown
    async def on_zaq_sub(self, ctx: Messageable):
        await ctx.send(f"{self.maximize_msg('zaqHeart zaqCool ', random.randint(50, 100))}zaqHeart")  # len 17
        log.debug(ctx)

    @event('raid')
    async def on_zaq_raid(self, ctx: Messageable):
        raid_msg = self.maximize_msg('zaqVA ', random.randint(50, 100))
        log.debug(raid_msg)
        await ctx.send(raid_msg)
        log.debug(ctx)

    @event('message')
    @message('zaqDisco', 'in')
    @cooldown(90)
    async def zaq_is_disco(self, ctx: Messageable):
        await ctx.send('zaqDisco')

    @event('message')
    @message('raccPog', 'in')
    @cooldown(90)
    async def zaq_is_pog(self, ctx: Messageable):
        await ctx.send('raccPog')

    @event('message')
    @message('catJAM', 'in')
    @cooldown(90)
    async def zaq_is_pog(self, ctx: Messageable):
        await ctx.send('catJAM')

    @event('message')
    @message('zaqCool', 'in')
    @cooldown(120)
    async def zaq_is_cool(self, ctx: Messageable):
        await ctx.send('zaqCool')

    @event('message')
    @message('Sadge 👑 🐘', 'in')
    @cooldown(60)
    async def queen_cutie(self, ctx: Messageable):
        await ctx.send('Sadge 👑 🐘')

    @event('message')
    @message('COPIUM', 'in')
    @cooldown(60)
    async def copium(self, ctx: Messageable):
        await ctx.send('COPIUM')

    @event('message')
    @message('AYAYA', 'in')
    @cooldown(60)
    async def ayaya(self, ctx: Messageable):
        await ctx.send('AYAYA')

    @event('message')
    @message('pepeSmoke', 'in')
    @cooldown(120)
    async def smoke_hayes_smoke(self, ctx: Messageable):
        await ctx.send('pepeSmoke')

    @event('message')
    @message('zaqHayes', 'in')
    @cooldown(60)
    async def good_shit_hayes(self, ctx: Messageable):
        await ctx.send('zaqHayes')

    @event('message')
    @message('cowDance', 'in')
    @cooldown(120)
    async def cow_dance(self, ctx: Messageable):
        await ctx.send('cowDance')

    @event('message')
    @message('MLADY')
    @cooldown(60)
    async def mlady(self, ctx: Messageable):
        await ctx.send('MLADY')

    @event('message')
    @author('richardharrow_')
    @message('ppHopAround')
    async def ppHopAround(self, ctx: Messageable):
        await ctx.send('ppHopAround')

    @event('message')
    @message('!ping', 'sw')
    async def lol_you_thought(self, ctx: Messageable):
        pick = ["I may be a bot but you can't just ping me like that GooseKnife", 'Gimme your fingers GooseKnife',
                f"c'mere {ctx.display_name} GooseKnife", 'ping me daddy zaqLewd', "i've been pinged AYAYA"]
        await ctx.send(random.choice(pick))

    @event('message')
    @author('nightbot')
    @message('Zaquelle has summoned her inner Wookie', 'sw')
    async def wookie(self, ctx: Messageable):
        await ctx.send('zaqWookie')

    @event('message')
    @author('oythebrave')
    @message('brb gotta pee')
    async def oys_gotta_pee(self, ctx: Messageable):
        await ctx.send('ok')

    @event('message')
    @author('nightbot')
    @message('zaqT THIS IS YOUR REMINDER TO DRINK WATER OR SOME SORT OF LIQUID BECAUSE YOUR BODY NEEDS IT AND SHIT zaqT')
    async def drink_water_zaq(self, ctx: Messageable):
        await ctx.send('zaqT')

    @event('message')
    @author('oythebrave')
    @message('This zaq is good')
    async def zaq_is_good(self, ctx: Messageable):
        await ctx.send('NODDERS')

    @event('message')
    @author('oythebrave')
    @message('zaqNOM')
    async def zaq_nom(self, ctx: Messageable):
        await ctx.send('zaqPop')

    @event('message')
    @cooldown(60)
    @message('zaqPop', 'in')
    async def zaq_nom(self, ctx: Messageable):
        await ctx.send('zaqPop')

    # @event('message')
    # @author('dwingert')
    # @message('Did ya know', 'sw')
    # def dwin_did_you_know(self, ctx: Messageable):
    #     ctx.send("did ya know that dwin deleted all the facts?")
    #     # ctx.send("did you know that y'all are cute paq")
    #     # pick = ["did you know that y'all are cute paq", 'did you know that dwin deleted all the facts',
    #     #         "did you know that y'all are dorks", 'did you know that dwin is a dork', 'did you know that?']
    #     # ctx.send(random.choice(pick))


if __name__ == '__main__':
    configure_logger(logging.DEBUG)

    Elenabot()
