from tkinter.constants import S
from elenabotlib import *
from tkinter import ttk
import tkinter as tk
import sys, os, ast
import configparser
import threading
import random

# Gonna be honest, I'm happy with this wrapper
# Kerobel suggested Qt as a UI library. I'll probably make a seperate version with Qt later (maybe)


class Elenabot:
    def __init__(self):
        self.setup_variables()
        self.app = tk.Tk()
        self.setup_window()
        self.app.after(100, self.check_config)
        self.app.mainloop()

    def setup_variables(self):
        # self.sticky_all = tk.E + tk.W + tk.N + tk.S
        self.bg_color = '#2C2F33'
        self.fg_color = '#23272A'
        self.greyple = '#99AAB5'
        self.tabs = {}

    def setup_style(self):
        style = ttk.Style()
        style.theme_create('elenabot', settings={
            "TNotebook": {
                "configure": {
                    "background": self.fg_color,  # Your margin color
                    # "tabmargins": [2, 5, 0, 0],  # margins: left, top, right, separator
                }
            },
            "TNotebook.Tab": {
                "configure": {
                    "background": self.fg_color,  # tab color when not selected
                    "padding": [10, 2],  # [space between text and horizontal tab-button border, space between text and vertical tab_button border]
                    "font": "white"
                },
                "map": {
                    "foreground": [("selected", "white"), ("!disabled", self.greyple)],
                    "background": [("selected", self.bg_color)],  # Tab color when selected
                    # "expand": [("selected", [1, 1, 1, 0])]  # text margins
                }
            }
        })
        style.theme_use('elenabot')

    def setup_window(self):
        self.app.title('Elenabot: wrapping elenabotlib')
        self.app.configure(bg=self.bg_color)
        self.app.geometry('850x450')
        self.setup_style()

        # setup left side
        self.event_list = tk.Frame(self.app, width=200, height=400, bg=self.fg_color)
        # self.event_list.grid(row=0, column=0, padx=10, pady=5)

        # https://www.geeksforgeeks.org/creating-tabbed-widget-with-python-tkinter/
        # https://stackoverflow.com/a/45850468/14125122
        # https://stackoverflow.com/a/61236766/14125122
        self.tab_frame = tk.Frame(self.app, width=200, height=400, bg=self.fg_color)
        # self.event_list.grid(row=1, column=1, padx=10, pady=5)
        self.tab_controller = ttk.Notebook(self.tab_frame)
        # self.tab_controller = CustomNotebook(self.tab_frame)
        self.tab_controller.pack(expand=True, fill='both', padx=10, pady=10)

        self.event_list.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        self.tab_frame.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')
        self.app.columnconfigure(1, weight=1)  # magic
        self.app.rowconfigure(0, weight=1)

    def add_tab(self, chan):
        tab = tk.Frame(self.tab_controller, bg=self.bg_color)
        self.tab_controller.add(tab, text=chan)
        # self.tabs[chan] = new_tab

        self.tabs[chan] = tk.Text(tab, bg=self.fg_color, fg="white")
        self.tabs[chan].pack(side='left', padx=5, pady=5, expand=True, fill='both')

        cscroll = tk.Scrollbar(self.tabs[chan], orient="vertical", command=self.tabs[chan].yview)
        cscroll.pack(side="right", expand=False, fill="y")

        self.tabs[chan].configure(yscrollcommand=cscroll.set)

        # self.tabs.update({chan: new_tab})
        # self.tab_controller.grid(padx=10, pady=10)
        # self.

    def load_listeners(self):
        self.listeners = {}

    def save_listeners(self):
        pass

    def listeners_window(self, data):
        pass

    def save_config(self):
        with open(self.cfile, 'w') as configfile:
            self.config.write(configfile)

    # https://github.com/RingoMar/rinLauncher/blob/main/ui.py
    def check_config(self):  # fuck this
        self.cfile = 'config.ini'
        self.config = configparser.ConfigParser()
        if not os.path.exists(self.cfile):
            confwin = tk.Toplevel(self.app)
            confwin.configure(bg=self.bg_color)
            confwin.title("Configuration Settings")
            confwin.geometry("420x200")
            confwin.resizable(False, False)

            # this could def be done better but im depressed and tired and dont care
            frames = {}
            labels = {}
            inputs = {}
            poplist = ['OAuth Token', 'Twitch Nickname', 'Initial Channel']
            matchlist = ['oauth', 'nickname', 'channels']
            for x in range(len(poplist)):
                frames[x] = tk.Frame(confwin, width=300, height=200, bg=self.fg_color)
                frames[x].grid(row=x, column=0, padx=25, pady=10)

                labels[x] = tk.Label(frames[x], fg="white", bg=self.fg_color, text=poplist[x])
                labels[x].grid()

                inputs[x] = tk.Entry(frames[x], width=27, fg="white", bg=self.bg_color)
                inputs[x].grid(column=1, row=0, padx=10, pady=3, ipadx=40)

            def process_config():
                cdict = {}
                for k, v in inputs.items():
                    if str(v.get()) != "":
                        if matchlist[k] == 'channels':
                            cdict[matchlist[k]] = [str(v.get())]
                        else:
                            cdict[matchlist[k]] = str(v.get())
                self.config['twitch'] = cdict
                self.save_config()
                self.setup_thread()
                confwin.destroy()

            save_frame = tk.Frame(confwin, width=300, height=200, bg=self.fg_color)
            save_frame.grid(row=len(poplist) + 1, column=0, padx=5, pady=5)

            save_but = tk.Button(save_frame, text="Save", fg="white", bg=self.bg_color, height=1, command=process_config)
            save_but.grid(column=1, row=0, padx=10, pady=5, sticky='w' + 'e' + 'n' + 's')
        else:
            self.config.read(self.cfile)
            self.setup_thread()

        # confwin.destroy()

    def setup_thread(self):
        self.load_listeners()
        channels = ast.literal_eval(self.config['twitch']['channels'])
        thread_args = (self.config['twitch']['oauth'], self.config['twitch']['nickname'], channels)
        threading.Thread(target=self.start_program, name='ElenabotlibWrapper', daemon=True, args=thread_args).start()

    def start_program(self, oauth, nickname, channels):
        class wrapping(Session):
            def __init__(cls):
                super().__init__()  # lol i hate this but :shrug:
                self.cls = cls  # unknown consequences
                cls.start(oauth, nickname, channels)

            @event('join_self')
            def on_bot_join_channel(cls, channel):
                if channel not in self.tabs:
                    self.add_tab(channel)

            @event('message')
            def on_message_sent(cls, ctx):
                to_insert = f'{ctx.display_name}: {ctx.message.content}'
                self.tabs[ctx.message.channel].insert(tk.END, to_insert + '\n')
                self.tabs[ctx.message.channel].see(tk.END)

            # @event('all')
            # def listen_for_event(cls, ctx):
            #     self.process_event(ctx)
            #     pass
        try:
            wrapping()
        except Exception as exc:
            log.exception(exc)

    # def process_event(self, ctx):  # this is running in the scope of the wrapper. 'self' is uniform?
    #     # log.debug(cls)
    #     # log.debug(ctx)
    #     pass


if __name__ == '__main__':
    configure_logger(logging.DEBUG)

    Elenabot()