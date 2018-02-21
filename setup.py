"""Setup"""

from setuptools import setup

def readme():
    """Readme"""
    with open("README.rst") as rhand:
        return rhand.read()

setup(name='PyGit',
      version='2.1',
      description='Automate common git tasks',
      long_description=readme(),
      classifiers=[
          'Developement Status :: 3 - Alpha',
          'Programming Language :: Python :: 3.6.1',
          'Topic :: Git :: Automation',
      ],
      keywords='git and github task automation',
      url='',
      author='Chidi Orji',
      author_email='orjichidi95@gmail.com',
      license='MIT',
      packages=['pygit'],
      install_requires=[
          'send2trash'
      ],
      zip_safe=False,
      test_suite='nose2.collector.collector',
      test_requires=["nose2"])
