from elenabotlib import Session, event, channel, cooldown, message, author, configure_logger, log
import configparser
import logging
import random
import hints
import ast
import os


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
            config['db'] = {
                'address': ''
            }
            with open(config_file, 'w') as configfile:
                config.write(configfile)
        else:
            config.read(config_file)

        if __debug__:
            # channels = ['zaquelle']
            import gen_stream_list
            channels = gen_stream_list.ActiveHasroot('gtarp')
            # if 'zaquelle' in channels:
            #     channels.remove('zaquelle')
            # self.dbaddress = config['db']['address'] + '_dev'
            # self.kekchannels = []
        else:
            channels = ast.literal_eval(config['twitch']['channels'])
            self.dbaddress = config['db']['address']  # overwrite DB Address with the one we want

        self.start(config['twitch']['oauth'], config['twitch']['nickname'], channels)

    if __debug__:
        # @event('join')
        # async def join_debug(self, ctx):
        #     # await self.part(ctx.channel)
        #     # self.auto_reconnect = False
        #     # await self.sock.close()
        #     if ctx.user == self.nick: return
        #     if ctx.user not in self.kekchannels:
        #         self.kekchannels.append(ctx.user)

        # @event('unhost')
        # async def on_unhost_debug(self, ctx):
        #     log.info(f'I have {len(self.kekchannels)} channels in memory right now!')
        #     log.info(ctx)

        # @event('host')
        # async def on_host_debug(self, ctx):
        #     log.info('Testing depreciation of host')

        @event('midnightsquid')
        async def midnightsquid_debug(self, ctx):
            log.info('Testing midnightsquid experiment')

        @event('message')
        @channel('burn')
        async def burn_test(self, ctx):
            log.info("BURN'S CHAT BE POPPING OFF")

    else:
        # async def raid_timeout(self):
        #     self.can_send_raid_msg = True
        #     await asyncio.sleep(20)
        #     del self.can_send_raid_msg

        # @event('host')
        # @channel('zaquelle')
        # async def join_on_raid(self, ctx: hints.HOSTTARGET):
        #     if ctx.viewers >= 40:
        #         log.debug(ctx)
        #         loop = asyncio.get_running_loop()
        #         loop.create_task(self.raid_timeout())
        #         self.last_raided = '#' + ctx.target
        #         self.last_raider = ctx.channel
        #         await self.join(ctx.target)

        # @event('message')
        # async def raiding_msg(self, ctx: hints.PRIVMSG):
        #     if not hasattr(self, 'can_send_raid_msg'): return
        #     if not hasattr(self, 'last_raided') and not hasattr(self, 'last_raider'): return
        #     if self.last_raided != ctx.channel and self.last_raider != '#zaquelle': return
        #     if 'zaqWiggle' in ctx.message.content:
        #         await ctx.send(self.fill_msg('zaqWiggle ', 320))
        #         await self.part(ctx.channel)
        #         del self.last_raided
        #         del self.last_raider
        #         # self.auto_reconnect = False
        #         # await self.sock.close()

        @event('message')
        @channel('zaquelle')
        @author('the33rd')
        async def not_today_33rd(self, ctx: hints.PRIVMSG):
            if not hasattr(self, 'last_33rd'): self.last_33rd = None

            # The send message has a 50% chance to succeed. This ensures it's not always happening and therefore being a nuisance.
            if self.last_33rd == 'zaqWiggle zaqWiggle' and ctx.message.content == 'zaqWiggle zaqWiggle zaqWiggle' and random.choice((True, False)):
                ctx.send("According to all known laws of aviation, there is no way a bee should be able to fly. Its wings are too small to get its fat little body off the ground. The bee, of course, flies anyway because bees don't care what humans think is impossible.")
            self.last_33rd = ctx.message.content

        @event('ritual:new_chatter')
        @channel('zaquelle')
        async def new_zaqpaq_chatter(self, ctx: hints.RITUAL):
            await ctx.send(f"raccPog raccPog raccPog Welcome {ctx.message.author} to the ZaqPaq! raccPog raccPog raccPog")

        @event('sub')
        @channel('zaquelle')
        @cooldown(5)  # 5 second cooldown
        async def on_zaq_sub(self, ctx: hints.SUBSCRIPTION):
            await ctx.send(self.fill_msg('zaqHeart ', random.randint(162, 404)))
            # await ctx.send(f"{self.maximize_msg('zaqHeart zaqWiggle ', random.randint(50, 100))}zaqHeart")  # len 17
            log.debug(ctx)

        @event('raid')
        @channel('zaquelle')
        async def on_zaq_raid(self, ctx: hints.RAID):
            await ctx.send(f"Incoming raid! {ctx.raider} is sending {ctx.viewers} raiders our way! raccPog raccPog raccPog")
            log.debug(ctx)

        @event('message')
        @channel('zaquelle')
        @message('zaqShy', 'in')
        @cooldown(90)
        async def zaq_shy(self, ctx: hints.PRIVMSG):
            await ctx.send('zaqShy')

        @event('message')
        @channel('zaquelle')
        @message('zaqSussy', 'in')
        @cooldown(90)
        async def zaq_sussy(self, ctx: hints.PRIVMSG):
            await ctx.send('zaqSussy')

        @event('message')
        @channel('zaquelle')
        @message('zaqCultist', 'in')
        @cooldown(90)
        async def zaq_cultist(self, ctx: hints.PRIVMSG):
            await ctx.send('zaqCultist')

        @event('message')
        @channel('zaquelle')
        @message('GIGAHAYES', 'in')
        @cooldown(120)
        async def zaq_GIGAHAYES(self, ctx: hints.PRIVMSG):
            await ctx.send('GIGAHAYES')

        @event('message')
        @channel('zaquelle')
        @message('VIBE', 'in')
        @cooldown(120)
        async def zaq_vibe(self, ctx: hints.PRIVMSG):
            await ctx.send('VIBE')

        @event('message')
        @channel('zaquelle')
        @message('zaqPlus1', 'in')
        @cooldown(90)
        async def zaq_plus_1(self, ctx: hints.PRIVMSG):
            await ctx.send('zaqPlus1')

        @event('message')
        @channel('zaquelle')
        @message('zaqMinus1', 'in')
        @cooldown(90)
        async def zaq_minus_1(self, ctx: hints.PRIVMSG):
            await ctx.send('zaqMinus1')

        @event('message')
        @channel('zaquelle')
        @message('zaqBenchTrial', 'in')
        @cooldown(90)
        async def zaq_bench_trial(self, ctx: hints.PRIVMSG):
            await ctx.send('zaqBenchTrial')

        @event('message')
        @channel('zaquelle')
        @message('zaqMDW', 'in')
        @cooldown(90)
        async def zaq_mdw(self, ctx: hints.PRIVMSG):
            await ctx.send('zaqMDW')

        @event('message')
        @channel('zaquelle')
        @message('raccRun', 'in')
        @cooldown(90)
        async def racc_run_7tv(self, ctx: hints.PRIVMSG):
            await ctx.send('raccRun')

        @event('message')
        @channel('zaquelle')
        @message('zaqDisco', 'in')
        @cooldown(90)
        async def zaq_is_disco(self, ctx: hints.PRIVMSG):
            await ctx.send('zaqDisco')

        @event('message')
        @channel('zaquelle')
        @message('POGCRAZY', 'sw')
        @cooldown(45)
        async def zaq_is_pogcrazy(self, ctx: hints.PRIVMSG):
            await ctx.send('POGCRAZY')

        @event('message')
        @channel('zaquelle')
        @message('raccPog', 'in')
        @cooldown(90)
        async def zaq_is_pog(self, ctx: hints.PRIVMSG):
            await ctx.send('raccPog')

        @event('message')
        @channel('zaquelle')
        @message('catJAM', 'in')
        @cooldown(90)
        async def zaq_is_catjam(self, ctx: hints.PRIVMSG):
            await ctx.send('catJAM')

        @event('message')
        @author('beruru')
        @channel('zaquelle')
        @message('zaqWiggle', 'in')
        @cooldown(30)
        async def beru_double_wiggle(self, ctx: hints.PRIVMSG):
            await ctx.send('zaqWiggle zaqWiggle')

        @event('message')
        @channel('zaquelle')
        @message('zaqWiggle', 'in')
        @cooldown(90)
        async def zaq_is_wiggle(self, ctx: hints.PRIVMSG):  # i could probably consolidate the above into this but im lazy
            if ctx.message.author.lower() == 'beruru': return
            await ctx.send('zaqWiggle')

        @event('message')
        @channel('zaquelle')
        @message('zaqBS', 'in')
        @cooldown(90)
        async def zaq_butt_stuff(self, ctx: hints.PRIVMSG):
            await ctx.send('zaqBS')

        @event('message')
        @channel('zaquelle')
        @message('zaqCool', 'in')
        @cooldown(60)
        async def zaq_is_cool(self, ctx: hints.PRIVMSG):
            if 'zaqCoolCop' in ctx.message.content:
                await ctx.send('zaqCoolCop')
                return
            await ctx.send('zaqCool')

        @event('message')
        @channel('zaquelle')
        @message('Sadge 👑 🐘', 'in')
        @cooldown(60)
        async def queen_cutie_1(self, ctx: hints.PRIVMSG):
            await ctx.send('Sadge 👑 🐘')

        @event('message')
        @channel('zaquelle')
        @message('PepeHands 👑 🐘', 'in')
        @cooldown(60)
        async def queen_cutie_2(self, ctx: hints.PRIVMSG):
            await ctx.send('PepeHands 👑 🐘')

        @event('message')
        @channel('zaquelle')
        @message('COPIUM', 'in')
        @cooldown(60)
        async def copium(self, ctx: hints.PRIVMSG):
            await ctx.send('COPIUM')

        @event('message')
        @channel('zaquelle')
        @message('AYAYA', 'in')
        @cooldown(60)
        async def ayaya(self, ctx: hints.PRIVMSG):
            await ctx.send('AYAYA')

        @event('message')
        @channel('zaquelle')
        @message('pepeSmoke', 'in')
        @cooldown(120)
        async def smoke_hayes_smoke(self, ctx: hints.PRIVMSG):
            await ctx.send('pepeSmoke')

        @event('message')
        @channel('zaquelle')
        @message('zaqHayes', 'in')
        @cooldown(60)
        async def good_shit_hayes(self, ctx: hints.PRIVMSG):
            await ctx.send('zaqHayes')

        @event('message')
        @channel('zaquelle')
        @message('MLADY')
        @cooldown(60)
        async def mlady(self, ctx: hints.PRIVMSG):
            await ctx.send('MLADY')

        @event('message')
        @channel('zaquelle')
        @author('richardharrow_')
        @message('ppHopAround')
        async def ppHopAround(self, ctx: hints.PRIVMSG):
            await ctx.send('ppHopAround')

        @event('message')
        @channel('zaquelle')
        @message('!ping', 'sw')
        async def lol_you_thought(self, ctx: hints.PRIVMSG):
            pick = ["I may be a bot but you can't just ping me like that zaqK", 'Gimme your fingers zaqK',
                    f"c'mere {ctx.user} zaqK", 'ping me daddy zaqLewd', "i've been pinged AYAYA"]
            await ctx.send(random.choice(pick))

        @event('message')
        @channel('zaquelle')
        @author('nightbot')
        @message('Zaquelle has summoned her inner Wookie', 'sw')
        async def wookie(self, ctx: hints.PRIVMSG):
            await ctx.send('zaqWookie')

        @event('message')
        @channel('zaquelle')
        @author('oythebrave')
        @message('brb gotta pee')
        async def oys_gotta_pee(self, ctx: hints.PRIVMSG):
            await ctx.send('ok')

        @event('message')
        @channel('zaquelle')
        @author('oythebrave')
        @message('FeelsHayesMan Glizzy')
        @cooldown(60)
        async def hayes_feels_glizzy_man(self, ctx: hints.PRIVMSG):
            await ctx.send('FeelsHayesMan Glizzy')

        @event('message')
        @channel('zaquelle')
        @author('nightbot')
        @message('zaqT THIS IS YOUR REMINDER TO DRINK WATER OR SOME SORT OF LIQUID BECAUSE YOUR BODY NEEDS IT AND SHIT zaqT')
        async def drink_water_zaq(self, ctx: hints.PRIVMSG):
            await ctx.send('zaqT')

        @event('message')
        @channel('zaquelle')
        @author('nightbot')
        @message("If you're new to the stream and you're enjoying the content, don't forget to follow the channel to know when I am live! zaqHeart")
        async def enjoy_content_guys(self, ctx: hints.PRIVMSG):
            await ctx.send('zaqHeart zaqHeart zaqHeart')

        @event('message')
        @channel('zaquelle')
        @author('nightbot')
        @message('Zaquelle is afk zaqPls so the raccoons can dance away zaqPls and with a smirk zaqPls the chat will lurk zaqPls when Zaq comes back to play zaqLurk')
        async def zaq_is_afk(self, ctx: hints.PRIVMSG):
            await ctx.send('Zaquelle is afk zaqPls so the raccoons can dance away zaqPls and with a smirk zaqPls the chat will lurk zaqPls when Zaq comes back to play zaqLurk')

        @event('message')
        @channel('zaquelle')
        @author('oythebrave')
        @message('This zaq is good')
        async def zaq_is_good(self, ctx: hints.PRIVMSG):
            await ctx.send('NODDERS')

        @event('message')
        @channel('zaquelle')
        @author('oythebrave')
        @message('zaqNOM')
        async def zaq_nom(self, ctx: hints.PRIVMSG):
            await ctx.send('zaqPop')

        @event('message')
        @channel('zaquelle')
        @message('zaqPop', 'in')
        @cooldown(60)
        async def zaq_pop(self, ctx: hints.PRIVMSG):
            await ctx.send('zaqPop')

        @event('message')
        @channel('zaquelle')
        @message('zaqCA', 'in')
        @cooldown(60)
        async def zaq_coppa(self, ctx: hints.PRIVMSG):
            await ctx.send('zaqCA')

        @event('message')
        @channel('zaquelle')
        @author('streamlabs')
        @message('A !raffle raffle has started for Viewers use !raffle to enter the raffle.', 'in')
        async def raffle_start(self, ctx: hints.PRIVMSG):
            await ctx.send('!raffle')


if __name__ == '__main__':
    configure_logger(logging.DEBUG)

    Elenabot()
