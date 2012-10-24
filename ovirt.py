#!/usr/bin/python
"""
script to create virtual machines on Ovirt
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
__version__ = "1.0"
__maintainer__ = "Karim Boumedhel"
__email__ = "karim.boumedhel@gmail.com"
__status__ = "Production"

ERR_NOOVIRTFILE="You need to create a correct ovirt.ini file in your home directory.Check documentation"
ERR_NOCOBBLERFILE="You need to create a correct cobbler.ini file in your home directory.Check documentation"
ERR_CLIENTNOTFOUND="Client not found"
ERR_CLIENTNOCONF="Client not found in conf file"
ERR_CLIENTNOPROFILE="You need to create an ini file for all clients with defined profiles.Check documentation"

usage="script to create virtual machines on Ovirt"
version="1.0"
parser = optparse.OptionParser("Usage: %prog [options] vmname")
parser.add_option("-c", "--cpu", dest="numcpu", type="int", help="Specify Number of CPUS")
parser.add_option("-f", "--diskformat", dest="diskformat", type="string", help="Specify Disk mode.Can be raw or cow")
parser.add_option("-l", "--listprofiles", dest="listprofiles", action="store_true", help="list available profiles")
parser.add_option("-m", "--memory", dest="memory", type="int", help="Specify Memory, in Mo")
parser.add_option("-n", "--new", dest="new",action="store_true", help="Create new VM")
parser.add_option("-b", "--bad", dest="bad",action="store_true", help="If set,treat all actions as not for a linux guest,meaning net interfaces will be of type e1000 and disk of type ide.Necessary for windows or solaris guests")
parser.add_option("-p", "--profile", dest="profile",type="string", help="specify Profile")
parser.add_option("-s", "--size", dest="disksize", type="int", help="Specify Disk size,in Go at VM creation")
parser.add_option("-a", "--adddisk", dest="adddisk", type="int", help="Specify Disk size,in Go to add")
parser.add_option("-C", "--client", dest="client", type="string", help="Specify Client")
parser.add_option("-D", "--storagedomain" , dest="storagedomain", type="string", help="Specify Domain")
parser.add_option("-F", "--forcekill", dest="forcekill", action="store_true", help="Dont ask confirmation when killing a VM")
parser.add_option("-K", "--kill", dest="kill", action="store_true" , help="specify VM to kill in virtual center.Confirmation will be asked unless -F/--forcekill flag is set.VM will also be killed in cobbler server if -Z/-cobbler flag set")
parser.add_option("-E", "--cluster", dest="clu", type="string", help="Specify Cluster")
parser.add_option("-H", "--listhosts", dest="listhosts", action="store_true", help="list hosts")
parser.add_option("-L", "--listclients", dest="listclients", action="store_true", help="list available clients")
parser.add_option("-M", "--listvms", dest="listvms", action="store_true", help="list all vms")
parser.add_option("-R", "--report", dest="report", action="store_true", help="Report about ovirt")
parser.add_option("-S", "--start", dest="start", action="store_true", help="Start VM")
parser.add_option("-T", "--thin", dest="thin", action="store_true", help="Use thin provisioning for disk")
parser.add_option("-W", "--stop", dest="stop", action="store_true", help="Stop VM")
parser.add_option("-X", "--search" , dest="search", type="string", help="Search VMS")
parser.add_option("-Y", "--nolaunch", dest="nolaunch", action="store_true", help="Dont Launch VM,just create it")
parser.add_option("-Z", "--cobbler", dest="cobbler", action="store_true", help="Cobbler support")
parser.add_option("-1", "--ip1", dest="ip1", type="string", help="Specify First IP")
parser.add_option("-2", "--ip2", dest="ip2", type="string", help="Specify Second IP")
parser.add_option("-3", "--ip3", dest="ip3", type="string", help="Specify Third IP")
parser.add_option("-N", "--numinterfaces", dest="numinterfaces", type="int", help="Specify number of net interfaces")
parser.add_option("-O", "--console", dest="console", action="store_true", help="Get a console")

MB = 1024*1024
GB = 1024*MB
(options, args) = parser.parse_args()
staticroutes=None
backuproutes=None
gwbackup=None
clients=[]
client = options.client
listclients = options.listclients
listhosts = options.listhosts
listvms = options.listvms
listprofiles = options.listprofiles
new=options.new
cobbleruser=None
cobblermac=None
diskformat = options.diskformat
disksize = options.disksize
ip1=options.ip1
ip2=options.ip2
ip3=options.ip3
memory = options.memory
start=options.start
stop=options.stop
report=options.report
numcpu = options.numcpu
thin=options.thin
kill=options.kill
forcekill=options.forcekill
clu=options.clu
storagedomain=options.storagedomain
adddisk=options.adddisk
bad=options.bad
cobbler=options.cobbler
nolaunch=options.nolaunch
search=options.search
profile = options.profile
console = options.console
installnet=None
numinterfaces=options.numinterfaces
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

if adddisk:adddisk=adddisk*GB
ohost,oport,ouser,opassword,ossl,oca,org=None,None,None,None,None,None,None
#thin provisioning
sparse=True
if bad:
 diskinterface,netinterface="ide","e1000"
else:
 diskinterface,netinterface="virtio","virtio"

if len(args)!=1 and new:
 print "Usage: %prog [options] vmname"
 sys.exit(1)

if os.path.exists("ovirt.ini"):
 ovirtconffile="ovirt.ini"
else:
 ovirtconffile=os.environ['HOME']+"/ovirt.ini"
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
 if not disksize and default.has_key("disksize"):disksize=int(default["disksize"])*GB
 if not memory and default.has_key("memory"):memory=int(default["memory"])*MB
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
 if ovirts[client].has_key("numcpu"):numcpu=int(ovirts[client]["numcpu"])
 if ovirts[client].has_key("diskformat"):diskformat=ovirts[client]["diskformat"]
 if ovirts[client].has_key("disksize"):disksize=int(ovirts[client]["disksize"])*GB
 if ovirts[client].has_key("memory"):memory=int(ovirts[client]["memory"])*MB
 if ovirts[client].has_key("storagedomain"):storagedomain=ovirts[client]["storagedomain"]
 if ovirts[client].has_key("numinterfaces"):numinterfaces=int(ovirts[client]["numinterfaces"])
 if ovirts[client].has_key("ssl"):ossl=True
 if ovirts[client].has_key("ca"):oca=ovirts[client]["ca"]
 if ovirts[client].has_key("org"):oorg=ovirts[client]["org"]
except KeyError,e:
 print "Problem parsing your ini file:Missing parameter %s" % e
 os._exit(1)

#TODO:check necessary parameters exist for a valid ovirt connection or exits
#if not ohost or not oport or not ouser or not opassword or not ossl or not clu or not numcpu or not diskformat or not disksize or not memory or not storagedomain or not numinterfaces:
# print "Missing parameters for ovirt"
# sys.exit(1)

#parse cobbler client auth file
if cobbler and client:
 if os.path.exists("cobbler.ini"):
  cobblerconffile="cobbler.ini"
 else:
  cobblerconffile=os.environ['HOME']+"/cobbler.ini"
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
if report:
 clusters=api.clusters.list()
 clusters=api.clusters.list()
 datacenters=api.datacenters.list()
 hosts=api.hosts.list()
 stores=api.storagedomains.list()
 print "Datacenters:"
 for ds in datacenters:
  print "Datacenter: %s Type: %s " % (ds.name,ds.storage_type)
 print "Clusters and Networks:"
 for clu  in clusters:
  print "Cluster: %s " % clu.name
  for net in clu.networks.list():print "Network: %s " % net.name
 print "Hosts:"
 for h in hosts:
  #print "Host: %s Cpu: %s Memory:%sGb" % (h.name,h.cpu.name,h.memory/1024/1024/1024)
  print "Host: %s Cpu: %s" % (h.name,h.cpu.name)
 print "Storage:"
 for s in stores:
  used=s.get_used()/1024/1024/1024
  available=s.get_available()/1024/1024/1024
  print "Storage: %s Type: %s Total space: %sGb Available space:%sGb" % (s.name,s.get_type(),used+available,available)
 sys.exit(0)


if len(args) == 1 and not new:
 name=args[0]
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
  vm=api.vms.get(name=name)
  if not vm:
   print "VM %s not found.Leaving..." % name
   sys.exit(1)
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
 if start: 
  if api.vms.get(name).status.state=="up":
   print "VM allready started"
   sys.exit(0)
  api.vms.get(name).start() 
  print "VM %s started" % name
  sys.exit(0)
 if stop:
  if api.vms.get(name).status.state=="down":
   print "VM allready stopped"
   sys.exit(0)
  api.vms.get(name).stop() 
  print "VM %s stopped" % name
  sys.exit(0)
 if adddisk:
  #clu=api.clusters.get(name=clu)
  if not storagedomain:
   print "No Storage Domain specified"
   sys.exit(1)
  else:
   storagedomain=api.storagedomains.get(name=storagedomain)
  api.vms.get(name).disks.add(params.Disk(storage_domains=params.StorageDomains(storage_domain=[storagedomain]),size=adddisk,type_="data",status=None,interface=diskinterface,format=diskformat,sparse=sparse,bootable=False))
  print "Disk with size %d GB added" % (adddisk/1024/1024/1024)
  _sys.exit(0)
 vm=api.vms.get(name=name)
 if not vm:
  print "VM %s not found.Leaving..." % name
  sys.exit(1)
 print "Name: %s" % vm.name
 print "Status: %s" % vm.status.state
 print "OS: %s" % vm.get_os().get_type()
 host=findhostbyid(api,vm.get_host().get_id())
 print "HOST: %s" % host
 print "CPU: %s sockets:%s" % (vm.cpu.topology.cores,vm.cpu.topology.sockets)
 memory=vm.memory/1024/1024
 print "Memory: %dMb" % memory
 for disk in vm.disks.list():
   size=disk.size/1024/1024/1024
   print "diskname: %s disksize: %sGB diskformat: %s thin: %s" % (disk.name,size,disk.format,disk.sparse)
 for nic in vm.nics.list():
  print "net interfaces: %s mac: %s net: %s type: %s " % (nic.name,nic.mac.address,nic.network.id,nic.interface)
 if console:
  if not oca or not os.path.exists(oca):
   print "a CA file is required in order to connect to console.Define one in ovirt.ini"
   sys.exit(1)
  if not oorg:
   print "Define your org in ovirt.ini"
   sys.exit(1)
  vm.ticket().set_ticket("")
  ticket=vm.ticket().get_ticket().get_value()
  address,port,sport=vm.get_display().get_address(),vm.get_display().get_port(),vm.get_display().get_secure_port()
  id=vm.get_host().get_id()
  realaddress=getip(api,vm.get_host().get_id())
  subject="%s,CN=%s" % (oorg,realaddress)
  print "Password:      %s" % ticket
  os.popen("remote-viewer --spice-ca-file %s --spice-host-subject '%s' spice://%s/?port=%s\&tls-port=%s" %  (oca,subject,address,port,sport))
 sys.exit(0)

#parse profile for specific client
if not os.path.exists("%s.ini" % client):
 print "You need to create a %s.ini within this directory.Check documentation" % client
 sys.exit(1)
try:
 conffile="%s.ini" % client
 c = ConfigParser.ConfigParser()
 c.read(conffile)
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
clu=profiles[profile]['clu']
if profiles[profile].has_key("guestid"):guestid=profiles[profile]['guestid']
if profiles[profile].has_key("numinterfaces"):numinterfaces=int(profiles[profile]['numinterfaces'])

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
 vm=api.vms.get(name=name)
 if vm:
  print "VM %s allready existing.Leaving..." % name
  os._exit(1)
 clu=api.clusters.get(name=clu)
 storagedomain=api.storagedomains.get(name=storagedomain)
 #api.vms.add(params.VM(name=name, memory=memory, cluster=clu, template=api.templates.get('Blank')))
 api.vms.add(params.VM(name=name, memory=memory, cluster=clu, template=api.templates.get('Blank'),os=params.OperatingSystem(type_=guestid),cpu=params.CPU(topology=params.CpuTopology(cores=numcpu))))
 #add nics
 api.vms.get(name).nics.add(params.NIC(name='nic1', network=params.Network(name=net1), interface=netinterface))
 if numinterfaces>=2:api.vms.get(name).nics.add(params.NIC(name='nic2', network=params.Network(name=net2), interface=netinterface))
 if numinterfaces>=3:api.vms.get(name).nics.add(params.NIC(name='nic3', network=params.Network(name=net3), interface=netinterface))
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

if not nolaunch:
 while api.vms.get(name).status.state =="image_locked":
  print "Waiting For image to be unlocked..."
  time.sleep(5) 
 api.vms.get(name).start()
 print "VM %s started" % name

#add guestid .not working at the moment...
#if guestid:
# ose=api.vms.get(name).get_os()
# ose.set_type(guestid)
# api.vms.get(name).update()

sys.exit(0)
