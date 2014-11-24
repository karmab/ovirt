#!/usr/bin/python

import ConfigParser
import json
import optparse
import os
import requests
import simplejson 
import sys

__author__ = "Karim Boumedhel"
__credits__ = ["Karim Boumedhel"]
__license__ = "GPL"
__version__ = "1.1"
__maintainer__ = "Karim Boumedhel"
__email__ = "karim.boumedhel@gmail.com"
__status__ = "Production"

ERR_NOFOREMANFILE="You need to create a correct foreman.ini file in your home directory.Check documentation"


perpage='1000'
#helper functions
def foremando(url, actiontype=None, postdata=None, user=None, password=None):
    headers = {'content-type': 'application/json', 'Accept': 'application/json' }
    #get environments
    if user and password:
        user     = user.encode('ascii')
        password = password.encode('ascii')
    if actiontype == 'POST':
        r = requests.post(url,verify=False, headers=headers,auth=(user,password),data=json.dumps(postdata))
    elif actiontype == 'DELETE':
        r = requests.delete(url,verify=False, headers=headers,auth=(user,password),data=postdata)
    elif actiontype == 'PUT':
        r = requests.put(url,verify=False, headers=headers,auth=(user,password),data=postdata)
    else:
        r = requests.get(url,verify=False, headers=headers,auth=(user,password))
    try:
        result = r.json()
        result = eval(str(result))
        return result
    except:
        return None

def foremangetid(protocol, host, port, user, password, searchtype, searchname):
    if searchtype == 'puppet':
        url = "%s://%s:%s/api/v2/smart_proxies?type=%s"  % (protocol, host, port, searchtype)
        result = foremando(url)
        return result[0]['smart_proxy']['id']
    else:
        url = "%s://%s:%s/api/v2/%s/%s" % (protocol, host, port, searchtype, searchname)
        result = foremando(url=url, user=user, password=password)
    if searchtype == 'ptables':
        shortname = 'ptable'
    elif searchtype.endswith('es') and searchtype != 'architectures':
        shortname = searchtype[:-2]
    else:
        shortname = searchtype[:-1]
    try:
        return str(result[shortname]['id'])
    except:
        return str(result['id'])

def orgid(protocol, host, port, user, password, orgname):
	url = "%s://%s:%s/api/v2/organizations" % (protocol, host, port)
        res = foremando(url=url, user=user, password=password)
        for  r in res['results']:
            if r['name'] == orgname:
        	return r['id']
	return None
		

