# coding=utf-8

from __future__ import unicode_literals, absolute_import, division, print_function

import sopel
from sopel import module

import os
from difflib import SequenceMatcher
from operator import itemgetter


def configure(config):
    pass


def setup(bot):

    bot.memory['commandslist'] = dict()
    for comtype in ['module', 'nickname', 'rule']:
        comtypedict = str(comtype + "_commands")
        bot.memory['commandslist'][comtypedict] = dict()

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

    for module in filepathlist:
        module_file_lines = []
        module_file = open(module, 'r')
        lines = module_file.readlines()
        for line in lines:
            module_file_lines.append(line)
        module_file.close()

        dict_from_file = dict()
        dict_from_file_complete = False
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

            # default command to filename
            if "validcoms" not in dict_from_file.keys():
                dict_from_file["validcoms"] = validcoms

            maincom = dict_from_file["validcoms"][0]
            if len(dict_from_file["validcoms"]) > 1:
                comaliases = spicemanip(bot, dict_from_file["validcoms"], '2+', 'list')
            else:
                comaliases = []

            bot.memory['commandslist'][comtypedict][maincom] = dict_from_file
            for comalias in comaliases:
                if comalias not in bot.memory['commandslist'][comtypedict].keys():
                    bot.memory['commandslist'][comtypedict][comalias] = {"aliasfor": maincom}


@module.rule('^\?(.*)')
def query_detection(bot, trigger):

    commands_list = dict()
    for commandstype in ['module_commands', 'nickname_commands']:
        for com in bot.memory['commandslist'][commandstype].keys():
            if com not in commands_list.keys():
                commands_list[com] = bot.memory['commandslist'][commandstype][com]

    triggerargsarray = spicemanip(bot, trigger, 'create')

    # command issued, check if valid
    querycommand = spicemanip(bot, triggerargsarray, 1).lower()[1:]
    if len(querycommand) == 1:
        commandlist = []
        for command in commands_list.keys():
            if command.lower().startswith(querycommand):
                commandlist.append(command)
        if commandlist == []:
            return bot.say("No commands match " + str(querycommand) + ".", trigger.nick)
        else:
            return bot.say("The following commands match " + str(querycommand) + ": " + spicemanip(bot, commandlist, 'andlist') + ".", trigger.nick)

    elif querycommand.endswith(tuple(["+"])):
        querycommand = querycommand[:-1]
        if querycommand not in commands_list.keys():
            return bot.say("The " + str(querycommand) + " does not appear to be valid.")
        realcom = querycommand
        if "aliasfor" in commands_list[querycommand].keys():
            realcom = commands_list[querycommand]["aliasfor"]
        validcomlist = commands_list[realcom]["validcoms"]
        return bot.say("The following commands match " + str(querycommand) + ": " + spicemanip(bot, validcomlist, 'andlist') + ".", trigger.nick)

    elif querycommand.endswith(tuple(['?'])):
        querycommand = querycommand[:-1]
        sim_com, sim_num = [], []
        for com in commands_list.keys():
            similarlevel = SequenceMatcher(None, querycommand.lower(), com.lower()).ratio()
            sim_com.append(com)
            sim_num.append(similarlevel)
        sim_num, sim_com = array_arrangesort(bot, sim_num, sim_com)
        closestmatch = spicemanip(bot, sim_com, 'reverse', "list")
        listnumb, relist = 1, []
        for item in closestmatch:
            if listnumb <= 10:
                relist.append(str(item))
            listnumb += 1
        return bot.say("The following commands may match " + str(querycommand) + ": " + spicemanip(bot, relist, 'andlist') + ".", trigger.nick)

    elif querycommand in commands_list.keys():
        return bot.say("The following commands match " + str(querycommand) + ": " + str(querycommand) + ".", trigger.nick)

    elif not querycommand:
        return

    else:
        commandlist = []
        for command in commands_list.keys():
            if command.lower().startswith(querycommand):
                commandlist.append(command)
        if commandlist == []:
            return bot.say("No commands match " + str(querycommand) + ".", trigger.nick)
        else:
            return bot.say("The following commands match " + str(querycommand) + ": " + spicemanip(bot, commandlist, 'andlist') + ".", trigger.nick)


"""
Array/List/String Manipulation
"""


