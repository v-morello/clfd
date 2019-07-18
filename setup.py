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

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='clfd',
    url='https://github.com/v-morello/clfd',
    author='Vincent Morello',
    author_email='vmorello@gmail.com',
    description='Smart RFI removal algorithms to be used on folded pulsar search and timing data',
    long_description=long_description,
    long_description_content_type='text/markdown',
    version=version,
    packages=setuptools.find_packages(),
    install_requires=[
        'numpy', 
        'pandas', 
        'tables'
        ],
    license='MIT License',

    entry_points = {
        'console_scripts': ['clfd=clfd.apps.cleanup:main'],
    },

    # NOTE (IMPORTANT): This means that everything mentioned in MANIFEST.in 
    # will be copied at install time to the package's folder placed in 
    # 'site-packages'. That way we include the test data files. 
    include_package_data=True,

    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
        "Topic :: Scientific/Engineering :: Astronomy"
        ],
)
