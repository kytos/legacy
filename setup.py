"""Setup script.

Run "python3 setup --help-commands" to list all available commands and their
descriptions.
"""
import os
import sys
from pathlib import Path
from subprocess import CalledProcessError, check_call

from pip.req import parse_requirements
from setuptools import Command, setup
from setuptools.command.develop import develop
from setuptools.command.install import install
from setuptools.command.test import test as TestCommand

if 'bdist_wheel' in sys.argv:
    raise RuntimeError("This setup.py does not support wheels")

# Paths setup with virtualenv detection
if 'VIRTUAL_ENV' in os.environ:
    BASE_ENV = Path(os.environ['VIRTUAL_ENV'])
else:
    BASE_ENV = Path('/')
# Kytos var folder
VAR_PATH = BASE_ENV / 'var' / 'lib' / 'kytos'
# Path for enabled NApps
ENABL_PATH = VAR_PATH / 'napps'
# Path to install NApps
INSTL_PATH = VAR_PATH / 'napps' / '.installed'
CURR_DIR = Path('.').resolve()

# NApps enabled by default
CORE_NAPPS = ['of_core']


class Linter(Command):
    """Code linters."""

    description = 'run Pylama on Python files'
    user_options = []

    def run(self):
        """Run linter."""
        self.lint()

    @staticmethod
    def lint():
        """Run pylama and radon."""
        files = 'tests setup.py napps'
        print('Pylama is running. It may take several seconds...')
        cmd = 'pylama {}'.format(files)
        try:
            check_call(cmd, shell=True)
        except CalledProcessError as e:
            print('FAILED: please, fix the linter error(s) above.')
            sys.exit(e.returncode)

    def initialize_options(self):
        """Abstract method not used."""
        pass

    def finalize_options(self):
        """Abstract method not used."""
        pass


class Test(TestCommand):
    """Run doctest and linter besides tests/*."""

    def run(self):
        """First, tests/*."""
        super().run()
        Linter.lint()
        self.run_doctest()

    @staticmethod
    def run_doctest():
        """Run Sphinx doctests."""
        print('Running examples in documentation')
        try:
            check_call('make doctest -C docs/', shell=True)
        except CalledProcessError as e:
            print("FAILED: please, fix the doc's error(s) above.")
            sys.exit(e.returncode)


class KytosInstall:
    """Common code for all install types."""

    @staticmethod
    def enable_core_napps():
        """Enable a NAPP by creating a symlink."""
        (ENABL_PATH / 'kytos').mkdir(parents=True, exist_ok=True)
        for napp in CORE_NAPPS:
            napp_path = Path('kytos', napp)
            src = ENABL_PATH / napp_path
            dst = INSTL_PATH / napp_path
            src.symlink_to(dst)


class InstallMode(install):
    """Create files in var/lib/kytos."""

    def run(self):
        """Create of_core as default napps enabled."""
        super().run()
        # Enable essential NApps
        KytosInstall.enable_core_napps()

    @classmethod
    def get_data_files(cls, path):
        """Get all files below `path`."""
        src = [str(x) for x in path.iterdir() if x.is_file()]
        if src:
            if path.parts[:2] == ('napps', 'kytos'):
                # Installion dir doesn't have "napps" module
                dst = INSTL_PATH / Path(*path.parts[1:])
                yield (str(dst), src)
            else:  # e.g. napps/__init__.py
                dst = VAR_PATH / path
            yield (str(dst), src)

        for data_files in cls.recurse_dirs(path):
            yield data_files

    @classmethod
    def recurse_dirs(cls, path):
        """Get files from all subfolders."""
        for d in path.iterdir():
            if d.is_dir() and d.parts[-1] != '__pycache__':
                for data_files in cls.get_data_files(d):
                    yield data_files


class DevelopMode(develop):
    """Recommended setup for kytos-core-napps developers.

    Instead of copying the files to the expected directories, a symlink is
    created on the system aiming the current source code.
    """

    def run(self):
        """Install the package in a developer mode."""
        super().run()
        self._create_kytos_symlinks()
        self._create_napps_symlinks()
        KytosInstall.enable_core_napps()

    @staticmethod
    def _create_kytos_symlinks():
        """Symlink to all kytos napps.

        ./napps/kytos/napp_name will generate a link in
        var/lib/kytos/napps/.installed/kytos/napp_name.
        """
        links = INSTL_PATH / 'kytos'
        links.mkdir(parents=True, exist_ok=True)
        code = CURR_DIR / 'napps' / 'kytos'
        for path in code.iterdir():
            last_folder = path.parts[-1]
            if path.is_dir() and last_folder != '__pycache__':
                src = links / last_folder
                src.symlink_to(path)

    @staticmethod
    def _create_napps_symlinks():
        """Symlink to files of napps folder.

        We cannot only symlink the napps folder because there should be a
        var/lib/kytos/napps/.installed folder.
        """
        src = ENABL_PATH / '__init__.py'
        dst = CURR_DIR / 'napps' / '__init__.py'
        src.symlink_to(dst)


# parse_requirements() returns generator of pip.req.InstallRequirement objects
requirements = parse_requirements('requirements.txt', session=False)

setup(name='kytos-napps',
      version='1.1.0b1.dev1',
      description='Core Napps developed by Kytos Team',
      url='http://github.com/kytos/kytos-napps',
      author='Kytos Team',
      author_email='of-ng-dev@ncc.unesp.br',
      license='MIT',
      install_requires=[str(ir.req) for ir in requirements],
      # data_files are not copied in DevelopMode
      data_files=list(InstallMode.get_data_files(Path('napps'))),
      cmdclass={
          'develop': DevelopMode,
          'install': InstallMode,
          'lint': Linter,
          'test': Test
      },
      zip_safe=False)