# Hub
def spicemanip(bot, inputs, outputtask, output_type='default'):

    # TODO 'this*that' or '1*that' replace either all strings matching, or an index value
    # TODO reverse sort z.sort(reverse = True)
    # list.extend adds lists to eachother

    mainoutputtask, suboutputtask = None, None

    # Input needs to be a list, but don't split a word into letters
    if not inputs:
        inputs = []
    if not isinstance(inputs, list):
        inputs = list(inputs.split(" "))
        inputs = [x for x in inputs if x and x not in ['', ' ']]
        inputs = [inputspart.strip() for inputspart in inputs]

    # Create return
    if outputtask == 'create':
        return inputs

    # Make temparray to preserve original order
    temparray = []
    for inputpart in inputs:
        temparray.append(inputpart)
    inputs = temparray

    # Convert outputtask to standard
    if outputtask in [0, 'complete']:
        outputtask = 'string'
    elif outputtask == 'index':
        mainoutputtask = inputs[1]
        suboutputtask = inputs[2]
        inputs = inputs[0]
    elif str(outputtask).isdigit():
        mainoutputtask, outputtask = int(outputtask), 'number'
    elif "^" in str(outputtask):
        mainoutputtask = str(outputtask).split("^", 1)[0]
        suboutputtask = str(outputtask).split("^", 1)[1]
        outputtask = 'rangebetween'
        if int(suboutputtask) < int(mainoutputtask):
            mainoutputtask, suboutputtask = suboutputtask, mainoutputtask
    elif str(outputtask).startswith("split_"):
        mainoutputtask = str(outputtask).replace("split_", "")
        outputtask = 'split'
    elif str(outputtask).endswith(tuple(["!", "+", "-", "<", ">"])):
        mainoutputtask = str(outputtask)
        if str(outputtask).endswith("!"):
            outputtask = 'exclude'
        if str(outputtask).endswith("+"):
            outputtask = 'incrange_plus'
        if str(outputtask).endswith("-"):
            outputtask = 'incrange_minus'
        if str(outputtask).endswith(">"):
            outputtask = 'excrange_plus'
        if str(outputtask).endswith("<"):
            outputtask = 'excrange_minus'
        for r in (("!", ""), ("+", ""), ("-", ""), ("<", ""), (">", "")):
            mainoutputtask = mainoutputtask.replace(*r)
    if mainoutputtask == 'last':
        mainoutputtask = len(inputs)

    if outputtask == 'string':
        returnvalue = inputs
    else:
        returnvalue = eval('spicemanip_' + outputtask + '(bot, inputs, outputtask, mainoutputtask, suboutputtask)')

    # default return if not specified
    if output_type == 'default':
        if outputtask in [
                            'string', 'number', 'rangebetween', 'exclude', 'random',
                            'incrange_plus', 'incrange_minus', 'excrange_plus', 'excrange_minus'
                            ]:
            output_type = 'string'
        elif outputtask in ['count']:
            output_type = 'dict'

    # verify output is correct
    if output_type == 'return':
        return returnvalue
    if output_type == 'string':
        if isinstance(returnvalue, list):
            returnvalue = ' '.join(returnvalue)
    elif output_type in ['list', 'array']:
        if not isinstance(returnvalue, list):
            returnvalue = list(returnvalue.split(" "))
            returnvalue = [x for x in returnvalue if x and x not in ['', ' ']]
            returnvalue = [inputspart.strip() for inputspart in returnvalue]
    return returnvalue


# compare 2 lists, based on the location of an index item, passthrough needs to be [indexitem, arraytoindex, arraytocompare]
def spicemanip_index(bot, indexitem, outputtask, arraytoindex, arraytocompare):
    item = ''
    for x, y in zip(arraytoindex, arraytocompare):
        if x == indexitem:
            item = y
    return item


