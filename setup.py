from setuptools import setup, find_packages

from afscripting import __version__

setup(
    name='afscripting',
    version=__version__,
    license='GPLv3+',
    author='Joel Dubowy',
    author_email='jdubowy@gmail.com',
    packages=find_packages(),
    scripts=[],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3.12",
        "Operating System :: POSIX",
        "Operating System :: MacOS"
    ],
    url='https://github.com/pnwairfire/afscripting',
    description='Scripting related utilities',
    install_requires=[
        "afconfig>=1.0.0,<2.0.0",
        "afdatetime>=3.0.0,<4.0.0"
    ],
    dependency_links=[
        "https://pypi.airfire.org/simple/afconfig/",
        "https://pypi.airfire.org/simple/afdatetime/"
    ]
)
