import elenabotlib

# This is simply a test to see if the formatter works.

msg = '@badge-info=subscriber/1;badges=subscriber/0,premium/1;color=#1E90FF;display-name=222;emotes=;flags=;id=5562a2ca-6d7d-4dfb-a99b-b476cf6d85b7;login=222;mod=0;msg-id=sub;msg-param-cumulative-months=1;msg-param-months=0;msg-param-multimonth-duration=1;msg-param-multimonth-tenure=0;msg-param-should-share-streak=0;msg-param-sub-plan-name=Sub(null);msg-param-sub-plan=Prime;msg-param-was-gifted=false;room-id=85498365;subscriber=1;system-msg=222subbed;tmi-sent-ts=1735781423367;user-id=123456;user-type=;vip=0 :tmi.twitch.tv USERNOTICE #null'

test = elenabotlib.Session.twitch_irc_formatter(elenabotlib.Session, msg)
print(test)