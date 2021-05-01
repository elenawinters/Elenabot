# dev notes

this is just my personal notes for this project

###### example of how i want to start the bot

```py
client_id = '746869735f69735f6e6f745f616e5f6964'  # this_is_not_an_id in hex
oauth_token = '746f6b656e5f6e6f745f666f756e64'  # token_not_found in hex
channels = [zaquelle, elenaberry, ringomar, tahhp, dwingert, oythebrave]

# todo: create a good rule format
elenabotlib.run(client_id, oauth_token, channels, load_everything_from_folder)
# the above is a blocking call

# folder_loader = elenabotlib.load.folders(load_folders)
# instructions = [folder_loader]
# elenabotlib.run(client_id, oauth_token, join_channels, instructions)  # 
```

```py
def run(self, client_id, oauth_token, channels, rules = []):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    client = elenabotlib.Bot(client_id=client_id, rules=rules)  # the arugment
    client.join(channels)

    loop.run_until_complete(client.start(oauth_token))
    loop.close()



def start(oauth_token):
    # do the stuff

```


badge_info: Badge = field(default_factory=str)
    badges: list[Badge] = field(default_factory=list),
    bits: str = field(default_factory=str)
    color: int = field(default_factory=list)
    display_name: str = field(default_factory=str)
    emotes: list = field(default_factory=list)
    flags: list = field(default_factory=list)
    id: str = field(default_factory=str)
    mod: bool = field(default_factory=bool)
    room_id: int = field(default_factory=int)
    subscriber: bool = field(default_factory=bool)
    tmi_sent_ts: int = field(default_factory=int)
    turbo: bool = field(default_factory=bool)
    user_id: int = field(default_factory=list)
    user_type: str = field(default_factory=str)
    message: Message = field(default_factory=str)
    send: types.FunctionType = field(default_factory=types.FunctionType)