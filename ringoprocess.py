import datetime
import json
import random
import re
import time
import traceback
from datetime import datetime as dt
from datetime import timedelta
from time import sleep as sleep

from colorama import Back, Fore, Style, init
from cogs.utils.dataIO import dataIO

import main
from vglobals import *
# from main import *

init()


giftcount = 0
mgft = False
blank = False

#the ghost of the subgoal file stuff is here boOOOOoooOooooOo


def send_to(text):
    """If you have multiple channels then you can send a messages based on who sent the message"""
    try:
        st = re.search(r"(#[a-zA-Z0-9-_\w]+) :", text)
        return st.group(1)
    except AttributeError:
        pass


def _findbadges(rx):
    """This is used to get only the important user badges"""

    user_meta = ""
    badgetype = ["broadcaster/", 'staff/', 'vip/', 'moderator/', 'subscriber/',
                 'sub-gifter/', 'turbo/', 'premium/', 'partner/', "bits/", 'global_mod/']
    for badge in badgetype:
        if re.search(badge, rx):
            bamount = re.search(r"bits/([0-9]+)", rx)
            gitnum = re.search(r"sub-gifter/([0-9]+)", rx)
            subnum = re.search(r"subscriber/([0-9]+)", rx)
            if badge == "bits/":
                user_meta += (f"[B/{bamount.group(1)}]")
            elif badge == "vip/":
                user_meta += "[VIP]"
            elif badge == "staff/":
                user_meta += "[TOS]"
            elif badge == "turbo/":
                user_meta += "[T]"
            elif badge == "partner/":
                user_meta += "[PART]"
            elif badge == "premium/":
                user_meta += "[P]"
            elif badge == "moderator/":
                user_meta += "[M]"
            elif badge == "sub-gifter/":
                user_meta += f"[GIFT/{gitnum.group(1)}]"
            elif badge == "global_mod/":
                user_meta += "[GM]"
            elif badge == "subscriber/":
                user_meta += (f"[S/{subnum.group(1)}]")
            elif badge == "broadcaster/":
                user_meta += "[BC]"
    return user_meta


def _Converttime(t):
    """This is used to convert seconds into days/hrs/min/sec for nice on the eyes"""
    sec = timedelta(seconds=int(t))
    d = dt(1, 1, 1) + sec
    ttt = ""
    if d.day-1 > 0:
        ttt += str("{}D ".format(d.day-1))
    if d.hour > 0:
        ttt += str("{}H ".format(d.hour))
    if d.minute > 0:
        ttt += str("{}M ".format(d.minute))
    if d.second > 0:
        ttt += str("{}S ".format(d.second))
    return ttt


def _getsubplan(num):
    """Sub Plans from raw to text"""
    plans = {
        "1000": "a Tier 1 sub",
        "2000": "a Tier 2 sub",
        "3000": "a Tier 3 sub",
        "Prime": "Twitch Prime"
    }
    _type = plans[num]
    return _type


