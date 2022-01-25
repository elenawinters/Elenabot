from elenabotlib import *
from tkinter import ttk
import tkinter as tk
import sys, os, ast
import configparser
import threading
import random

# Gonna be honest, I'm happy with this wrapper
# Kerobel suggested Qt as a UI library. I'll probably make a seperate version with Qt later (maybe)


@dataclass
class Listener:
    event: str


@dataclass
class MemoryState:
    login: str = None
    listeners: list[Listener] = None
    user: dict[str, USERSTATE] = field(default_factory=dict)
    schedule: str = None


@dataclass
class ScrollbarPosition:
    hi: int = 0
    lo: int = 0


@dataclass
class TabStruct:
    tab: str = None
    limit: int = 2000
    upper: int = 0
    scroll_pos: ScrollbarPosition = None


class Elenabot:
    def __init__(self):
        self.setup_variables()
        self.app = tk.Tk()
        self.setup_window()
        self.app.after(100, self.check_config)
        self.app.mainloop()

    def setup_variables(self):
        self.state = MemoryState()
        self.bg_color = '#2C2F33'
        self.fg_color = '#23272A'
        self.greyple = '#99AAB5'
        self.tabs = {}

    def setup_style(self):
        style = ttk.Style()
        style.theme_create('elenabot', settings={
            "TNotebook": {
                "configure": {
                    "background": self.fg_color  # Your margin color
                }
            },
            "TNotebook.Tab": {
                "configure": {
                    "background": self.fg_color,  # tab color when not selected
                    "padding": [10, 2],  # [space between text and horizontal tab-button border, space between text and vertical tab_button border]
                    "focuscolor": self.bg_color,  # match focus color so the lines stop showing Madge
                    "font": "white"
                },
                "map": {
                    "foreground": [("selected", "white"), ("!disabled", self.greyple)],
                    "background": [("selected", self.bg_color)]  # Tab color when selected
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
        self.event_list = tk.Frame(self.app, width=200, height=20, bg=self.fg_color)
        # self.event_list.grid(row=0, column=0, padx=10, pady=5)

        # https://www.geeksforgeeks.org/creating-tabbed-widget-with-python-tkinter/
        # https://stackoverflow.com/a/45850468/14125122
        # https://stackoverflow.com/a/61236766/14125122
        self.tab_frame = tk.Frame(self.app, width=80, height=80, bg=self.fg_color)
        # self.tab_frame = tk.Frame(self.app, bg=self.fg_color)
        self.tab_controller = ttk.Notebook(self.tab_frame)
        self.tab_controller.pack(expand=True, fill='both', padx=10, pady=10)

        # https://stackoverflow.com/a/14012720/14125122  Use this for getting channel name
        # This needs to be incorporated into the add_tab function somehow
        self.mb_entry = tk.Entry(self.tab_frame, bg=self.bg_color, fg='white')
        self.mb_entry.pack(expand=True, fill='both', padx=10, pady=(0, 10), side='left')
        self.mb_entry.configure(insertbackground=self.greyple)

        def process_send(event=None):
            if msg := self.mb_entry.get():
                self.mb_entry.delete(0, 'end')
                self.send_message(msg)

        self.mb_entry.bind('<Return>', process_send)

        send_button = tk.Button(self.tab_frame, fg="white", bg=self.bg_color, height=1, width=3, command=process_send)
        send_button.pack(expand=False, fill='both', padx=(0, 10), pady=(0, 10), side='right')

        # self.event_list.pack(padx=10, pady=10)
        # self.tab_frame.pack(padx=(0, 10), pady=10)

        self.event_list.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        self.tab_frame.grid(row=0, column=1, padx=(0, 10), pady=10, sticky='nsew')
        # self.mb_frame.grid(row=1, column=1, padx=10, pady=10, sticky='nsew')
        self.app.columnconfigure(1, weight=1)  # magic
        self.app.rowconfigure(0, weight=1)

    def send_message(self, message):
        chan = self.tab_controller.tab(self.tab_controller.select(), 'text')
        to_insert = f'{self.cls.nick}: {message}\n'
        self.update_messages_widget(to_insert, chan)
        self.cls.send(message, chan)

    def add_tab(self, chan):
        tab = tk.Frame(self.tab_controller, bg=self.bg_color)
        self.tab_controller.add(tab, text=chan)

        self.tabs[chan] = TabStruct()

        self.tabs[chan].tab = tk.Text(tab, bg=self.fg_color, fg="white", width=0, height=0)
        self.tabs[chan].tab.pack(side='left', padx=5, pady=5, expand=True, fill='both')

        cscroll = tk.Scrollbar(tab, orient="vertical", command=self.tabs[chan].tab.yview)
        cscroll.pack(side="right", expand=False, fill="y")

        def scrollpos(y0, y1):
            cscroll.set(y0, y1)
            self.tabs[chan].scroll_pos = ScrollbarPosition(float(y0), float(y1))

        self.tabs[chan].tab.configure(yscrollcommand=scrollpos, insertbackground=self.fg_color, state='disabled')

    def destroy_tab(self):
        return NotImplementedError

    def load_listeners(self):
        pass

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

    def setup_thread(self):
        self.load_listeners()
        channels = ast.literal_eval(self.config['twitch']['channels'])
        thread_args = (self.config['twitch']['oauth'], self.config['twitch']['nickname'], channels)
        threading.Thread(target=self.start_program, name='ElenabotlibWrapper', daemon=True, args=thread_args).start()

    def update_messages_widget(self, message, chan):
        scroll_pos = self.tabs[chan].scroll_pos.lo

        self.tabs[chan].tab.configure(state='normal')
        self.tabs[chan].tab.insert(tk.END, message)

        del_line = 0
        currline = int(self.tabs[chan].tab.index('end-1c').split('.')[0])
        if int(currline > self.tabs[chan].limit):
            del_line = currline - self.tabs[chan].limit
            self.tabs[chan].tab.delete(f'{del_line}.0', f'{del_line + 1}.0')

        self.tabs[chan].tab.configure(state='disabled')

        line_count = currline - del_line
        scroll_line = scroll_pos * line_count
        if line_count - scroll_line <= 3:
            self.tabs[chan].tab.see(tk.END)

    def check_schedule(self, ctx):
        pass

    def start_program(self, oauth, nickname, channels):
        class wrapping(Session):
            def __init__(cls):
                super().__init__()  # lol i hate this but :shrug:
                self.cls = cls  # unknown consequences
                cls.start(oauth, nickname, channels)

            @event('join_self')
            async def on_bot_join_channel(cls, channel):
                if channel not in self.tabs:
                    self.add_tab(channel)

            @event('part_self')
            async def on_bot_part_channel(cls, channel):
                if channel in self.tabs:
                    self.destroy_tab(channel)

            @event('message')  # https://stackoverflow.com/a/34769569/14125122
            async def on_message_sent(cls, ctx):
                to_insert = f'{ctx.message.author}: {ctx.message.content}\n'
                self.update_messages_widget(to_insert, ctx.message.channel)
                # log.debug(f'{ctx.message.channel}: Line Count: {line_count}; Scrollbar Line: {scroll_line}; Difference: {diff}')

            @event('userstate')
            async def set_userstate_channel(cls, ctx):
                self.check_schedule(ctx)

            # @event('notice')
            # def receive_notice(cls, ctx):
            #     self.check_schedule(ctx)

            # @event('all')
            # def listen_for_event(cls, ctx):
            #     self.process_event(ctx)

        try:
            wrapping()
        except Exception as exc:
            log.exception(exc)

    # def process_event(self, ctx):
    #     name = type(ctx).__name__


if __name__ == '__main__':
    configure_logger(logging.DEBUG)

    Elenabot()
