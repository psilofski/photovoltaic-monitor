#!/usr/bin/python
# -*- coding: utf-8 -*-
import webbrowser, os
from Tkinter import *
from ttk import * #Tkinter.ttk on python 3
import tkMessageBox
from threading import Thread, activeCount
from tracker import mailclient
from essentials import *
import time
import matplotlib.pyplot as plt
from datetime import datetime, date
from database import *
from math import isnan
import optionssms
import choosedate

##from mathematics import suminverters

software='PV-Parks Monitor 1.1a (Demo)'
decor_path='decor/'
bgr = {'canvas': 'Light Grey', 'form': '#c9f6e5'}

################################################################################

def makeWidgets():
    global entries, clocks, aa, trackers, entriestr
    
    def guionline(park, multithread=0):
        parkLabel = park['Name']
        if park['No'] != ignorechar:
            entries[parkLabel].config(background='Yellow')
            if multithread==0:
                #window.canv.update_idletasks(window)
                window.update()

            park = monitorPark(park, options) # check park

            problem = park['error']
            res = park['response']
            entries[parkLabel].config(background='White')
            if problem == 'none':
                park.update({'Color':'Black'})
            elif problem == 'inverter':
                park.update({'Color':'Red'})
            elif problem == 'network':
                park.update({'Color':'Magenta'})
            elif problem == 'lowPR':
                park.update({'Color':'Blue'})        
            else:
                park.update({'Color':'Grey'})
                
            entries[parkLabel].config(foreground=park['Color'])
            aa[parkLabel].config(foreground=park['Color'])                
            entries[parkLabel].delete(0, END)
            entries[parkLabel].insert(0, res[0])  #****************************aggyles********
            try:
                clocks[parkLabel].config(text=park['Clock'])
            except KeyError:
                pass
##            status = '..' + park['AA'] + '..'
            # terminal output
##            print (status),
##            if problem != 'none': print problem
##        else:
##            status = ''
##            entries[parkLabel].config(background='Light Grey')
        return park

    def checkbadparks(parks):
        for park in parks:
            if park['error'] != 'none' and park['error'] != 'lowPR':
                guionline(park)
        return 

    def checkallparks(parks):
        thr={}
    ##    thr['trackers'] = Thread(target=mailclient, args=(trackers,entriestr,))
        for park in parks:               
            thr[park['AA']] = Thread(target=guionline, args=(park,1,))
            thr[park['AA']].start()
##        THREAD_LIMIT = 5           
##        while activeCount() > THREAD_LIMIT:
##            print activeCount()
##            time.sleep(0.5)

    def checktrackers(trackers,entriestr):
        thrtrak = Thread(target=mailclient, args=(trackers,entriestr,))
        thrtrak.start()

        
    def dailyplotPark(p, plotitems, date_asked):
##        try:
            plotPark(p, plotitems, date_asked)
##        except KeyError:
##            pass
            
    def autonetworkcheck(parks):
        global thrNetwork
##        start = datetime.time(datetime.now())
        
        def inthread(parks):
            global prevreporterror
            while autonetwork.get() == 1:
                try:
                    step = int(options['varCombo'].get())*60
                except ValueError:
                    step = 30*60
                    options['varCombo'].set(30)
######################################doing the auto scan############
                From = options['varFrom'].get()
                Till = options['varTill'].get()
                if int(From)>int(Till):
                    From = options['varTill'].get()
                    Till = options['varFrom'].get()

                nowHour = datetime.now().strftime('%H')

                if From <= nowHour and Till > nowHour:
                    res = []
                    for p in parks:
                        if p['AA'] != ignorechar:
                            if autonetwork.get() == 1:
    ##                            window.protocol("WM_DELETE_WINDOW", exit) #removing "X" button
                                options['date'] = date.today()  #*****Auto Monitoring today
                                options['dateentry'].config(foreground='Grey')
                                
                                parkLabel = p['Name']  
                                entries[parkLabel].config(background='Light Green')                                                                                                       
                                timeout = options['timeout'].get()                            
                                if options['varAutoMode'].get() == 'Network':
                                    res = str(checksite(p['DNS'], p['routerPort'], p['loggerPort'], timeout))
                                    entries[parkLabel].config(background='White')
                                    if res != '200':
                                        entries[parkLabel].config(background='light pink')
