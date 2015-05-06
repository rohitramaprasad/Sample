#!/usr/bin/env python

import os
import re
import shutil
import subprocess
import sys
import stat

from lib.config import LIBCHROMIUMCONTENT_COMMIT, BASE_URL, PLATFORM, \
                       get_target_arch
from lib.util import scoped_cwd, rm_rf, get_atom_shell_version, make_zip, \
                     execute, get_chromedriver_version, atom_gyp


ATOM_SHELL_VERSION = get_atom_shell_version()

SOURCE_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DIST_DIR = os.path.join(SOURCE_ROOT, 'dist')
OUT_DIR = os.path.join(SOURCE_ROOT, 'out', 'R')
CHROMIUM_DIR = os.path.join(SOURCE_ROOT, 'vendor', 'brightray', 'vendor',
                            'download', 'libchromiumcontent', 'static_library')

PROJECT_NAME = atom_gyp()['project_name%']
PRODUCT_NAME = atom_gyp()['product_name%']

TARGET_BINARIES = {
  'darwin': [
  ],
  'win32': [
    '{0}.exe'.format(PROJECT_NAME),  # 'electron.exe'
    'content_shell.pak',
    'd3dcompiler_47.dll',
    'ffmpegsumo.dll',
    'icudtl.dat',
    'libEGL.dll',
    'libGLESv2.dll',
    'node.dll',
    'content_resources_200_percent.pak',
    'ui_resources_200_percent.pak',
    'xinput1_3.dll',
    'natives_blob.bin',
    'snapshot_blob.bin',
  ],
  'linux': [
    PROJECT_NAME,  # 'electron'
    'content_shell.pak',
    'icudtl.dat',
    'libffmpegsumo.so',
    'libnode.so',
    'natives_blob.bin',
    'snapshot_blob.bin',
  ],
}
TARGET_DIRECTORIES = {
  'darwin': [
    '{0}.app'.format(PRODUCT_NAME),
  ],
  'win32': [
    'resources',
    'locales',
  ],
  'linux': [
    'resources',
    'locales',
  ],
}

SYSTEM_LIBRARIES = [
  'libgcrypt.so',
  'libnotify.so',
]


def main():
  rm_rf(DIST_DIR)
  os.makedirs(DIST_DIR)

  force_build()
  create_symbols()
  copy_binaries()
  copy_chromedriver()
  copy_license()

  if PLATFORM == 'linux':
    strip_binaries()
    copy_system_libraries()

  create_version()
  create_dist_zip()
  create_chromedriver_zip()
  create_symbols_zip()


def force_build():
  build = os.path.join(SOURCE_ROOT, 'script', 'build.py')
  execute([sys.executable, build, '-c', 'Release'])


def copy_binaries():
  for binary in TARGET_BINARIES[PLATFORM]:
    shutil.copy2(os.path.join(OUT_DIR, binary), DIST_DIR)

  for directory in TARGET_DIRECTORIES[PLATFORM]:
    shutil.copytree(os.path.join(OUT_DIR, directory),
                    os.path.join(DIST_DIR, directory),
                    symlinks=True)


def copy_chromedriver():
  if PLATFORM == 'win32':
    chromedriver = 'chromedriver.exe'
  else:
    chromedriver = 'chromedriver'
  src = os.path.join(CHROMIUM_DIR, chromedriver)
  dest = os.path.join(DIST_DIR, chromedriver)

  # Copy file and keep the executable bit.
  shutil.copyfile(src, dest)
  os.chmod(dest, os.stat(dest).st_mode | stat.S_IEXEC)


def copy_license():
  shutil.copy2(os.path.join(SOURCE_ROOT, 'LICENSE'), DIST_DIR)


def strip_binaries():
  for binary in TARGET_BINARIES[PLATFORM]:
    if binary.endswith('.so') or '.' not in binary:
      execute(['strip', os.path.join(DIST_DIR, binary)])


def copy_system_libraries():
  executable_path = os.path.join(OUT_DIR, PROJECT_NAME)  # our/R/electron
  ldd = execute(['ldd', executable_path])
  lib_re = re.compile('\t(.*) => (.+) \(.*\)$')
  for line in ldd.splitlines():
    m = lib_re.match(line)
    if not m:
      continue
    for i, library in enumerate(SYSTEM_LIBRARIES):
      real_library = m.group(1)
      if real_library.startswith(library):
        shutil.copyfile(m.group(2), os.path.join(DIST_DIR, real_library))
        SYSTEM_LIBRARIES[i] = real_library


def create_version():
  version_path = os.path.join(SOURCE_ROOT, 'dist', 'version')
  with open(version_path, 'w') as version_file:
    version_file.write(ATOM_SHELL_VERSION)


def create_symbols():
  destination = os.path.join(DIST_DIR, '{0}.breakpad.syms'.format(PROJECT_NAME))
  dump_symbols = os.path.join(SOURCE_ROOT, 'script', 'dump-symbols.py')
  execute([sys.executable, dump_symbols, destination])


def create_dist_zip():
  dist_name = '{0}-{1}-{2}-{3}.zip'.format(PROJECT_NAME, ATOM_SHELL_VERSION,
                                           PLATFORM, get_target_arch())
  zip_file = os.path.join(SOURCE_ROOT, 'dist', dist_name)

  with scoped_cwd(DIST_DIR):
    files = TARGET_BINARIES[PLATFORM] +  ['LICENSE', 'version']
    if PLATFORM == 'linux':
      files += [lib for lib in SYSTEM_LIBRARIES if os.path.exists(lib)]
    dirs = TARGET_DIRECTORIES[PLATFORM]
    make_zip(zip_file, files, dirs)


def create_chromedriver_zip():
  dist_name = 'chromedriver-{0}-{1}-{2}.zip'.format(get_chromedriver_version(),
                                                    PLATFORM, get_target_arch())
  zip_file = os.path.join(SOURCE_ROOT, 'dist', dist_name)

  with scoped_cwd(DIST_DIR):
    files = ['LICENSE']
    if PLATFORM == 'win32':
      files += ['chromedriver.exe']
    else:
      files += ['chromedriver']
    make_zip(zip_file, files, [])


def create_symbols_zip():
  dist_name = '{0}-{1}-{2}-{3}-symbols.zip'.format(PROJECT_NAME,
                                                   ATOM_SHELL_VERSION,
                                                   PLATFORM,
                                                   get_target_arch())
  zip_file = os.path.join(SOURCE_ROOT, 'dist', dist_name)

  with scoped_cwd(DIST_DIR):
    files = ['LICENSE', 'version']
    dirs = ['{0}.breakpad.syms'.format(PROJECT_NAME)]
    make_zip(zip_file, files, dirs)


if __name__ == '__main__':
  sys.exit(main())
