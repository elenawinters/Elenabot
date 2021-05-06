from elenabotlib import *
import tkinter as tk
import sys, os, ast
import configparser
import threading
import random

# Gonna be honest, I'm happy with this wrapper

class Elenabot:
    def __init__(self):
        self.listeners = {}

        # setup tkinter shit
        self.app = tk.Tk()
        self.setup_window()
        self.setup_thread()
        self.app.mainloop()

    def setup_window(self):
        self.app.title('Elenabot: wrapping elenabotlib')
        self.app.geometry('850x450')

        # setup left side
        self.event_list = tk.Frame(self.app, width=200, height=400, bg='#6f7676')
        self.event_list.grid(row=0, column=0, padx=10, pady=5)

        # self.event_list_scrollbar = Scrollbar(self.frame_right, orient="vertical", command=self.event_list.yview)
        # self.event_list_scrollbar.pack(side="right", expand=True, fill="y")

    def listeners_window(self, data):
        pass

    def setup_thread(self):  # in the UI implementation, we need to do setup of config here. we can then read it in the wrapper like normal
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
        thread_args = (config['twitch']['oauth'], config['twitch']['nickname'], channels)
        threading.Thread(target=self.start_program, name=f'ElenabotlibWrapper', daemon=True, args=thread_args).start()

    def start_program(self, oauth, nickname, channels):
        class wrapping(Session):
            def __init__(cls):
                super().__init__()  # lol i hate this but :shrug:
                cls.start(oauth, nickname, channels)

            @event('all')
            def listen_for_event(cls, ctx):
                self.process_event(cls, ctx)
                pass
        try:
            wrapping()
        except Exception as exc:
            log.exception(exc)

    def process_event(self, cls, ctx):  # this is running in the scope of the wrapper.
        # for x in self.listeners:
            
        # log.debug(cls)
        # log.debug(ctx)
        pass

if __name__ == '__main__':
    configure_logger(logging.DEBUG)

    Elenabot()