##                                        aa[parkLabel].config(background='light pink')
                                    else:
                                        entries[parkLabel].config(background='white')
##                                        aa[parkLabel].config(background='Light Grey')
                                        if p['error'] == 'network':
                                            guionline(p, 1)
                                            
                                elif options['varAutoMode'].get() == 'Data':
                                    try:
                                        res.append(guionline(p, 1)) #it IS a threaded task, hence the "1"
                                    except KeyError:
                                        pass
                                    
    ##                print 'xaxa' + prevreporterror                              
                    if options['varAutoMode'].get() == 'Data' and True in ['inverter' in r.values() for r in res]:                    
                        reporterror = ''
                        for p in res:
                            if 'inverter' in p['error']:
                                reporterror = reporterror + p['Name'] + '| fault: ' + str(p['response'][0][-1]) + '\n'

                        if reporterror != prevreporterror:
                        
                            with open('globals/' + 'authsms.pk', 'rb') as f:
                                reportconfig = pickle.load(f)
                                email = reportconfig['email']
                                errsms = reportconfig['errsms']
                                mobile = reportconfig['mobile']

                            if errsms:
                                res, smscredits, success = send_sms(mobile, reporterror, reportconfig)
                                creditinfo.config(text=smscredits)
    ##                            creditinfo.config(text=smscredits(reportconfig))
                                
                            sendreport('inverter fault', reporterror, email)
                            print reporterror

                        prevreporterror = reporterror       
#############################################################################
                    
                autoprogress.config( maximum=step )         
                pause = True
                pauseNo = 0
                while pause == True and pauseNo < step: # pause for 1 sec until step passes
                    if autonetwork.get() == 1:                      
                        time.sleep(1)
                        autoprogress.step()
                        pauseNo = pauseNo + 1
                    else:
                        pause = False
                        autoprogress.stop()
                autoprogress.stop()
