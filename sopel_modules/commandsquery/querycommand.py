# coding=utf-8

from __future__ import unicode_literals, absolute_import, division, print_function

from sopel import module

from .commandsquery import *

import os
from difflib import SequenceMatcher
from operator import itemgetter
import threading

try:
    from sopel_modules.botevents.botevents import *
    botevents_installed = True
except ImportError:
    botevents_installed = False

import spicemanip


@module.rule('^\?(.*)')
def query_detection(bot, trigger):

    while "Sopel-CommandsQuery" not in bot.memory:
        pass

    # command must start with
    if not str(trigger).startswith(tuple(['?'])):
        return

    commands_list = dict()
    for commandstype in bot.memory['Sopel-CommandsQuery'].keys():
        if not commandstype.endswith("_count"):
            for com in bot.memory['Sopel-CommandsQuery'][commandstype].keys():
                if com not in commands_list.keys():
                    commands_list[com] = bot.memory['Sopel-CommandsQuery'][commandstype][com]

    triggerargsarray = spicemanip.main(trigger, 'create')

    # command issued, check if valid
    querycommand = spicemanip.main(triggerargsarray, 1).lower()[1:]
    if len(querycommand) == 1:
        commandlist = []
        for command in commands_list.keys():
            if command.lower().startswith(querycommand):
                commandlist.append(command)
        if commandlist == []:
            bot.notice("No commands match " + str(querycommand) + ".", trigger.nick)
            return
        else:
            bot.notice("The following commands match " + str(querycommand) + ": " + spicemanip.main(commandlist, 'andlist') + ".", trigger.nick)
            return

    elif querycommand.endswith(tuple(["+"])):
        querycommand = querycommand[:-1]
        if querycommand not in commands_list.keys():
            bot.notice("The " + str(querycommand) + " does not appear to be valid.")
            return
        realcom = querycommand
        if "aliasfor" in commands_list[querycommand].keys():
            realcom = commands_list[querycommand]["aliasfor"]
        validcomlist = commands_list[realcom]["validcoms"]
        bot.notice("The following commands match " + str(querycommand) + ": " + spicemanip.main(validcomlist, 'andlist') + ".", trigger.nick)
        return

    elif querycommand.endswith(tuple(['?'])):
        querycommand = querycommand[:-1]
        sim_com, sim_num = [], []
        for com in commands_list.keys():
            similarlevel = SequenceMatcher(None, querycommand.lower(), com.lower()).ratio()
            sim_com.append(com)
            sim_num.append(similarlevel)
        sim_num, sim_com = (list(x) for x in zip(*sorted(zip(sim_num, sim_com), key=itemgetter(0))))
        closestmatch = spicemanip.main(sim_com, 'reverse', "list")
        listnumb, relist = 1, []
        for item in closestmatch:
            if listnumb <= 10:
                relist.append(str(item))
            listnumb += 1
        bot.notice("The following commands may match " + str(querycommand) + ": " + spicemanip.main(relist, 'andlist') + ".", trigger.nick)
        return

    elif querycommand in commands_list.keys():
        bot.notice("The following commands match " + str(querycommand) + ": " + str(querycommand) + ".", trigger.nick)
        return

    elif not querycommand:
        return

    else:
        commandlist = []
        for command in commands_list.keys():
            if command.lower().startswith(querycommand):
                commandlist.append(command)
        if commandlist == []:
            bot.notice("No commands match " + str(querycommand) + ".", trigger.nick)
            return
        else:
            bot.notice("The following commands match " + str(querycommand) + ": " + spicemanip.main(commandlist, 'andlist') + ".", trigger.nick)
            return
