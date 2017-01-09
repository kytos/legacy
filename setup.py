"""Setup script.

Run "python3 setup --help-commands" to list all available commands and their
descriptions.
"""
import os
import sys
from subprocess import call

from pip.req import parse_requirements
from setuptools import Command, setup

from setuptools.command.install import install

if 'bdist_wheel' in sys.argv:
    raise RuntimeError("This setup.py does not support wheels")

if 'VIRTUAL_ENV' in os.environ:
    BASE_ENV = os.environ['VIRTUAL_ENV']
else:
    BASE_ENV = '/'


class Doctest(Command):
    """Run Sphinx doctest."""

    if sys.argv[-1] == 'test':
        print('Running examples in documentation')
        call('make doctest -C docs/', shell=True)


class Linter(Command):
    """Run several code linters."""

    description = 'Run many code linters. It may take a while'
    user_options = []

    def __init__(self, *args, **kwargs):
        """Define linters and a message about them."""
        super().__init__(*args, **kwargs)
        'pyflakes,isort,pycodestyle,pydocstyle,pylint,radon'.split(',')
        self.linters = ['pyflakes', 'isort', 'pycodestyle', 'pydocstyle',
                        'pylint', 'radon']
        self.extra_msg = 'It may take a while. For a faster version (and ' \
                         'less checks), run "quick_lint".'

    def initialize_options(self):
        """For now, options are ignored."""
        pass

    def finalize_options(self):
        """For now, options are ignored."""
        pass

    def run(self):
        """Run pylama and radon."""
        files = 'setup.py kytos'
        print('running pylama with {}. {}'.format(', '.join(self.linters),
                                                  self.extra_msg))
        cmd = 'pylama -l {} {}'.format(','.join(self.linters), files)
        call(cmd, shell=True)
        print('Low grades (<= C) for Maintainability Index:')
        call('radon mi --min=C ' + files, shell=True)


class FastLinter(Linter):
    """Same as Linter, but without the slow pylint."""

    description = 'Same as "lint", but much faster (no pylama_pylint).'

    def __init__(self, *args, **kwargs):
        """Remove slow linters and redefine the message about the rest."""
        super().__init__(*args, **kwargs)
        self.linters.remove('pylint')
        self.extra_msg = 'This a faster version of "lint", without pylint. ' \
                         'Run the slower "lint" after solving these issues:'


napps_path = os.path.join(BASE_ENV, 'var/lib/kytos/napps/')
installed_path = napps_path + '.installed/kytos/'
enabled_path = napps_path + 'kytos/'

class Installer(install):
    """Customized setuptools install command - prints a friendly greeting."""

    def run(self):
        """Create of_core as default napps enabled."""
        install.run(self)
        os.symlink(installed_path+'of_core', enabled_path+'of_core')
        open(napps_path+'__init__.py', 'w').close()
        open(enabled_path+'__init__.py', 'w').close()

def retrieve_apps(kytos_napps_path):
    """Retrieve the list of files within each app directory."""
    apps = []
    for napp_name in os.listdir("./kytos"):
        app_files = []
        app_path = os.path.join("./kytos", napp_name)
        for file_name in os.listdir(app_path):
            file_path = os.path.join(app_path, file_name)
            if os.path.isfile(file_path):  # Only select files
                app_files.append(file_path)
        apps.append((os.path.join(kytos_napps_path, napp_name), app_files))
    return apps

def napps_structures():
    directories = retrieve_apps(installed_path)
    directories.append((enabled_path,[]))
    return directories


# parse_requirements() returns generator of pip.req.InstallRequirement objects
requirements = parse_requirements('requirements.txt', session=False)


setup(name='kyco-core-napps',
      version='1.1.0b1.dev1',
      description='Core Napps developed by Kytos Team',
      url='http://github.com/kytos/kyco-core-napps',
      author='Kytos Team',
      author_email='of-ng-dev@ncc.unesp.br',
      license='MIT',
      install_requires=[str(ir.req) for ir in requirements],
      data_files=napps_structures(),
      cmdclass={
          'lint': Linter,
          'quick_lint': FastLinter,
          'install': Installer
      },
      zip_safe=False)
