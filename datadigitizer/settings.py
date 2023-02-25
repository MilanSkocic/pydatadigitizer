r"""
Settings module.
"""
import os
import configparser
import re
from typing import Dict
from . import version


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
                    _s = re.findall(r"\d{0,9}e.\d{0,9}", i)
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


def save_cfg():
    r"""
    Save the configuration file.
    """
    fpath = os.path.abspath(CFG_PATH)
    with open(fpath, 'w') as fobj:
        cfg.write(fobj)


APP_NAME = version.__package_name__.replace(' ', '').lower()
CFG_FOLDER = os.path.abspath(os.path.expanduser('~') + '/' + '.' + APP_NAME + '/')
CFG_NAME = APP_NAME + ".ini"
CFG_PATH = os.path.abspath(CFG_FOLDER + "/" + CFG_NAME)

if not os.path.exists(CFG_FOLDER):
    os.mkdir(CFG_FOLDER)

folder_settings = {'image folder': os.path.expanduser('~'),
                  'image name': '',
                  'data folder': os.path.expanduser('~'),
                  'data name': ''}
cfg_dict = dict(FOLDERS=folder_settings)
cfg = configparser.ConfigParser(converters={'_typed_option': _typed_option})
cfg.update(cfg_dict)

if not os.path.exists(CFG_PATH):
    save_cfg()
else:
    user_cfg = configparser.ConfigParser(converters={'_typed_option': _typed_option})
    user_cfg.read(CFG_PATH)
    cfg.update(user_cfg)
