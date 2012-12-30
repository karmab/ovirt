#!/usr/bin/python
"""
script to create virtual machines on ovirt/rhev
used some samples from https://access.redhat.com/knowledge/docs/en-US/Red_Hat_Enterprise_Virtualization/3.1-Beta/html/Developer_Guide/Example_Attaching_an_ISO_Image_to_a_Virtual_Machine_using_Python.html and the http://markmc.fedorapeople.org/rhevm-api/en-US/html/
"""

import sys
import optparse
import os
import time
import xmlrpclib
import urllib
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

ERR_NOOVIRTFILE="You need to create a correct ovirt.ini file in your home directory.Check documentation"
ERR_NOCOBBLERFILE="You need to create a correct cobbler.ini file in your home directory.Check documentation"
ERR_CLIENTNOTFOUND="Client not found"
ERR_CLIENTNOCONF="Client not found in conf file"
ERR_CLIENTNOPROFILE="Missing client file in your home directory.Check documentation"

usage="script to create virtual machines on ovirt/rhev"
version="1.8"
parser = optparse.OptionParser("Usage: %prog [options] vmname",version=version)
creationgroup = optparse.OptionGroup(parser, "Creation options")
creationgroup.add_option("-b", "--bad", dest="bad",action="store_true", help="If set,treat all actions as not for a linux guest,meaning net interfaces will be of type e1000 and disk of type ide.Necessary for windows or solaris guests")
creationgroup.add_option("-c", "--cpu", dest="numcpu", type="int", help="Specify Number of CPUS")
creationgroup.add_option("-d", "--disk", dest="disksize2", metavar="DISKSIZE",type="int", help="Specify Disk size,in Go at VM creation")
creationgroup.add_option("-e", "--extra", dest="extra", type="string", help="Extra parameters to add to cmdline")
creationgroup.add_option("-f", "--diskformat", dest="diskformat", type="string", help="Specify Disk mode.Can be raw or cow")
creationgroup.add_option("-m", "--memory", dest="memory2", metavar="MEMORY",type="int", help="Specify Memory, in Mo")
creationgroup.add_option("-n", "--new", dest="new",action="store_true", help="Create new VM")
creationgroup.add_option("-p", "--profile", dest="profile",type="string", help="specify Profile")
creationgroup.add_option("-D", "--storagedomain" , dest="storagedomain", type="string", help="Specify Storage Domain")
creationgroup.add_option("-E", "--cluster", dest="clu", metavar="CLUSTER",type="string", help="Specify Cluster")
creationgroup.add_option("-N", "--numinterfaces", dest="numinterfaces", type="int", help="Specify number of net interfaces")
creationgroup.add_option("-T", "--thin", dest="thin", action="store_true", help="Use thin provisioning for disk")
creationgroup.add_option("-Y", "--nolaunch", dest="nolaunch", action="store_true", help="Dont Launch VM,just create it")
creationgroup.add_option("-8", "--mac1", dest="mac1", type="string", help="Specify mac to assign to first interface of vm when creating it or deploying from template.if a number is provided,only last octet of the mac will be set")
parser.add_option_group(creationgroup)

actiongroup = optparse.OptionGroup(parser, "Action options")
actiongroup.add_option("-a", "--adddisk", dest="adddisk", metavar="DISKSIZE",type="int", help="Specify Disk size,in Go to add")
actiongroup.add_option("-g", "--guestid", dest="guestid", type="string", help="Change guestid of VM")
actiongroup.add_option("-i", "--iso", dest="iso", type="string", help="Specify iso to add to VM")
actiongroup.add_option("-j", "--migrate", dest="migrate", action="store_true", help="Migrate VM")
actiongroup.add_option("-k", "--host", dest="host", type="string", help="Host to use when migrating a VM")
actiongroup.add_option("-o", "--console", dest="console", action="store_true", help="Get a console")
actiongroup.add_option("-q", "--quit", dest="isoquit", action="store_true", help="Remove iso from VM")
actiongroup.add_option("-r", "--restart", dest="restart", action="store_true", help="Restart vm")
actiongroup.add_option("-s", "--start", dest="start", action="store_true", help="Start VM")
actiongroup.add_option("-t", "--tags", dest="tags", type="string", help="Add tags to VM")
actiongroup.add_option("-u", "--deletetag", dest="deletetag", type="string", help="Delete tag from VM")
actiongroup.add_option("-v", "--reset", dest="reset", action="store_true", help="Reset kernel parameters for given VM")
actiongroup.add_option("-w", "--stop", dest="stop", action="store_true", help="Stop VM")
actiongroup.add_option("-x", "--kernel", dest="kernel", type="string", help="Specify kernel to boot VM")
actiongroup.add_option("-y", "--initrd", dest="initrd", type="string", help="Specify initrd to boot VM")
actiongroup.add_option("-z", "--cmdline", dest="cmdline", type="string", help="Specify cmdline to boot VM")
actiongroup.add_option("-B", "--boot", dest="boot", type="string", help="Specify Boot sequence,using two values separated by colons.Values can be hd,network,cdrom.If you only provivde one options, second boot option will be set to None")
#actiongroup.add_option("-Q", "--hanging", dest="hanging", action="store_true", help="Check hanging tasks")
actiongroup.add_option("-K", "--kill", dest="kill", action="store_true" , help="specify VM to kill in virtual center.Confirmation will be asked unless -F/--forcekill flag is set.VM will also be killed in cobbler server if -Z/-cobbler flag set")
actiongroup.add_option("-F", "--forcekill", dest="forcekill", action="store_true", help="Dont ask confirmation when killing a VM")
actiongroup.add_option("-4", "--runonce", dest="runonce", action="store_true", help="Runonce VM.you will need to pass kernel,initrd and cmdline")
actiongroup.add_option("-5", "--template", dest="template", type="string", help="Deploy VM from template")
parser.add_option_group(actiongroup)

