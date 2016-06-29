#!/usr/bin/python
"""
script to launch stopped vms with tag first_install
used some samples from https://access.redhat.com/knowledge/docs/en-US/Red_Hat_Enterprise_Virtualization/3.1-Beta/html/Developer_Guide/Example_Attaching_an_ISO_Image_to_a_Virtual_Machine_using_Python.html
"""

import sys
import optparse
import os
import time
import xmlrpclib
import ConfigParser
from ovirtsdk.api import API
from ovirtsdk.xml import params

__author__ = "Karim Boumedhel"
__credits__ = ["Karim Boumedhel"]
__license__ = "GPL"
__version__ = "1.1"
__maintainer__ = "Karim Boumedhel"
__email__ = "karim.boumedhel@gmail.com"
__status__ = "Production"

ERR_NOOVIRTFILE = "You need to create a correct ovirt.ini file in your home directory.Check documentation"
ERR_CLIENTNOTFOUND = "Client not found"
ERR_CLIENTNOCONF = "Client not found in conf file"

usage = "script to launch stopped vms with tag first_install"
version = "0.1"
parser = optparse.OptionParser("Usage: %prog [options] vmname")
parser.add_option("-t", "--tag", dest="tag", type="string",
                  default="first_install", help="Tag to use to find vms")
parser.add_option("-l", "--listclients", dest="listclients",
                  action="store_true", help="List Available Clients")
parser.add_option("-i", "--insecure", dest="insecure",
                  default=False, action="store_true", help="Connect without ssl")

(options, args) = parser.parse_args()
tag = options.tag
listclients = options.listclients
insecure = options.insecure
client = None
insecure = options.insecure
ohost, oport, ouser, opassword, oca, oorg = None, None, None, None, None, None

ovirtconffile = os.environ['HOME'] + "/ovirt.ini"
# parse ovirt client auth file
if not os.path.exists(ovirtconffile):
    print "Missing %s in your  home directory.Check documentation" % ovirtconffile
    sys.exit(1)
try:
    c = ConfigParser.ConfigParser()
    c.read(ovirtconffile)
    ovirts = {}
    default = {}
    for cli in c.sections():
        for option in c.options(cli):
            if cli == "default":
                default[option] = c.get(cli, option)
                continue
            if cli not in ovirts.keys():
                ovirts[cli] = {option: c.get(cli, option)}
            else:
                ovirts[cli][option] = c.get(cli, option)
except:
    print ERR_NOOVIRTFILE
    os._exit(1)

if listclients:
    print "Available Clients:"
    for cli in sorted(ovirts):
        print cli
    print "Current default client is: %s" % (default["client"])
    sys.exit(0)

if not client:
    try:
        client = default['client']
    except:
        print "No client defined as default in your ini file or specified in command line"
        os._exit(1)

try:
    ohost = ovirts[client]['host']
    oport = ovirts[client]['port']
    ouser = ovirts[client]['user']
    opassword = ovirts[client]['password']
    if 'ssl' in ovirts[client].keys():
        ossl = ovirts[client]['ssl']
    if 'clu' in ovirts[client].keys():
        clu = ovirts[client]['clu']
    if 'storagedomain' in ovirts[client].keys():
        storagedomain = ovirts[client]['storagedomain']
    if 'ssl' in ovirts[client].keys():
        ossl = True
    if 'ca' in ovirts[client].keys():
        oca = ovirts[client]['ca']
    if 'org' in ovirts[client].keys():
        oorg = ovirts[client]['org']
except KeyError, e:
    print "Problem parsing your ini file:Missing parameter %s" % e
    os._exit(1)

if not insecure:
    url = "https://%s:%s/api" % (ohost, oport)
else:
    url = "http://%s:%s/api" % (ohost, oport)

api = API(url=url, username=ouser, password=opassword, insecure=True)
# searchs vms with matching tag
vms = api.vms.list()
launched = 0
for vm in vms:
    if vm.status.state == "up":
        continue
    for tg in vm.get_tags().list():
        if tg.name == tag:
            # delete tag
            tg.delete()
            # remove kernel options
            vm.os.kernel, vm.os.initrd, vm.os.cmdline = "", "", ""
            # ensure first boot is hd( and set second as cdrom
            vm.os.boot = [params.Boot(dev="hd"), params.Boot(dev="cdrom")]
            # launch vm
            vm.start()
            print "vm %s started" % vm.name
            launched = launched + 1

if launched == 0:
    print "No matching vms found"
else:
    print "%d vms were launched" % (launched)

sys.exit(0)
