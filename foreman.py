import json
import optparse
import requests
import simplejson 

__author__ = "Karim Boumedhel"
__credits__ = ["Karim Boumedhel"]
__license__ = "GPL"
__version__ = "1.1"
__maintainer__ = "Karim Boumedhel"
__email__ = "karim.boumedhel@gmail.com"
__status__ = "Production"



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
    def create(self, name, dns, ip, mac=None, operatingsystem=None, environment=None, arch="x86_64", puppet=None, ptable=None, powerup=None, memory=None, core=None, compute=None, profile=None, hostgroup=None,build=False):
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
	envid = foremangetid(protocol, host, port, user, password, 'environments', environment)
        res= foremando(url=url, user=user, password=password)
        results = {}
        for  r in res['results']:
            name = r["name"]
	    if r['environment_id']== int(envid) or r['title'].split('/')[0] in results.keys():
            	del r["name"]
            	results[name]=r
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

if  __name__ =='__main__':
	usage         = 'script to create systems on foreman'
	version       = '1.0'
	parser        = optparse.OptionParser('Usage: %prog [options] system',version=version)
	creationgroup = optparse.OptionGroup(parser, 'Creation options')
	creationgroup.add_option('-H', '--host', dest='host', type='string', help='foreman host')
	creationgroup.add_option('-P', '--port', dest='port', type='string', default='443',help='foreman port')
	creationgroup.add_option('-u', '--user', dest='user', type='string', default='admin',  help='foreman port')
	creationgroup.add_option('-p', '--password', dest='password', type='string', default='changeme', help='foreman password')
	creationgroup.add_option('-n', '--name', dest='name', type='string', help='name')
	creationgroup.add_option('-d', '--dns', dest='dns', type='string', help='dns')
	creationgroup.add_option('-i', '--ip', dest='ip', type='string', help='ip')
	creationgroup.add_option('-m', '--mac', dest='mac', type='string', help='mac')
	creationgroup.add_option('-X', '--hostgroup', dest='hostgroup', type='string', help='hostgroup')
	creationgroup.add_option('-b', '--build', action="store_true", help='build')
	creationgroup.add_option('-c', '--compute', dest='compute', type='string', help='compute')
	creationgroup.add_option('-Z', '--profile', dest='profile', type='string', default='1-Small', help='profile')
	parser.add_option_group(creationgroup)
	(options, args) = parser.parse_args()
	host      = options.host
	port      = options.port
	user      = options.user
	password  = options.password
	name      = options.name
	dns       = options.dns
	ip        = options.ip
	mac       = options.mac
	hostgroup = options.hostgroup
	build     = options.build
	compute   = options.compute
	profile   = options.profile
	f = Foreman(host, port, user, password, secure= True)	
	f.create(name=name, dns=dns, ip=ip, mac=mac, hostgroup=hostgroup, compute=compute, profile=profile, build=build)