listinggroup = optparse.OptionGroup(parser, "Listing options")
listinggroup.add_option("-l", "--listprofiles", dest="listprofiles", action="store_true", help="list available profiles")
listinggroup.add_option("-H", "--listhosts", dest="listhosts", action="store_true", help="List hosts")
listinggroup.add_option("-I", "--listisos", dest="listisos", action="store_true", help="List isos")
listinggroup.add_option("-L", "--listclients", dest="listclients", action="store_true", help="list available clients")
listinggroup.add_option("-O", "--listtags", dest="listtags", action="store_true", help="List available tags")
listinggroup.add_option("-V", "--listvms", dest="listvms", action="store_true", help="list all vms")
parser.add_option_group(listinggroup)

cobblergroup = optparse.OptionGroup(parser, "Cobbler options")
cobblergroup.add_option("-Z", "--cobbler", dest="cobbler", action="store_true", help="Cobbler support")
cobblergroup.add_option("-1", "--ip1", dest="ip1", type="string", help="Specify First IP")
cobblergroup.add_option("-2", "--ip2", dest="ip2", type="string", help="Specify Second IP")
cobblergroup.add_option("-3", "--ip3", dest="ip3", type="string", help="Specify Third IP")
parser.add_option_group(cobblergroup)

parser.add_option("-A", "--activate", dest="activate", type="string", help="Activate specified storageDomain")
parser.add_option("-C", "--client", dest="client", type="string", help="Specify Client")
parser.add_option("-M", "--maintenance", dest="maintenance", type="string", help="Put in maintenance specified storageDomain")
parser.add_option("-S", "--summary", dest="summary", action="store_true", help="Summary of your ovirt setup")
parser.add_option("-X", "--search" , dest="search", type="string", help="Search VMS")
parser.add_option("-9", "--switchclient", dest="switchclient", type="string", help="Switch default client")

MB = 1024*1024
GB = 1024*MB
(options, args) = parser.parse_args()
staticroutes=None
backuproutes=None
gwbackup=None
clients=[]
boot = options.boot
extra = options.extra
reset = options.reset
client = options.client
guestid = options.guestid
listclients = options.listclients
switchclient = options.switchclient
listisos = options.listisos
host = options.host
listhosts = options.listhosts
listvms = options.listvms
listprofiles = options.listprofiles
new=options.new
cobbleruser=None
cobblermac=None
diskformat = options.diskformat
disksize2 = options.disksize2
if disksize2:disksize2=disksize2*GB
ip1=options.ip1
ip2=options.ip2
ip3=options.ip3
activate=options.activate
maintenance=options.maintenance
kernel=options.kernel
initrd=options.initrd
cmdline=options.cmdline
memory2 = options.memory2
if memory2:memory2=memory2*MB
restart=options.restart
start=options.start
runonce=options.runonce
stop=options.stop
summary=options.summary
numcpu = options.numcpu
thin=options.thin
kill=options.kill
forcekill=options.forcekill
clu=options.clu
storagedomain=options.storagedomain
adddisk=options.adddisk
if adddisk:adddisk=adddisk*GB
bad=options.bad
cobbler=options.cobbler
nolaunch=options.nolaunch
search=options.search
profile = options.profile
console = options.console
listtags = options.listtags
tags = options.tags
deletetag = options.deletetag
installnet=None
boot1,boot2="hd","network"
numinterfaces=options.numinterfaces
iso=options.iso
isoquit=options.isoquit
migrate=options.migrate
template=options.template
mac1=options.mac1
#hanging=options.hanging
macaddr=[]
guestrhel332="rhel_3"
guestrhel364="rhel_3x64"
guestrhel432="rhel_4"
guestrhel464="rhel_4x64"
guestrhel532="rhel_5"
guestrhel564="rhel_5x64"
guestrhel632="rhel_6"
guestrhel664="rhel_6x64"
guestother="other"
guestotherlinux="other_linux"
guestwindowsxp="windows_xp"
guestwindows7="windows_7"
guestwindows764="windows_7x64"
guestwindows2003="windows_2003"
guestwindows200364="windows_2003x64"
guestwindows2008="windows_2008"
guestwindows200864="windows_2008x64"


def findhostbyid(api,id):
 hosts=api.hosts
 for h in hosts.list():
  if h.get_id()==id:return h.get_name()

def findclubyid(api,id):
 clusters=api.clusters
 for clu in clusters.list():
  if clu.get_id()==id:return clu.get_name()

def getip(api,id):
 hosts=api.hosts
 for h in hosts.list():
  if h.get_id()==id:return h.get_address()

def switchstoragedomain(api,storagedomain,activate=True):
 action=False
 sd=api.storagedomains.get(name=storagedomain)
 if not sd:
  print "Storage domain not found"
  sys.exit(1)
 else:
  id=sd.get_id()
  sds=[]
  for ds in api.datacenters.list():
   for s in ds.storagedomains.list():
    if activate: 
     if s.get_status().get_state()!="active" and s.get_id()==id:
      s.activate()
      print "StorageDomain %s activated" % (storagedomain)
      action=True
    if not activate: 
     if s.get_status().get_state()=="active" and s.get_id()==id:
      s.deactivate()
      print "StorageDomain %s put in maintenance" % (storagedomain)
      action=True
 if not action:print "No actions needed..."