##                datewant = options['dateentry'].cget('text')  #********************************
                options['date'] = datetime.strptime(options['dateentry'].cget('text'), '%d %b %y').date()  #***************************************
                options['dateentry'].config(foreground='Black')

        if autonetwork.get() == 1:
            thrNetwork = Thread(target=inthread, args=(parks,))
            thrNetwork.start()
            
    def quitapp():
        if tkMessageBox.askokcancel("Quit", "Do you really wish to quit?"):
            
            with open('globals/' + 'options.pk', 'wb') as f: #auto save options
                opts = {}
                for keys in options:
                    try:
                        opts[keys]=options[keys].get()
                    except AttributeError:
                        pass
                pickle.dump(opts, f)
                
            quitsignal.set(1)
            autonetwork.set(0)
            options['timeout'].set(1)
    ##        thrquit = Thread(target = window.quit)
    ##        thrquit.join()
            try:
                thrNetwork.join(10)
                os._exit(0)
            except NameError:
                window.quit()        
    ##        window.quit()
        
    def sendallsms():
        if tkMessageBox.askokcancel("Send SMS", "Are you sure to send SMS's?"):
            try:
                with open('globals/' + 'authsms.pk', 'rb') as f:
                    sms_auth = pickle.load(f)
                    opt = sms_auth['options']
           
                for park in parks:
                    if sendsms[park['AA']].get() == 1:
                        try:
                            msg = ''
                            if opt['date'] == 1:
                                msg = msg + date.today().strftime('%d-%m-%y') + '\n'
                            if opt['name'] == 1:
                                msg = msg + park['Name'] + '\n'
                            if opt['En'] == 1:
                                msg = msg + 'Energy: ' + park['Edaily'] + 'KWh\n'
                            if opt['PR'] == 1:
                                msg = msg + 'PR: ' + park['PRdaily'] + '%\n'
                            if opt['euro'] == 1:
                                money = str(round(float(park['Edaily'])*float(park['WattPrice']), 1))
        ##                        euro = u'\u20ac'
        ##                        euro = '€'
        ##                        euro = euros.encode('utf-8')
                                msg = msg + 'Gain: ' + money + ' euro'
        ##                    print msg

                            res, smscredits, success = send_sms(park['smsNum'], msg, sms_auth)
        ##                    with open('temp', 'wb') as tmp:
        ##                        pickle.dump(res, tmp)
                               
                            creditinfo.config(text=smscredits)
                        except KeyError:
                            print 'No data to send!'
                            
                if success is not True:
                    tkMessageBox.showerror ('SMS Error', 'Could not send some/all SMSs')
                else:
                    tkMessageBox.showinfo ("SMS's Sent", "All SMS's succesfully sent!")
                        
            except IOError:
                tkMessageBox.showerror ('SMS Error', 'SMS configuration Error!')
            except NameError:
                tkMessageBox.showerror ('SMS Error', 'Nothing to send!')

            
    def saveVar(var, filename):
        foo = {}
        for park in parks:
            foo.update({park['AA']:var[park['AA']].get()})
        with open('globals/' + filename, 'wb') as f:            
            pickle.dump(foo, f)

        if filename == 'choicesms.pk': 
            tkMessageBox.showinfo ("SMS config", "SMS recipients saved!")

                   
    window = Tk()
    options = {}
    
    window.geometry("%dx%d%+d%+d" % (750, len(parks)*40, 0, 0))
    window.title(software)
    
    window.protocol("WM_DELETE_WINDOW", quitapp) #manual quitting
    
    lowbar = Frame(window)
    lowbar.grid(row=2, column=0, sticky=W+E)
    lowbar.columnconfigure(14, weight=1)

    autoprogress = Progressbar( lowbar, orient='vertical', length=24 )
    autoprogress.grid(row=0,column=0)
    
    Label( lowbar, text = '  Step (min):').grid(row=0,column=2 )
    autooptions = {}
    valCombo = ( 5, 15, 30, 60, 120, 240, 360 )
    options['varCombo'] = StringVar()
    options['varCombo'].set( 60 )
    cboCombo = Combobox( lowbar, width=4, values=valCombo, textvariable=options['varCombo'] )
    cboCombo.grid(row=0, column=3)

    Label( lowbar, text='From:').grid(row=0,column=4 )
    Label( lowbar, text='Till:').grid(row=0,column=6 )
    
    valHour = ( '00', '01', '02', '03', '04', '05', '06', '07', '08', '09',
                '10', '11', '12', '13', '14', '15', '16', '17', '18', '19',
                '20', '21', '22', '23', '24' )
    
    options['varFrom'] = StringVar()
    options['varFrom'].set( '06' )
    cboFrom = Combobox( lowbar, width=2, values=valHour, textvariable=options['varFrom'] )
    cboFrom.grid(row=0, column=5)

    options['varTill'] = StringVar()
    options['varTill'].set( '21' )
    cboTill = Combobox( lowbar, width=2, values=valHour, textvariable=options['varTill'] )
    cboTill.grid(row=0, column=7)
                
    Label( lowbar, text = '  Mode:').grid(row=0,column=8 )
    valAutoMode = ( 'Network', 'Data' )
    options['varAutoMode'] = StringVar()
    testbox = Spinbox(lowbar, values = valAutoMode, textvariable=options['varAutoMode'], width=8, wrap=1)
    options['varAutoMode'].set( 'Data' )
    testbox.grid(row=0, column=9)

    global prevreporterror
    prevreporterror = ''
    autonetwork = IntVar()
