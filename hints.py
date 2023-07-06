# THIS FILE CONTAINS THE TYPE HINTS FOR THE PROGRAM.
# BECAUSE OF HOW THE NEW VERSION WORKS,
# THIS MAY NOT ALWAYS BE ENTIRELY ACCURATE.

from dataclasses import dataclass

# taken from https://www.pythondoeswhat.com/2023/03/annotation-inheritance.html
# only using this for testing.
def inherit_annotations(cls):
    annotations = {}
    for parent in cls.__mro__[::-1]:
        # print(parent.__name__)
    	# reverse order so children override parents
        annotations.update(getattr(parent, "__annotations__", {}))
        # use getattr(): not everything has __annotations__
    cls.__annotations__.update(annotations)
    return cls


@dataclass
class Badge:
    name: str
    version: int


@dataclass
class Message:
    author: str
    channel: str
    content: str


@dataclass
class Sendable:
    send: str


@dataclass
@inherit_annotations
class Messageable(Sendable):
    message: Message


@dataclass
@inherit_annotations
class CLEARCHAT(Messageable):  # the minimum data that would be provided would just be the channel
    tmi_sent_ts: str
    ban_duration: int


@dataclass
@inherit_annotations
class CLEARMSG(Messageable):
    target_msg_id: str
    login: str


@dataclass
@inherit_annotations
class ROOMSTATE(Sendable):
    channel: str
    emote_only: bool
    followers_only: int
    r9k: bool
    slow: int
    subs_only: bool


@dataclass
@inherit_annotations
class NOTICE(Messageable):
    msg_id: str


@dataclass
class GLOBALUSERSTATE:  # in this codebase, this is considered the base struct for most actions
    badge_info: list[Badge]
    badges: list[Badge]
    color: str
    display_name: str
    emote_sets: list[int]
    turbo: bool
    user_id: int
    user_type: str
    vip: bool


@dataclass
@inherit_annotations
class USERSTATE(GLOBALUSERSTATE, Messageable):
    mod: bool
    subscriber: bool


@dataclass
class PINNED_CHAT:  # this is kinda new and hard for me to test currently. I'll probably obscure it under PRIVMSG eventually
    pinned_chat_paid_amount: int
    pinned_chat_paid_canonical_amount: int
    pinned_chat_paid_currency: str
    pinned_chat_paid_exponent: int
    pinned_chat_paid_is_system_messag: bool
    pinned_chat_paid_level: str


@dataclass
@inherit_annotations
class PRIVMSG(USERSTATE, PINNED_CHAT):
    bits: str
    emotes: list
    flags: list
    id: str
    room_id: int
    tmi_sent_ts: int
    action: bool



@dataclass
@inherit_annotations
class HOSTTARGET(Sendable):
    channel: str
    target: str
    viewers: int


@dataclass
@inherit_annotations
class JOIN(Sendable):  # join and part are the same struct, but for readability, they are seperated
    channel: str
    user: str


@dataclass
@inherit_annotations
class PART(Sendable):
    channel: str
    user: str


@dataclass
@inherit_annotations
class USERNOTICEBASE(PRIVMSG):  # this is the baseclass for USERNOTICE. used by the subclasses
    system_msg: str
    msg_id: str
    login: str


@dataclass
@inherit_annotations
class USERNOTICE(USERNOTICEBASE):  # there are a ton of params
    msg_param_cumulative_months: int
    msg_param_displayName: str
    msg_param_viewerCount: int
    msg_param_login: str
    msg_param_months: int
    msg_param_promo_gift_total: str
    msg_param_promo_name: str
    msg_param_recipient_display_name: str
    msg_param_recipient_id: str
    msg_param_recipient_user_name: str
    msg_param_sender_login: str
    msg_param_sender_name: str
    msg_param_multimonth_tenure: int
    msg_param_should_share_streak: int
    msg_param_streak_months: int
    msg_param_sub_plan_name: str
    msg_param_sub_plan: str
    msg_param_was_gifted: bool
    msg_param_ritual_name: str
    msg_param_threshold: int
    msg_param_gift_months: int


# Here we implement some custom ones for the bot dev to use
# USERNOTICE subclasses
@dataclass
@inherit_annotations
class SUBSCRIPTION(USERNOTICEBASE):  # This should be complete
    promo_total: int
    promo_name: str
    cumulative: int
    months: int
    recipient: str
    recipient_id: str
    sender: str
    share_streak: bool
    streak: int
    plan: str
    plan_name: str
    gifted_months: int


@dataclass
@inherit_annotations
class RITUAL(USERNOTICEBASE):  # yes this is a thing lol
    name: str


@dataclass
@inherit_annotations
class RAID(USERNOTICEBASE):
    raider: str
    viewers: int
