import setuptools
from setuptools import setup


setup(
    name='clfd-pulsar',
    url='https://github.com/v-morello/clfd',
    author='Vincent Morello',
    author_email='vmorello@gmail.com',
    description='Smart RFI removal algorithms to be used on folded pulsar search and timing data',
    version='0.1.0',
    packages=setuptools.find_packages(),
    install_requires=['numpy','pandas'],
    license='MIT License',
)
