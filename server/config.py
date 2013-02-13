'''
File: config.py
Author: Damien Riquet <d.riquet@gmail.com>
Description: This file defines a function that reads a configuration file
             In this configuration file, there is all data related to a game
'''

# imports
from ConfigParser import SafeConfigParser
from os.path import isfile

# exceptions
class ConfigException(Exception):
    pass


def load_config(filename):
    """
    Loads the configuration file
    Verify that the file exists and that data from the config file is valid

    @param filename: name of the file to load
    @raise ConfigException: if the file does not exist or the config file is not valid
    """
    if not isfile(filename):
        raise ConfigException("Config file '%s' does not exist / is not a file", filename)

    config = SafeConfigParser()
    config.read(filename)

    if not config.has_section('initial'):
        raise ConfigException("No 'initial' section in to the config file '%s'", filename)

    options = [ 'timing_limit', 'turn_max', 'move_len', 'view_radius', 'bullet_amount', 'shot_radius', 'shot_success',
                'attack_radius', 'contagion_amount', 'contagion_radius', 'berzerk_delay', 'berzerk_radius', ]

    for option in options:
        if not config.has_option('initial', option):
            raise ConfigException("Mission option '%s' into the config file '%s'", option, filename)

    return config

