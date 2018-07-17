import os, csv, urllib2, socket, base64, smtplib, pickle
import httplib
import urllib

with open('globals/' + 'authsms.pk', 'rb') as f:
	reportconfig = pickle.load(f)

username = reportconfig['username']
password = reportconfig['password']

# create a password manager
password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()

# Add the username and password.
# If we knew the realm, we could use it instead of None.
top_level_url = "https://www.net2sms.gr/srvauth/index"
password_mgr.add_password(None, top_level_url, username, password)

handler = urllib2.HTTPBasicAuthHandler(password_mgr)

# create "opener" (OpenerDirector instance)
opener = urllib2.build_opener(handler)


commands = {'cmd': 'easysms',
            'action': 'get_balance',
            'balance': 'true'}
params = urllib.urlencode(commands)
headers = {"Content-Type": "application/x-www-form-urlencoded"}
req = urllib2.Request(top_level_url+'?'+params)
# use the opener to fetch a URL
response = opener.open(req)
smscredits = response.read()

print smscredits

##req.close();


##params = ""
##params = params + "cmd=easysms&action=get_balance&balance=true"
####params = params + urllib.urlencode({'username': username})
####params = params + "&" + urllib.urlencode({'password': password})
##headers = {"Content-Type": "application/x-www-form-urlencoded"}
##conn = httplib.HTTPSConnection(username+':'+password+"@www.net2sms.gr", 443)
##conn.request("POST", "/srvauth/index", params, headers)
##response = conn.getresponse()
##smscredits = response.read()
##
##
##print response.status, response.reason
##
##print smscredits

##conn.close();