##    autonetstep = 20 #every minutes checks network
    autoScan = Checkbutton(lowbar,  text="Auto Scan", indicatoron=False, variable=autonetwork, command=(lambda: autonetworkcheck(parks)))
    autoScan.grid(row=0,column=1)

    try:
        Label(lowbar, text="SMS's: ").grid(row=0, column=10)
        creditinfo = Label(lowbar)
        creditinfo.grid(row=0, column=11)
        creditinfo.config(text=smscredits(readconfig()))
    except IOError:
        pass 
        
    quitsignal = IntVar() 
    # create a toplevel menu
    menubar = Menu(window)
    window.config(menu=menubar)

    appmenu = Menu(menubar, tearoff=0)
    appmenu.add_command(label="Configure...", command=lambda: optionssms.Dialog(window))
    appmenu.add_command(label="About...", command=lambda: aboutbox())
    appmenu.add_separator()
    appmenu.add_command(label="Quit!", command=lambda: quitapp())
    menubar.add_cascade(label="Application", menu=appmenu)

    optionsmenu = Menu(menubar, tearoff=0)

    
    monitormenu = Menu(menubar, tearoff=1)
    monitormenu.add_command(label="All Parks", command=(lambda: checkallparks(parks)))
    monitormenu.add_command(label="Bad Parks", command=(lambda: checkbadparks(parks)))
    monitormenu.add_separator() #
    monitormenu.add_command(label="Trackers", command=(lambda: checktrackers(trackers,entriestr)))

    monitormenu.add_separator() #
    modemenu = Menu(monitormenu, tearoff=0)
    monitormenu.add_cascade(label="Mode", menu=modemenu)
    options['tests'] = StringVar()
    modemenu.add_radiobutton(label='Online', value='Online', variable=options['tests'])
    modemenu.add_radiobutton(label='Offline', value='Offline', variable=options['tests'])
    modemenu.add_radiobutton(label='Network Only', value='Network', variable=options['tests'])
    options['tests'].set('Online')
    
    toutmenu = Menu(monitormenu, tearoff=0)
    monitormenu.add_cascade(label="Timeout", menu=toutmenu)
    options['timeout'] = IntVar()
    for items in ['10', '20', '50', '100', '200', '500']:
        toutmenu.add_radiobutton(label=items, value=int(items), variable=options['timeout'])
    options['timeout'].set(200)
##    monitormenu.add_separator() #
##    
##    autonetwork = IntVar()
####    autonetstep = 20 #every minutes checks network
##    monitormenu.add_checkbutton(label='Auto Network', variable=autonetwork, command=(lambda: autonetworkcheck(parks, options['varCombo'])))
    
##    menubar.add_cascade(label="Options", menu=optionsmenu)
    menubar.add_cascade(label="Monitor", menu=monitormenu)


    plotmenu = Menu(menubar, tearoff=1)
    plotoptions_sort = ['PR', 'Pac,sum', 'Pac' , 'Irradiance' , 'Tmodule', 'Tambient']
    plotitems =  {'y_axis':plotoptions_sort}
    for items in plotoptions_sort:
        plotitems[items] = IntVar()
        plotmenu.add_checkbutton(label=items, variable=plotitems[items])
        
    plotmenu.add_separator()
##    xplotmenu = Menu(plotmenu, tearoff=0)
    plotitems['x_axis'] = StringVar()
    for items in ['Clock', 'Irradiance' , 'Tmodule', 'Tambient']:
        plotmenu.add_radiobutton(label=items, value=str(items), variable=plotitems['x_axis'])
    plotitems['x_axis'].set('Clock')
    plotmenu.add_separator() #    
##    plotmenu.add_cascade(label='x Axis', menu=xplotmenu)

##    detplotmenu = Menu(plotmenu, tearoff=0)
    plotitems['detail'] = StringVar()
    for items in ['Hourly', 'Daily']:
        plotmenu.add_radiobutton(label=items, value=str(items), variable=plotitems['detail'])
    plotitems['detail'].set('Hourly')
