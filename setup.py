import os
import importlib.util
from setuptools import setup, find_packages

# local import of version.py file
spec = importlib.util.spec_from_file_location('version', './datadigitizer/version.py')
version = importlib.util.module_from_spec(spec)
spec.loader.exec_module(version)


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname),'r', encoding='utf-8').read()


def get_python():
    py_version = ''
    try:
        requirements = read('./REQUIREMENTS.txt').split('\n')
        for package in requirements:
            if package.startswith('python'):
                py_version = package.split('python')[1]
    except FileNotFoundError:
        py_version = ''

    return py_version


def get_dependencies():

    dependencies = list()
    try:
        requirements = read('./REQUIREMENTS.txt').split('\n')
        for package in requirements:
            if not package.startswith('python'):
                dependencies.append(package)
    except FileNotFoundError:
        dependencies = list()
    return dependencies


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
      python_requires=get_python(),
      install_requires=get_dependencies(),
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
