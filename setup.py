r"""
Copyright (C) 2020-2021 Milan Skocic.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Author: Milan Skocic <milan.skocic@gmail.com>
"""
import os
from setuptools import setup, find_packages
import datadigitizer


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname), 'r', encoding='utf-8').read()


setup(name=datadigitizer.__package_name__,
      version=datadigitizer.__version__,
      maintainer=datadigitizer.__maintainer__,
      maintainer_email=datadigitizer.__maintainer_email__,
      author=datadigitizer.__author__,
      author_email=datadigitizer.__author_email__,
      description=datadigitizer.__package_name__,
      long_description=read('README.rst'),
      url='https://milanskocic.github.io/PyDatadigitizer/index.html',
      download_url='https://github.com/MilanSkocic/PyDatadigitizer/',
      packages=find_packages(),
      include_package_data=True,
      python_requires='>=3.6',
      install_requires=read('./requirements.txt').split('\n'),
      classifiers=["Development Status :: 5 - Production/Stable",
                   "Intended Audience :: Science/Research",
                   "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
                   "Programming Language :: Python",
                   "Programming Language :: Python :: 3 :: Only",
                   "Programming Language :: Python :: 3.6",
                   "Programming Language :: Python :: 3.7",
                   "Programming Language :: Python :: 3.8",
                   "Programming Language :: Python :: 3.9",
                   "Topic :: Scientific/Engineering",
                   "Operating System :: OS Independent"]
      )
