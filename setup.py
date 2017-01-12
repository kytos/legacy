"""Setup script.

Run "python3 setup --help-commands" to list all available commands and their
descriptions.
"""
import os
import sys
from os import listdir
from os.path import isdir, isfile, join
from subprocess import call

from pip.req import parse_requirements
from setuptools import Command, setup
from setuptools.command.develop import develop
from setuptools.command.install import install

if 'bdist_wheel' in sys.argv:
    raise RuntimeError("This setup.py does not support wheels")

if 'VIRTUAL_ENV' in os.environ:
    BASE_ENV = os.environ['VIRTUAL_ENV']
else:
    BASE_ENV = '/'

NAPPS_PATHS = {
    'main': join(BASE_ENV, 'var/lib/kytos/napps')
}
NAPPS_PATHS['installed'] = join(NAPPS_PATHS.get('main'), '.installed')
NAPPS_PATHS['enabled'] = join(NAPPS_PATHS.get('main'), 'kytos')
CORE_NAPPS = ['of_core']


def enable_core_napps():
    """Enable a NAPP by creating a symlink."""
    for napp in CORE_NAPPS:
        src = join(NAPPS_PATHS.get('installed'), 'kytos', napp)
        dst = join(NAPPS_PATHS.get('enabled'), napp)
        os.symlink(src, dst)

    # Create the __init__.py file for the 'napps' directory and also the
    # 'napps/kytos' directory
    open(NAPPS_PATHS.get('main')+'/__init__.py', 'w').close()
    open(NAPPS_PATHS.get('enabled')+'/__init__.py', 'w').close()


def create_napps_base_folders():
    for directory in NAPPS_PATHS:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)


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


class InstallMode(install):
    """Customized setuptools install command - prints a friendly greeting."""

    def run(self):
        """Create of_core as default napps enabled."""
        create_napps_base_folders()
        install.run(self)

        # Enable each defined 'CORE_NAPP'
        enable_core_napps()


class DevelopMode(develop):
    """Customized setuptools develop command - prints a friendly greeting."""

    def run(self):
        """Install the package in a developer mode.

        Instead of copying the files to the expected directories, a symlink is
        created on the system aiming the current source code.
        """
        create_napps_base_folders()
        develop.run(self)
        origin_path = os.path.dirname(os.path.realpath(__file__))

        os.makedirs(NAPPS_PATHS.get('enabled'))
        os.makedirs(NAPPS_PATHS.get('installed'))
        src = join(origin_path, 'kytos')
        dst = join(NAPPS_PATHS.get('installed'), 'kytos')
        os.symlink(src, dst)

        # Enable each defined 'CORE_NAPP'
        enable_core_napps()


def retrieve_apps(kytos_napps_path):
    """Retrieve the list of files within each app directory."""
    apps = []
    parent = "./kytos"
    napp_names = (f for f in listdir(parent) if isdir(join(parent, f)))
    for napp_name in napp_names:
        app_files = []
        app_path = join(parent, napp_name)
        for file_name in listdir(app_path):
            file_path = join(app_path, file_name)
            if isfile(file_path):  # Only select files
                app_files.append(file_path)
        apps.append((join(kytos_napps_path, napp_name), app_files))
    return apps


def napps_structures():
    directories = retrieve_apps(NAPPS_PATHS.get('installed')+'/kytos')
    directories.append((NAPPS_PATHS.get('enabled'), []))
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
          'install': InstallMode,
          'develop': DevelopMode
      },
      zip_safe=False)
