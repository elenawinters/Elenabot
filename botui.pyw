from elenabotlib import *
import tkinter as tk
import sys, os, ast
import configparser
import threading
import random

# Gonna be honest, I'm happy with this wrapper


class Elenabot:
    def __init__(self):
        self.setup_variables()
        self.app = tk.Tk()
        self.setup_window()
        self.app.after(100, self.check_config)
        self.app.mainloop()

    def setup_variables(self):
        self.bg_color = '#2C2F33'
        self.fg_color = '#23272A'

    def setup_window(self):
        self.app.title('Elenabot: wrapping elenabotlib')
        self.app.configure(bg=self.bg_color)
        self.app.geometry('850x450')

        # setup left side
        self.event_list = tk.Frame(self.app, width=200, height=400, bg='#6f7676')
        self.event_list.grid(row=0, column=0, padx=10, pady=5)

        # self.event_list_scrollbar = Scrollbar(self.frame_right, orient="vertical", command=self.event_list.yview)
        # self.event_list_scrollbar.pack(side="right", expand=True, fill="y")

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

                inputs[x] = tk.Entry(frames[x], width=27, fg = "white", bg=self.bg_color)
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

            save_frame = tk.Frame(confwin, width=300, height= 200, bg=self.fg_color)
            save_frame.grid(row=len(poplist)+1, column=0, padx=5, pady=5)

            save_but = tk.Button(save_frame, text = "Save" , fg = "white", bg=self.bg_color, height=1, command=process_config)
            save_but.grid(column=1, row=0, padx=10, pady=5, sticky='w'+'e'+'n'+'s')
        else:
            self.config.read(self.cfile)
            self.setup_thread()

        # confwin.destroy()

    def setup_thread(self):
        channels = ast.literal_eval(self.config['twitch']['channels'])
        thread_args = (self.config['twitch']['oauth'], self.config['twitch']['nickname'], channels)
        threading.Thread(target=self.start_program, name='ElenabotlibWrapper', daemon=True, args=thread_args).start()

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

    def process_event(self, cls, ctx):  # this is running in the scope of the wrapper. 'self' is uniform?
        log.debug(cls)
        log.debug(ctx)
        pass

if __name__ == '__main__':
    configure_logger(logging.DEBUG)

    Elenabot()
