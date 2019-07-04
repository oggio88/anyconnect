#!/usr/bin/env python3

from os import environ
from sys import argv
from urllib.request import urlopen, Request
import ssl

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

    data = """endpoint.os.version="Linux";
    endpoint.file["LinuxFUpdate"] = {};
    endpoint.file["LinuxFUpdate"].exists = "true";
    endpoint.file["LinuxFUpdate"].path = "/etc/cron.d/fupdate";
    endpoint.file["LinuxFUpdate"].name = "fupdate";
    endpoint.file["LinuxLaptopPass"] = {};
    endpoint.file["LinuxLaptopPass"].exists = "true";
    endpoint.file["LinuxLaptopPass"].path = "/etc/.adm-laptop-pass";
    endpoint.file["LinuxLaptopPass"].name = ".adm-laptop-pass";
    """
    url = "https://%s/+CSCOE+/sdesktop/scan.xml?reusebrowser=1" % (environ['CSD_HOSTNAME'])
    ctx = ssl.SSLContext()
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.check_hostname = False
    ctx.load_default_certs()
    request = Request(url, headers={'Cookie': 'sdesktop=' + environ['CSD_TOKEN'], 'Content-Type': 'text/xml'})
    with urlopen(request, data=data.encode(), context=ctx) as request:
        pass



