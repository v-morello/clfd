import os
import setuptools
from setuptools import setup

def parse_version():
    thisdir = os.path.dirname(__file__)
    version_file = os.path.join(thisdir, 'clfd', '_version.py')
    with open(version_file, 'r') as fobj:
        text = fobj.read()
    items = {}
    exec(text, None, items)
    return items['__version__']

version = parse_version()

setup(
    name='clfd-pulsar',
    url='https://github.com/v-morello/clfd',
    author='Vincent Morello',
    author_email='vmorello@gmail.com',
    description='Smart RFI removal algorithms to be used on folded pulsar search and timing data',
    version=version,
    packages=setuptools.find_packages(),
    install_requires=['numpy', 'pandas', 'tables'],
    license='MIT License',
)
