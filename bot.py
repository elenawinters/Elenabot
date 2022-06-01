from elenabotlib import *
from hints import *
import sys, os, ast
import configparser
import random


class Elenabot(Session):
    def __init__(self):
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

        if __debug__:
            import gen_stream_list
            # channels = gen_stream_list.ActiveHasroot('nopixel')
            # channels = ['zaquelle', 'sixyrp', 'oneprotectivefox']
            channels = gen_stream_list.ActiveHasroot('gtarp')
            self.kekchannels = []
        else:
            channels = ast.literal_eval(config['twitch']['channels'])

        self.start(config['twitch']['oauth'], config['twitch']['nickname'], channels)

    if __debug__:
        @event('join')
        async def join_debug(self, ctx):
            if ctx.user == self.nick: return
            if ctx.user not in self.kekchannels:
                self.kekchannels.append(ctx.user)

        @event('unhost')
        async def on_unhost_debug(self, ctx):
            log.info(f'I have {len(self.kekchannels)} channels in memory right now!')
            log.info(ctx)

        @event('host')
        async def on_host_debug(self, ctx):
            log.info(f'I have {len(self.kekchannels)} channels in memory right now!')
            log.info(ctx)
            # await self.part(ctx.channel)
            if ctx.channel not in self.kekchannels:
                self.kekchannels.append(ctx.target)
            await self.join(ctx.target)

        @event('message')
        @channel('burn')
        async def burn_test(self, ctx):
            log.info("BURN'S CHAT BE POPPING OFF")

        @event('cap')
        async def get_cap(self, ctx):
            log.debug(ctx)

    else:
        @event('host')
        @channel('zaquelle')
        async def join_on_raid(self, ctx: HOSTTARGET):
            if ctx.viewers >= 40:
                log.debug(ctx)
                self.last_raided = '#' + ctx.target
                self.last_raider = ctx.channel
                await self.join(ctx.target)
                # log.debug(f'{ctx.channel} has hosted {ctx.target}')
                # log.debug(f'Joining target: {ctx.target}')

        # @event('join:self')
        # async def you_got_raided(self, ctx: JOIN):
        #     if not hasattr(self, 'last_raided') and not hasattr(self, 'last_raider'): return
        #     if self.last_raided == ctx.channel and self.last_raider == '#zaquelle':
        #         log.debug(f'{ctx.channel} was raided by {self.last_raider}; raid acknowledged.')
        #         self.auto_reconnect = False
        #         await self.sock.close()

        @event('message')
        async def raiding_msg(self, ctx: PRIVMSG):
            if not hasattr(self, 'last_raided') and not hasattr(self, 'last_raider'): return
            if self.last_raided != ctx.channel and self.last_raider != '#zaquelle': return
            if 'zaqWiggle' in ctx.message.content:
                await ctx.send(self.fill_msg('zaqWiggle ', 320))
                self.auto_reconnect = False
                await self.sock.close()

        @event('ritual:new_chatter')
        @channel('zaquelle')
        async def new_zaqpaq_chatter(self, ctx: RITUAL):
            await ctx.send(f"raccPog raccPog raccPog Welcome {ctx.message.author} to the ZaqPaq! raccPog raccPog raccPog")

        @event('sub')
        @channel('zaquelle')
        @cooldown(5)  # 5 second cooldown
        async def on_zaq_sub(self, ctx: SUBSCRIPTION):
            await ctx.send(f"{self.maximize_msg('zaqHeart zaqWiggle ', random.randint(50, 100))}zaqHeart")  # len 17
            log.debug(ctx)

        @event('raid')
        @channel('zaquelle')
        async def on_zaq_raid(self, ctx: RAID):
            raid_msg = f"INCOMING! {ctx.raider} is sending {ctx.viewers} raiders our way! raccPog raccPog raccPog"
            await ctx.send(raid_msg)
            log.debug(ctx)

        @event('message')
        @channel('zaquelle')
        @message('zaqPlus1', 'in')
        @cooldown(90)
        async def zaq_plus_1(self, ctx: PRIVMSG):
            await ctx.send('zaqPlus1')

        @event('message')
        @channel('zaquelle')
        @message('zaqMinus1', 'in')
        @cooldown(90)
        async def zaq_minus_1(self, ctx: PRIVMSG):
            await ctx.send('zaqMinus1')

        @event('message')
        @channel('zaquelle')
        @message('raccRun', 'in')
        @cooldown(90)
        async def racc_run_7tv(self, ctx: PRIVMSG):
            await ctx.send('raccRun')

        @event('message')
        @channel('zaquelle')
        @message('zaqDisco', 'in')
        @cooldown(90)
        async def zaq_is_disco(self, ctx: PRIVMSG):
            await ctx.send('zaqDisco')

        @event('message')
        @channel('zaquelle')
        @message('POGCRAZY', 'sw')
        @cooldown(45)
        async def zaq_is_pogcrazy(self, ctx: PRIVMSG):
            await ctx.send('POGCRAZY')

        @event('message')
        @channel('zaquelle')
        @message('raccPog', 'in')
        @cooldown(90)
        async def zaq_is_pog(self, ctx: PRIVMSG):
            await ctx.send('raccPog')

        @event('message')
        @channel('zaquelle')
        @message('catJAM', 'in')
        @cooldown(90)
        async def zaq_is_pog(self, ctx: PRIVMSG):
            await ctx.send('catJAM')

        @event('message')
        @channel('zaquelle')
        @message('zaqWiggle', 'in')
        @cooldown(90)
        async def zaq_is_pog(self, ctx: PRIVMSG):
            await ctx.send('zaqWiggle')

        @event('message')
        @channel('zaquelle')
        @message('zaqBS', 'in')
        @cooldown(90)
        async def zaq_butt_stuff(self, ctx: PRIVMSG):
            await ctx.send('zaqBS')

        @event('message')
        @channel('zaquelle')
        @message('zaqCool', 'in')
        @cooldown(120)
        async def zaq_is_cool(self, ctx: PRIVMSG):
            await ctx.send('zaqCool')

        @event('message')
        @channel('zaquelle')
        @message('Sadge 👑 🐘', 'in')
        @cooldown(60)
        async def queen_cutie_1(self, ctx: PRIVMSG):
            await ctx.send('Sadge 👑 🐘')

        @event('message')
        @channel('zaquelle')
        @message('PepeHands 👑 🐘', 'in')
        @cooldown(60)
        async def queen_cutie_2(self, ctx: PRIVMSG):
            await ctx.send('PepeHands 👑 🐘')

        @event('message')
        @channel('zaquelle')
        @message('COPIUM', 'in')
        @cooldown(60)
        async def copium(self, ctx: PRIVMSG):
            await ctx.send('COPIUM')

        @event('message')
        @channel('zaquelle')
        @message('AYAYA', 'in')
        @cooldown(60)
        async def ayaya(self, ctx: PRIVMSG):
            await ctx.send('AYAYA')

        @event('message')
        @channel('zaquelle')
        @message('pepeSmoke', 'in')
        @cooldown(120)
        async def smoke_hayes_smoke(self, ctx: PRIVMSG):
            await ctx.send('pepeSmoke')

        @event('message')
        @channel('zaquelle')
        @message('zaqHayes', 'in')
        @cooldown(60)
        async def good_shit_hayes(self, ctx: PRIVMSG):
            await ctx.send('zaqHayes')

        # @event('message')
        # @channel('zaquelle')
        # @message('cowDance', 'in')
        # @cooldown(120)
        # async def cow_dance(self, ctx: PRIVMSG):
        #     await ctx.send('cowDance')

        @event('message')
        @channel('zaquelle')
        @message('MLADY')
        @cooldown(60)
        async def mlady(self, ctx: PRIVMSG):
            await ctx.send('MLADY')

        @event('message')
        @channel('zaquelle')
        @author('richardharrow_')
        @message('ppHopAround')
        async def ppHopAround(self, ctx: PRIVMSG):
            await ctx.send('ppHopAround')

        @event('message')
        @channel('zaquelle')
        @message('!ping', 'sw')
        async def lol_you_thought(self, ctx: PRIVMSG):
            pick = ["I may be a bot but you can't just ping me like that zaqK", 'Gimme your fingers zaqK',
                    f"c'mere {ctx.display_name} zaqK", 'ping me daddy zaqLewd', "i've been pinged AYAYA"]
            await ctx.send(random.choice(pick))

        @event('message')
        @channel('zaquelle')
        @author('nightbot')
        @message('Zaquelle has summoned her inner Wookie', 'sw')
        async def wookie(self, ctx: PRIVMSG):
            await ctx.send('zaqWookie')

        @event('message')
        @channel('zaquelle')
        @author('oythebrave')
        @message('brb gotta pee')
        async def oys_gotta_pee(self, ctx: PRIVMSG):
            await ctx.send('ok')

        @event('message')
        @channel('zaquelle')
        @author('oythebrave')
        @message('FeelsHayesMan Glizzy')
        @cooldown(60)
        async def hayes_feels_glizzy_man(self, ctx: PRIVMSG):
            await ctx.send('FeelsHayesMan Glizzy')

        @event('message')
        @channel('zaquelle')
        @author('nightbot')
        @message('zaqT THIS IS YOUR REMINDER TO DRINK WATER OR SOME SORT OF LIQUID BECAUSE YOUR BODY NEEDS IT AND SHIT zaqT')
        async def drink_water_zaq(self, ctx: PRIVMSG):
            await ctx.send('zaqT')

        @event('message')
        @channel('zaquelle')
        @author('nightbot')
        @message('Zaquelle is afk zaqPls so the raccoons can dance away zaqPls and with a smirk zaqPls the chat will lurk zaqPls when Zaq comes back to play zaqLurk')
        async def zaq_is_afk(self, ctx: PRIVMSG):
            await ctx.send('Zaquelle is afk zaqPls so the raccoons can dance away zaqPls and with a smirk zaqPls the chat will lurk zaqPls when Zaq comes back to play zaqLurk')

        @event('message')
        @channel('zaquelle')
        @author('oythebrave')
        @message('This zaq is good')
        async def zaq_is_good(self, ctx: PRIVMSG):
            await ctx.send('NODDERS')

        @event('message')
        @channel('zaquelle')
        @author('oythebrave')
        @message('zaqNOM')
        async def zaq_nom(self, ctx: PRIVMSG):
            await ctx.send('zaqPop')

        @event('message')
        @channel('zaquelle')
        @message('zaqPop', 'in')
        @cooldown(60)
        async def zaq_nom(self, ctx: PRIVMSG):
            await ctx.send('zaqPop')

        @event('message')
        @channel('zaquelle')
        @message('zaqCA', 'in')
        @cooldown(60)
        async def zaq_coppa(self, ctx: PRIVMSG):
            await ctx.send('zaqCA')

        @event('message')
        @channel('zaquelle')
        @author('streamlabs')
        @message('A !raffle raffle has started for Viewers use !raffle to enter the raffle.', 'in')
        async def raffle_start(self, ctx: PRIVMSG):
            await ctx.send('!raffle')

        # @event('message')
        # @channel('zaquelle')
        # @author('dwingert')
        # @message('Did ya know', 'sw')
        # def dwin_did_you_know(self, ctx: PRIVMSG):
        #     ctx.send("did ya know that dwin deleted all the facts?")
        #     # ctx.send("did you know that y'all are cute paq")
        #     # pick = ["did you know that y'all are cute paq", 'did you know that dwin deleted all the facts',
        #     #         "did you know that y'all are dorks", 'did you know that dwin is a dork', 'did you know that?']
        #     # ctx.send(random.choice(pick))


if __name__ == '__main__':
    configure_logger(logging.DEBUG)

    Elenabot()
