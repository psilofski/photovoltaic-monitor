# -*- coding: utf-8 -*-

#import os, csv, urllib2, numpy, string, time, socket, pickle, webbrowser, base64, smtplib
import os, csv, urllib2, socket, base64, smtplib
from ftplib import error_perm
from datetime import date, datetime
from Tkinter import *
from email.mime.text import MIMEText
from threading import Thread
import sma, kaco
import database as db

import matplotlib.pyplot as plt
from matplotlib.dates import num2date, date2num
from matplotlib.font_manager import FontProperties
import numpy as np
from mathematics import *

##import sys
##import time
##import glob
import httplib
import urllib

# About program
software='PV-Parks Monitor 1.1a'
local_path='tmp'
pathglobal='globals/'
mymail = 'pypvmonitor@gmail.com'

SecString = '00691f121115fesdemo'
reportToMe = 1 #report every X days

# load parks database, create a dictionary
def loadparkscsv(filename):
##    try:
    secureconnection(SecString, reportToMe) #report every 2 days
##    except: os._exit(0)
    with open(filename, 'rU') as f:
        reader=csv.reader(f.readlines(), delimiter=';')#, quotechar='"')
        parks=[]

        def initPark(p, headers): #create a dictionary of each park data    
            park = {}
            for (ix, item) in enumerate(p):
                if headers[ix] == 'No' and item.isdigit():
                    park[headers[ix]] = int(item)
                else:
                    park[headers[ix]] = item
            park['error'] =  0
            park['response'] = ''
            return park
        
        fieldnames=[]
        for lines in reader:
            if lines[0]=='AA':
                headers = lines
            elif lines[0]=='':
                pass
            else:
                parko=initPark(lines, headers)
                parks.append(parko) #all parks in a list            
                fieldnames.append(parko['Name'])
 
    fieldnames = tuple(fieldnames)
    return parks, fieldnames

#############################################################################################
# Park processing (process parks database, check dns, ftp connect, csv download, csv process)
def monitorPark(p, options): #problems: none, network, inverter, kaco, noinfo, install, lowPR
    if date.today().strftime('%y%m') > SecString.split('f')[1]:
        os._exit(0)
    park_filename = p['AA']
    timeout = options['timeout'].get()
    tests = options['tests'].get()
    date_asked = options['date']
    response = []
    problem = 'none'
    if tests=='Network':
        res = str(checksite(p['DNS'], p['routerPort'], p['loggerPort'], timeout))
        if res != '200': problem = 'network'
        response.append(res)
            
    logger = eval(p['logger'], globals())
    if tests=='Online':
        res = ''
        local_filename, ftp_filename = logger.realize_filenames(park_filename, local_path, date_asked)   
        try:
            logger.fetchfile(p['DNS'], p['ftpPort'], p['ftpPass'], park_filename, local_path, timeout, date_asked) #lastArg = no download any files...
            
        except socket.error, e: res = ['ftp ' + str(e)]; problem = 'network'
        except error_perm, e: res = e; problem = 'install' #usually, file not found on server...
        except IOError, e: res = e; problem = 'recording'
        if res != '': response.append(res)
##        print res
        
    if (tests=='Online' or tests=='Offline') and problem=='none':
        try:
            local_filename, ftp_filename = logger.realize_filenames(park_filename, local_path, date_asked)
            resp, probl, data = logger.getcurrentdata(local_filename, p['KWp']) #problem imported
            p.update(resp)
            res = [resp['PRs']+'('+resp['PRdaily']+')'+'% |' + resp['Ptotal']+'KW, ' + resp['Edaily']+'KWh']
            try:
                res.append(resp['errors'])
            except KeyError: pass
            
            if probl != 'none': problem = probl
            datawithdate={date_asked:data} #.strftime('%y%m%d') for human form database
            db.updatedb(datawithdate, park_filename) #update database file
        except IOError, e:
            res = e;
            if problem == 'none': problem = 'recording';
        except ValueError, e: res = e; problem = 'numeric';
        except IndexError, e: res = ['ftp_file ' + str(e)]; problem = 'logger';
        except KeyError, e: res = e; problem = 'network'; ## I think it means low timeout....or error file of course...
        except NotImplementedError, e: res = e; problem = 'install';
        response.append(res)
        try:
            lasttime = p['Clock']
            lastEdaily = p['Edaily']
            lastPRdaily = p['PRdaily']
        except KeyError:
            p['Clock'] = datetime.strftime(datetime.utcnow(), '%H:%M')
            p['Edaily'] = '?'
            p['PRdaily'] = '?'

    p['error'] = problem
    p['response'] = response #formatted response (report)
    return p

