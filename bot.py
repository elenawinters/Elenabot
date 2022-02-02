from elenabotlib import *
import sys, os, ast
import configparser
import random


class StatTracker:
    def __init__(self, ctx):
        self.ctx = ctx

    def process(self):
        pass


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
                'channels': ['tmiloadtesting2', 'twitchmedia_qs_10'],  # this is standard list format in the ini file. example: ['elenaberry']
                'nickname': 'your_lowercase_username'
            }
            with open(config_file, 'w') as configfile:
                config.write(configfile)
        else:
            config.read(config_file)

        channels = ast.literal_eval(config['twitch']['channels'])
        # import gen_stream_list
        # channels = gen_stream_list.ActiveHasroot('nopixel')
        # channels = gen_stream_list.ActiveHasroot('gtarp')

        self.start(config['twitch']['oauth'], config['twitch']['nickname'], channels)

    if __debug__:
        @event('join')
        async def join_debug(self, ctx: JOIN):
            log.info(ctx)

        @event('part')
        async def part_debug(self, ctx: PART):
            log.info(ctx)

        # @event('roomstate')  # this was experimental code from before i added smartjoin
        # async def mass_join(self, ctx: ROOMSTATE):
        #     await asyncio.sleep(0.55)
        #     if self.megaindex < len(megachannels):
        #         name = megachannels[self.megaindex]
        #         self.megaindex += 1
        #         await self.join([name])

        # @event('message')  # STAT TRACKER
        # async def track_stats(self, ctx: Messageable):
        #     log.info(ctx)
        #     # StatTracker(ctx).process()

        # @event('host')
        # async def on_host_debug(self, ctx: HOSTTARGET):
        #     log.info(ctx)
            # await self.part(ctx.channel)
            # await self.join(ctx.target)

        # @event('raid')
        # async def on_raid_debug(self, ctx: RAID):
        #     # if ctx.message.author in self.channels:
        #     #     await self.part(ctx.message.author)

        #     log.info(ctx)

        # @event('anysub')
        # async def on_sub_debug(self, ctx: Messageable):
        #     log.debug(ctx)

    else:
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
            await ctx.send(f"{self.maximize_msg('zaqHeart zaqWiggle ', random.randint(50, 100))}zaqHeart")  # len 17
            log.debug(ctx)

        @event('raid')
        async def on_zaq_raid(self, ctx: RAID):
            # log.debug('Incoming raid. Prepare for raid message!')
            raid_msg = f"Incoming raid! {ctx.raider} is sending {ctx.viewers} raiders our way! raccPog raccPog raccPog"
            # log.debug(raid_msg)
            await ctx.send(raid_msg)
            # log.debug('Attempted to send raid message! Prepare for raid information dump!')
            log.debug(ctx)

        @event('message')
        @message('zaqDisco', 'in')
        @cooldown(90)
        async def zaq_is_disco(self, ctx: Messageable):
            await ctx.send('zaqDisco')
        
        @event('message')
        @message('POGCRAZY', 'sw')
        @cooldown(45)
        async def zaq_is_pogcrazy(self, ctx: Messageable):
            await ctx.send('POGCRAZY')

        @event('message')
        @message('raccPog', 'in')
        @cooldown(90)
        async def zaq_is_pog(self, ctx: Messageable):
            await ctx.send('raccPog')

        @event('message')
        @message('catJam', 'in')
        @cooldown(90)
        async def zaq_is_pog(self, ctx: Messageable):
            await ctx.send('catJam')

        @event('message')
        @message('zaqWiggle', 'in')
        @cooldown(90)
        async def zaq_is_pog(self, ctx: Messageable):
            await ctx.send('zaqWiggle')

        @event('message')
        @message('zaqBS', 'in')
        @cooldown(90)
        async def zaq_butt_stuff(self, ctx: Messageable):
            await ctx.send('zaqBS')

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

        # @event('message')
        # @message('cowDance', 'in')
        # @cooldown(120)
        # async def cow_dance(self, ctx: Messageable):
        #     await ctx.send('cowDance')

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
            pick = ["I may be a bot but you can't just ping me like that zaqK", 'Gimme your fingers zaqK',
                    f"c'mere {ctx.display_name} zaqK", 'ping me daddy zaqLewd', "i've been pinged AYAYA"]
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
        @author('oythebrave')
        @message('FeelsHayesMan Glizzy')
        @cooldown(60)
        async def hayes_feels_glizzy_man(self, ctx: Messageable):
            await ctx.send('FeelsHayesMan Glizzy')

        @event('message')
        @author('nightbot')
        @message('zaqT THIS IS YOUR REMINDER TO DRINK WATER OR SOME SORT OF LIQUID BECAUSE YOUR BODY NEEDS IT AND SHIT zaqT')
        async def drink_water_zaq(self, ctx: Messageable):
            await ctx.send('zaqT')

        @event('message')
        @author('nightbot')
        @message('Zaquelle is afk zaqPls so the raccoons can dance away zaqPls and with a smirk zaqPls the chat will lurk zaqPls when Zaq comes back to play zaqLurk')
        async def zaq_is_afk(self, ctx: Messageable):
            await ctx.send('Zaquelle is afk zaqPls so the raccoons can dance away zaqPls and with a smirk zaqPls the chat will lurk zaqPls when Zaq comes back to play zaqLurk')

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

        @event('message')
        @cooldown(60)
        @message('zaqCA', 'in')
        async def zaq_coppa(self, ctx: Messageable):
            await ctx.send('zaqCA')

        @event('message')
        @author('streamlabs')
        @message('A !raffle raffle has started for Viewers use !raffle to enter the raffle.', 'in')
        async def raffle_start(self, ctx: Messageable):
            await ctx.send('!raffle')

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
