import setuptools
from setuptools import setup


setup(
    name='clfd-pulsar',
    url='https://bitbucket.org/vmorello/clfd',
    author='Vincent Morello',
    author_email='vmorello@gmail.com',
    description='Smart RFI removal algorithms to be used on folded pulsar search and timing data',
    version='0.1',
    packages=setuptools.find_packages(),
    license='MIT License',
    long_description=open('README.md').read(),
)