def chatformater(text, sock):
    """My chat formatter for dumping messages from chat into the console"""
    global blank
    try:
        DPN = ""
        badges = _findbadges(text)
        bitamount = re.search(r"bits=([0-9]+)", text)
        if "bits=" in text:
            ctime = ("{:{tfmt}}".format(dt.now(), tfmt="[%H:%M:%S]"))
            badges = _findbadges(text)
            user = re.search(r"display-name=([a-zA-Z0-9-_\w]+)", text)
            stream = re.search(r"(#[a-zA-Z0-9-_\w]+) :", text)
            findbit = ("PRIVMSG {} :".format(stream.group(1)))
            bitmsg = text.split(findbit)
            try:
                DPN += user.group(1)
            except AttributeError:
                user = re.search(
                    r":([a-zA-Z0-9-_\w]+)!([a-zA-Z0-9-_\w]+)@([a-zA-Z0-9-_\w]+)", text)
                try:
                    DPN += user.group(1)
                except AttributeError:
                    DPN += "Anon"

            try:
                print(ctime + Fore.WHITE + Back.RED + DPN + " Cheared " +
                      bitamount.group(1) + " bits!" + Style.RESET_ALL)
                print(ctime + Fore.WHITE + Back.RED + badges +
                      DPN + ": " + bitmsg[1] + Style.RESET_ALL)
            except IndexError:
                print(Fore.WHITE + Back.RED + DPN + " Cheared " +
                      bitamount.group(1) + " bits!" + Style.RESET_ALL)

        elif str("PRIVMSG") in text:
            stream = re.search(r"(#[a-zA-Z0-9-_\w]+) :", text)
            findprv = ("PRIVMSG {} :".format(stream.group(1)))
            pri = text.split(findprv)
            ctime = ("{:{tfmt}}".format(dt.now(), tfmt="[%H:%M:%S]"))
            user = re.search(r"display-name=([a-zA-Z0-9-_\w]+)", text)
            try:
                DPN += user.group(1)
            except AttributeError:
                user = re.search(
                    r":([a-zA-Z0-9-_\w]+)!([a-zA-Z0-9-_\w]+)@([a-zA-Z0-9-_\w]+)", text)
                try:
                    DPN += user.group(1)
                except AttributeError:
                    DPN += "Anon"
            if not DPN == "RingoMar":
                addline()
            if "ringo" in text.lower():
                privM = Fore.WHITE + Back.BLUE + pri[1].replace("ACTION ", "[me]").replace("",
                                                                                            "[/me]") + Style.RESET_ALL
            else:
                privM = pri[1].replace(
                    "ACTION ", "[me]").replace("", "[/me]")

            if stream.group(1) == ("#" + botname):
                thestream = (f"[{stream.group(1)}]")
            else:
                thestream = (
                    "[" + Fore.GREEN + stream.group(1) + Style.RESET_ALL + "]")
            print(ctime + thestream + badges + DPN + ": " + privM)

    except Exception as e:
        ErrorData.error(e)
        ErrorData.error(traceback.format_exc())
    return


def historicalchatformater(text, sock):
    """ For prining past messages to the console when you first join or re join chat to catch up
    using: https://recent-messages.robotty.de/api/v2/recent-messages/zaquelle
    """
    global blank
    try:
        DPN = ""
        badges = _findbadges(text)
        bitamount = re.search(r"bits=([0-9]+)", text)
        if "bits=" in text:
            ctime = ("{:{tfmt}}".format(dt.now(), tfmt="[%H:%M:%S]"))
            badges = _findbadges(text)
            user = re.search(r"display-name=([a-zA-Z0-9-_\w]+)", text)
            stream = re.search(r"(#[a-zA-Z0-9-_\w]+) :", text)
            findbit = ("PRIVMSG {} :".format(stream.group(1)))
            bitmsg = text.split(findbit)
            try:
                DPN += user.group(1)
            except AttributeError:
                user = re.search(
                    r":([a-zA-Z0-9-_\w]+)!([a-zA-Z0-9-_\w]+)@([a-zA-Z0-9-_\w]+)", text)
                try:
                    DPN += user.group(1)
                except AttributeError:
                    DPN += "Anon"

            try:
                print(ctime + Fore.WHITE + Back.RED + DPN + " Cheared " +
                      bitamount.group(1) + " bits!" + Style.RESET_ALL)
                print(ctime + Fore.WHITE + Back.RED + badges +
                      DPN + ": " + bitmsg[1] + Style.RESET_ALL)
            except IndexError:
                print(Fore.WHITE + Back.RED + DPN + " Cheared " +
                      bitamount.group(1) + " bits!" + Style.RESET_ALL)

        elif str("PRIVMSG") in text:
            stream = re.search(r"(PRIVMSG #[a-zA-Z0-9-_\w]+) ", text)
            pri = text.split(stream.group(1))
            chanName = stream.group(1).split(" ")
            # historical
            ctime = ("{:{tfmt}}".format(dt.now(), tfmt="[%H:%M:%S]"))
            user = re.search(r"display-name=([a-zA-Z0-9-_\w]+)", text)
            try:
                DPN += user.group(1)
            except AttributeError:
                user = re.search(
                    r":([a-zA-Z0-9-_\w]+)!([a-zA-Z0-9-_\w]+)@([a-zA-Z0-9-_\w]+)", text)
                try:
                    DPN += user.group(1)
                except AttributeError:
                    DPN += "Anon"
            if "ringo" in text.lower():
                privM = Fore.WHITE + Back.BLUE + pri[1].replace("ACTION ", "[me]").replace("",
                                                                                            "[/me]") + Style.RESET_ALL
            else:
                privM = pri[1].replace(
                    "ACTION ", "[me]").replace("", "[/me]")

            if chanName[1] == ("#" + botname):
                thestream = (f"[HISTORICAL {chanName[1]}]")
            else:
                thestream = ("[" + "HISTORICAL" + Fore.GREEN +
                             chanName[1] + Style.RESET_ALL + "]")
            print(ctime + thestream + badges + DPN + privM)

    except Exception as e:
        ErrorData.error(e)
        ErrorData.error(traceback.format_exc())
    return


