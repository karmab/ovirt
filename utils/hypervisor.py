#!/usr/bin/python

import getpass
import xml.etree.ElementTree as ET
import optparse
import os
import re
import sys
sys.path.append("/usr/share/vdsm")
from vdsm import vdscli

version = "0.0"
parser = optparse.OptionParser(
    "Usage: %prog [options] vmname", version=version)
parser.add_option("-c", "--cert", dest="cert", type="string",
                  help="path to the CA cert file required in order to connect to console.Get it from http://${OVIRT}/ca.crt, keep only the CERTIFICATE part")
parser.add_option("-d", "--display", dest="display", type="string", default="ovirtmgmt",
                  help="Display network when launching VM.Defaults to ovirtmgmt")
parser.add_option("-l", "--list", dest="listing",
                  action="store_true", help="List vms")
parser.add_option("-p", "--port", dest="port", default="54321",
                  type="string", help="Port to connect to.Defaults to localhost")
parser.add_option("-o", "--console", dest="console",
                  action="store_true", help="Get console")
parser.add_option("-s", "--start", dest="start",
                  action="store_true", help="start vm")
parser.add_option("-w", "--stop", dest="stop",
                  action="store_true", help="stop vm")
parser.add_option("-H", "--host", dest="host", default="127.0.0.1",
                  type="string", help="Server to connect to.Defaults to localhost")
parser.add_option("-O", "--org", dest="org", type="string",
                  help="Organisation for console mode")
parser.add_option("-S", "--startspm", dest="startspm",
                  action="store_true", help="start SPM role")
parser.add_option("-T", "--truststore", dest="truststore", default="/etc/pki/vdsm",
                  type="string", help="Path containing cert files.Defaults to /etc/pki/vdsm")
parser.add_option("-V", "--vnc", dest="vnc", action="store_true",
                  help="Force VNC protocol when launching a VM")
parser.add_option("-X", "--spice", dest="spice", action="store_true",
                  help="Force SPICE protocol when launching a VM")
parser.add_option("-W", "--stopspm", dest="stopspm",
                  action="store_true", help="stop SPM role")

(options, args) = parser.parse_args()
cert = options.cert
host = options.host
listing = options.listing
display = options.display
# migrate=options.migrate
port = options.port
start = options.start
stop = options.stop
stopspm = options.stopspm
startspm = options.startspm
console = options.console
org = options.org
truststore = options.truststore
spice = options.spice
vnc = options.vnc

# helper functions for ssh based consults


def sshconnect(host):
    username = "root"
    try:
        import paramiko
    except ImportError:
        print "Paramiko s module is required for ssh operations with the SPM"
        print "Either install it or launch the script locally"
        os._exit(1)
    password = getpass.getpass("Enter Root Password for host %s:" % host)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.load_host_keys(os.path.expanduser(
        os.path.join("~", ".ssh", "known_hosts")))
    ssh.connect(host, username=username, password=password)
    return ssh


def sshlist(ssh, directory):
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("ls %s" % directory)
    return ssh_stdout.read()


def sshfile(ssh, path):
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("cat %s" % path)
    return ssh_stdout.read()