def checkiso(api,iso=None):
 isodomains=[]
 datacenters=api.datacenters.list()
 for ds in datacenters:
  for sd in ds.storagedomains.list():
   if sd.get_type()=="iso" and sd.get_status().get_state()=="active":isodomains.append(sd)
 if len(isodomains)==0:
  print "No iso domain found.Leaving..."
  sys.exit(1)
 for sd in isodomains:
  if not iso:print "Isodomain: %s" % (sd.get_name())
  if not iso:print "Available isos:"
  isodomainid=sd.get_id()
  sdfiles=api.storagedomains.get(id=isodomainid).files
  for f in sdfiles.list():
   if not iso:
    print f.get_id()
   elif f.get_id()==iso:
    return f
 sys.exit(0)

ohost,oport,ouser,opassword,ossl,oca,oorg=None,None,None,None,None,None,None
#thin provisioning
sparse=True
if bad:
 diskinterface,netinterface="ide","e1000"
else:
 diskinterface,netinterface="virtio","virtio"

if len(args)!=1 and new:
 print "Usage: %prog [options] vmname"
 sys.exit(1)

ovirtconffile="%s/ovirt.ini" %(os.environ['HOME'])
#parse ovirt client auth file
if not os.path.exists(ovirtconffile):
 print "Missing %s in your  home directory.Check documentation" % ovirtconffile
 sys.exit(1)
try:
 c = ConfigParser.ConfigParser()
 c.read(ovirtconffile)
 ovirts={}
 default={}
 for cli in c.sections():
  for option in  c.options(cli):
   if cli=="default":
    default[option]=c.get(cli,option)
    continue
   if not ovirts.has_key(cli):
    ovirts[cli]={option : c.get(cli,option)}
   else:
    ovirts[cli][option]=c.get(cli,option)
except:
 print ERR_NOOVIRTFILE
 os._exit(1)

if listclients:
 print "Available Clients:"
 for cli in  sorted(ovirts):
  print cli
 print "Current default client is: %s" % (default["client"])
 sys.exit(0)

if switchclient:
 if switchclient not in ovirts.keys():
  print "Client not defined...Leaving"
 else: 
  mod = open(ovirtconffile).readlines()
  f=open(ovirtconffile,"w")
  for line in mod:
   if line.startswith("client"):
    f.write("client=%s\n" % switchclient)
   else:
    f.write(line)
  f.close() 
  print "Default Client set to %s" % (switchclient)
 sys.exit(0)

if not client:
 try:
  client=default['client']
 except:
  print "No client defined as default in your ini file or specified in command line"
  os._exit(1)

#PARSE DEFAULT SECTION
try:
 if not clu and default.has_key("clu"):clu=default["clu"]
 if not numcpu and default.has_key("numcpu"):numcpu=int(default["numcpu"])
 if not diskformat and default.has_key("diskformat"):diskformat=default["diskformat"]
 if default.has_key("disksize"):disksize=int(default["disksize"])*GB
 if default.has_key("memory"):memory=int(default["memory"])*MB
 if not storagedomain and default.has_key("storagedomain"):storagedomain=default["storagedomain"]
 if not numinterfaces and default.has_key("numinterfaces"):numinterfaces=int(default["numinterfaces"])
 if not ossl and default.has_key("ssl"):ossl=True
except:
 print "Problem parsing default section in your ini file"
 os._exit(1)

try:
 ohost=ovirts[client]["host"]
 oport=ovirts[client]["port"]
 ouser=ovirts[client]["user"]
 opassword=ovirts[client]["password"]
 if ovirts[client].has_key("ssl"):ossl=ovirts[client]["ssl"]
 if ovirts[client].has_key("clu"):clu=ovirts[client]["clu"]
 if not numcpu and ovirts[client].has_key("numcpu"):numcpu=int(ovirts[client]["numcpu"])
 if ovirts[client].has_key("diskformat"):diskformat=ovirts[client]["diskformat"]
 if ovirts[client].has_key("diskinterface"):diskinterface=ovirts[client]["diskformat"]
 if ovirts[client].has_key("disksize"):disksize=int(ovirts[client]["disksize"])*GB
 if ovirts[client].has_key("memory"):memory=int(ovirts[client]["memory"])*MB
 if not storagedomain and ovirts[client].has_key("storagedomain"):storagedomain=ovirts[client]["storagedomain"]
 if ovirts[client].has_key("numinterfaces"):numinterfaces=int(ovirts[client]["numinterfaces"])
 if ovirts[client].has_key("netinterface"):diskinterface=ovirts[client]["netinterface"]
 if ovirts[client].has_key("ssl"):ossl=True
 if ovirts[client].has_key("ca"):oca=ovirts[client]["ca"]
 if ovirts[client].has_key("org"):oorg=ovirts[client]["org"]
 #if ovirts[client].has_key("runonce"):runonce=True
except KeyError,e:
 print "Problem parsing your ini file:Missing parameter %s" % e
 os._exit(1)

#TODO:check necessary parameters exist for a valid ovirt connection or exits
#if not ohost or not oport or not ouser or not opassword or not ossl or not clu or not numcpu or not diskformat or not disksize or not memory or not storagedomain or not numinterfaces:
# print "Missing parameters for ovirt"
# sys.exit(1)

#parse cobbler client auth file
if cobbler and client:
 cobblerconffile="%s/cobbler.ini" % (os.environ['HOME'])
 if not os.path.exists(cobblerconffile):
  print "Missing %s in your  home directory.Check documentation" % cobblerconffile
  sys.exit(1)
 try:
  c = ConfigParser.ConfigParser()
  c.read(cobblerconffile)
  cobblers={}
  for cli in c.sections():
   for option in  c.options(cli):
    if not cobblers.has_key(cli):
     cobblers[cli]={option : c.get(cli,option)}
    else:
     cobblers[cli][option]=c.get(cli,option)
  cobblerhost=cobblers[client]['host']
  cobbleruser=cobblers[client]['user']
  cobblerpassword=cobblers[client]['password']
  if cobblers[client].has_key("mac"):cobblermac=cobblers[client]['mac']
 except:
  print ERR_NOCOBBLERFILE
  os._exit(1)