def Cheermotes(text, sock):
    """ When people send cheers in chat the bot replys
    Chnage the text on this
    """
    try:
        DPN = ""
        schan = send_to(text)
        bitamount = re.search(r"bits=([0-9]+)", text)
        if "bits=" in text:
            user = re.search(r"display-name=([a-zA-Z0-9-_\w]+)", text)
            try:
                DPN += user.group(1)
            except AttributeError:
                user = re.search(
                    r":([a-zA-Z0-9-_\w]+)!([a-zA-Z0-9-_\w]+)@([a-zA-Z0-9-_\w]+)", text)
                try:
                    DPN += user.group(1)
                except AttributeError:
                    DPN += "Anon"

            ba = bitamount.group(1)
            bn = DPN
            if str(bn) == "AnAnonymousCheerer":
                if int(ba) == 69:
                    sock.send(("PRIVMSG {} :Ghost {} bits, how lewd. zaqLewd\r\n").format(
                        schan, ba).encode("utf-8"))
                elif int(ba) == 1:
                    sock.send(("PRIVMSG {} :{} Bit.\r\n").format(
                        schan, ba).encode("utf-8"))
                else:
                    sock.send(("PRIVMSG {} :{} Bits.\r\n").format(
                        schan, ba).encode("utf-8"))
            elif int(ba) == 69:
                sock.send(("PRIVMSG {} :zaqLewd {} bits\r\n").format(
                    schan, ba).encode("utf-8"))
            elif int(ba) == 100 or int(ba) == 500:
                sock.send(("PRIVMSG {} :{} bits? zaqOMGA Raccoon murder!\r\n").format(
                    schan, ba).encode("utf-8"))
            elif int(ba) > 999:
                sock.send(("PRIVMSG {} :Wow {} is whole lotta bits! zaqOMGA\r\n").format(
                    schan, ba).encode("utf-8"))
            elif int(ba) > 9999:
                sock.send(("PRIVMSG {} :zaqOMGA Sooooooo much bits! zaqOMGA\r\n").format(
                    schan, ba).encode("utf-8"))
            elif int(ba) >= 5:
                sock.send(("PRIVMSG {} :BIGRACC {} BITS! BIGRACC \r\n").format(
                    schan, ba).encode("utf-8"))

    except Exception as e:
        ErrorData.error(e)
        ErrorData.error(traceback.format_exc())
    return


