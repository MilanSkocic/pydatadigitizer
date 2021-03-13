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
      url='https://milanskocic.github.io/datadigitizer/index.html',
      download_url='https://github.com/MilanSkocic/datadigitizer/',
      packages=find_packages(),
      include_package_data=True,
      python_requires='>=3.6',
      install_requires=read('./requirements.txt').split('\n'),
      classifiers=["Development Status :: 5 - Production/Stable",
                   "Intended Audience :: Science/Research",
                   "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
                   "Programming Language :: Python",
                   "Programming Language :: Python :: 3 :: Only",
                   "Topic :: Scientific/Engineering",
                   "Operating System :: Microsoft :: Windows",
                   "Operating System :: POSIX :: Linux",
                   "Operating System :: MacOS"]
      )