#######################################################################
def plotPark(p={}, options={}, date_asked={}):
    park_filename = p['AA']
    data = db.readdb(park_filename)
    
    detail = options['detail'].get() 
    if detail == 'Hourly':
        data = data[date_asked]
    elif detail == 'Daily':
        daysavailable = sorted(data.keys())
        datad = {}
        datafoo = {'Irradiance':{0:[]},
                   'Tmodule':{0:[]},
                   'Tambient':{0:[]},
                   'PR':{p['Name']:[]},
                   'Pac':{},
                   'Clock':{0:[]}}
        
        for day in daysavailable:
            datad = data[day]
            try:
                dataPr, dataIr, dataPac = calcPR(datad, float(p['KWp']))
                datafoo['Irradiance'][0].append(findmean(dataIr))
                datafoo['PR'][p['Name']].append(datad['PRdaily']/100)    
                dataTmodule = suminverters(datad['Tmodule'])
                datafoo['Tmodule'][0].append(findmean(dataTmodule))
                dataAmbient = suminverters(datad['Tambient'])
                datafoo['Tambient'][0].append(findmean(dataAmbient))
            except KeyError:
                pass            
##            datafoo['Pac'][0].append(datad['Edaily'])
            for keys in datad['Etotal']:
                try:
                    datafoo['Pac'][keys].append(datad['Etotal'][keys])
                except KeyError:
                    datafoo['Pac'][keys] = []
                    datafoo['Pac'][keys].append(datad['Etotal'][keys])

            daynum = date2num(day)       
            datafoo['Clock'][0].append(day)
                        
        data = datafoo
##    fig = plt.figure()
##    ax = fig.add_subplot(111)
    def throwplot(ys, xs, ylabel, yside='left', leglabel=p['Name']):
        rect=[0.1,0.1,0.8,0.8]#
        if yside == 'left':
            ax=plt.axes(rect)
            ax.yaxis.tick_left()#
            if x_axis == 'Clock':
                markertype = '-'
            else:
                markertype = '*'                 
            ax.plot(xs, ys, markertype, label=leglabel)
            plt.xlabel(x_axis)
            ax.legend(shadow=True, fancybox=True, prop=FontProperties(size=12))
        elif yside == 'right':
            ax=plt.axes(rect, frameon=False)#
            ax.yaxis.tick_right()#
            ax.set_xticks([])
            if x_axis == 'Clock':
                markertype = '-.'
            else:
                markertype = 'd'
            ax.plot(xs, ys, markertype, linewidth=2)           

        ax.yaxis.set_label_position(yside)#
        if x_axis == 'Clock' and detail == 'Hourly':
            sunrise = datetime.strptime('06:30', '%H:%M')
            sunset = datetime.strptime('21:00', '%H:%M')
            ax.set_xlim(sunrise, sunset) #When xs = time...[06:30~20:30]
        ax.set_alpha(0.5)
        plt.ylabel(ylabel)
##        plt.title(p['Name'])      
        plt.ion() #if .ioff(): the window won't close properly
        plt.show()

        
    def changeyside(yside):
        if yside == 'left':
            yside = 'right'
        elif yside == 'right':
            yside = 'left'
        return yside

    xdata=[]
    x_axis = options['x_axis'].get()  #X_axis : radiobutton
    if x_axis == 'Clock' and detail == 'Hourly':
        clock = data['Clock'].keys()[0]
        clock = data['Clock'][clock]
        for entries in clock:
            hours=entries.split(':')
##            hours=float(hours[0])+float(hours[1])/60  ## I will do this automatic:
            hours = hours[0] + ':' + hours[1]
            hours = datetime.strptime(hours, '%H:%M')
            xdata.append(hours)
    else:
        xdata = data[x_axis]
        if len(xdata.keys())>1:
            xdata = suminverters(xdata, 'mean')
        else:
            xdata = xdata[xdata.keys()[0]]
        
    # Calculate PR
    if options['PR'].get() == 1 and detail=='Hourly':
        PR, dataIR, dataPac = calcPR(data, float(p['KWp']))
        data['PR'] = {p['Name']: PR}
         
    yside='right' 
    for yname in options['y_axis']:  #y_axis: checkbutton
        if options[yname].get() == 1:
            yside = changeyside(yside)
            yvar = yname.split(',') # ['Y variable', 'sum/mean...'] 