if ossl:
 url = "https://%s:%s/api" % (ohost,oport)
 #api = API(url=url, username=ouser, password=opassword, ca_file=ossl)
else:
 url = "http://%s:%s/api" % (ohost,oport)

api = API(url=url, username=ouser, password=opassword, insecure=True)

#LIST VMS
if listvms:
 for vm in api.vms.list():print vm.get_name()
 sys.exit(0)

if listisos:
 checkiso(api)
 sys.exit(0)

if listtags:
 for tag  in api.tags.list():
  print "TAG: %s" % tag.get_name()
 sys.exit(0)

if activate:
 switchstoragedomain(api,activate)
 sys.exit(0) 

if maintenance:
 switchstoragedomain(api,maintenance,False) 
 sys.exit(0) 

#if hanging:
# print dir(api)
# sys.exit(0) 

#LIST HOSTS
if listhosts:
 #create a dict hostid->vms
 hosts={}
 for vm in api.vms.list():
  if vm.get_host() !=None:name,hostid=vm.get_name(),vm.get_host().get_id()
  if hosts.has_key(hostid):
   hosts[hostid].append(name)
  else:
   hosts[hostid]=[name]

 for h in api.hosts.list():
  print "Name: %s  " % h.get_name()
  print "Cluster: %s  " % findclubyid(api,h.get_cluster().get_id())
  print "IP: %s  " % h.get_address()
  hostid=h.get_id()
  if hosts.has_key(hostid):
   print "VMS: %s  " % ",".join(hosts[hostid])
  print ""
 sys.exit(0)

#SEARCH VMS
if search:
 vms=api.vms.list()
 vmfound=False
 for vm in vms:
  if search.replace("*","").upper() in vm.name.upper():
   if not vmfound:print "Vms found:"
   print vm.name
   vmfound=True
 if not vmfound:print "No matching vms found"
 sys.exit(0)

#REPORT 
if summary:
 nodcs=[]
 clusters=api.clusters.list()
 clusters=api.clusters.list()
 datacenters=api.datacenters.list()
 hosts=api.hosts.list()
 for ds in datacenters: 
  print "Datacenter: %s Type: %s Status: %s" % (ds.name,ds.storage_type,ds.get_status().get_state())
  for s in ds.storagedomains.list():#stor.get_status().get_state()
   if s.get_status().get_state()=="active":
    used=s.get_used()/1024/1024/1024
    available=s.get_available()/1024/1024/1024
    print "Storage: %s Type: %s Status: %s Total space: %sGb Available space:%sGb" % (s.name,s.get_type(),s.get_status().get_state(),used+available,available)
   else:
    print "Storage: %s Type: %s Status: %s Total space: N/A Available space:N/A" % (s.name,s.get_type(),s.get_status().get_state())
  for clu  in clusters:
   if not clu.get_data_center():
    if clu not in nodcs:nodcs.append(clu)
    continue
   cludc=api.datacenters.get(id=clu.get_data_center().get_id()).get_name()
   if cludc != ds.get_name():continue
   print "Cluster: %s" % (clu.name)
   for net in clu.networks.list():
    if net.get_display():
     print "Network: %s  (Set as display network)" % net.name
    else:
     print "Network: %s " % net.name
   for h in hosts:
    #print "Host: %s Cpu: %s Memory:%sGb" % (h.name,h.cpu.name,h.memory/1024/1024/1024)
    cluh=api.clusters.get(id=h.get_cluster().get_id()).get_name()
    if cluh == clu.name:print "Host: %s Cpu: %s" % (h.name,h.cpu.name)
  print "\n" 
 #handles clusters with no associated DC
 if len(nodcs)>0:
  print "Datacenter: N/A"
  for clu in nodcs:
   print "Cluster: %s" % (clu.name)
   for net in clu.networks.list():
    if net.get_display():
     print "Network: %s  (Set as display network)" % net.name
    else:
     print "Network: %s " % net.name
   for h in hosts:
    cluh=api.clusters.get(id=h.get_cluster().get_id()).get_name()
    if cluh == clu.name:print "Host: %s Cpu: %s" % (h.name,h.cpu.name)
 sys.exit(0)


if template:
 if len(args) != 1:
  print "Usage:ovirt.py -5 template name"
  sys.exit(0)
 temp=api.templates.get(name=template)
 if not temp:
  print "Template %s not found..." % (template)
  print "Existing templates:"
  templates=api.templates.list()
  for temp in templates:
   if temp.get_name()!="Blank":print "%s" % (temp.get_name())
  sys.exit(0)
 else:
  name=args[0]
  clu=temp.get_cluster()
  api.vms.add(params.VM(name=name,cluster=clu,template=temp))
  print "VM %s deployed from %s" % (name,template)
  if mac1:
   while api.vms.get(name).status.state!="down":
    print "Waiting for VM to be down to upgrade mac..."
    time.sleep(5) 
   for nic in api.vms.get(name).nics.list():
    if not ":" in mac1:mac1="%s%s" % (nic.mac.address[:-2],mac1)
    nic.mac.address=mac1
    nic.update()
    print "Mac updated"
    break
 sys.exit(0)

