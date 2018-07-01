#!/usr/bin/env python3

import stat

from hashlib import md5
from sys import argv
from os import environ, makedirs, getcwd, chmod
from os.path import join, exists, splitext, basename
from platform import machine, system
from urllib.parse import urlparse
from urllib.request import urlopen
from urllib.error import HTTPError
from io import TextIOWrapper
from subprocess import check_call
from .utils import DirectoryContext
from .buffer import ZBuffer, Buffer


class ParseError(ValueError):
    pass

def parse_line(line):
    cursor = 0
    index = line.find(' ')
    err = lambda: ParseError("Unable to parse line '%s', error after column %d" % line, cursor)
    if index == -1:
        raise err()
    digest = line[:index]
    cursor = index + 1
    index = line.find('(', cursor)
    if index == -1:
        raise err()
    cursor = index + 1
    index = line.find(')', cursor)
    if index == -1:
        raise err()
    filename = line[cursor:index]
    cursor = index
    index = line.find(' = ', cursor)
    if index == -1:
        raise err()
    cursor = index
    digest_string = line[cursor + 3:].strip()
    return digest, filename, digest_string


def compute_md5(stream):
    hasher = md5()
    while True:
        buf = stream.read(1024)
        hasher.update(buf)
        if len(buf) < 1024:
            break
    return hasher.hexdigest()


def download_file(url, out):
    # print('Downloading %s' % join(getcwd(), basename(url.path)))
    url_string = url._replace(path=join(url.path + '.gz')).geturl()
    try:
        with urlopen(url_string) as request:
            stream = ZBuffer(request, Buffer.Mode.read, format=ZBuffer.Format.GZIP)
            while True:
                buf = stream.read(1024)
                out.write(buf)
                if len(buf) < 1024:
                    break
        print("Downloaded %s", url_string)
    except HTTPError as err:
        print(err)
        url_string = url.geturl()
        with urlopen(url_string) as request:
            while True:
                buf = request.read(1024)
                out.write(buf)
                if len(buf) < 1024:
                    break
        print("Downloaded %s", url_string)


def run():
    parms = dict()
    index = 1
    while index < len(argv):
        arg = argv[index]
        if arg and arg[0] == '-':
            value = argv[index+1] if len(argv) > index+1 else True
            if isinstance(value, str) and value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            parms[arg[1:]] = value
            index += 2
        else:
            index += 1

    hostscan_dir = join(environ['HOME'], '.cisco', 'hostscan')
    #print(argv)
    #print(parms)
    #print(urlparse(parms['url']))
    if system() == "Linux":
        if machine() == 'x86_64':
            arch = 'linux_x64'
        elif machine() == 'i386':
            arch = 'linux_i386'
    else:
        raise ValueError('Unsupported system: "%s"' % system())

    file_url = urlparse(parms['url'])
    file_url = file_url._replace(path=join(file_url.path, 'sdesktop', 'hostscan', arch))
    manifest_url = file_url._replace(path=join(file_url.path, 'manifest'))
    print('Manifest URL: %s' % manifest_url.geturl())
    resources = dict()
    library_extensions = {'.dylib', '.so', '.dat'}
    with urlopen(manifest_url.geturl()) as request:
        text_buffer = TextIOWrapper(request)
        for line in text_buffer:
            digest_type, filename, digest_value = parse_line(line)
            resources[filename] = (digest_type, digest_value)
            _, ext = splitext(filename)
            if ext in library_extensions:
                directory = 'lib'
            else:
                directory = 'bin'
            with DirectoryContext(join(hostscan_dir, directory), create=True):
                download_url = file_url._replace(path=join(file_url.path, filename))
                if exists(filename):
                    if digest_type == 'MD5':
                        current_digest = compute_md5(open(filename, 'rb'))
                    else:
                        raise ValueError('Unknown digest type "%s"' % digest_type)
                    if current_digest != digest_value:
                        with open(filename, 'wb') as file:
                            download_file(download_url, file)
                    else:
                        print('%s is up-to-date' % join(getcwd(), filename))
                else:
                    with open(filename, 'wb') as file:
                        download_file(download_url, file)
                if directory == 'bin':
                    chmod(filename, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH |
                          stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH |
                          stat.S_IWUSR)


    with DirectoryContext(join(hostscan_dir, 'bin')):
        cmd = [join(getcwd(), 'cstub'),
                '-ticket', parms['ticket'],
                '-stub', parms['stub'],
                '-group', parms['group'],
                '-url', parms['url'],
                '-certhash', parms['certhash']]
        check_call(cmd)



