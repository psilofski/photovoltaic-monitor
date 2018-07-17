import os, csv, urllib2, numpy, string, time, socket
from ftplib import FTP, error_perm
from datetime import date
import socket
from mathematics import *

#from joblib import Parallel, delayed
#from pprint import pprint
#from glob import glob #list files in directory with wildcards
#from Tkinter import *

##global today
##today = date.today().strftime('%y%m%d')
ftpUser = 'admin'

def realize_filenames(parkName, local_path, date_asked):
    global kacofiles
    kacofiles = ['_ana_','_kwr_']#,'anomalie_']
    date_filename = date_asked.strftime('%y%m%d')
    ftp_filenames = ['int'+kacofiles[0]+date_filename+'.txt', 'int'+kacofiles[1]+date_filename+'.txt']#, kacofiles[2]+'kwr.txt']
    local_filenames = {}
    for (i, label) in enumerate(ftp_filenames):
        local_filenames[label] = os.path.join(local_path, parkName+kacofiles[i]+'.txt')
    return local_filenames, ftp_filenames

#############################################################################
def fetchfile(loggerDns, port , ftpPasswd, parkName, local_path, timeout, date_asked):
    local_filenames, ftp_filenames = realize_filenames(parkName, local_path, date_asked)
    socket.setdefaulttimeout(timeout)
    ftp = FTP()
    ftp.connect(loggerDns)
    response = []
    ok_filenames = []
    ftp.login(ftpUser, ftpPasswd)
    ftp.set_pasv(0) # set active ftp
    ftp.cwd('data/' + date_asked.strftime('%y%m%d')) # cd to path
    for filename in ftp_filenames:
        with open(local_filenames[filename], 'wb') as f:
            try:    # Gia ton makrygiannaki olh h istoria   ###
                ftp.retrbinary('RETR %s' % filename, lambda data: f.write(data))
                response.append(local_filenames[filename]+' saved')
                ok_filenames.append(filename)
            except error_perm, e: pass ####
            #    filenm = 'kaco_status_' + today +'.txt'
            #    try:
            #        ftp.retrbinary('RETR %s' % [filenm], lambda data: f.write(data))
            #        response.append(local_filenames[filename]+' saved')
            #    except error_perm, e: response.append(e)            
    ftp.quit()
    return response, ok_filenames

############################################################################3
def translatedata(filenames):
    def openascsv(ftype):
        return csv.reader(open(ftype, 'rU').readlines(), delimiter=';', quotechar='"')
    
    for keys in filenames: #take the 3 file's instances to read later...
        try: 
            if keys.find(kacofiles[0]) != -1:
                ana = openascsv(filenames[keys])
            elif keys.find(kacofiles[1]) != -1:
                kwr = openascsv(filenames[keys])
        except IOError: pass
        
        #elif keys.find(kacofiles[2]) != -1:
            #try: anomalie = openascsv(filenames[keys]) # sometimes this file is not found
            #except IOError: pass
            
    # ana file: Irradiance
    try: ###
        anadata = []
        for lines in ana:
            if lines[0] == 'Uhrzeit': anaheaders = lines
            try:
                hour = float(lines[0].split(':')[0])
                anadata.append(lines)
            except ValueError: pass
            # kwr file: Electricals
    except NameError: pass   ####
    kwrdata = []
    for lines in kwr:
        if lines[0] == '' and lines[2] == 'Adresse': kwrheaders = lines
        try:
            hour = float(lines[0].split(':')[0])
            kwrdata.append(lines)
        except ValueError: pass
                   
    def catchdata(indata, outdata, inverter):
        foo=[]
        try:                
            foo = outdata[inverter]
            foo.append(indata)
        except KeyError:
            foo.append(indata)
        outdata[inverter] = foo
        return outdata
        
    def s2num(data):
        for keys in data:
            data[keys] = numpy.array(data[keys], float)
        return data
        
    def blanc2nan(lines):
        i = -1 #to replace empties with nan
        try:
            while 1:
                i=lines.index('', i+1)
                lines[i]=numpy.nan
        except ValueError:
            pass
        return lines
        
    # initializing database entries:
    try: ############
        irr_i = anaheaders.index('GD_N0'); Irradiance = {}
        Temp0_i = anaheaders.index('T_U0'); Temp0_i = {}
    except NameError: pass  #########
    inv_i = kwrheaders.index('Adresse'); Clock = {}
    Vdc_i = kwrheaders.index('U_DC_0'); Vdc = {}
    Idc_i = kwrheaders.index('I_DC_0'); Idc = {}
    Pdc_i = kwrheaders.index('P_DC_WR'); Pdc = {}
    Vac_i = kwrheaders.index('U_AC_0'); Vac = {}
    Iac_i = kwrheaders.index('I_AC_0'); Iac = {}
    Pac_i = kwrheaders.index('P_AC_WR'); Pac = {}
    Temp_i = kwrheaders.index('T_WR'); Temp = {}
    En_i = kwrheaders.index('E_D_WR'); En = {}
    alldata = {}
    sens_Clock = {}
    
    for lines in kwrdata: # all other values
        lines = blanc2nan(lines)
        inverter = lines[inv_i] # inverter address (which inverter)       
        #alldata = catchdata(lines, alldata, inverter) #useless, but impressive...
        Vdc = catchdata(lines[Vdc_i], Vdc, inverter)
        Idc = catchdata(lines[Idc_i], Idc, inverter)
        Pdc = catchdata(lines[Pdc_i], Pdc, inverter)
        Vac = catchdata(lines[Vac_i], Vac, inverter)
        Iac = catchdata(lines[Iac_i], Iac, inverter)
        Pac = catchdata(lines[Pac_i], Pac, inverter)
        Temp = catchdata(lines[Temp_i], Temp, 'inverters')
        En = catchdata(lines[En_i], En, inverter)
        Clock = catchdata(lines[0], Clock, inverter)

    try:   ########    
        for lines in anadata: # sensor data (currently, only Irradiance
            lines = blanc2nan(lines)
            Irradiance = catchdata(lines[irr_i], Irradiance, 'sensors')
            try:
                TempEnv = catchdata(lines[Temp0_i], Temp0_i, 'sensors')
            except TypeError: pass # ???????????????????
            Clock = catchdata(lines[0], sens_Clock, 'sensors')
    except NameError: pass ##########3
    