def noticesend(text, sock):
    """ This is for all subs/resubs/gift subs
    note that the subgoal stuff is still sort of in it might need to rewrite a it of it
    """
    try:
        global giftcount
        global mgft
        # badges = _findbadges(text)

        DPN = ""
        RDP = ""
        STPE = ""
        memeSubTime = dt.now().strftime('%Y%m%d%H%M%S')
        if str("tmi.twitch.tv USERNOTICE ") in text:
            messagetype = re.search(r"msg-id=([a-zA-Z]+)", text)
            gs = re.search(
                r"system-msg=[a-zA-Z0-9-_\w]+ (gifted)", text.replace("\s", " "))
            user = re.search(r"display-name=([a-zA-Z0-9-_\w]+)", text)
            try:
                try:
                    DPN += user.group(1)
                except AttributeError:
                    user = re.search(
                        r":([a-zA-Z0-9-_\w]+)!([a-zA-Z0-9-_\w]+)@([a-zA-Z0-9-_\w]+)", text)
                    try:
                        DPN += user.group(1)
                    except AttributeError:
                        DPN += "Annon"
                subtype = re.search(r"plan=([e-rE-R0-9]+)", text)
                try:
                    if str(_getsubplan(subtype.group(1))) == "Twitch Prime":
                        STPE += "NODDERS WITH PRIME raccPog  "
                    elif str(_getsubplan(subtype.group(1))) == "a Tier 3 sub":
                        STPE += "They have joined the Tier 3 club!"
                except AttributeError:
                    pass
                if str(messagetype.group(1)) == "resub":
                    giftcount = 0
                    get_months = re.search(
                        r"msg-param-cumulative-months=([0-9]+)", text)
                    if get_months.group(1) == "36":
                        sock.send(("PRIVMSG {} :.me peepoBike zaqOMGA 3 YEARS! zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA {}\r\n").format(
                            chan, STPE).encode("utf-8"))
                    elif get_months.group(1) == "24":
                        sock.send(("PRIVMSG {} :.me zaqHugA 2 YEARS! zaqClap zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA {}\r\n").format(
                            chan, STPE).encode("utf-8"))
                    elif get_months.group(1) == "9":
                        sock.send(("PRIVMSG {} :.me raccPog A Twitch Baby! zaqOMGA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA {}\r\n").format(
                            chan, DPN, STPE).encode("utf-8"))
                    else:
                        sock.send(("PRIVMSG {} :.me MYAAA {} months! MYAAA  zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA {}\r\n").format(
                            chan, get_months.group(1), STPE).encode("utf-8"))
                    print(Fore.WHITE + Back.RED + DPN + " Resubed for: {} months with {}!".format(
                        get_months.group(1),   _getsubplan(subtype.group(1))) + Style.RESET_ALL)
                elif str(messagetype.group(1)) == "sub":
                    giftcount = 0
                    sock.send(("PRIVMSG {} :zaqOMGA Welcome to the ZaqPaq! zaqOMGA zaqHA {}\r\n").format(
                        chan, STPE).encode("utf-8"))
                    print(Fore.WHITE + Back.RED + DPN + " subscribed with " +
                          _getsubplan(subtype.group(1)) + Style.RESET_ALL)
                elif str(messagetype.group(1)) == "bitsbadgetier":
                    sock.send(("PRIVMSG {} :NODDERS N E W BITS BADGE TIER zaqHA\r\n").format(
                        chan).encode("utf-8"))
                    bitbd = re.search(r"msg-param-threshold=([0-9]+)", text)
                    print(Fore.WHITE + Back.RED + DPN +
                          " Just got a new bit tier! {}!".format(bitbd.group(1)) + Style.RESET_ALL)
                elif str(messagetype.group(1)) == "raid":
                    rc = re.search(r"msg-param-viewerCount=([0-9]+)", text)
                    if int(rc.group(1)) > 2:
                        sock.send(("PRIVMSG {} :{} Raiders! Welcome! zaqVA zaqVA \r\n").format(
                            chan, rc.group(1)).encode("utf-8"))
                    elif int(rc.group(1)) > 10:
                        sock.send(("PRIVMSG {} :{} Raiders! Welcome! zaqVA zaqVA zaqVA zaqVA zaqVA zaqVA \r\n").format(
                            chan, rc.group(1)).encode("utf-8"))
                    elif int(rc.group(1)) > 50:
                        sock.send(("PRIVMSG {} :{} Raiders! Welcome! zaqVA zaqVA zaqVA zaqVA zaqVA zaqVA zaqVA zaqVA zaqVA\r\n").format(
                            chan, rc.group(1)).encode("utf-8"))
                    elif int(rc.group(1)) > 99:
                        sock.send(("PRIVMSG {} :{} Raiders! Welcome! zaqVA zaqVA zaqVA zaqVA zaqVA zaqVA zaqVA zaqVA zaqVA zaqVA zaqVA zaqVA zaqVA zaqVA zaqVA zaqVA zaqVA zaqVA zaqVA zaqVA zaqVA zaqVA zaqVA zaqVA \r\n").format(
                            chan, rc.group(1)).encode("utf-8"))
                    print(Fore.WHITE + Back.RED + DPN +
                          " Raid with {} viewers!".format(rc.group(1)) + Style.RESET_ALL)
                elif str(messagetype.group(1)) == "primepaidupgrade":
                    addsubformeme(memeSubTime)
                    sock.send(("PRIVMSG {} :POOF! zaqMagic {} had an evolution from prime! zaqHA {}\r\n").format(
                        chan, DPN, STPE).encode("utf-8"))
                    print(Fore.WHITE + Back.RED + DPN + " Upgraded from prime to {}!".format(
                        _getsubplan(subtype.group(1))) + Style.RESET_ALL)
                elif str(messagetype.group(1)) == "giftpaidupgrade":
                    sn = re.search(
                        r"msg-param-sender-name=([a-zA-Z0-9-_\w]+)", text)
                    sock.send(("PRIVMSG {} :raccPog raccPog raccPog zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA \r\n").format(
                        chan, DPN, sn.group(1)).encode("utf-8"))
                    print(Fore.WHITE + Back.RED + DPN +
                          " is continuing a sub from {}!".format(sn.group(1)) + Style.RESET_ALL)
                elif str(messagetype.group(1)) == "ritual":
                    pass
                elif str(messagetype.group(1)) == "subgift" or gs:
                    rname = re.search(
                        r"msg-param-recipient-display-name=([a-zA-Z0-9-_\w]+)", text)
                    print(Fore.WHITE + Back.RED + DPN + " gifted {} to {} ".format(
                        _getsubplan(subtype.group(1)), rname.group(1)) + Style.RESET_ALL)
                    if (giftcount) > 0:
                        giftcount -= 1
                        pass
                    elif mgft == True:
                        mgft = False
                        sock.send(("PRIVMSG {} :zaqDisco {} Violently took some raccoons and put them in trash cans! zaqDisco\r\n").format(
                            chan, DPN).encode("utf-8"))
                        print(Fore.WHITE + Back.RED + DPN +
                              " Dropped a mass gift sub " + Style.RESET_ALL)
                    else:
                        try:
                            RDP += rname.group(1)
                        except AttributeError:
                            pass
                        if str(rname.group(1)) == "RingoMar":
                            sock.send(("PRIVMSG {} :You didn't have to but thank you for gifting me a sub zaqAWA\r\n").format(
                                chan).encode("utf-8"))
                        elif str(DPN).lower() == "kilil":
                            kilil = [f'.me Kilil pops up behind {RDP}. "You can be an honorary Paq member now!"', f'Kilil gets an extra long grabby stik, and pulls {RDP} out of a garbo pile, dusts them off.', f'Kilil gave {RDP} a zaqHug and left a free sub in their pocket. zaqAWA', f'Kilil opened up a trapped door under your seat, and you now have your own trash can {RDP}!',
                                     f'Kilil turns on a mega fan pointed at {RDP} and blows them into a trashcan! zaqHug 💨 zaqVA', f'A loud explosion erupts as Kilil snipes {RDP} into a can zaqVA', f'Kilil does a one handed drift drive-by on {RDP} waschBLE BLAPBLAP', f'Kilil zooms by in a hot air balloon and picks up {RDP} with a long grabber stick zaqS 🎈']
                            sock.send(("PRIVMSG {} :{}\r\n").format(
                                chan, random.choice(kilil)).encode("utf-8"))
                        else:
                            sock.send(("PRIVMSG {} :🕹 ☜ zaqPbt {} played a mini claw game and picked up {}! zaqAWA\r\n").format(
                                chan, DPN, RDP).encode("utf-8"))
                elif str(messagetype.group(1)) == "submysterygift":
                    giftcount = 0
                    giftcounta = re.search(
                        r"msg-param-mass-gift-count=([0-9]+)", text)
                    deting = int(giftcounta.group(1))
                    fcount = (deting - 1)
                    if fcount > 0:
                        mgft = True
                    giftcount += int(fcount)
                    addsub(deting)
                    print(Fore.WHITE + Back.RED + DPN + " is mass gifting {} people with {} ".format(
                        deting, _getsubplan(subtype.group(1))) + Style.RESET_ALL)
                elif str(messagetype.group(1)) == "extendsub":
                    extendamt = re.search(
                        r"msg-param-sub-benefit-end-month=([0-9]+)", text)
                    sock.send(("PRIVMSG {} :zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA zaqHA\r\n").format(
                        chan, DPN, extendamt.group(1)).encode("utf-8"))
                    print(Fore.WHITE + Back.RED + DPN +
                          " has extended a sub" + Style.RESET_ALL)

                else:
                    """Some times the socket spits out data we dont use just prini it out""" 
                    print("Untracked Data: ", text)
            except Exception as e:
                ErrorData.error(e)
                ErrorData.info('"{}"'.format(text))
                ErrorData.error(traceback.format_exc())
            if getsubgoal() == 69:
                sock.send(("PRIVMSG {} :.me Pog Subgoal is now at 69\r\n").format(
                    chan).encode("utf-8"))
            else:
                pass
    except Exception as e:
        ErrorData.error(e)
        ErrorData.info('"{}"'.format(text))
        ErrorData.error(traceback.format_exc())
    return