##    plotmenu.add_cascade(label='Detail...', menu=detplotmenu)
    
    plotmenu.add_separator()
    plotmenu.add_command(label="New plot...", command=lambda: plt.figure().show())
    menubar.add_cascade(label="Plots", menu=plotmenu)


    reportmenu = Menu(menubar, tearoff=0)
    reportmenu.add_command(label="send SMS!", command=lambda: sendallsms())
    reportmenu.add_separator()
    reportmenu.add_command(label="Save state", command=lambda: saveVar(sendsms, 'choicesms.pk'))
    menubar.add_cascade(label="Report", menu=reportmenu)


    def sortmainform(parks, key):
        global entries, clocks, aa, trackers
        if key != 'No':           
            sparks = []
            fooparks = []
            for park in parks:
                try:
                    park[key]=float(park[key])
                    if isnan(park[key]):
                        fooparks.append(park)
                    else:
                        sparks.append(park)
                except ValueError:
                    fooparks.append(park)
                except KeyError:
                    fooparks.append(park)
##            print park.keys()

            sparks = sorted(sparks, key=lambda k: k[key], reverse=True)
            parks = sparks + fooparks
        else:
            parks = sorted(parks, key=lambda k: k[key])
        entries, clocks, aa, trackers, entriestr = drawmainform(parks, canvas)
        return
        
    sortmenu = Menu(menubar, tearoff=0)    
    sortmenu.add_command(label="No", command=lambda: sortmainform(parks, 'No'))
    sortmenu.add_separator()
    sortmenu.add_command(label="PRdaily", command=lambda: sortmainform(parks, 'PRdaily'))
    sortmenu.add_command(label="Edaily", command=lambda: sortmainform(parks, 'Edaily'))
    menubar.add_cascade(label="Sort", menu=sortmenu)

##    dbmenu = Menu(menubar, tearoff=0)
##    dbmenu.add_command(label="Custom Date...", command=lambda: customdate(window))
##    menubar.add_cascade(label="Database", menu=dbmenu)

###############################################
##    top=window.winfo_toplevel()
##    top.rowconfigure(0, weight=1)
##    top.columnconfigure(0, weight=1)
################################################
    vscrollbar = AutoScrollbar(window)
    vscrollbar.grid(row=0, column=1, sticky=N+S)
    hscrollbar = AutoScrollbar(window, orient=HORIZONTAL)
    hscrollbar.grid(row=1, column=0, sticky=E+W)

    canvas = Canvas(window,
                    yscrollcommand=vscrollbar.set,
                    xscrollcommand=hscrollbar.set)
    canvas.config(background=bgr['canvas'])
    canvas.grid(row=0, column=0, sticky=N+S+E+W)

    vscrollbar.config(command=canvas.yview)
    hscrollbar.config(command=canvas.xview)

    # make the canvas expandable
    window.grid_rowconfigure(0, weight=1)
    window.grid_columnconfigure(0, weight=1)

    #Initialize some vars:
    iconinfo = PhotoImage(file=decor_path+"iconinfo.gif")
    icontracker = PhotoImage(file=decor_path+"linktracker.gif")
    iconlogger = PhotoImage(file=decor_path+"linklogger.gif")
    iconcam = PhotoImage(file=decor_path+"linkcamera.gif")
    iconplot= PhotoImage(file=decor_path+"iconplot.gif")
    iconsms= PhotoImage(file=decor_path+"sms_protocol.gif")
    iconcalendar= PhotoImage(file=decor_path+"iconcalendar.gif")
    
    col = {'No': 1, 'label': 2, 'ent': 4, 'clc': 5, 'info': 6, 'plot':3,
           'linkL': 7, 'linkT':9, 'linkC':8, 'trackers':10, 'sms':0} #GUI columns


    sendsms={}
    try: # import last sms checkbuttons state...
        with open('globals/' + 'choicesms.pk', 'rb') as f:
            state = pickle.load(f)
        for park in parks:
            foo = IntVar()
            foo.set(state[park['AA']])
            sendsms.update( {park['AA']: foo} )
    except :
        for park in parks:
            sendsms.update({park['AA']: IntVar()})
            
