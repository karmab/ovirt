#!/usr/bin/python 

import xml.etree.ElementTree as ET
import optparse
import os
import re
import sys
sys.path.append("/usr/share/vdsm")
from vdsm import vdscli

version="0.0"
parser = optparse.OptionParser("Usage: %prog [options] vmname",version=version)
parser.add_option("-c", "--cert", dest="cert", type="string", help="path to the CA cert file required in order to connect to console.Get it from http://${OVIRT}/ca.crt, keep only the CERTIFICATE part")
parser.add_option("-l", "--list", dest="listing", action="store_true", help="List vms")
parser.add_option("-m", "--migrate", dest="migrate", type="string", help="Migrate Vm to specified host")
parser.add_option("-p", "--port", dest="port", default="54321",type="string", help="Port to connect to.Defaults to localhost")
parser.add_option("-o", "--console", dest="console", action="store_true", help="Get console")
parser.add_option("-w", "--stop", dest="stop", action="store_true", help="stop vm")
parser.add_option("-H", "--host", dest="host", default="127.0.0.1",type="string", help="Server to connect to.Defaults to localhost")
parser.add_option("-O", "--org", dest="org",type="string", help="Organisation for console mode")
parser.add_option("-T", "--truststore", dest="truststore", default="/etc/pki/vdsm",type="string", help="Path containing cert files.Defaults to /etc/pki/vdsm")
(options, args) = parser.parse_args()
cert=options.cert
host=options.host
listing=options.listing
migrate=options.migrate
port=options.port
stop=options.stop
console=options.console
org=options.org
truststore=options.truststore

useSSL = True
s=vdscli.connect("%s:%s" % (host,port),useSSL, truststore)

#check if i am spm
try:
 spuid=s.getConnectedStoragePoolsList()["poollist"][0]
 if s.getSpmStatus(spuid)['spm_st']['spmStatus']=="SPM":
  spm=True
 else:
  spm=False
except:
 spm=False

if listing:
 vms={}
 vmids=[]
 for vm in  s.list(True)["vmList"]:
  vms[vm["vmName"]]="%s on port %s" % (vm["display"],vm["displayPort"])
  vmids.append(vm["vmId"])
 for vm in sorted(vms):
  print "%s using %s" % (vm,vms[vm])
 if spm:
  print "not running vms:"
  sppath= "/rhev/data-center/%s/mastersd/master/vms" % spuid
  if host=="127.0.0.1":
   for id in os.listdir(sppath):
    if id in vmids:continue
    #f=open("%s/%s/%s.ovf" % (sppath,id,id))
    #regname=re.compile(".*<Name>(.*)</Name>.*")
    #for line in f.readlines():
     #m=regname.match(line)
     #if m:print m.group(1)
    #f.close()
    tree = ET.parse("%s/%s/%s.ovf" % (sppath,id,id))
    root = tree.getroot()
    for content in root.findall('Content'):
     name=content.findall("Name")[0].text
     print "%s" % name   
  else:
   print "SSH should be used here..."
 sys.exit(0)

#once here, a vm is expected
if len(args) !=1:
 print "Usage: %prog [options] vmname"
 sys.exit(0)
else:
 vms={}
 name=args[0]
 for vm in  s.list(True)["vmList"]:vms[vm["vmName"]]={"vmid":vm["vmId"],"vmdisplay":vm["display"],"vmport":vm["displayPort"]}
 if name not in vms:
  print "VM not found.leaving..."
  sys.exit(1)
 else:
  vmid=vm["vmId"]
  vmdisplay=vm["display"]
  vmport=vm["displayPort"]
  vmsport=vm["displaySecurePort"]
  vmip=vm["displayIp"]
  if vmip=="0":vmip="127.0.0.1"

if console:
 if not cert or not org:
  print "You need to use -c cert  and -o org too"
  sys.exit(0)
 ticket="123"
 s.setVmTicket(vmid,"123",60)
 subject="%s,CN=%s" % (org,vmip)
 print "Password copied to clipboard:  %s" % ticket
 #copy to clipboard
 if os.environ.has_key("KDE_FULL_SESSION") or os.environ.has_key("KDEDIRS"):
  os.popen("qdbus org.kde.klipper /klipper setClipboardContents %s" % ticket)
 else:
  os.popen("xsel", "wb").write(ticket)
 if vmdisplay=="qxl":
  os.popen("remote-viewer --spice-ca-file %s --spice-host-subject '%s' spice://%s/?port=%s\&tls-port=%s &" %  (cert,subject,host,vmport,vmsport))
 else:
  os.popen("remote-viewer vnc://%s:%s &" %  (host,vmport))
 sys.exit(0)

if stop:
  s.destroy(vmid)
  print "vm %s stopped" % name
  sys.exit(0)

#to implement:
#-launch vm
#migrate vm and get stats about migration
#get a serial console
#-get spm status
#stop spm status
#start spm status 
#inform about where to find needed certs

sys.exit(0)
