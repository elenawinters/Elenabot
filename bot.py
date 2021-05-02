from elenabotlib import *
import sys, os, ast
import configparser

class Elenabot(Session):
    def __init__(self):
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

    @event('message')
    @author('elenaberry')
    @channel('elenaberry')
    @message('test')
    def bot_test(self, ctx):
        ctx.send('This is a test message')

    @event('message')
    @author('oythebrave')
    @message('brb gotta pee')
    def oys_gotta_pee(self, ctx):
        ctx.send('ok')

    @event('message')
    @author('nightbot')
    @message('zaqT THIS IS YOUR REMINDER TO DRINK WATER OR SOME SORT OF LIQUID BECAUSE YOUR BODY NEEDS IT AND SHIT zaqT')
    def drink_water_zaq(self, ctx):
        ctx.send('zaqT')

    @event('message')
    @author('oythebrave')
    @message('This zaq is good')
    def zaq_is_good(self, ctx):
        ctx.send('NODDERS')

    @event('message')
    @author('oythebrave')
    @message('zaqNOM')
    def zaq_nom(self, ctx):
        ctx.send('zaqPop')

    @event('message')
    @author('dwingert')
    @message('Did you know', 'sw')
    def dwin_did_you_know(self, ctx):
        ctx.send("did you know that y'all are cute paq")

if __name__ == '__main__':
    configure_logger(logging.DEBUG)

    Elenabot()
