import os
import configparser
import re
from . import version

APP_NAME = version.__package_name__.replace(' ', '').lower()
CFG_FOLDER = os.path.abspath(os.path.expanduser('~') + '/' + '.' + APP_NAME + '/')

if not os.path.exists(CFG_FOLDER):
    os.mkdir(CFG_FOLDER)

# default profiles
DEFAULT_PROFILE_VALUES = {}

# folders profile - each section is a profile for the profile type folders
name = 'folders'
default_values = {'image folder': os.path.expanduser('~')}
default_folders_profile_ini = dict(DEFAULT=default_values,
                                   LAST=default_values)

# map default values to each profile_type
DEFAULT_PROFILE_VALUES.update({name: default_folders_profile_ini})

# map all profile types to the desired profile (section): dict(profile_type=profile_name)
# profiles.ini configuration file has only a DEFAULT section where the profile types are mapped to the profile names
# Each profile_type correspond to a file profile_type.ini
mappping_profiles = dict(folders='LAST')
DEFAULT_PROFILE_TYPES = dict(DEFAULT=mappping_profiles)


def _typed_option(s):
    r"""
    Parse data from config file

    Parameters
    -----------
    s: str
        Value of the config value.

    Returns
    --------
    typed_elements: int/float or str or iterable
    """

    if isinstance(s, str):
        str_elements = s.replace(' ', '')
        str_elements = str_elements.replace('(', '').replace(')', '')
        str_elements = str_elements.replace('\'', '').replace('"', '')
        str_elements = str_elements.replace('[', '').replace(']', '')
        str_elements = str_elements.replace('{', '').replace('}', '')
        str_elements = str_elements.split(',')

        typed_elements = []

        for i in str_elements:
            try:
                if '.' in i:
                    new_element = float(i)
                else:
                    _s = re.findall("\d{0,9}e.\d{0,9}", i)
                    if len(_s) > 0:
                        new_element = float(i)
                    else:
                        new_element = int(i)

            except ValueError:
                if i.lower() == 'true':
                    new_element = True
                elif i.lower() == 'false':
                    new_element = False
                else:
                    new_element = str(i)

            typed_elements.append(new_element)

        if len(typed_elements) == 1:
            return typed_elements[0]
        else:
            return tuple(typed_elements)
    else:
        return s


def read_cfg(cfg_folder, cfg_name, cfg_default, update=True):
    if not os.path.exists(cfg_folder):
        os.mkdir(cfg_folder)

    _cfg = configparser.ConfigParser(converters={'_typed_option': _typed_option})
    _cfg.read_dict(cfg_default)

    cfg = configparser.ConfigParser(converters={'_typed_option': _typed_option})

    fpath = os.path.abspath(cfg_folder + '/' + cfg_name + '.ini')

    if not os.path.exists(fpath):
        save_cfg(cfg_folder, cfg_name, _cfg)
        cfg.update(_cfg)
    else:
        cfg.read(fpath)

    if update:
        cfg.defaults().update(_cfg.defaults())
        with open(fpath, 'w') as fobj:
            cfg.write(fobj)

    return cfg


def save_cfg(cfg_folder, cfg_name, cfg):
    fpath = os.path.abspath(cfg_folder + '/' + cfg_name + '.ini')
    with open(fpath, 'w') as fobj:
        cfg.write(fobj)


def read_profiles():
    return read_cfg(CFG_FOLDER, 'profiles', DEFAULT_PROFILE_TYPES, update=False)