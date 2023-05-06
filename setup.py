r"""
Setup
"""
from pathlib import Path
from setuptools import setup, find_packages
import datadigitizer


setup(name=datadigitizer.__package_name__,
      version=datadigitizer.__version__,
      maintainer=datadigitizer.__maintainer__,
      maintainer_email=datadigitizer.__maintainer_email__,
      author=datadigitizer.__author__,
      author_email=datadigitizer.__author_email__,
      description=datadigitizer.__package_name__,
      long_description=Path('README.rst').read_text(encoding="utf-8"),
      url='https://milanskocic.github.io/PyDatadigitizer/index.html',
      download_url='https://github.com/MilanSkocic/PyDatadigitizer/',
      packages=find_packages(),
      include_package_data=True,
      python_requires='>=3.7',
      install_requires=Path('requirements.txt').read_text(encoding="utf-8").split('\n'),
      classifiers=["Development Status :: 5 - Production/Stable",
                   "Intended Audience :: Science/Research",
                   "License :: OSI Approved :: GNU General Public License v3 (GPLv3)"])