##    Clock = Clock.keys[0] # I won't need any others...
    #Clock['sensors'] = sens_Clock['0']
    database = {'Clock': Clock, 'Vdc': s2num(Vdc), 'Idc': s2num(Idc), 'Pdc': s2num(Pdc), 'Vac': s2num(Vac), 'Iac': s2num(Iac), 'Pac': s2num(Pac), 'En': s2num(En)}
    try: ####
        database['Irradiance'] = s2num(Irradiance)
    except NameError: pass  ####
    try: ####
        database['Tmodule'] = s2num(Temp)
    except NameError: pass  ####
    try:
        database.update( {'Tambient': s2num(TempEnv)} )
    except NameError:
        pass
##    database = {date_asked: database}
                  
    return database
####################################################################################

def getcurrentdata(filenames, KWp):
    data = translatedata(filenames)
    problem = 'none'
    Pac = []
    #i_sun = data['Clock']['sensors'].index('14:00:00') # please, replace i_sun with -1. Now, testin...************8
    for keys in data['Pac']:
        currentPac = data['Pac'][keys][-1]
        Pac.append(currentPac)
        if currentPac == 0 or numpy.isnan(currentPac): problem = 'inverter'
    Ptotal = numpy.nansum(Pac)/1000

    def daily(item):
        foo=[]
        Etotal = {}
        for keys in item:
            inv_daily=numpy.nansum(item[keys])
            foo.append(inv_daily)
            Etotal.update({keys:inv_daily/1000})
        return numpy.nansum(foo), Etotal
    Edaily, Etotal = daily(data['En'])
    Edaily = str(round(Edaily/1000, 1))
##    Etotal = str(round(Etotal, 3)) # Directly from csv
    
    
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
    timeNow = data['Clock'][data['Clock'].keys()[0]][-1]  # From '1st' device in dict...
    tfoo = timeNow.split(':') #(HR:MN:SEC)
    timeNow = tfoo[0] + ':' + tfoo[1]
    
    Ptotal = str(round(Ptotal, 1))+'KW '
##    res = str(PRs)+'('+str(PRdaily)+')'+'% |' + Ptotal + Edaily + 'KWh, ' + '('+timeNow+')'
    res = {'PRs': str(PRs), 'PRdaily': str(PRdaily), 'Ptotal': str(Ptotal), 'Edaily': str(Edaily), 'Clock': timeNow}
    
    data.update({'PRdaily': PRdaily, 'Etotal':Etotal, 'Edaily':Edaily})
    return res, problem, data
#####################################################################################

#local_filenames, ftp_filenames = realize_filenames('kaco14', 'tmp/')
#d = translatedata(local_filenames)

    