if len(args) == 1 and not new:
 name=args[0]
 vm=api.vms.get(name=name)
 if not vm:
  print "VM %s not found.Leaving..." % name
  sys.exit(1)
 if runonce and not new:
  if api.vms.get(name).status.state=="up" or api.vms.get(name).status.state=="powering_up":
   print "VM allready started"
  else:
   action=params.Action()
   if kernel and initrd and cmdline:
    action.vm=params.VM(os=params.OperatingSystem(kernel=kernel,initrd=initrd,cmdline=cmdline))
   elif iso:
    iso=checkiso(api,iso)
    boot1 = params.Boot(dev="cdrom")
    boot2 = params.Boot(dev="hd")
    cdrom=params.CdRom(file=iso)
    vm.cdroms.add(cdrom)
    vm.update()
    action.vm=params.VM(os=params.OperatingSystem(boot=[boot1,boot2]))
   elif boot:
    boot=boot.split(",")
    boot1=boot[0]
    if len(boot) !=2:
     boot2=None
    else:
     boot2=boot[1]
    if boot1==boot2:
     print "Same boot options provided"
     sys.exit(1)
    if boot1 not in ["hd","cdrom","network"] or boot2 not in ["hd","cdrom","network",None]:
     print "incorrect boot options provided.Leaving..."
     sys.exit(1)
    boot1 = params.Boot(dev=boot1)
    boot2 = params.Boot(dev=boot2)
    action.vm=params.VM(os=params.OperatingSystem(boot=[boot1,boot2]))
   else:
    print "No special options passed for runonce.Leaving..."
    sys.exit(0)
   api.vms.get(name).start(action=action)
   print "VM %s started in runonce mode" % name
  sys.exit(0)
 if kill:
  if cobbler:
   s = xmlrpclib.Server("http://%s/cobbler_api" % cobblerhost)
   token = s.login(cobbleruser,cobblerpassword)
   system=s.find_system({"name":name})
   if system==[]:
    print "%s not found in cobbler...Not doing anything at this level" % (name)
   else:
    s.remove_system(name,token)
    s.sync(token)
    print "%s sucessfully killed in %s" % (name,cobblerhost)
  if not forcekill:
   sure=raw_input("Confirm you want to destroy VM %s:(y/N)" % name)
   if sure!="Y":
    print "Not doing anything"
    sys.exit(1)
  if api.vms.get(name).status.state=="up" or api.vms.get(name).status.state=="powering_up":
   api.vms.get(name).stop()
   print "VM %s stopped" % name
  api.vms.get(name).delete() 
  print "VM %s killed" % name
  sys.exit(0)
 if stop:
  if api.vms.get(name).status.state=="down":
   print "VM allready stopped"
   sys.exit(0)
  api.vms.get(name).stop() 
  print "VM %s stopped" % name
 if migrate:
  if host:
   host=api.hosts.get(name=host)
   if host:
    action=params.Action()
    action.host=host
    vm.migrate(action=action)
  else:
   vm.migrate()
  print "VM s migration launched"
 if isoquit:
  for cd in vm.cdroms.list():cd.delete()
  vm.update()
  print "Removed iso from VM"
 if iso:
  isofound=False
  isodomains=[]
  for sd in api.storagedomains.list():
   if sd.get_type()=="iso":isodomains.append(sd)
  if len(isodomains)==0:
   print "No iso domain found.Leaving..."
   sys.exit(1)
  for sd in isodomains:
   for f in sd.files.list():
    if f.get_id()==iso: 
     isofound=True
     cdrom=params.CdRom(vm=vm,file=f)
     vm.cdroms.add(cdrom)
     vm.update()
     print "Added iso %s from Isodomain %s" % (iso,sd.get_name())
  if not isofound:
   print "Iso not available.Leaving..."
   sys.exit(1)
 if boot:
  boot=boot.split(",")
  boot1=boot[0]
  if len(boot) !=2:
   boot2=None
  else:
   boot2=boot[1]
  if boot1==boot2:
   print "Same boot options provided"
   sys.exit(1)
  if boot1 not in ["hd","cdrom","network"] or boot2 not in ["hd","cdrom","network",None]:
   print "incorrect boot options provided.Leaving..."
   sys.exit(1)
  boot1 = params.Boot(dev=boot1)
  boot2 = params.Boot(dev=boot2)
  vm.os.boot = [ boot1, boot2 ]
  print "boot options correctly changed for %s" % (name)
  vm.update()
 if reset:
  vm.os.kernel,vm.os.initrd,vm.os.cmdline="","",""
  vm.update()
  print "kernel options resetted for %s" % (name)
 if kernel: 
  vm.os.kernel=kernel
  vm.update()
  print "kernel correctly changed for %s" % (name)
 if initrd:
  vm.os.initrd=initrd
  vm.update()
  print "initrd correctly changed for %s" % (name)
 if cmdline:
  vm.os.cmdline=cmdline
  vm.update()
  print "cmdline correctly changed for %s" % (name)
 if extra:
  vm.os.cmdline="%s %s" % (vm.os.cmdline,extra)
  vm.update()
  print "extra cmdline correctly changed for %s" % (name)
 if tags:
  tags=tags.split(",")
  for tag in tags:
   tagfound=False
   for tg  in api.tags.list():
    if tg.get_name()==tag:
     tagfound=True
     vm.tags.add(tg)
     vm.update()
     print "Tag %s added to %s" % (tag,name)
     sys.exit(0)
   if not tagfound:
    print "Tag not available..."
    sure=raw_input("Do you want me to create tag %s and add it to vm %s:(y/N)" % (tag,name))
    if sure!="Y":
     print "Not doing anything"
     sys.exit(1)
    tag = params.Tag(name=tag)
    api.tags.add(tag)
    print "Tag %s added..." % (tag.get_name())
    vm.tags.add(tag)
    vm.update()
    print "Tag %s added to %s" % (tag,name)
 if deletetag:
  tags=vm.tags.list()
  for tag in tags:
   if tag.get_name()==deletetag: 
    tag.delete()
    print "Tag %s removed from %s" % (deletetag,name)
 if guestid:
  vm.os.type_=guestid
  vm.update()
  print "Guestid set to %s for %s" % (guestid,name)
  sys.exit(0)
 if adddisk:
  #clu=api.clusters.get(name=clu)
  if not storagedomain:
   print "No Storage Domain specified"
   sys.exit(1)
  else:
   if not disksize and not disksize2:
    print "No Disksize specified"
    sys.exit(1)
   if diskformat=="raw":sparse=False
   storagedomain=api.storagedomains.get(name=storagedomain)
   api.vms.get(name).disks.add(params.Disk(storage_domains=params.StorageDomains(storage_domain=[storagedomain]),size=adddisk,type_="data",status=None,interface=diskinterface,format=diskformat,sparse=sparse,bootable=False))
   print "Disk with size %d GB added" % (adddisk/1024/1024/1024)
 if start: 
  if api.vms.get(name).status.state=="up" or api.vms.get(name).status.state=="powering_up":
   print "VM allready started"
  else:
   if host:
    hostname=host
    host=api.hosts.get(name=host)
    action=params.Action()
    placement_policy=params.VmPlacementPolicy(host=host)
    action.vm=params.VM(placement_policy=placement_policy)
    api.vms.get(name).start(action=action) 
    print "VM %s started on %s" % (name,hostname)
   else:
    api.vms.get(name).start()
    print "VM %s started" % name
 if restart:
  if api.vms.get(name).status.state!="down":api.vms.get(name).stop() 
  api.vms.get(name).start() 
  print "VM %s restarted" % name
 vm=api.vms.get(name=name)
 if not vm:
  print "VM %s not found.Leaving..." % name
  sys.exit(1)
 print "Name: %s" % vm.name
 print "Uid: %s" % vm.get_id()
 host=vm.get_host()
 if host:
  hostid=host.get_id()
  print "Host: %s" % api.hosts.get(id=hostid).get_name()
 print "Boot1: %s" % (vm.os.boot[0].get_dev())
 if len(vm.os.boot)==2:
  print "Boot2: %s" % (vm.os.boot[1].get_dev())
 for cdrom in vm.get_cdroms().list():
  if cdrom.get_file():print "Cdrom: %s" % cdrom.get_file().get_id()
 if vm.os.kernel or vm.os.initrd or vm.os.cmdline:
  print "Kernel: %s Initrd:%s Cmdline:%s" % (vm.os.kernel,vm.os.initrd,vm.os.cmdline)
 print "Status: %s" % vm.status.state
 print "Os: %s" % vm.get_os().get_type()
 if vm.status.state=="up":
  host=findhostbyid(api,vm.get_host().get_id())
  print "Host: %s" % host
 print "Cpu: %s sockets:%s" % (vm.cpu.topology.cores,vm.cpu.topology.sockets)
 if vm.status.state=="up":
  for info in vm.get_statistics().list(): 
   if info.get_description()=="CPU used by guest" or info.get_description()=="Memory used (agent)":
    for i in info.get_values().get_value():value=i.get_datum()
    print "%s: %s" % (info.get_description(),value)
 memory=vm.memory/1024/1024
 print "Memory: %dMb" % memory
 for disk in vm.disks.list():
   size=disk.size/1024/1024/1024
   #for stor in disk.get_storage_domains().get_storage_domain():print stor.name
   print "diskname: %s disksize: %sGB diskformat: %s thin: %s status: %s" % (disk.name,size,disk.format,disk.sparse,disk.get_status().get_state())
 for nic in vm.nics.list():
  net=api.networks.get(id=nic.network.id).get_name()
  print "net interfaces: %s mac: %s net: %s type: %s " % (nic.name,nic.mac.address,net,nic.interface)
 for tag in vm.get_tags().list():
   print "Tags: %s" % tag.get_name()
 if vm.get_custom_properties():
  for custom in vm.get_custom_properties().get_custom_property():
   print "Custom Property: %s Value: %s" % (custom.get_name(),custom.get_value())
 if console:
  if vm.status.state=="down":
   print "Machine down"
   sys.exit(1)
  while api.vms.get(name=name).status.state=="wait_for_launch":
   print "Waiting for machine to be up..."
   time.sleep(5)
  if not oca or not os.path.exists(oca):
   print " CA cert file is required in order to connect to console.Get it from http://${OVIRT}/ca.crt, keep only the CERTIFICATE part and define its path in ovirt.ini"
   sys.exit(1)
  if not oorg:
   print "Define your org in ovirt.ini"
   sys.exit(1)
  vm=api.vms.get(name=name)
  print dir(vm.get_display())
  sys.exit(0)
  vm.ticket().set_ticket("")
  ticket=vm.ticket().get_ticket().get_value()
  address,port,sport=vm.get_display().get_address(),vm.get_display().get_port(),vm.get_display().get_secure_port()
  id=vm.get_host().get_id()
  realaddress=getip(api,vm.get_host().get_id())
  subject="%s,CN=%s" % (oorg,realaddress)
  print "Password copied to clipboard:	%s" % ticket
  #copy to clipboard
  if os.environ.has_key("KDE_FULL_SESSION") or os.environ.has_key("KDEDIRS"):
   os.popen("qdbus org.kde.klipper /klipper setClipboardContents %s" % ticket)
  else:
   os.popen("xsel", "wb").write(ticket)
  protocol=vm.get_display().get_type()
  if protocol=="spice":
   os.popen("remote-viewer --spice-ca-file %s --spice-host-subject '%s' spice://%s/?port=%s\&tls-port=%s &" %  (oca,subject,address,port,sport))
  elif protocol=="vnc":
   os.popen("remote-viewer vnc://%s:%s &" %  (address,port))
 sys.exit(0)

