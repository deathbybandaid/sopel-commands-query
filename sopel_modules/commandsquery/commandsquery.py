# coding=utf-8

from __future__ import unicode_literals, absolute_import, division, print_function

import sopel
from sopel import module
from sopel.tools import stderr

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


def configure(config):
    pass


def setup(bot):
    stderr("[Sopel-CommandsQuery] Evaluating Core Commands List")

    threading.Thread(target=setup_thread, args=(bot,)).start()


def setup_thread(bot):

    bot.memory['Sopel-CommandsQuery'] = dict()
    for comtype in ['module', 'nickname', 'rule']:
        bot.memory['Sopel-CommandsQuery'][comtype + "_commands"] = dict()
        bot.memory['Sopel-CommandsQuery'][comtype + "_commands_count"] = 0

    filepathlisting = []

    # main Modules directory
    main_dir = os.path.dirname(os.path.abspath(sopel.__file__))
    modules_dir = os.path.join(main_dir, 'modules')
    filepathlisting.append(modules_dir)

    # Home Directory
    home_modules_dir = os.path.join(bot.config.homedir, 'modules')
    if os.path.isdir(home_modules_dir):
        filepathlisting.append(home_modules_dir)

    # pypi installed
    try:
        import sopel_modules
        pypi_modules = os.path.dirname(os.path.abspath(sopel_modules.__file__))
        pypi_modules_dir = os.path.join(pypi_modules, 'modules')
        filepathlisting.append(pypi_modules_dir)
    except Exception:
        pass

    # Extra directories
    filepathlist = []
    for directory in bot.config.core.extra:
        filepathlisting.append(directory)

    for directory in filepathlisting:
        for pathname in os.listdir(directory):
            path = os.path.join(directory, pathname)
            if (os.path.isfile(path) and path.endswith('.py') and not path.startswith('_')):
                filepathlist.append(str(path))

    # CoreTasks
    ct_path = os.path.join(main_dir, 'coretasks.py')
    filepathlist.append(ct_path)

    for modulefile in filepathlist:
        module_file_lines = []
        module_file = open(modulefile, 'r')
        lines = module_file.readlines()
        for line in lines:
            module_file_lines.append(line)
        module_file.close()

        dict_from_file = dict()
        filelinelist = []

        for line in module_file_lines:

            if str(line).startswith("@"):
                line = str(line)[1:]

                # Commands
                if str(line).startswith(tuple(["commands", "module.commands", "sopel.module.commands"])):
                    comtype = "module"
                    line = str(line).split("commands(")[-1]
                    line = str("(" + line)
                    validcoms = eval(str(line))
                    if isinstance(validcoms, tuple):
                        validcoms = list(validcoms)
                    else:
                        validcoms = [validcoms]
                    validcomdict = {"comtype": comtype, "validcoms": validcoms}
                    filelinelist.append(validcomdict)
                elif str(line).startswith(tuple(["nickname_commands", "module.nickname_commands", "sopel.module.nickname_commands"])):
                    comtype = "nickname"
                    line = str(line).split("commands(")[-1]
                    line = str("(" + line)
                    validcoms = eval(str(line))
                    if isinstance(validcoms, tuple):
                        validcoms = list(validcoms)
                    else:
                        validcoms = [validcoms]
                    nickified = []
                    for nickcom in validcoms:
                        nickified.append(str(bot.nick) + " " + nickcom)
                    validcomdict = {"comtype": comtype, "validcoms": nickified}
                    filelinelist.append(validcomdict)
                elif str(line).startswith(tuple(["rule", "module.rule", "sopel.module.rule"])):
                    comtype = "rule"
                    line = str(line).split("rule(")[-1]
                    validcoms = [str("(" + line)]
                    validcomdict = {"comtype": comtype, "validcoms": validcoms}
                    filelinelist.append(validcomdict)

        for atlinefound in filelinelist:

            comtype = atlinefound["comtype"]
            validcoms = atlinefound["validcoms"]

            comtypedict = str(comtype + "_commands")

            bot.memory['Sopel-CommandsQuery'][comtypedict + "_count"] += 1

            # default command to filename
            if "validcoms" not in dict_from_file.keys():
                dict_from_file["validcoms"] = validcoms

            maincom = dict_from_file["validcoms"][0]
            if len(dict_from_file["validcoms"]) > 1:
                comaliases = spicemanip.main(dict_from_file["validcoms"], '2+', 'list')
            else:
                comaliases = []

            bot.memory['Sopel-CommandsQuery'][comtypedict][maincom] = dict_from_file
            for comalias in comaliases:
                if comalias not in bot.memory['Sopel-CommandsQuery'][comtypedict].keys():
                    bot.memory['Sopel-CommandsQuery'][comtypedict][comalias] = {"aliasfor": maincom}

    for comtype in ['module_commands', 'nickname_commands', 'rule_commands']:
        stderr("[Sopel-CommandsQuery] Found " + str(len(bot.memory['Sopel-CommandsQuery'][comtype].keys())) + " " + comtype + " commands.")

    if botevents_installed:
        set_bot_event(bot, "Sopel-CommandsQuery")


def commandsquery_register(bot, command_type, validcoms, aliasfor=None):

    if not isinstance(validcoms, list):
        validcoms = [validcoms]

    if 'Sopel-CommandsQuery' not in bot.memory:
        bot.memory['Sopel-CommandsQuery'] = dict()

    if command_type not in bot.memory['Sopel-CommandsQuery'].keys():
        bot.memory['Sopel-CommandsQuery'][command_type] = dict()
        bot.memory['Sopel-CommandsQuery'][command_type + "_count"] = 0
    bot.memory['Sopel-CommandsQuery'][command_type + "_count"] += 1

    dict_from_file = dict()

    # default command to filename
    if "validcoms" not in dict_from_file.keys():
        dict_from_file["validcoms"] = validcoms

    if not aliasfor:

        maincom = dict_from_file["validcoms"][0]
        if len(dict_from_file["validcoms"]) > 1:
            comaliases = spicemanip.main(dict_from_file["validcoms"], '2+', 'list')
        else:
            comaliases = []
        bot.memory['Sopel-CommandsQuery'][command_type][maincom] = dict_from_file
    else:
        comaliases = validcoms

    for comalias in comaliases:
        if comalias not in bot.memory['Sopel-CommandsQuery'][command_type].keys():
            bot.memory['Sopel-CommandsQuery'][command_type][comalias] = {"aliasfor": aliasfor}
