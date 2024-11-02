r"""Setup"""
from setuptools import setup, Extension

version = None
with open("./VERSION", "r") as f:
    version = f.read().strip()

if __name__ == "__main__":

    setup(version=version)