#parse profile for specific client
clientfile="%s/%s.ini" % (os.environ['HOME'],client)
if not os.path.exists(clientfile):
 print "You need to create a %s.ini in your homedirectory.Check documentation" % client
 sys.exit(1)
try:
 c = ConfigParser.ConfigParser()
 c.read(clientfile)
 profiles={}
 for prof in c.sections():
  for option in  c.options(prof):
   if not profiles.has_key(prof):
    profiles[prof]={option : c.get(prof,option)}
   else:
    profiles[prof][option]=c.get(prof,option)
except:
 print ERR_CLIENTNOPROFILE

if listprofiles:
 print "Use one of the availables profiles:"
 for profile in sorted(profiles.keys()): print profile
 sys.exit(0)


if not new:
 print "No or non-existent arguments given...Leaving"
 sys.exit(0)
if len(args) == 1:name=args[0]
if not name:name=raw_input("enter machine s name:\n")
if cobbler:
 s = xmlrpclib.Server("http://%s/cobbler_api" % cobblerhost)
 token = s.login(cobbleruser,cobblerpassword)
 system=s.find_system({"name":name})
 if system!=[]:
  print "%s allready defined in cobbler...Use the following command if you plan to reinstall this machine:" % (name)
  print "%s -ZK %s -C %s" % (sys.argv[0],name,client)
  sys.exit(0)

