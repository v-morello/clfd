# type: ignore

import pathlib
import versioneer

from setuptools import setup, find_packages


here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")
install_requires = [
    "rich",
    "numpy",
    "scipy",
    "priwo",
    "click",
    "pandas",
    "matplotlib",
]


setup(
    name="clfd",
    version=versioneer.get_version(),
    description="Smart RFI removal algorithms to be used on folded pulsar search and timing data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/v-morello/clfd",
    author="Vincent Morello",
    author_email="vmorello@gmail.com",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Scientific/Engineering :: Astronomy",
    ],
    keywords=(
        "RFI",
        "pulsars",
        "astronomy",
        "RFI mitigation",
        "radio astronomy",
        "data processing",
    ),
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_package_data=True,
    python_requires=">3.5, <4",
    install_requires=install_requires,
    project_urls={
        "Source": "https://github.com/v-morello/clfd",
        "Bug Reports": "https://github.com/v-morello/clfd/issues",
    },
    cmd_class=versioneer.get_cmdclass(),
    zip_safe=False,
)