def mopping(text):
    """MODES? modCheck"""
    schan = send_to(text)
    timecut = (" {} :".format(schan))
    tmsg = text.split(timecut)
    ctime = ("{:{tfmt}}".format(dt.now(), tfmt="[%H:%M:%S]"))
    try:
        if "@ban-duration" in text:
            time = re.search(r"@ban-duration=([0-9]+)", text)
            time_len = (int(time.group(1)))
            rg = _Converttime(time_len)
            if time_len < 59:
                print(">>" + ctime + Fore.RED + "Chatter {} was given a timeout for {}s".format(
                    tmsg[1], time.group(1)) + Style.RESET_ALL)
            else:
                print(">>" + ctime + Fore.RED + "Chatter {} was given a timeout for {}s".format(
                    tmsg[1], time.group(1)) + Style.RESET_ALL + (" ({})").format(rg[:-1]))
        elif "@login" in text:
            user = re.search(r"@login=([a-zA-Z0-9-_\w]+)", text)
            print(">>" + ctime + Fore.RED + "Chatter {} was purged for saying:".format(
                user.group(1)) + Style.RESET_ALL + tmsg[1].replace("ACTION ", "[me]").replace("", "[/me]"))
        elif "CLEARCHAT" in text:
            try:
                print(
                    ">>" + ctime + Fore.RED + "Chatter {} was permanently banned.".format(tmsg[1]) + Style.RESET_ALL)
            except IndexError:
                print(
                    ">>" + ctime + Fore.RED + "Chat was cleared by a moderator." + Style.RESET_ALL)

    except Exception as e:
        ErrorData.error(e)
        ErrorData.info('"{}"'.format(text))
        ErrorData.error(traceback.format_exc())
    return