#VM CREATION IN FOREMAN
class Foreman:
    def __init__(self, host, port, user, password,secure=False):
        host = host.encode('ascii')
        port = str(port).encode('ascii')
        user = user.encode('ascii')
        password = password.encode('ascii')
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        if secure:
            self.protocol = 'https'
        else:
            self.protocol = 'http'
    def delete(self, name, dns=None):
	if '.' in name:
		dns  = name.split('.')[1:]
		name = name.split('.')[0]
        host, user , password, protocol = self.host, self.user, self.password, self.protocol
        name = name.encode('ascii')
        if dns:
            dns = dns.encode('ascii')
            name = "%s.%s" % (name, dns)
        url = "%s://%s/api/v2/hosts/%s" % (protocol, host, name)
        result = foremando(url=url, actiontype='DELETE', user=user, password=password)
        if result:
            print "%s deleted in Foreman" % name
        else:
            print "Nothing to do in foreman"
    def create(self, name, dns, ip, mac=None, operatingsystem=None, environment=None, arch="x86_64", puppet=None, ptable=None, powerup=None, memory=None, core=None, compute=None, profile=None, hostgroup=None,build=False, location=None, organization=None):
        host, port, user , password, protocol = self.host, self.port, self.user, self.password, self.protocol
        name = name.encode('ascii')
        dns = dns.encode('ascii')
        if ip:
            ip = ip.encode('ascii')
        if mac:
            mac = mac.encode('ascii')
        if operatingsystem:
            operatingsystem = operatingsystem.encode('ascii')
        if arch:
            arch = arch.encode('ascii')
        if puppet:
            puppet = puppet.encode('ascii')
        if ptable:
            ptable = ptable.encode('ascii')
        if powerup:
            powerup = powerup.encode('ascii')
        if memory:
            memory = memory.encode('ascii')
        if core:
            core = core.encode('ascii')
        if compute:
            compute = compute.encode('ascii')
        if profile:
            profile = profile.encode('ascii')
        if hostgroup:
            hostgroup = hostgroup.encode('ascii')
        if location:
            location = location.encode('ascii')
        if organization:
            organization = organization.encode('ascii')
        url = "%s://%s:%s/api/v2/hosts" % (protocol, host, port)
        postdata = {}
        if dns:
            name = "%s.%s" % (name, dns)
        postdata['host'] = {'name':name}
        if operatingsystem:
            osid = foremangetid(protocol, host, port, user, password, 'operatingsystems', operatingsystem)
            postdata['host']['operatingsystem_id'] = osid
	if not hostgroup:
            	if not environment:
			environment = "production"
            	environment = environment.encode('ascii')
        	envid = foremangetid(protocol, host, port, user, password, 'environments', environment)
        	postdata['host']['environment_id'] = envid
        postdata['host']['build'] = build
        if arch:
            archid = foremangetid(protocol, host, port, user, password, 'architectures', arch)
            postdata['host']['architecture_id'] = archid
        if puppet:
            puppetid = foremangetid(protocol, host, port, user, password, 'puppet', puppet)
            postdata['host']['puppet_proxy_id'] = puppetid
        if not build:
            postdata['host']['managed'] = False
        if ip:
            postdata['host']['ip'] = ip
        if mac:
            postdata['host']['mac'] = mac
        if compute:
            computeid = foremangetid(protocol, host, port, user, password, 'compute_resources', compute)
            postdata['host']['compute_resource_id'] = computeid
        if profile:
            profileid = foremangetid(protocol, host, port, user, password, 'compute_profiles', profile)
            postdata['host']['compute_profile_id'] = profileid
        if hostgroup:
            hostgroupid = foremangetid(protocol, host, port, user, password, 'hostgroups', hostgroup)
            postdata['host']['hostgroup_id'] = hostgroupid
        if ptable:
            ptableid = foremangetid(protocol, host, port, user, password, 'ptables', ptable)
            postdata['host']['ptable_id'] = ptableid
        if location:
            locationid = foremangetid(protocol, host, port, user, password, 'locations', location)
            postdata['host']['location_id'] = locationid
        if organization:
            postdata['host']['organization_id'] = orgid(protocol, host, port, user, password, organization)
        result = foremando(url=url, actiontype="POST", postdata=postdata, user=user, password=password)
        if not result.has_key('errors'):
            print "%s created in Foreman" % name
        else:
            print "%s not created in Foreman because %s" % (name, result["errors"][0])

    def addclasses(self, name, dns, classes):
        name = name.encode('ascii')
        dns = dns.encode('ascii')
        classes = classes.encode("ascii")
        host, port, user , password, protocol = self.host, self.port, self.user, self.password, self.protocol
        classes = classes.split(',')
        for classe in classes:
            classid = foremangetid(protocol, host, port, user, password, 'puppetclasses', classe)
            url = "%s://%s:%s/api/v2/hosts/%s.%s/puppetclass_ids" % (protocol, host, port, name, dns)
            postdata = {'puppetclass_id': classid}
            foremando(url=url, actiontype="POST", postdata=postdata, user=user, password=password)
            print "class %s added to %s.%s" % (classe,name,dns)

    def hostgroups(self, environment):
        host, port, user , password, protocol = self.host, self.port, self.user, self.password, self.protocol
        url = "%s://%s:%s/api/v2/hostgroups?per_page=%s" % (protocol, host, port, perpage)
        res= foremando(url=url, user=user, password=password)
        results = []
        for  r in res['results']:
		results.append(r['title'])
        return sorted(results)
    def vms(self):
        host, port, user , password, protocol = self.host, self.port, self.user, self.password, self.protocol
        url = "%s://%s:%s/api/v2/hosts" % (protocol, host, port)
        res= foremando(url=url, user=user, password=password)
        results = []
        for  r in res['results']:
		results.append(r['name'])
        return sorted(results)
	

    def classes(self, environment):
        host, port, user , password, protocol = self.host, self.port, self.user, self.password, self.protocol
        url = "%s://%s:%s/api/v2/puppetclasses?search=environment+=+%s&per_page=%s" % (protocol, host, port, environment, perpage)
        res= foremando(url=url, user=user, password=password)
        results=[]
        res = res['results']
        for  module in res:
            if len(res[module]) == 1:
                results.append(module)
            else:
                for classe in res[module]:
                    results.append(classe['name'])
        return sorted(results)

    def exists(self, name,dns=None):
        host, port, user , password, protocol = self.host, self.port, self.user, self.password, self.protocol
        if dns:
            name = "%s.%s" % (name, dns)
        url = "%s://%s:%s/api/v2/hosts"  % (protocol, host, port)
        res = foremando(url=url, user=user, password=password)
        for  r in res['results']:
            currentname = r['name']
            if currentname == name:
                return True
        return False

    def classinfo(self, name ):
        host, port, user , password, protocol = self.host, self.port, self.user, self.password, self.protocol
        url = "%s://%s:%s/api/v2/puppetclasses/%s" % (protocol, host, port, name)
        res= foremando(url=url, user=user, password=password)
        results={}
        parameters = res['smart_class_parameters']
        for parameter in parameters:
            parameterid = parameter['id']
            parametername = parameter['parameter']
            parameterurl = "%s://%s:%s/api/v2/smart_class_parameters/%s-%s" % (protocol, host, port, parameterid, parametername)
            res= foremando(url=parameterurl, user=user, password=password)
            print res
            required = res['required']
            defaultvalue = res['default_value']
            results[parametername]=[defaultvalue, required]
        return results

    def override(self, name, parameter, parameterid=None ):
        host, port, user , password, protocol = self.host, self.port, self.user, self.password, self.protocol
        if not parameterid:
            url = "%s://%s:%s/api/v2/puppetclasses/%s" % (protocol, host, port, name)
            res= foremando(url=url, user=user, password=password)
            classparameters = res['smart_class_parameters']
            for param in classparameters:
                if param['parameter'] == parameter:
                    parameterid = param['id']
                    break
            if parameterid == None:
                print "parameterid for parameter %s of class %s not found" % (parameter, name)
                return False
            parameterurl = "%s://%s:%s/api/v2/smart_class_parameters/%s-%s" % (protocol, host, port, parameterid, parameter)
            postdata = {}
            postdata["smart_class_parameter"] = { "override": True }
            postdata = simplejson.dumps(postdata)
            res = foremando(url=parameterurl, actiontype="PUT", postdata=postdata, user=user, password=password)
            print "parameter %s of class %s set as overriden" % (parameter, name)

    def addparameters(self, name, dns, parameters):
        host, port, user , password, protocol = self.host, self.port, self.user, self.password, self.protocol
        name = name.encode('ascii')
        dns = dns.encode('ascii')
        parameters = parameters.encode('ascii')
        parameters = parameters.split(' ')
        parametersid = {}
        parametersurl = "%s://%s:%s/api/v2/smart_class_parameters?per_page=10000" % (protocol, host, port)
        res = foremando(url=parametersurl, user=user, password=password)
        res = res['results']
        for p in res:
            parametersid[p["parameter"]] = p["id"]
        for parameter in parameters:
            try:
                parameter, value = parameter.split("=")
            except:
                print "Cant split parameter=value for %s" % parameter
                continue
            if not parametersid.has_key(parameter):
                    print "parameter %s not found" % (parameter)
                    continue
            else:
                print "handling parameter %s" % (parameter)
                parameterid = parametersid[parameter]
            parameterurl = "%s://%s:%s/api/v2/smart_class_parameters/%s-%s" % (protocol, host, port, parameterid, parameter)
            res = foremando(url=parameterurl, user=user, password=password)
            override, override_values, override_values_count, parameter_type = res['override'], res['override_values'], res['override_values_count'], res['parameter_type']
            if not override:
                postdata = {}
                postdata["smart_class_parameter"] = { "override": True }
                postdata = simplejson.dumps(postdata)
                res = foremando(url=parameterurl, actiontype="PUT", postdata=postdata, user=user, password=password)
                print "parameter %s set as overriden" % (parameter)
            overrideid = 0
            if len(override_values) > 0:
                for o in override_values:
                    match = o['match'].split('=')
                    if match[0] == 'fqdn' and match[1] == "%s.%s" % (name,dns):
                        overrideid =  o['id']
                        break
            if overrideid == 0:
                postdata = { "override_value": { "match":"fqdn=%s.%s" % (name,dns) } }
                if parameter_type == 'string':
                    postdata["override_value"]["value"] = value
                elif parameter_type == 'array':    
                    value = value.split(',')
                    postdata["override_value"]["value"] = value
                overrideurl = "%s://%s:%s/api/v2/smart_class_parameters/%s/override_values" % (protocol, host, port, parameter)
                res = foremando(url=overrideurl, actiontype="POST", postdata=postdata, user=user, password=password)
                print "parameter %s created for %s.%s" % (parameter, name, dns)
            else:    
                postdata = { "override_value": { "match":"fqdn=%s.%s" % (name,dns) } }
                if parameter_type == 'string':
                    postdata["override_value"]["value"] = value
                elif parameter_type == 'array':    
                    value = value.split(',')
                    postdata["override_value"]["value"] = value
                postdata = simplejson.dumps(postdata)
                overrideurl = "%s://%s:%s/api/v2/smart_class_parameters/%s/override_values/%s" % (protocol, host, port, parameter, overrideid)
                res = foremando(url=overrideurl, actiontype="PUT", postdata=postdata, user=user, password=password)
                print "parameter %s updated for %s.%s" % (parameter, name, dns)

    def start(self, name, dns=None):
        host, port, user , password, protocol = self.host, self.port, self.user, self.password, self.protocol
	if '.' in name:
		dns  = '.'.join(name.split('.')[1:])
		name = name.split('.')[0]
        url = "%s://%s:%s/api/v2/hosts/%s.%s/power" % (protocol, host, port, name,dns)
	postdata = {}
	postdata['power_action'] = 'start'
	postdata = simplejson.dumps(postdata)
        res= foremando(url=url, actiontype="PUT", postdata=postdata,user=user, password=password)
	print "machine %s.%s started" % (name, dns)

    def stop(self, name, dns=None):
        host, port, user , password, protocol = self.host, self.port, self.user, self.password, self.protocol
	if '.' in name:
		dns  = '.'.join(name.split('.')[1:])
		name = name.split('.')[0]
        url = "%s://%s:%s/api/v2/hosts/%s/power" % (protocol, host, port, name)
	postdata = {}
	postdata['power_action'] = 'stop'
	postdata = simplejson.dumps(postdata)
        res= foremando(url=url, actiontype="PUT", postdata=postdata,user=user, password=password)
	print "machine %s.%s stopped" % (parameter, name, dns)

    def console(self, name, dns=None):
        host, port, user , password, protocol = self.host, self.port, self.user, self.password, self.protocol
	if '.' in name:
		dns  = '.'.join(name.split('.')[1:])
		name = name.split('.')[0]
        url = "%s://%s:%s/hosts/%s.%s/console" % (protocol, host, port, name, dns)
	print url
    def info(self, name, dns=None):
        host, port, user , password, protocol = self.host, self.port, self.user, self.password, self.protocol
	if '.' in name:
		dns  = '.'.join(name.split('.')[1:])
		name = name.split('.')[0]
        url = "%s://%s:%s/api/v2/hosts/%s.%s" % (protocol, host, port, name, dns)
	res = foremando(url=url, user=user, password=password)
	print "Name: %s" % res['name']
	print "Profile: %s" % res['compute_profile_name']
	print "Ip: %s" % res['ip']
	print "Mac: %s" % res['mac']
	print "OS: %s" % res['operatingsystem_name']
	print "Hostgroup: %s" % res['hostgroup_name']
	print "ENV: %s" % res['environment_name']
	

