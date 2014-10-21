#!/usr/bin/python
"""foreman sample to use without ovirt(baremetal stuff)"""

import sys
from foreman import Foreman

foremanhost='192.168.8.223'
foremanport=443
foremanuser='admin'
foremanpassword='changeme'
foremansecure=True
name='satriani1'
dns='xxx.org'
ip1='192.168.8.226'
#mac1='00:1a:4a:aa:11:55'
hostgroup='base6'
compute='bumblefoot'
profile='1-Small'

f = Foreman(foremanhost, foremanport, foremanuser, foremanpassword, foremansecure)
#f.create(name=name, dns=dns, ip=ip1, mac=mac1, hostgroup=hostgroup, build=True)
f.create(name=name, dns=dns, ip=ip1, hostgroup=hostgroup, compute=compute, profile=profile, build=True)
