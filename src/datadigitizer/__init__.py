r"""
Initialization.
"""
import argparse
from .version import *
from datadigitizer.gui import App, tk

def cli():

    p = argparse.ArgumentParser(description="Digitize graphs.", prog="datadigitizer_cli")
    p.add_argument("-g", "--gui", action="store_true", required=False, help="Run GUI.")

    args = p.parse_args()

    if args.gui:
        application()


def application():
    root = tk.Tk()
    app = App(master=root)
    app.run()
