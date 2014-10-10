#!/usr/bin/python
"""foreman sample to use without ovirt(baremetal stuff)"""

import sys
from foreman import Foreman

foremanhost='192.168.8.148'
foremanport=443
foremanuser='admin'
foremanpassword='changeme'
foremansecure=True
name='satriani1'
dns='karma'
ip1='192.168.8.230'
mac1='00:1a:4a:aa:11:55'
hostgroup='base_RedHat_6'

f = Foreman(foremanhost, foremanport, foremanuser, foremanpassword, foremansecure)
f.create(name=name, dns=dns, ip=ip1, mac=mac1, hostgroup=hostgroup, build=True)
