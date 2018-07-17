#!/usr/bin/python
# -*- coding: utf-8 -*-

#http://www.doughellmann.com/PyMOTW/imaplib/  ####LOTS TO LEARN...####

from Tkinter import * 
import imaplib, string, StringIO, rfc822
import time
import pickle



###USER = 'trackers@plasisgroup.com'
###PASSWORD = 'pla123'
##readfilter = '(FROM "atlas@mechatron.gr")'
##USER = 'pv-monitoring@plasisgroup.com'
##PASSWORD = 'pvmon123*()'

def stopme(bstop):
   print 'Stop...'
   bstop.destroy()

def mailclient(parks, entries):

   try:
      with open('globals/' + 'authsms.pk', 'rb') as f:
         auth = pickle.load(f)
                      
      SERVER = auth['trServer']
      USER = auth['trUser']
      PASSWORD = auth['trPass']
      readfilter = auth['trFilter']

   except IOError:
      pass
   except KeyError:
      pass

##    bstop = Button(lowbar, text='Stop', command=(lambda: stopme(bstop))).grid(row=0, column=1)
##    lowbar.update()
    # Connect & login
   server = imaplib.IMAP4(SERVER)
   server.login(USER, PASSWORD)
   server.select()

   resp, items = server.search(None, readfilter) #(None, '(FLAGS "\\Recent")')
   items = string.split(items[0])
   mesgs = len(items)
   print mesgs
   if mesgs > 600: items = items[-600:] # read "only" 500 last mails...
   for mail in items: #[600:-1]: # last 600 mails to read...
     resp, data = server.fetch(mail, "(RFC822)")
     text = data[0][1]
     message = rfc822.Message(StringIO.StringIO(text))
     #try:
     received = str(message.getallmatchingheaders('Received')).split(';')[1][12:20]
     subject = str(message.getallmatchingheaders('Subject')).split(':')
     eols = -6 #end of line characters in subject

     parkname = subject[1][6:]
     try: ########################################################
         TrackerNo = subject[3][1]
         if subject[2] == '  Tracker' or subject[2] == ' Tracker':
             status = subject[3][3:eols]
         elif subject[2][2:7] == 'Event':
             status = subject[2].split(',')[0][-2:]
     except IndexError: #Server restart
         status = '000'
         TrackerNo = '1'            
         
     for park in parks:
         if park['parkNameTracker'] == parkname:
             if status == 'OK' or status == 'RTC Error' or status == '000':
                 entries[parkname][TrackerNo].config(foreground='Grey')
             elif status == '13' or status == '27':
                 entries[parkname][TrackerNo].config(foreground='Black')
             elif status == '28' or status == '29' or status == ' 7':
                 entries[parkname][TrackerNo].config(foreground='Red')
             else:
                 entries[parkname][TrackerNo].config(foreground='Purple')                
             entries[parkname][TrackerNo].delete(0, END)
             entries[parkname][TrackerNo].insert(0, status)

             
   def cleanmailbox(maxmailbox):
     try:
         for mail in items[0:-maxmailbox]:
             res, error = server.store(mail, '+FLAGS', '\\Deleted')
         resp, data = server.expunge() ##Perform actual deleting
         resp = 'mailbox cleaned'
     except IndexError: resp = 'mailbox is clean'
   return resp

   ##    if mesgs>4000: print cleanmailbox(3000)
        
   server.logout()                          
   return


def makewidgets():
    master = Tk()
    master.title(apptitle)
    frame = Frame(master, bd=2, relief=SUNKEN)
    frame.grid(row=0, column=0)
    form = Frame(frame, bd=2, relief=SUNKEN)
    form.grid(row=0, column=0, sticky=N+S+E+W)
    entries = {}
    for (ix, park) in enumerate(parks):
        i_p = park['AA']
        parkname = park['parkNameTracker']
        aa = Label(form, text=i_p).grid(row=ix, column=0)
        name = Label(form, text=park['Name']).grid(row=ix, column=1)
        trName = Label(form, text=parkname, fg='Blue').grid(row=ix, column=2)
        entries[parkname] = {}
        for iy in range(int(park['NofTrackers'])):
           ent = Entry(form, width=3)
           ent.grid(row=ix, column=3+iy, sticky=E+W)
           #entries[label][str(iy+1)] = ent
           entries[parkname][str(iy+1)]=ent
           
    lowbar = Frame(frame)
    lowbar.grid(row=1, column=0)
    brun = Button(lowbar, text='run', command=(lambda: mailclient(parks, entries))).grid(row=0, column=0)
    bexit=Button(lowbar, text="Quit", command=master.quit).grid(row=0, column=2, sticky=E)#.pack(side=RIGHT)
    ent = Entry(lowbar, width=8).grid(row=0, column=3, sticky=E)
    entries['clock'] = ent
    return master   

   
   
if __name__ == "__main__":
    from monitor import loadparkscsv
    parka, fieldnames = loadparkscsv('parks.csv')
    parks = []
    for park in parka:
        if park['parkNameTracker'] != '':
            parks.append(park)
    apptitle = 'Tracker - monitoring'
    master = makewidgets()
    master.mainloop()
