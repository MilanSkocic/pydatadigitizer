import os
import importlib.util
from setuptools import setup, find_packages

# local import of version.py file
spec = importlib.util.spec_from_file_location('version', './datadigitizer/version.py')
version = importlib.util.module_from_spec(spec)
spec.loader.exec_module(version)


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname), 'r', encoding='utf-8').read()


setup(name=version.__package_name__,
      version=version.__version__,
      maintainer=version.__maintainer__,
      maintainer_email=version.__maintainer_email__,
      author=version.__author__,
      author_email=version.__author_email__,
      description=version.__package_name__,
      long_description=read('README.rst'),
      url='https://github.com/MilanSkocic/datadigitizer',
      download_url='https://github.com/MilanSkocic/datadigitizer',
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
