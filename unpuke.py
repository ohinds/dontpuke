#!/usr/bin/env python

"""Utility to extract archives (zip or tar-based) without puking the
contents all over the current working directory. If the top level of the
archive isn't a directory, extraction is performed into a new one.

Supported file formats:
zip
anything the tar utility supports

Oliver Hinds <ohinds@gmail.com>
"""

import argparse
import os
import re
import subprocess
import sys


def parse_args(argv):
    parser = argparse.ArgumentParser('Archive extraction utility that makes '
                                     'sure to extract to a directory')
    parser.add_argument('source', nargs=1)
    parser.add_argument('destination', nargs='?', default=os.getcwd())
    return parser.parse_args(argv)


def guess_file_type(archive):
    if archive.endswith('.zip'):
        return 'zip'
    elif (archive.endswith('.tar') or
          archive.endswith('.tar.gz') or
          archive.endswith('.tgz') or
          archive.endswith('.tar.bz') or
          archive.endswith('.tbz')):
        return 'tar'
    else:
        raise ValueError("Can't guess archive type for %s" % archive)


def get_archive_file_list(archive):
    file_type = guess_file_type(archive)

    if file_type == 'zip':
        command = ['unzip', '-l']
    elif file_type == 'tar':
        command = ['tar', '-taf']

    lister = subprocess.Popen(command + [archive],
                              stdout=subprocess.PIPE)
    file_list, _ = lister.communicate()
    file_list = file_list.split('\n')
    if file_type == 'zip':
        tmp_file_list = file_list[3:-3]
        file_list = []
        for f in tmp_file_list:
            file_list.append(' '.join(f.split()[3:]))

    return file_list


def test_for_top_level_directory(file_list):
    def get_first_dir(path):
        dirs, base = os.path.split(path)
        if os.path.split(dirs)[0] == '':
            return dirs
        return get_first_dir(dirs)

    potential_top_level = None
    for f in file_list:
        if f == '':
            continue

        if os.path.dirname(f) == '':
            return False

        path = get_first_dir(f)
        if potential_top_level is None:
            potential_top_level = path

        if path != potential_top_level:
            return False

    return True


def extract_by_format(archive, dest_dir):
    file_type = guess_file_type(archive)

    if file_type == 'zip':
        command = ['unzip',
                   '-d', dest_dir]
    elif file_type == 'tar':
        command = ['tar',
                   '--directory', dest_dir,
                   '-xaf']

    extract = subprocess.check_call(command + [archive])


def main(argv):
    options = parse_args(argv[1:])
    options.source = options.source[0]

    if not os.path.exists(options.source):
        raise ValueError("Archive %s not found" % options.source)

    files = get_archive_file_list(options.source)

    if not test_for_top_level_directory(files):
        name, _ = os.path.splitext(os.path.basename(options.source))
        dest = os.path.join(options.destination, name)
        print "Creating top level directory %s for archive" % dest
        os.mkdir(dest)
    else:
        dest = options.destination

    print "Extracting %s to %s" % (options.source, dest)

    extract_by_format(options.source, dest)

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