if  __name__ =='__main__':
	usage         = 'script to create systems on foreman'
	version       = '1.0'
	parser        = optparse.OptionParser('Usage: %prog [options] system',version=version)
	actiongroup   = optparse.OptionGroup(parser, 'Action options')
	actiongroup.add_option('-s', '--start', dest='start', action="store_true" , help='Start system')
	actiongroup.add_option('-w', '--stop', dest='stop', action="store_true" , help='Stop system')
	actiongroup.add_option('-o', '--console', dest='console', action="store_true" , help='Get console')
	parser.add_option_group(actiongroup)
	creationgroup = optparse.OptionGroup(parser, 'Creation options')
	creationgroup.add_option('-H', '--host', dest='host', type='string', help='foreman host')
	creationgroup.add_option('-P', '--port', dest='port', type='string', default='443',help='foreman port')
	creationgroup.add_option('-u', '--user', dest='user', type='string', default='admin',  help='foreman port')
	creationgroup.add_option('-p', '--password', dest='password', type='string', default='changeme', help='foreman password')
	creationgroup.add_option('-n', '--new', action="store_true", help='new')
	creationgroup.add_option('-d', '--dns', dest='dns', type='string', help='dns')
	creationgroup.add_option('-i', '--ip', dest='ip', type='string', help='ip')
	creationgroup.add_option('-k', '--kill', dest="kill", action="store_true", help="Kill machine")
	creationgroup.add_option('-l', '--location', dest='location', type='string', help='location')
	creationgroup.add_option('-m', '--mac', dest='mac', type='string', help='mac')
	creationgroup.add_option('-O', '--organization', dest='organization', type='string', help='Organization')
	creationgroup.add_option('-X', '--hostgroup', dest='hostgroup', type='string', help='hostgroup')
	creationgroup.add_option('-b', '--build', action="store_true", help='build')
	creationgroup.add_option('-c', '--compute', dest='compute', type='string', help='compute')
	creationgroup.add_option('-Z', '--profile', dest='profile', type='string', default='1-Small', help='profile')
	parser.add_option_group(creationgroup)
	listinggroup = optparse.OptionGroup(parser, "Listing options")
	listinggroup.add_option("-a", "--archs", dest="listarchs", action="store_true", help="List archs")
	listinggroup.add_option("--domains", dest="listdomains", action="store_true", help="List domains")
	listinggroup.add_option("--environments", dest="listenvironments", action="store_true", help="List environments")
	listinggroup.add_option("--hostgroups", dest="listhostgroups", action="store_true", help="List hostgroups")
	listinggroup.add_option('-V','--listvms', dest="listvms", action="store_true", help="List Machines")
	listinggroup.add_option("--oses", dest="listos", action="store_true", help="List os")
	listinggroup.add_option("--puppets", dest="listpuppets", action="store_true", help="List puppets")
	listinggroup.add_option("-L", "--clients", dest="listclients", action="store_true", help="list available clients")
	listinggroup.add_option("-R", "--computes", dest="listcomputes", action="store_true", help="List compute resources")
	listinggroup.add_option("-9", "--switchclient", dest="switchclient", type="string", help="Switch default client")
	parser.add_option_group(listinggroup)
	parser.add_option("-C", "--client", dest="client", type="string", help="Specify Client")
	(options, args) = parser.parse_args()
	host             = options.host
	port             = options.port
	user             = options.user
	password         = options.password
	new              = options.new
	dns              = options.dns
	ip               = options.ip
	kill             = options.kill
	location         = options.location
	mac              = options.mac
	organization     = options.organization
	hostgroup        = options.hostgroup
	build            = options.build
	compute          = options.compute
	profile          = options.profile
	listenvironments = options.listenvironments
	listvms          = options.listvms
	listhostgroups   = options.listhostgroups
	listarchs        = options.listarchs
	listos           = options.listos
	listdomains      = options.listdomains
	listpuppets      = options.listpuppets
	listcomputes     = options.listcomputes
	#puppetclass     = options.puppetclass
	listclients      = options.listclients
	switchclient     = options.switchclient
	client           = options.client
	start            = options.start
	stop             = options.stop
	console          = options.console
	env              = 'production'


	foremanconffile  ="%s/foreman.ini" %(os.environ['HOME'])
	#parse foreman client auth file
	if not os.path.exists(foremanconffile):
    		print "Missing %s in your  home directory.Check documentation" % foremanconffile
    		sys.exit(1)
	try:
    		c = ConfigParser.ConfigParser()
    		c.read(foremanconffile)
    		foremans={}
    		default={}
    		for cli in c.sections():
        		for option in  c.options(cli):
            			if cli=="default":
                			default[option]=c.get(cli,option)
                			continue
            			if not foremans.has_key(cli):
                			foremans[cli]={option : c.get(cli,option)}
            			else:
                			foremans[cli][option]=c.get(cli,option)
	except KeyError,e:
    		print ERR_NOFOREMANFILE
    		print e
    		os._exit(1)
	if listclients:
    		print "Available Clients:"
    		for cli in  sorted(foremans):
        		print cli
    		if default.has_key("client"):
			print "Current default client is: %s" % (default["client"])
    		sys.exit(0)
	if switchclient:
    		if switchclient not in foremans.keys():
        		print "Client not defined...Leaving"
    		else:
        		mod = open(foremanconffile).readlines()
        		f=open(foremanconffile,"w")
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
	try:
		if not host and foremans[client].has_key('host'):
    			host=foremans[client]["host"]
    		if not port and foremans[client].has_key("port"):
        		port = foremans[client]["port"]
    		if not user and foremans[client].has_key("user"):
        		user = foremans[client]["user"]
	    	if not password and foremans[client].has_key("password"):
			password = foremans[client]["password"]
	    	if not mac and foremans[client].has_key("mac"):
			mac = foremans[client]["mac"]
	    	if foremans[client].has_key("os"):
			foremanos = foremans[client]["os"]
	    	if foremans[client].has_key("env"):
			env = foremans[client]["env"]
	    	if foremans[client].has_key("arch"):
			arch = foremans[client]["arch"]
	    	if foremans[client].has_key("puppet"):
			puppet = foremans[client]["puppet"]
	    	if foremans[client].has_key("ptable"):
			ptable = foremans[client]["ptable"]
	    	if not dns and foremans[client].has_key('dns'):
			dns = foremans[client]['dns']
	    	if not organization and foremans[client].has_key('organization'):
			organization = foremans[client]['organization']
	    	if not location and foremans[client].has_key('location'):
			location = foremans[client]['location']

	except KeyError,e:
    		print "Problem parsing foreman ini file:Missing parameter %s" % e
    		os._exit(1)

	f = Foreman(host, port, user, password, secure= True)	
	if listhostgroups:
		for hg in sorted(f.hostgroups(env)):
			print hg
		sys.exit(0)
	if listvms:
		for vm in sorted(f.vms()):
			print vm
		sys.exit(0)
	if len(args) != 1:
		print "Usage:foreman.py [options] name"
		sys.exit(0)
	name = args[0]
	if new:
		f.create(name=name, dns=dns, ip=ip, mac=mac, hostgroup=hostgroup, compute=compute, profile=profile, build=build, location=location, organization= organization)
		sys.exit(0)
	if kill:
		f.delete(name=name, dns=dns)
		sys.exit(0)
	if start:
		f.start(name=name, dns=dns)
	if stop:
		f.stop(name=name, dns=dns)
	if console:
		f.console(name=name, dns=dns)
        f.info(name=name, dns=dns)