if not profile:
 print "Choose a profile for your machine:"
 #propose available profiles
 for prof in profiles.keys():print prof
 profile=raw_input()
#check if profile is within our keys or exit
if not profiles.has_key(profile):
 print "Invalid profile"
 sys.exit(0)

#grab all conf from profile 
if profiles[profile].has_key("clu"):clu=profiles[profile]["clu"]
if profiles[profile].has_key("numinterfaces"):numinterfaces=int(profiles[profile]["numinterfaces"])
if profiles[profile].has_key("boot1"):boot1=profiles[profile]["boot1"]
if profiles[profile].has_key("boot2"):boot2=profiles[profile]["boot2"]
if profiles[profile].has_key("iso"):iso=profiles[profile]["iso"]
if profiles[profile].has_key("storagedomain"):storagedomain=profiles[profile]["storagedomain"]
if profiles[profile].has_key("netinterface"):netinterface=profiles[profile]["netinterface"]
if profiles[profile].has_key("diskinterface"):netinterface=profiles[profile]["diskinterface"]
if profiles.has_key("disksize"):disksize=int(profiles[profile]["disksize"])*GB
if not guestid and profiles[profile].has_key("guestid"):guestid=profiles[profile]["guestid"]
if not tags and profiles[profile].has_key("tags"):tags=profiles[profile]["tags"]
if not kernel and profiles[profile].has_key("kernel"):kernel=profiles[profile]["kernel"]
if not initrd and profiles[profile].has_key("initrd"):initrd=profiles[profile]["initrd"]
if not cmdline and profiles[profile].has_key("cmdline"):cmdline=profiles[profile]["cmdline"]
if not runonce and profiles[profile].has_key("runonce"):runonce=True

if extra:cmdline="%s %s" %(cmdline,extra)
#grab nets 
if numinterfaces == 1:
 net1=profiles[profile]['net1']
 if installnet:
  nets=[installnet]
 else:
  nets=[net1]
elif numinterfaces == 2:
 net1=profiles[profile]['net1']
 net2=profiles[profile]['net2']
 if installnet:
  nets=[net1,installnet]
 else:
  nets=[net1,net2]
#cluster machines
elif numinterfaces == 3:
 net1=profiles[profile]['net1']
 net2=profiles[profile]['net2']
 net3=profiles[profile]['net3']
 if installnet:
  nets=[net1,installnet,net3]
 else:
  nets=[net1,net2,net3]


#VM CREATION IN OVIRT
 
try:
#TODO check that clu and storagedomain exist and that there is space there
 if memory2:memory=memory2
 if disksize2:disksize=disksize2
 if not memory or not disksize:
  print "Missing memory or disk info for VM %s. Wont be created" % name
  os._exit(1)
 if diskformat=="raw":sparse=False
 vm=api.vms.get(name=name)
 if vm:
  print "VM %s allready existing.Leaving..." % name
  os._exit(1)
 clu=api.clusters.get(name=clu)
 storagedomain=api.storagedomains.get(name=storagedomain)
 #boot order
 boot=[params.Boot(dev=boot1),params.Boot(dev=boot2)]
 #vm creation
 #if runonce specified,dont put kernelopts in VM definition, but rather at launch time
 if runonce:
  kernel2,initrd2,cmdline2=kernel,initrd,cmdline 
  kernel,initrd,cmdline=None,None,None
 api.vms.add(params.VM(name=name, memory=memory, cluster=clu, template=api.templates.get('Blank'),os=params.OperatingSystem(type_=guestid,boot=boot,kernel=kernel,initrd=initrd,cmdline=cmdline),cpu=params.CPU(topology=params.CpuTopology(cores=numcpu)),type_="server"))
 #add nics
 api.vms.get(name).nics.add(params.NIC(name='eth0', network=params.Network(name=net1), interface=netinterface))
 if mac1:
  for nic in api.vms.get(name).nics.list():
   if not ":" in mac1:mac1="%s%s" % (nic.mac.address[:-2],mac1)
   nic.mac.address=mac1
   nic.update()
   break
 if numinterfaces>=2:api.vms.get(name).nics.add(params.NIC(name='eth1', network=params.Network(name=net2), interface=netinterface))
 if numinterfaces>=3:api.vms.get(name).nics.add(params.NIC(name='eth2', network=params.Network(name=net3), interface=netinterface))
 if iso:
  iso=checkiso(api,iso)
  cdrom=params.CdRom(file=iso)
  api.vms.get(name).cdroms.add(cdrom)
 if tags:
  tags=tags.split(",")
  for tag in tags: 
   for tg  in api.tags.list():
    if tg.get_name()==tag:
     tagfound=True
     api.vms.get(name).tags.add(tg)
 api.vms.get(name).update()
 #add disks
 api.vms.get(name).disks.add(params.Disk(storage_domains=params.StorageDomains(storage_domain=[storagedomain]),size=disksize,type_='system',status=None,interface=diskinterface,format=diskformat,sparse=sparse,bootable=True))
 print "VM %s created" % name
 if cobbler:
  #retrieve MACS for cobbler
  vm=api.vms.get(name=name)
  for nic in vm.nics.list():
   macaddr.append(nic.mac.address)