def getvminfo(host, vmid, display, root):
    cmd = {}
    cmd["vmId"] = vmid
    # cmd["display"]="qxl"
    cmd["kvmEnable"] = "True"
    cmd["vmType"] = "kvm"
    cmd["tabletEnable"] = "True"
    cmd["vmEnable"] = "True"
    cmd["irqChip"] = "True"
    cmd["nice"] = 0
    cmd["keyboardLayout"] = "en-us"
    cmd["acpiEnable"] = "True"
    cmd["display"] = "qxl"
    cmd["displayIp"] = host
    cmd["spiceMonitors"] = "1"
    cmd["displayNetwork"] = display
    disks = []
    for child in root:
        if child.tag == "Section" and "ovf:DiskSection_Type" in child.attrib.values():
            for disk in child.findall("Disk"):
                for info in disk.attrib:
                    if "boot" in info:
                        diskboot = disk.attrib[info]
                    if "fileRef" in info:
                        diskimageid, diskvolid = disk.attrib[info].split("/")
                    if "volume-format" in info:
                        diskformat = disk.attrib[info].lower()
                disks.append({"boot": diskboot, "volumeID": diskvolid,
                              "imageID": diskimageid, "format": diskformat})

    for content in root.findall("Content"):
        name = content.findall("Name")[0].text
        display = content.findall("DefaultDisplayType")[0].text
        if display != "1"or vnc:
            cmd["display"] = "vnc"
        if spice:
            cmd["display"] = "qxl"
        sections = content.findall("Section")
        for hardware in sections:
            if "ovf:VirtualHardwareSection_Type" in hardware.attrib.values():
                macs = []
                nicnames = []
                bridges = []
                nicmodels = []
                diskdomids = []
                diskpoolids = []
                for item in hardware.findall("Item"):
                    for element in item:
                        if "num_of_sockets" in element.tag:
                            smp = element.text
                        if "cpu_per_socket" in element.tag:
                            cpuspersocket = element.text
                        if "VirtualQuantity" in element.tag:
                            memory = element.text
                        if "AllocationUnits" in element.tag:
                            memoryunits = element.text
                        if "MACAddress" in element.tag:
                            macs.append(element.text)
                        if "Name" in element.tag:
                            nicnames.append(element.text)
                        if "Connection" in element.tag:
                            bridges.append(element.text)
                        if "ResourceSubType" in element.tag:
                            if element.text == "1":
                                nicmodels.append("rtl8139")
                            if element.text == "2":
                                nicmodels.append("e1000")
                            if element.text == "3":
                                nicmodels.append("pv")
                        if "StorageId" in element.tag:
                            diskdomids.append(element.text)
                        if "StoragePoolId" in element.tag:
                            diskpoolids.append(element.text)

    counter = 0
    cmd["drives"] = []
    for disk in disks:
        cmd["drives"].append(disk)
        cmd["drives"][counter]["domainID"] = diskdomids[counter]
        cmd["drives"][counter]["poolID"] = diskpoolids[counter]
        counter = counter + 1

    cmd["memSize"] = memory
    cmd["smpCoresPerSocket"] = cpuspersocket
    cmd["smp"] = smp
    cmd["bridge"] = ",".join(bridges)
    cmd["macAddr"] = ",".join(macs)
    cmd["vmName"] = name
    cmd["nicModel"] = ",".join(nicmodels)
    return cmd

useSSL = True
s = vdscli.connect("%s:%s" % (host, port), useSSL, truststore)

# check if i am spm
try:
    spuid = s.getConnectedStoragePoolsList()["poollist"][0]
    sppath = "/rhev/data-center/%s/mastersd/master/vms" % spuid
    if s.getSpmStatus(spuid)['spm_st']['spmStatus'] == "SPM":
        spm = True
    else:
        spm = False
except:
    spm = False

if listing:
    vms = {}
    vmids = []
    print "VMS running on this host:"
    for vm in s.list(True)["vmList"]:
        vms[vm["vmName"]] = "%s on port %s" % (
            vm["display"], vm["displayPort"])
        vmids.append(vm["vmId"])
    for vm in sorted(vms):
        print "%s using %s" % (vm, vms[vm])
    if spm:
        print "VMS reported by this host,as SPM:\n"
        if host == "127.0.0.1":
            for id in os.listdir(sppath):
                if id in vmids:
                    continue
                tree = ET.parse("%s/%s/%s.ovf" % (sppath, id, id))
                root = tree.getroot()
                for content in root.findall('Content'):
                    name = content.findall("Name")[0].text
                    print "%s" % name
        else:
            ssh = sshconnect(host)
            for id in sshlist(ssh, sppath).split("\n"):
                if id in vmids or id == "":
                    continue
                tree = sshfile(ssh, "%s/%s/%s.ovf" % (sppath, id, id))
                root = ET.fromstring(tree)
                # now we can parse
                for content in root.findall('Content'):
                    name = content.findall("Name")[0].text
                    print "%s" % name
    sys.exit(0)

