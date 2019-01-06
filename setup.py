"""Setup"""

import os
import sys
import site

from pathlib import Path
from subprocess import call
from setuptools import setup

def readme():
    """Readme"""
    with open("README.md") as rhand:
        return rhand.read()


setup(name='python-git',
      version='2018.01.31',
      description='Automate boring git tasks',
      long_description=readme(),
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Programming Language :: Python :: 3.6',
          'License :: OSI Approved :: MIT License',
          'Intended Audience :: Developers',
          'Natural Language :: English',
          'Operating System :: POSIX :: Linux',
          'Operating System :: Microsoft :: Windows :: Windows 10',
          'Topic :: Software Development :: Version Control :: Git',
          'Topic :: Utilities',
      ],
      keywords='automate boring git and github tasks',
      url='https://github.com/chidimo/python-git',
      download_url='https://github.com/chidimo/python-git/archive/master.zip',
      author='Chidi Orji',
      author_email='orjichidi95@gmail.com',
      license='MIT',
      packages=['pygit'],
      install_requires=[
          'send2trash'
      ],
      zip_safe=False,)