except:
 print "Failure creating VM"
 os._exit(1)


#VM CREATION IN COBBLER
#grab ips and extra routes for cobbler

if cobbler:
 if profiles[profile].has_key("nextserver"):nextserver=profiles[profile]['nextserver']
 if profiles[profile].has_key("gwbackup"):gwbackup=profiles[profile]['gwbackup']
 if profiles[profile].has_key("gwstatic"):gwstatic=profiles[profile]['gwstatic']
 if profiles[profile].has_key("staticroutes"):staticroutes=profiles[profile]['staticroutes']
 if profiles[profile].has_key("subnet1"):subnet1=profiles[profile]['subnet1']
 if profiles[profile].has_key("subnet2"):subnet2=profiles[profile]['subnet2']
 if profiles[profile].has_key("subnet3"):subnet3=profiles[profile]['subnet3']
 if numinterfaces == 1:
  if not subnet1:
   print "Missing subnet in client ini file.Check documentation"
   sys.exit(1)
  if not ip1:ip1=raw_input("Enter first ip:\n")
 elif numinterfaces == 2:
  if not subnet1 or not subnet2:
   print "Missing subnet in client ini file.Check documentation"
   sys.exit(1)
  if not ip1:ip1=raw_input("Enter first ip:\n")
  if not ip2:ip2=raw_input("Enter second ip:\n")
 #cluster machines
 elif numinterfaces == 3:
  if not subnet1 or not subnet2 or not subnet3:
   print "Missing subnet in client ini file.Check documentation"
   sys.exit(1)
  if not ip1:ip1=raw_input("Enter first service ip:\n")
  if not ip2:ip2=raw_input("Enter second ip:\n")
  if not ip3:ip3=raw_input("Enter third ip:\n")
 if gwstatic and staticroutes:staticroutes=staticroutes.replace(",",":%s " % gwstatic)+":"+gwstatic
 if gwbackup and backuproutes:
  backuproutes=backuproutes.replace(",",":%s " % gwbackup)+":"+gwbackup
  staticroutes="%s %s" % (staticroutes,backuproutes)

 #3-create cobbler system 
 system = s.new_system(token)
 s.modify_system(system,'name',name,token)
 s.modify_system(system,'hostname',name,token)
 s.modify_system(system,'profile',profile,token)
 #if nextserver:s.modify_system(system,'server',nextserver,token)
 if numinterfaces==1:
  if staticroutes:
   eth0={"macaddress-eth0":macaddr[0],"static-eth0":1,"ipaddress-eth0":ip1,"subnet-eth0":subnet1,"staticroutes-eth0":staticroutes}
  else:
   eth0={"macaddress-eth0":macaddr[0],"static-eth0":1,"ipaddress-eth0":ip1,"subnet-eth0":subnet1}
  s.modify_system(system,'modify_interface',eth0,token)
 elif numinterfaces==2:
  eth0={"macaddress-eth0":macaddr[0],"static-eth0":1,"ipaddress-eth0":ip1,"subnet-eth0":subnet1}
  if staticroutes:
   eth1={"macaddress-eth1":macaddr[1],"static-eth1":1,"ipaddress-eth1":ip2,"subnet-eth1":subnet2,"staticroutes-eth1":staticroutes}
  else:
   eth1={"macaddress-eth1":macaddr[1],"static-eth1":1,"ipaddress-eth1":ip2,"subnet-eth1":subnet2}
  s.modify_system(system,'modify_interface',eth0,token)
  s.modify_system(system,'modify_interface',eth1,token)
 elif numinterfaces==3:
  eth0={"macaddress-eth0":macaddr[0],"static-eth0":1,"ipaddress-eth0":ip1,"subnet-eth0":subnet1}
  if staticroutes:
   eth1={"macaddress-eth1":macaddr[1],"static-eth1":1,"ipaddress-eth1":ip2,"subnet-eth1":subnet2,"staticroutes-eth1":staticroutes}
  else:
   eth1={"macaddress-eth1":macaddr[1],"static-eth1":1,"ipaddress-eth1":ip2,"subnet-eth1":subnet2}
  eth2={"macaddress-eth2":macaddr[2],"static-eth2":1,"ipaddress-eth2":ip3,"subnet-eth2":subnet3}
  s.modify_system(system,'modify_interface',eth0,token)
  s.modify_system(system,'modify_interface',eth1,token)
  s.modify_system(system,'modify_interface',eth2,token)
 s.save_system(system,token)
 s.sync(token)
 print "VM %s created in cobbler" % name

if nolaunch and runonce:
 print "Both runonce and nolaunch specified for VM...nonsense!"
 sys.exit(0)
if not nolaunch:
 while api.vms.get(name).status.state =="image_locked":
  print "Waiting For image to be unlocked..."
  time.sleep(5) 
 for disk in api.vms.get(name).disks.list():
  while disk.get_status().get_state()=="Locked" or disk.get_status().get_state()=="locked":
   print "disk still in %s state" % disk.get_status().get_state()
   time.sleep(5) 
 #at this point,VM is ready to be started
 if runonce:
  action=params.Action()
  action.vm=params.VM(os=params.OperatingSystem(kernel=kernel2,initrd=initrd2,cmdline=cmdline2))
  api.vms.get(name).start(action=action)
 else:
  api.vms.get(name).start()
 print "VM %s started" % name

sys.exit(0)
