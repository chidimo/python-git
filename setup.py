"""Setup"""
# https://stackoverflow.com/questions/20288711/post-install-script-with-python-setuptools?rq=1
# https://stackoverflow.com/questions/17806485/execute-a-python-script-post-install-using-distutils-setuptools
# https://pymotw.com/2/site/#module-sitecustomize
# https://stackoverflow.com/questions/136097/what-is-the-difference-between-staticmethod-and-classmethod-in-python?rq=1
# https://www.programcreek.com/python/example/54257/site.USER_BASE

import os
import sys
import site
from subprocess import call
from setuptools import setup
from setuptools.command.install import install as _install

# def get_site_packages_directory():
#     """Returns site packages directory"""
#     # try iterating over sys.path
#     try:
#         return next(p for p in sys.path if 'site-packages' in p)
#     except StopIteration:
#         pass

#     # try manually constructing the path and check if it exists
#     py_version = '{}.{}'.format(sys.version_info[0], sys.version_info[1])

#     prefix_paths = [
#         sys.prefix + '/lib/python{}/dist-packages/',
#         sys.prefix + '/lib/python{}/site-packages/',
#         sys.prefix + '/local/lib/python{}/dist-packages/',
#         sys.prefix + '/local/lib/python{}/site-packages/',
#         '/Library/Python/{}/site-packages/',
#     ]

#     py_installation_paths = [each.format(py_version) for each in prefix_paths]
#     paths = py_installation_paths + [
#         # these paths for versionless installs like jupyter
#         sys.prefix + '/lib/dist-packages/',
#         sys.prefix + '/lib/site-packages/',
#         sys.prefix + '/local/lib/dist-packages/',
#         sys.prefix + '/local/lib/site-packages/',
#     ]
#     for path in paths:
#         if os.path.exists(path):
#             return path
#     return None

# def add_initialize_directory_to_system_path(install_directory):
#     """Adds the initialize.py file to path"""
#     if os.path.exists(install_directory):
#         program_directory = '{}/pygit-3.0-py3.6.egg/pygit'.format(install_directory)
#         print('\n\nTo initialize pygit, please run')
#         print('\t', program_directory + '/initialize.py')
#         print('with the appropriate command line arguments\n\n')
#     else:
#         print('Program directory, ', install_directory, ' is missing')
#     return

# def _post_install(dir):
#     install_dir = get_site_packages_directory()
#     add_initialize_directory_to_system_path(install_dir)

# class install(_install):
#     def run(self):
#         print("USING CUSTOM INSTALLL")
#         _install.run(self)
#         self.execute(_post_install, (self.install_lib,),
#                      msg="Running post install task")

def readme():
    """Readme"""
    with open("README.md") as rhand:
        return rhand.read()

setup(name='pygit',
      version='3.0',
      description='Automate common git tasks',
      long_description=readme(),
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Programming Language :: Python :: 3.6',
          'Topic :: Git :: Automation',
          'License :: OSI Approved :: MIT License',
          'Natural Language :: English',
          'Operating System :: POSIX :: Linux',
          'Operating System :: Microsoft :: Windows :: Windows 10',
          'Topic :: Software Development :: Version Control :: Git',
          'Topic :: Utilities',
      ],
      keywords='automate boring git and github tasks',
      url='https://github.com/immensity/pygit',
      download_url='https://github.com/immensity/pygit/archive/3.0.tar.gz',
      author='Chidi Orji',
      author_email='orjichidi95@gmail.com',
      license='MIT',
      packages=['pygit'],
      install_requires=[
          'send2trash'
      ],
      zip_safe=False,
      test_suite='nose2.collector.collector',)

# setup(
#     cmdclass={'install': install},
# )