##    sendsms={}
##    for park in parks:
##        sendsms.update({park['AA']:IntVar()})

    def drawmainform(parks, canvas):
        # create canvas contents
        form = Canvas(canvas)
        form.config(bg=bgr['form'])
        form.rowconfigure(1, weight=1)
        form.columnconfigure(1, weight=1)

        entries = {}
        entriestr = {}
        clocks = {}
        aa = {}
        trackers = []
                
        for (ix, park) in enumerate(parks):
            label = park['Name']
            i_p = park['No']
            if park['No'] != ignorechar:
                aa[label] = Button(form, text=i_p, width=1, command = lambda p=park: guionline(p)) #button for solo park
                aa[label].grid(row=ix, column=col['No'])
                binfo = Button(form, image=iconinfo, command=lambda p=park: infowindow(p, options))
                binfo.grid(row=ix, column=col['info'])
                binfo.image = iconinfo
                bplot = Button(form, image=iconplot, command=lambda p=park: dailyplotPark(p, plotitems, options['date']))
                bplot.grid(row=ix, column=col['plot'])
                bplot.image = iconplot
                
            lab = Label(form, text=label)
            lab.config(background=bgr['form'])
            lab.grid(row=ix, column=col['label'])
            #lab.bind('<Double-Button-1>', lambda ix=ix: temp(parks[ix]))
            #names[label] = lab
            ent = Entry(form)
            ent.grid(row=ix, column=col['ent'], ipadx=70, sticky=E+W)
            entries[label] = ent
            clc = Label(form, bg=bgr['form'], )
            clc.grid(row=ix, column=col['clc'], ipadx=0, sticky=E+W)
            clocks[label] = clc
            
            try: #if rerun loop for sorting purpose...
                entries[label].config(foreground=park['Color'])
                aa[label].config(foreground=park['Color'])
                entries[label].delete(0, END)
                entries[label].insert(0, park['response'])
                clocks[label].config(text=park['Clock'])
            except KeyError:
                pass            
            
            if park['loggerPort'] != '':
                blinkLogger = Button(form, image=iconlogger,
                                     command=lambda p=park: webbrowser.open_new('http://' +p['DNS'] +':' +p['loggerPort'] +p['browserAddr']))
                blinkLogger.grid(row=ix, column=col['linkL'])
                blinkLogger.image = iconlogger
                
            if park['trackerPort'] != '':
                blinkTracker = Button(form, image=icontracker,
                                      command=lambda p=park: webbrowser.open_new('http://' +p['DNS'] +':' +p['trackerPort']))
                blinkTracker.grid(row=ix, column=col['linkT'])
                blinkTracker.image = icontracker
                
                trackers.append(park)
                parkname = park['parkNameTracker']
                entriestr[parkname] = {}
                for iy in range(int(park['NofTrackers'])):
                   entrac = Entry(form, width=3)
                   entrac.grid(row=ix, column=col['trackers']+iy, sticky=E+W)
                   #entries[label][str(iy+1)] = ent
                   entriestr[parkname][str(iy+1)]=entrac

               
            if parks[ix]['CameraPort'] != '':
                blinkCam = Button(form, image=iconcam,
                                  command=lambda p=parks[ix]: webbrowser.open_new('http://' +p['DNS'] +':' +p['CameraPort'].split('(')[0]))
                blinkCam.grid(row=ix, column=col['linkC'])
                blinkCam.image = iconcam

            if parks[ix]['smsNum'] != '':
                bsms = Checkbutton(form, bg=bgr['form'], image=iconsms, indicatoron=False, variable = sendsms[park['AA']])
                bsms.grid(row=ix, column=col['sms'])
                bsms.image = iconsms

        canvas.create_window(0, 0, anchor=NW, window=form)
        form.update_idletasks()
        return entries, clocks, aa, trackers, entriestr

    # Initialize parks form
    entries, clocks, aa, trackers, entriestr = drawmainform(parks, canvas)
    canvas.config(scrollregion=canvas.bbox("all"))

    def customdate(parks, window):
        global cdate
        dateDialog = choosedate.Dialog(window)
        try:
            date_asked = dateDialog.result
            options['dateentry'].config(text=date_asked.strftime('%d %b %y'))
            options['date'] = date_asked #global options
        except AttributeError:
            pass
        except ValueError:
            pass

        for park in parks:
            park_filename = park['AA']
            parkLabel = park['Name']