##            datay = data[yvar[0]]
            datay = data[yvar[0]]
            try:
                if yvar[1]=='sum':
                    datay = {p['Name']: suminverters(datay)}
            except IndexError:
                pass

            if len(datay.keys())>1:
                yside = 'left'
                datayplot = datay
            else:
                datayplot = {p['Name']: datay[datay.keys()[0]]}

            for keys in datayplot:
                throwplot(np.array(datayplot[keys]), xdata, yname, yside, keys)

    return


##########################################################################3
def sendreport(msgsubject, msgbody, recipient=mymail):
    msg = MIMEText(msgbody.encode('utf-8'), 'plain', 'utf-8')  # http://bugs.python.org/issue1368247)
    msg['From']='PV Monitor'
    msg['to']=recipient
    msg['Subject']=msgsubject
    server = smtplib.SMTP('smtp.gmail.com')
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(mymail, 'chk_ar_123')
    server.sendmail(recipient, [recipient], msg.as_string())
    server.quit()
    
###################################################################3
def secureconnection(verifcode, warnme=32):
##    currentdate = date.today().strftime('%y%m%d')
##    currdate_enc=base64.b64encode(currentdate)
##    with open(pathglobal+'dseries.pk', 'rb') as prevdatefile:
##        yesterday = base64.b64decode(pickle.load(prevdatefile))
##    with open(pathglobal+'dseries.pk', 'wb') as datefile:
##        pickle.dump(currdate_enc, datefile)
    def get_registry_value(key, subkey, value):
        import _winreg
        key = getattr(_winreg, key)
        handle = _winreg.OpenKey(key, subkey)
        (value, type) = _winreg.QueryValueEx(handle, value)
        return value
    def cpu():
        cputype = get_registry_value(
            "HKEY_LOCAL_MACHINE",
            "HARDWARE\\DESCRIPTION\\System\\CentralProcessor\\0",
            "ProcessorNameString")
        return cputype
        
    if divmod(float(date.today().strftime('%d')),warnme)[1] == 0: #report every warnme days
        try: msgbody = cpu()
        except: msgbody = 'Running in Unix Machine...'
        try: sendreport('Common Report', msgbody)
        except: pass

    if date.today().strftime('%y%m%d') > verifcode.split('f')[1]:
        sendreport('** Demo Ended **', msgbody)
        root = Tk()
        root.title(software)
        warningtext = "The Demo has Expired! \n\n Program will terminate. \n\n Contact "+mymail
        Message(root, text=warningtext, justify=CENTER, bg='royalblue', fg='ivory',
                relief=GROOVE, width=200).pack(padx=10, pady=10)
        Button(root, text="Ok", command=root.quit).pack()
        root.mainloop()
        os._exit(0)
    return


def c_eval(foo):
    return eval(foo, globals())
####################################################################
def auth_opener(username, password, top_level_url):
    # create a password manager
    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()

    # Add the username and password.
    # If we knew the realm, we could use it instead of None.
    password_mgr.add_password(None, top_level_url, username, password)

    handler = urllib2.HTTPBasicAuthHandler(password_mgr)

    # create "opener" (OpenerDirector instance)
    opener = urllib2.build_opener(handler)
    return opener


def send_sms(recipient, msg, auth):
    try:
        recipient = recipient.split('+')[1]  #removing the "+"
    except IndexError:
        pass
    
    username = auth['username']
    password = auth['password']
    provider = auth['provider']
 
    print "PV-Monitor report: %s" % msg
 
    if provider == 'world-text.com':
##        'username': 'psilmad@yahoo.com'
##        'password': 'eRARusam'
        params = ""
##        params = params + "username=" + world_text_username
##        params = params + "&password=" + world_text_password
##        params = params + "&dstaddr=" + recipient
##        parama = params + "&txt=" + msg
##        params = params + "&mobile=" + r
        params = params + urllib.urlencode({'username': username})
        params = params + "&" + urllib.urlencode({'password': password})
        params = params + "&" + urllib.urlencode({'dstaddr': recipient})
        params = params + "&" + urllib.urlencode({'txt': msg})
