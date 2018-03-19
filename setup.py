"""Setup"""
# https://stackoverflow.com/questions/20288711/post-install-script-with-python-setuptools?rq=1
# https://stackoverflow.com/questions/17806485/execute-a-python-script-post-install-using-distutils-setuptools
# https://pymotw.com/2/site/#module-sitecustomize

import os
import sys
import site
from subprocess import call
from setuptools import setup
from setuptools.command.install import install as _install

def get_package_install_directory():
    """Return the installation directory, or None"""
    if '--user' in sys.argv:
        paths = (site.getusersitepackages(),)
    else:
        py_version = '%s.%s' % (sys.version_info[0], sys.version_info[1])
        paths = (s % (py_version) for s in (
            sys.prefix + '/lib/python%s/dist-packages/',
            sys.prefix + '/lib/python%s/site-packages/',
            sys.prefix + '/local/lib/python%s/dist-packages/',
            sys.prefix + '/local/lib/python%s/site-packages/',
            '/Library/Python/%s/site-packages/',
        ))
        paths = tuple(paths) + (
            # these paths likely work for anaconda install
            sys.prefix + '/lib/dist-packages/',
            sys.prefix + '/lib/site-packages/',
            sys.prefix + '/local/lib/dist-packages/',
            sys.prefix + '/local/lib/site-packages/',
        )

    for path in paths:
        if os.path.exists(path):
            print("++++++++path exists", path)
            install_path = path + 'chi'# build path to file 
            site.addsitedir(install_path) # add the installation dir to path. my main aim
            return path
    print('no installation path found', file=sys.stderr)
    return None

def _post_install(dir):
    get_package_install_directory()

class install(_install):
    def run(self):
        _install.run(self)
        self.execute(_post_install, (self.install_lib,),
                     msg="Running post install task")

def readme():
    """Readme"""
    with open("README.md") as rhand:
        return rhand.read()

setup(name='PyGit',
      version='3.0',
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
      test_suite='nose2.collector.collector',)

setup(
    cmdclass={'install': install},
)