##            clocks[parkLabel].config(fg='Black')
            entries[parkLabel].config(foreground='black')
            try:
                data = db.readdb(park_filename)[date_asked]
                in_entry = 'PR: ' + str(data['PRdaily']) + '%, Energy: ' + str(data['Edaily']) + 'KW'
                entries[parkLabel].delete(0, END)
                entries[parkLabel].insert(0, in_entry)
                last_time = data['Clock'][data['Clock'].keys()[0]][-1][0:5] #ouf...
                clocks[parkLabel].config(text=last_time)
                park.update( {'PRdaily': data['PRdaily'], 'Edaily': data['Edaily'] })
##                print park.keys()
            except KeyError:
                entries[parkLabel].delete(0, END)
                clocks[parkLabel].config(text='')
            except IOError:
                entries[parkLabel].delete(0, END)
                clocks[parkLabel].config(text='')                

    
    options['dateentry'] = Label(lowbar, )
    options['dateentry'].grid(row=0, column=15, sticky=E)
    options['date'] = date.today()
    options['dateentry'].config(text=options['date'].strftime('%d %b %y'))
    
    bdate = Button(lowbar, image=iconcalendar, command=lambda: customdate(parks, window))
    bdate.grid(row=0, column=16, sticky=E)
    bdate.image = iconcalendar

    try: # import last options state...
        with open('globals/' + 'options.pk', 'rb') as f:
            opts = pickle.load(f)

        for keys in opts:
            options[keys].set( opts[keys] )

    except IOError: pass
    except KeyError: pass
    except EOFError: pass
##    options['dateentry'].bind('<Double-Button-1>', customdate)
    
##    lowbar.grid_columnconfigure(1, weight=1)
##    
##    invertermenu = LabelFrame(lowbar, bg=bgr['lowbar'])
##    invertermenu.grid(row=0, column=0, sticky=W)

##    options = {} 
##    Label(lowbar, text = 'timeout(sec): ').grid(row=0,column=0)
##    timeout=Scale(lowbar, from_=10, to=300, resolution=10, orient=HORIZONTAL, font=('Helvetica',7), tickinterval=1 )
##    timeout.set(150)
##    timeout.grid(row=0, column=1)
##    options['timeout'] = timeout

##    Label(invertermenu,bg= bgr['lowbar'], text = 'tests: ').grid(row=0,column=2)
##    testbox = Spinbox(invertermenu, values = ['Online', 'Offline', 'Network'], width=7, wrap=1)
##    testbox.grid(row=0, column=3)
##    options['tests'] = testbox

##    bbadparks = Button(invertermenu, text="bad only", command=(lambda: checkbadparks(parks))).grid(row=0, column=4)#pack(side=LEFT)
##    btestAll = Button(invertermenu, text="SWEEP", command=(lambda: checkallparks(parks))).grid(row=0, column=5)#.pack(side=LEFT)

##    Label(invertermenu,bg= bgr['lowbar'], text = 'plot: ').grid(row=0,column=6)
##    plotbox = Spinbox(invertermenu, values = ['sum(Pac)','Irradiance', 'Tmodule', 'Pac',], width=10, wrap=1)
##    plotbox.grid(row=0, column=7)
##    options['plots'] = plotbox
    
##    btrack = Button(lowbar, text='TRACKERS', command=(lambda: mailclient(trackers,entriestr))).grid(row=0, column=1, sticky=E)
##    babout = Button(lowbar, text='ABOUT', command=(lambda: aboutbox())).grid(row=0, column=2, sticky=E)
##    bexit=Button(lowbar, text="Quit", command=window.quit).grid(row=0, column=3, sticky=E)#.pack(side=RIGHT)
    return window

##############################################################################################################   
def runme():#if __name__ == "__main__":
    global parks, fieldnames, ignorechar
    ignorechar = 'x'
    parks, fieldnames = loadparkscsv('parks.csv')
    parks = sorted(parks, key=lambda k: k['No'])
    window=makeWidgets()
    window.mainloop()

if __name__ == "__main__":
    parks, fieldnames = loadparkscsv('parks.csv')
    window=makeWidgets()
    window.mainloop()