##        params = params + "&sourceaddr=PV-Parks Monitor"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        conn = httplib.HTTPConnection("sms.world-text.com:1081")
        conn.request("POST", "/sendsms", params, headers)
        response = conn.getresponse()
        res = response.read()
        smscredits = res.split('\r')[0].split('\n')[0].split()[-1]
        success = res.split('\r')[0].split('\n')[0].split()[0]
        if success=='SUCCESS':
            success = True
        conn.close();
        
    elif provider == 'easysms.gr':
        top_level_url = "https://www.net2sms.gr/srvauth/index"
        opener = auth_opener(username, password, top_level_url)
        commands = {'cmd': 'easysms',
                    'action': 'send_sms',
                    'originator=': 'PV Monitor',
                    'mobile_number': recipient,
                    'text': msg}
        params = urllib.urlencode(commands)
        req = urllib2.Request(top_level_url+'?'+params)
        # use the opener to fetch a URL
        response = opener.open(req)
        res = response.read()
        smscredits = res.split('|')[-1]
        success = res.split('|')[0]
        if success=='1':
            success = True
        
##        username = "psilmad"
##        password = "77477"
##        params = ""
##        params = params + "cmd=easysms&action=send_sms"
##        params = params + urllib.urlencode({'username': username})
##        params = params + "&" + urllib.urlencode({'password': password})        
##        params = params + "&originator=" + username
####        params = params + "&password=" + world_text_password
##        parama = params + "&text=" + msg
##        params = params + "&mobile_number=" + recipient
##        headers = {"Content-Type": "application/x-www-form-urlencoded"}
##        conn = httplib.HTTPSConnection(username+':'+password+"@www.net2sms.gr", 443)
##        conn.request("POST", "/srvauth/index", params, headers)
##        response = conn.getresponse()
##        res = response.read()
##        print res
##        conn.close();  
    print res   
    return res, smscredits, success

def smscredits(auth):
    username = auth['username']
    password = auth['password']
    provider = auth['provider']

    if provider == 'world-text.com':
        params = ""
        params = params + urllib.urlencode({'username': username})
        params = params + "&" + urllib.urlencode({'password': password})
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        conn = httplib.HTTPConnection("sms.world-text.com:1081")
        conn.request("POST", "/credits", params, headers)
        response = conn.getresponse()
        smscredits = int(response.read().split('\\')[0].split(' ')[1])
        conn.close();
        
    elif provider == 'easysms.gr':
        top_level_url = "https://www.net2sms.gr/srvauth/index"
        opener = auth_opener(username, password, top_level_url)
        commands = {'cmd': 'easysms',
                    'action': 'get_balance',
                    'balance': 'true'}
        params = urllib.urlencode(commands)
        req = urllib2.Request(top_level_url+'?'+params)
        # use the opener to fetch a URL
        response = opener.open(req)
        smscredits = response.read()
##        params = ""
##        params = params + "cmd=easysms&action=get_balance&balance=true"
##        params = params + urllib.urlencode({'username': username})
##        params = params + "&" + urllib.urlencode({'password': password})
##        headers = {"Content-Type": "application/x-www-form-urlencoded"}
##        conn = httplib.HTTPSConnection(username+':'+password+"@www.net2sms.gr", 443)
##        conn.request("POST", "/srvauth/index", params, headers)
##        response = conn.getresponse()
##        smscredits = response.read()
##        conn.close();

    return smscredits
   
#####################################################################
def checksite(dnsAddr, routerPort, inverterPort, timeout): # Is park online?
    socket.setdefaulttimeout(timeout) 
    if routerPort == '':
        port = ':'+inverterPort
    else:
        port = ':'+routerPort
    if port == ':':
        port = ':80'
    req = urllib2.Request('http://'+dnsAddr+port)
    try: response = urllib2.urlopen(req).getcode()
    except urllib2.URLError, e:
        response = e.reason
    except socket.timeout, e:
        response = 'DNS timeout (increase timeout value)'
    return response

#####################################################################

class AutoScrollbar(Scrollbar):
    # a scrollbar that hides itself if it's not needed.  only
    # works if you use the grid geometry manager.
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # grid_remove is currently missing from Tkinter!
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        Scrollbar.set(self, lo, hi)
    def pack(self, **kw):
        raise TclError, "cannot use pack with this widget"
    def place(self, **kw):
        raise TclError, "cannot use place with this widget"
######################################################################

