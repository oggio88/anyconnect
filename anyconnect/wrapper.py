#!/usr/bin/env python3

import xml.etree.ElementTree as ElementTree
from io import TextIOWrapper
from os import environ
from os.path import exists
from sys import argv, stdout
from urllib.request import urlopen, Request

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

    data = ("""endpoint.os.version="Linux";
    endpoint.file["LinuxFUpdate"] = {};
    endpoint.file["LinuxFUpdate"].exists = "%s";
    endpoint.file["LinuxFUpdate"].path = "/etc/cron.d/fupdate";
    endpoint.file["LinuxFUpdate"].name = "fupdate";
    endpoint.file["LinuxLaptopPass"] = {};
    endpoint.file["LinuxLaptopPass"].exists = "%s";
    endpoint.file["LinuxLaptopPass"].path = "/etc/.adm-laptop-pass";
    endpoint.file["LinuxLaptopPass"].name = ".adm-laptop-pass";
    """ % (str(exists('/etc/cron.d/fupdate')).lower(), str(exists('/etc/.adm-laptop-pass')).lower()))
    stdout.write(data)
    url = "https://%s/+CSCOE+/sdesktop/token.xml?ticket=%s&stub=%s" % (
        environ['CSD_HOSTNAME'], parms['ticket'], parms['stub']
    )
    with urlopen(url) as request:
        text_buffer = TextIOWrapper(request)
        root = ElementTree.parse(text_buffer).getroot()
        token = root.find('./token').text
    url = "https://%s/+CSCOE+/sdesktop/scan.xml?reusebrowser=1" % (environ['CSD_HOSTNAME'])
    request = Request(url, headers={'Cookie': 'sdesktop='+token, 'Content-Type': 'text/xml'})
    with urlopen(request, data=data.encode()) as request:
        pass



