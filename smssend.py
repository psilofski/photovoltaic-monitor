#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import time
import glob
import httplib
import urllib
 
##recepients = []
## 
##recepients.append("306994704833")
 
world_text_username = "psilmad@yahoo.com"
world_text_password = "eRARusam"
 
##def usage():
##    print "alertme.py <message to send>"
##    sys.exit(0)
 
def send_sms(msg, recipients):
    global recepients, world_text_username, world_text_password
 
    print "PV-Monitor report: %s" % msg
 
    for r in recipients:
        params = ""
        params = params + "username=" + world_text_username
        params = params + "&password=" + world_text_password
        params = params + "&dstaddr=" + r
        parama = params + "&txt=" + msg
        params = params + "&" + urllib.urlencode({'message': msg})
##        params = params + "&sourceaddr=SMSAlert"
##        params = params + "&mobile=" + r
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        conn = httplib.HTTPConnection("sms.world-text.com:1081")
        conn.request("POST", "/sendsms", params, headers)
        conn.close();
        print params, '\n', headers
##if len(sys.argv) != 2:
##    usage()
## 
send_sms('ti xamparia?\nxaxa', ['306994704833'])#(sys.argv[1])