# split list by string
def spicemanip_split(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    split_array = []
    restring = ' '.join(inputs)
    if mainoutputtask not in inputs:
        split_array = [restring]
    else:
        split_array = restring.split(mainoutputtask)
    split_array = [x for x in split_array if x and x not in ['', ' ']]
    split_array = [inputspart.strip() for inputspart in split_array]
    if split_array == []:
        split_array = [[]]
    return split_array


# dedupe list
def spicemanip_dedupe(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    newlist = []
    for inputspart in inputs:
        if inputspart not in newlist:
            newlist.append(inputspart)
    return newlist


# Sort list
def spicemanip_sort(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    return sorted(inputs)


# reverse sort list
def spicemanip_rsort(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    return sorted(inputs)[::-1]


# count items in list, return dictionary
def spicemanip_count(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    returndict = dict()
    if inputs == []:
        return returndict
    uniqueinputitems, uniquecount = [], []
    for inputspart in inputs:
        if inputspart not in uniqueinputitems:
            uniqueinputitems.append(inputspart)
    for uniqueinputspart in uniqueinputitems:
        count = 0
        for ele in inputs:
            if (ele == uniqueinputspart):
                count += 1
        uniquecount.append(count)
    for inputsitem, unumber in zip(uniqueinputitems, uniquecount):
        returndict[inputsitem] = unumber
    return returndict


# random item from list
def spicemanip_random(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    randomselectlist = []
    for temppart in inputs:
        randomselectlist.append(temppart)
    while len(randomselectlist) > 1:
        random.shuffle(randomselectlist)
        randomselect = randomselectlist[random.randint(0, len(randomselectlist) - 1)]
        randomselectlist.remove(randomselect)
    randomselect = randomselectlist[0]
    return randomselect


# remove random item from list
def spicemanip_exrandom(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return []
    randremove = spicemanip_random(bot, inputs, outputtask, mainoutputtask, suboutputtask)
    inputs.remove(randremove)
    return inputs


# Convert list into lowercase
def spicemanip_lower(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    return [inputspart.lower() for inputspart in inputs]


# Convert list to uppercase
def spicemanip_upper(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    return [inputspart.upper() for inputspart in inputs]


# Convert list to uppercase
def spicemanip_title(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    return [inputspart.title() for inputspart in inputs]


# Reverse List Order
def spicemanip_reverse(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return []
    return inputs[::-1]


# comma seperated list
def spicemanip_list(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    return ', '.join(str(x) for x in inputs)


# comma seperated list with and
def spicemanip_andlist(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    if len(inputs) < 2:
        return ' '.join(inputs)
    lastentry = str("and " + str(inputs[len(inputs) - 1]))
    del inputs[-1]
    inputs.append(lastentry)
    if len(inputs) == 2:
        return ' '.join(inputs)
    return ', '.join(str(x) for x in inputs)


# comma seperated list with or
def spicemanip_orlist(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    if len(inputs) < 2:
        return ' '.join(inputs)
    lastentry = str("or " + str(inputs[len(inputs) - 1]))
    del inputs[-1]
    inputs.append(lastentry)
    if len(inputs) == 2:
        return ' '.join(inputs)
    return ', '.join(str(x) for x in inputs)


# exclude number
def spicemanip_exclude(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    del inputs[int(mainoutputtask) - 1]
    return ' '.join(inputs)


# Convert list to string
def spicemanip_string(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    return ' '.join(inputs)


# Get number item from list
def spicemanip_number(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    elif len(inputs) == 1:
        return inputs[0]
    elif int(mainoutputtask) > len(inputs) or int(mainoutputtask) < 0:
        return ''
    else:
        return inputs[int(mainoutputtask) - 1]


# Get Last item from list
def spicemanip_last(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    return inputs[len(inputs) - 1]


# range between items in list
def spicemanip_rangebetween(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    if not str(mainoutputtask).isdigit() or not str(suboutputtask).isdigit():
        return ''
    mainoutputtask, suboutputtask = int(mainoutputtask), int(suboutputtask)
    if suboutputtask == mainoutputtask:
        return spicemanip_number(bot, inputs, outputtask, mainoutputtask, suboutputtask)
    if suboutputtask < mainoutputtask:
        return []
    if mainoutputtask < 0:
        mainoutputtask = 1
    if suboutputtask > len(inputs):
        suboutputtask = len(inputs)
    newlist = []
    for i in range(mainoutputtask, suboutputtask + 1):
        newlist.append(str(spicemanip_number(bot, inputs, outputtask, i, suboutputtask)))
    if newlist == []:
        return ''
    return ' '.join(newlist)


# Forward Range includes index number
def spicemanip_incrange_plus(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    return spicemanip_rangebetween(bot, inputs, outputtask, int(mainoutputtask), len(inputs))


# Reverse Range includes index number
def spicemanip_incrange_minus(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    return spicemanip_rangebetween(bot, inputs, outputtask, 1, int(mainoutputtask))


# Forward Range excludes index number
def spicemanip_excrange_plus(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    return spicemanip_rangebetween(bot, inputs, outputtask, int(mainoutputtask) + 1, len(inputs))


# Reverse Range excludes index number
def spicemanip_excrange_minus(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    return spicemanip_rangebetween(bot, inputs, outputtask, 1, int(mainoutputtask) - 1)


def array_arrangesort(bot, sortbyarray, arrayb):
    sortbyarray, arrayb = (list(x) for x in zip(*sorted(zip(sortbyarray, arrayb), key=itemgetter(0))))
    return sortbyarray, arrayb