def serverinfo(text):
    """Twtich just sending updates here"""
    try:
        ctime = ("{:{tfmt}}".format(dt.now(), tfmt="[%H:%M:%S]"))
        schan = send_to(text)
        startmsg = re.search(r":tmi.twitch.tv [0-9]+ " + botname, text)
        roomsate = re.search(r":tmi.twitch.tv NOTICE " + chan + " :", text)
        modslist = re.search(
            ":" + botname + r".tmi.twitch.tv [0-9]+ " + botname, text)
        if ":jtv MODE" in text:
            print(Fore.WHITE + Back.GREEN + ctime +
                  "[INFO]" + Style.RESET_ALL + text)
        elif startmsg:
            print(Fore.WHITE + Back.GREEN + ctime +
                  "[INFO]" + Style.RESET_ALL + text)
        elif "USERSTATE" in text:
            DPN = ""
            user = re.search(r"display-name=([a-zA-Z0-9-_\w]+)", text)
            try:
                DPN += user.group(1)
            except AttributeError:
                user = re.search(
                    r":([a-zA-Z0-9-_\w]+)!([a-zA-Z0-9-_\w]+)@([a-zA-Z0-9-_\w]+)", text)
                try:
                    DPN += user.group(1)
                except AttributeError:
                    DPN += "Anon"
            badges = _findbadges(text)
            usm = text.split(":tmi.twitch.tv ")
            print(Fore.WHITE + Back.BLUE + ctime +
                  "[MSG]" + Style.RESET_ALL + badges + DPN + ": " + usm[1])
        elif "ROOMSTATE #" in text:
            try:
                roomstatus = re.search(r"([a-zA-Z0-9-_]+)=1", text)
                rs = text.split(":")
                if not roomstatus:
                    print(Fore.WHITE + Back.BLUE + ctime +
                          "[ROOM]" + Style.RESET_ALL + ":NORMAL :" + rs[1])
                else:
                    xroom = roomstatus.group(1).replace(
                        "-", " ").replace("=1", "")
                    print(Fore.WHITE + Back.BLUE + ctime +
                          "[ROOM]" + Style.RESET_ALL + ":" + xroom.upper() + " :" + rs[1])
            except IndexError:
                pass
        elif modslist:
            print(Fore.WHITE + Back.GREEN + ctime +
                  "[INFO]" + Style.RESET_ALL + text)
        elif "HOSTTARGET" in text:
            findnum = ("{} :".format(schan))
            tmsg = text.split(findnum)
            if tmsg[1] == ":- 0":
                pass
            else:
                hostinfo = re.split(" ", tmsg[1])
                if str(hostinfo[1]) == "-":
                    print(Fore.WHITE + Back.GREEN + ctime +
                          "[INFO]" + Style.RESET_ALL + ":{} is hosting {} ".format(schan, hostinfo[0]))
                elif int(hostinfo[1]) > 0:
                    print(Fore.WHITE + Back.GREEN + ctime +
                          "[INFO]" + Style.RESET_ALL + ":{} is hosting {} for {} viewers".format(schan,
                                                                                                 hostinfo[0], hostinfo[1]))
        elif roomsate:
            splitrs = " NOTICE " + schan + " :"
            rs_msg = text.split(splitrs)
            print(Fore.WHITE + Back.GREEN + ctime +
                  "[INFO]" + Style.RESET_ALL + rs_msg[1])
        elif ".tmi.twitch.tv PART #" in text or ".tmi.twitch.tv JOIN #" in text:
            pass
        elif "PING :tmi.twitch.tv" in text:
            pass

    except Exception as e:
        ErrorData.error(e)
        ErrorData.error(traceback.format_exc())

    return