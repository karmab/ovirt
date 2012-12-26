#!/usr/bin/python 

import optparse
import sys
sys.path.append("/usr/share/vdsm")
from vdsm import vdscli

version="0.0"
parser = optparse.OptionParser("Usage: %prog [options] vmname",version=version)
parser.add_option("-l", "--list", dest="listing", action="store_true", help="List vms")
parser.add_option("-m", "--migrate", dest="migrate", type="string", help="Migrate Vm to specified host")
parser.add_option("-p", "--port", dest="port", default="54321",type="string", help="Port to connect to.Defaults to localhost")
parser.add_option("-w", "--stop", dest="stop", action="store_true", help="stop vms")
parser.add_option("-H", "--host", dest="host", default="127.0.0.1",type="string", help="Server to connect to.Defaults to localhost")
(options, args) = parser.parse_args()
host=options.host
listing=options.listing
migrate=options.migrate
port=options.port
stop=options.stop

useSSL = True
truststore = None
s=vdscli.connect("%s:%s" % (host,port),useSSL, truststore)
if listing:
 vms=[]
 for vm in  s.list(True)["vmList"]:vms.append(vm["vmName"])
 for vm in sorted(vms):print vm
 sys.exit(0)

if stop and len(args) == 1:
 vms={}
 name=args[0]
 for vm in  s.list(True)["vmList"]:vms[vm["vmName"]]=vm["vmId"]
 if name not in vms:
  print "VM not found.leaving..."
  sys.exit(1)
 else:
  vmid=vms[name]
  s.destroy(vmid)
  print "vm %s stopped" % name

#to implement:
#-launch vm
#migrate vm and get stats about migration
#get a ticket for console
#get a serial console
#-get spm status
#stop spm status
#start spm status 
#inform about where to find needed certs

sys.exit(0)