if stopspm:
    if not spm:
        print "I m not spm anyway"
        sys.exit(0)
    s.spmStop(spuid)
    print "spm role stopped"
    sys.exit(0)

if startspm:
    if spm:
        print "I m already spm"
        sys.exit(0)
    s.spmStart(spuid)
    print "spm role started"
    sys.exit(0)

# once here, a vm is expected
if len(args) != 1:
    print "Usage: %prog [options] vmname"
    sys.exit(0)
elif not start:
    vms = {}
    name = args[0]
    for vm in s.list(True)["vmList"]:
        vms[vm["vmName"]] = {"vmid": vm["vmId"], "vmdisplay": vm[
            "display"], "vmport": vm["displayPort"]}
    if name not in vms:
        print "VM not found.leaving..."
        sys.exit(1)
    else:
        vmid = vm["vmId"]
        vmdisplay = vm["display"]
        vmport = vm["displayPort"]
        vmsport = vm["displaySecurePort"]
        vmip = vm["displayIp"]
        if vmip == "0":
            vmip = "127.0.0.1"

if console:
    if not cert or not org:
        print "You need to use -c cert  and -o org too"
        sys.exit(0)
    ticket = "123"
    s.setVmTicket(vmid, "123", 60)
    subject = "%s,CN=%s" % (org, vmip)
    print "Password copied to clipboard:  %s" % ticket
    # copy to clipboard
    if 'KDE_FULL_SESSION' in os.environ.keys() or 'KDEDIRS' in os.environ.keys():
        os.popen("qdbus org.kde.klipper /klipper setClipboardContents %s" % ticket)
    else:
        os.popen("xsel", "wb").write(ticket)
    if vmdisplay == "qxl":
        os.popen("remote-viewer --spice-ca-file %s --spice-host-subject '%s' spice://%s/?port=%s\&tls-port=%s &" %
                 (cert, subject, host, vmport, vmsport))
    else:
        os.popen("remote-viewer vnc://%s:%s &" % (host, vmport))
    sys.exit(0)

if stop:
    s.destroy(vmid)
    print "vm %s stopped" % name
    sys.exit(0)

if start:
    vmfound = False
    name = args[0]
    for vm in s.list(True)["vmList"]:
        if name == vm["vmName"]:
            print "vm %s already running on this host" % name
            sys.exit(1)
    if not spm:
        print "vm can not only be launched on SPM"
        sys.exit(0)
    name = args[0]
    print "will launch vm %s.Please check it s not running on another hypervisor!!!" % name
    if host == "127.0.0.1":
        for id in os.listdir(sppath):
            if vmfound:
                break
            tree = ET.parse("%s/%s/%s.ovf" % (sppath, id, id))
            root = tree.getroot()
            for content in root.findall('Content'):
                vmname = content.findall("Name")[0].text
                template = content.findall("TemplateId")[0].text
                if template != "00000000-0000-0000-0000-000000000000":
                    continue
                if vmname == name:
                    vmfound = True
                    vminfo = root
                    vmid = id
                    break
    else:
        ssh = sshconnect(host)
        for id in sshlist(ssh, sppath).split("\n"):
            if vmfound:
                break
            if id == "":
                continue
            tree = sshfile(ssh, "%s/%s/%s.ovf" % (sppath, id, id))
            root = ET.fromstring(tree)
            # now we can parse
            for content in root.findall('Content'):
                vmname = content.findall("Name")[0].text
                template = content.findall("TemplateId")[0].text
                if template != "00000000-0000-0000-0000-000000000000":
                    continue
                if vmname == name:
                    vmfound = True
                    vminfo = root
                    vmid = id
                    break
    if not vmfound:
        print "vm not found"
        sys.exit(1)
    else:
        cmd = getvminfo(host, vmid, display, root)
        s.create(cmd)
        print "vm %s started" % name
