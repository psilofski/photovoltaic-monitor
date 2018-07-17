# sma modules
import os, csv, urllib2, numpy, string, time
from ftplib import FTP
from datetime import date
import socket
from database import translatekeys
from mathematics import *
#from joblib import Parallel, delayed
#from pprint import pprint
#from glob import glob #list files in directory with wildcards
#from Tkinter import *


user='installer'
path_ftp='/DATA/20'
local_path='tmp'
##global currentday
##currentday=date.today().strftime('%y%m%d')

def realize_filenames(parkName, local_path, date_asked):
    ftp_filename = '20' + date_asked.strftime('%y-%m-%d') 
    local_filename = os.path.join(local_path, parkName + '.csv')
    return local_filename, ftp_filename

##############################################################################
def fetchfile(loggerDns, port, ftpPasswd, parkName, local_path, timeout, date_asked): # fetch csv via ftp
    local_filename, ftp_filename = realize_filenames(parkName, local_path, date_asked)
    socket.setdefaulttimeout(timeout)
    ftp = FTP()        
    if port == '': port = 21
    ftp.connect(loggerDns, port)#, timeout)
    #ftp=FTP(loggerDns,user,ftpPasswd) # Ftp Connect, default port
    
    try:  # when user is other than default (testing purposes) **********************8
        credentials = ftpPasswd.split(' /*/ ')
        ftpPasswd = credentials[1]
        user = credentials[0]
        path_ftp='DATA/20' #*****
    except IndexError:
        pass          #******************8888888
    
    ftp.login(user, ftpPasswd)

    paths = path_ftp + date.today().strftime('%y')
    ftp.cwd(paths) #cd <>
        
    files = [] # sma saves more files in one day
    ftp.retrlines('LIST', files.append)   # ls ##################################################
    record_files = -1
    for foo in files:
        real_file = foo.split(' ')[-1]
        #print real_file[:10], ftp_filename
        if real_file[:10] == ftp_filename:
            record_files = record_files + 1
                   
    if record_files > 0:
        ftp_filename = ftp_filename + '(' + str(record_files) + ')'
        
    file_to_download = ftp_filename + '.csv'    
##    print ftp.size(file_to_download)   #*************************  
    with open(local_filename, 'wb') as f:
        ftp.retrbinary('RETR %s' % file_to_download, lambda data: f.write(data))

    ftp.quit()

    response = ftp_filename + ' saved...'
    return response, local_filename

################################################################################
# process csv file
def translatedata(filename):
    devicereader=csv.reader(open(filename, 'rU').readlines()[2:5], delimiter=';', quotechar='"')
    devices = 'clock'
    serials = '000'
    for (i, lines) in enumerate(devicereader):
        if i == 0: devices = ['clock'] + lines[1:]
        if i == 1: serialnum = ['000'] + lines[1:]
        if i == 2: dataheaders = lines

    def blanc2nan(lines):
        i = -1 #to replace empties with nan
        try: ###########################1###
            while 1:
                i=lines.index('', i+1)
                lines[i]=numpy.nan
        except ValueError: ##############1###
            pass
        return lines
    
    reader=csv.reader(open(filename, 'rU').readlines()[6:], delimiter=';', quotechar='"')
    data = {}
    headers = {}
    tdata = {}
    foo = []
    for lines in reader:
        lines = blanc2nan(lines)
        for (iy, val) in enumerate(lines):
            item = dataheaders[iy]
            serial = serialnum[iy]
            try: val = float(val)
            except: pass
            try:
                data[item][serial].append(val)
            except KeyError:
                try:
                    data[item][serial] = [val]
                except KeyError:
                    data[item] = {}
                    data[item][serial] = [val]
                    
    database = translatekeys('sma', data)                    
##    database = {date_asked: data}
    
    return database

#####################################################################################
def getcurrentdata(filenames, KWp):
    data = translatedata(filenames)
    problem = 'none'
    
    def getcurrentsum(item): #for any value to add...
        #item = numpy.array(item, float)
        foo = []
        for s_n in item:
            foo.append(item[s_n][-1])
        meanfoo = numpy.nansum(foo)        
        return meanfoo

    def getEnergysum(item): #max-min, only for daily energy
        foo = []
        Etotal = {}
        for s_n in item:
            inv_daily=numpy.nanmax(item[s_n])-numpy.nanmin(item[s_n])
            inv_daily = round(inv_daily, 3)
            foo.append(inv_daily)
            
            Etotal.update({s_n:inv_daily})
        meanfoo = numpy.nansum(foo)        
        return meanfoo, Etotal

    Ptotal = round(getcurrentsum(data['Pac'])/1000, 1)
    Esum, Etotal = getEnergysum(data['En_meter'])
    Edaily = round(Esum, 1)
    
    res = []
    try:
        PRseries, dataIr, dataPac = calcPR(data, float(KWp))
        PRseries = PRseries*100
        PRs = round(PRseries[-1], 1)
        PRdaily = round(findmean(PRseries), 1)
        if PRdaily < 80:
            problem='lowPR' 
    except KeyError:
        PRs='noSensors'
        PRdaily='-'
    except ValueError:
        PRs='none'
        PRdaily='-'
##    res = [str(PRs)+'('+str(PRdaily)+')'+'% |' + str(Ptotal)+'KW, ' + str(Edaily)+'KWh']
    res = {'PRs': str(PRs), 'PRdaily': str(PRdaily), 'Ptotal': str(Ptotal), 'Edaily': str(Edaily)}

    def checkfailures(fault, problem):
        errors = {}       
        for keys in data[fault]:
            errordata = data[fault][keys][-1]
            if errordata != 0 and not numpy.isnan(errordata):# #numpy.nan
                errors[keys[-3:]] = data[fault][keys][-1]
                problem = 'inverter'
        return problem, errors

    problem, errors = checkfailures('Error', problem)
##    except KeyError: problem, errors = checkfailures('Fehler')
    if problem == 'inverter': res.update({'errors': errors})
    timeNow = data['Clock'][data['Clock'].keys()[0]][-1]
##    res.append(timeNow)
    res.update({'Clock': timeNow})

    data.update({'PRdaily': PRdaily, 'Etotal': Etotal, 'Edaily': Edaily})
    return res, problem, data
