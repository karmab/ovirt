###ovirt.py repository

[![Build Status](https://travis-ci.org/karmab/ovirt.svg?branch=master)](https://travis-ci.org/karmab/ovirt)
[![Code Climate](https://codeclimate.com/github/karmab/ovirt/badges/gpa.svg)](https://codeclimate.com/github/karmab/ovirt)

This script allows creation/stop/start/runonce/console/add disk or iso/migrate/deploy/listing from template/add tags,... for ovirt/rhev-m virtual machines ( plus creation in cobbler for pxe installs) in a multi-client way

##Requisites

- ovirt-engine-sdk-python rpm
- python-requests rpm 
- python-prettytable rpm
- ovirt.ini file in your home directory or in same directory as program (look at sample for syntax)
- a client.ini (for instance nyse.ini) in your home directory for every client you want to manage.This file will contain profiles (disksize,number of network interfaces and type,...) used when creating machines (and also by cobbler if you have a cobbler setup) (look at sample for syntax)

##Contents

-    `README.txt` this file
-    `ovirt.py`  start/stop/migrate/creates/deletes virtual machines in ovirt/rhev-m of several clients
-    `hypervisor.py` start/stop/get console of virtual machines connecting directly to the hypervisor (usefull when manager is down) 
-    `foreman.py`  class used by ovirt.py for foreman support. can also be used on its own

##Typical uses
     
- CREATE VIRTUAL MACHINE V0100 BASED ON PROFILE BE6 FOR CLIENT BIGCOMPANY, PROVIDING IPS FOR COBBLER TOO
    - `ovirt.py -ZC bigcompany -n v0100 -p be6 -1 192.168.1.100 -2 192.168.10.100`
-   DELETE VIRTUAL MACHINE V0100 FROM CLIENT NYSE
    -   `ovirt.py -C nyse -K v0100`
-    GET A CONSOLE FOR VIRTUAL MACHINE HENDRIX ( IN DEFAULT CLIENT)
    -    `ovirt.py -o hendrix`
-    START A VM KIPA02 DIRECTLY THROUGH THE HYPERVISOR WITH 
    -    `hypervisor.py -T ~/vdsm_certs -H 192.168.6.1 -s kipa02`
-    CREATE THE MACHINE DIRECTLY IN FOREMAN (specifying foremanip, name and dns of the vm, the hostgroup and compute resource to use,and build mode)
    -    `foreman.py -H  192.168.8.223 -n satriani -d xxx.org -X base6 -b -c bumblefoot`

##Problems?

Send me a mail at [karimboumedhel@gmail.com](mailto:karimboumedhel@gmail.com) !

Mac Fly!!!

karmab