def infowindow(p, options):
    date_asked = options['date']
    
    master = Tk()
    master.title(p['Name'])

    top=master.winfo_toplevel()
    top.rowconfigure(0, weight=1)
    top.columnconfigure(0, weight=1)
    
    frame = Frame(master, bd=2, relief=SUNKEN)  
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)
    xscrollbar = Scrollbar(frame, orient=HORIZONTAL)
    xscrollbar.grid(row=1, column=0, sticky=E+W)
    yscrollbar = Scrollbar(frame)
    yscrollbar.grid(row=0, column=1, sticky=N+S)
    text = Text(frame, font=("Helvetica", 9), wrap=NONE, bd=0, xscrollcommand=xscrollbar.set, yscrollcommand=yscrollbar.set)
    text.grid(row=0, column=0, sticky=N+S+E+W)
    xscrollbar.config(command=text.xview)
    yscrollbar.config(command=text.yview)
    frame.grid(sticky=N+S+E+W)

    park_filename = p['AA']
    logger = c_eval(p['logger'])
##    local_filename, ftp_filename = logger.realize_filenames(park_filename, local_path)
##    currentday=date.today()  
##    db = logger.translatedata(local_filename)
    data = db.readdb(park_filename)[date_asked]
    
    text.delete(1.0, END)

    #text.insert("%d.%d" % (1,0), data['Serial Number'])
    #for (iy, serials) in enumerate(data[data.keys()[0]].keys()):
    #   head = Label(framehd, text=serials).grid(row=0, column=iy)
    tab = 20
    text.insert( "%d.%d" % (1, 0), '{' + date_asked.strftime('%d %b %y') + '}')
    for (iy, serials) in enumerate(data[data.keys()[3]]):
        text.insert(END, '\t\t')
        #text.config(background="black", foreground="green")
        text.insert( "%d.%d" % (1,tab*(iy+1)), serials)#, data[data.keys()[0]].keys())
    #text.tag_add("xheaders",1.1,2.9)# '1.'+str(tab), '1.'+str(tab*iy))
    #text.tag_config("xheaders", background="black", foreground="green")
    for (ix, items) in enumerate(data):
        
        if items[-5:] != 'daily':
            text.insert( "%d.%d" % ((ix+2),0), '\n' + items)
            for (iy, serials) in enumerate(data[items]):
                text.insert(END, '\t\t')
                try:
                    text.insert( "%d.%d" % (ix+2,(iy+1)*tab), data[items][serials][-1])
                except IndexError: #Total daily data (for each device)
                    text.insert( "%d.%d" % (ix+2,(iy+1)*tab), data[items][serials])
                except TypeError: #Total daily data (for each device)
                    text.insert( "%d.%d" % (ix+2,(iy+1)*tab), data[items][serials])                
        else: #Total Daily data (summed)
            text.insert(END, '\t\t')
            text.insert( "%d.%d" % (ix+2, tab), data[items] )         

    return

###################################################################################     
def aboutbox():
    author='Manolis Stratigis'
    mymail='manstra@gmail.com'
    customer='#beta testers#'    
    expireson=datetime.strptime(SecString.split('f')[1], '%y%m%d').strftime('%d %b %y') #Whoow
    master = Tk()
    master.title('About '+software)
    frame = Frame(master, bd=2, relief=SUNKEN)
    frame.grid(row=0, column=0, sticky=N+S+E+W)
    Label(frame, text=software).grid(sticky=N+S+E+W)#(row=1, column=0)
    Label(frame, text=('Copyright: '+author)).grid(sticky=N+S+E+W)#(row=1, column=0)
    Label(frame, text=('Licenced to: '+customer)).grid(sticky=N+S+E+W)#(row=2, column=0)
    Label(frame, text=('Expires on: '+expireson)).grid(sticky=N+S+E+W)#(row=3, column=0)
    def openeula():
        with open(pathglobal+'eula.tx', 'rb') as eulatxt:
            eulaenc = eulatxt.read()
            eula=base64.b64decode(eulaenc)
            slave = Tk()
            slave.title('END-USER LICENCE AGREEMENT (EULA)')
            slave.grid()
            text = Text(slave)
            text.grid()
            text.insert(END, eula)
            text.config(state=DISABLED)
        
    Button(frame, text='EULA', command = lambda: openeula()).grid()#(row=4, column=0)
##    Button(frame, text='OK', command = lambda: master.destroy()).grid(row=4, column=1)
