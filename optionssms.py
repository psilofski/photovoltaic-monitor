from Tkinter import *
from ttk import *
import tkMessageBox
import os, pickle
from essentials import sendreport, send_sms

class Dialog(Toplevel):

    def __init__(self, parent, title = None):

        Toplevel.__init__(self, parent)
        self.transient(parent)

        if title:
            self.title(title)

        self.parent = parent

        self.result = None

        body = Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)

        self.buttonbox()

        self.grab_set()

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                  parent.winfo_rooty()+50))

        self.initial_focus.focus_set()

        self.wait_window(self)

    #
    # construction hooks

    def body(self, master):
        # create dialog body.  return widget that should have
        # initial focus.  this method should be overridden
        Label(master, text = 'SMS Report', font = "Helvetica 10 bold").grid(row=0, columnspan=2)
        Label(master, text = 'Provider: ').grid(row=1, sticky=E)
        self.pr = StringVar()
        self.prb = Combobox(master, textvariable=self.pr, values=['world-text.com', 'easysms.gr'])#, wrap=1)
        self.prb.grid(row=1, column=1)
        
        Label(master, text="Username:").grid(row=2, sticky=E)
        Label(master, text="Password:").grid(row=3, sticky=E)

        self.e1 = Entry(master)
        self.e2 = Entry(master, show="*")

        self.e1.grid(row=2, column=1)
        self.e2.grid(row=3, column=1)
        Label(master, text="Report Items: ").grid(row=5, column=0, sticky=E)

        self.cdate = IntVar()
        self.ck1 = Checkbutton(master, text="Date", variable=self.cdate)
        self.ck1.grid(row=5, column=1, columnspan=2, sticky=W)
        self.cname = IntVar()
        self.ck2 = Checkbutton(master, text="Park Name", variable=self.cname)
        self.ck2.grid(row=6, column=1, columnspan=2, sticky=W)
        self.cEn = IntVar()
        self.ck3 = Checkbutton(master, text="Total Energy", variable=self.cEn)
        self.ck3.grid(row=7, column=1, columnspan=2, sticky=W)
        self.cPR = IntVar()
        self.ck4 = Checkbutton(master, text="Performance Ratio", variable=self.cPR)
        self.ck4.grid(row=8, column=1, columnspan=2, sticky=W)
        self.ceuro = IntVar()
        self.ck5 = Checkbutton(master, text="Monetary Gain", variable=self.ceuro)
        self.ck5.grid(row=9, column=1, columnspan=2, sticky=W)

        #E-mail configuration
        style = Style()
        style.configure("BW.TLabel", background="black")
##        style.configure('TLabelframe.Label', font='bold')
        
        Frame(master, height=200, width=1, style="BW.TLabel").grid(row=0, column=2, rowspan=10) #separator
        
        Label(master, text='Auto Error Report', font = "Helvetica 10 bold").grid(row=0, column=3, columnspan=2)
        Label(master, text='Email:').grid(row=1, column=3, sticky=E)

        self.ers = IntVar()
        Checkbutton(master, text='Mobile:', variable=self.ers).grid(row=2, column=3, sticky=E)

        self.em = Entry(master)
        self.mob = Entry(master)

        self.em.grid(row=1, column=4)
        self.mob.grid(row=2, column=4)

        Button(master, text="Test Email", width=10, command=self.testemail).grid(row=3, column=3, sticky=E)
        Button(master, text="Test SMS", width=10, command=self.testsms).grid(row=3, column=4, sticky=W)

        # Tracker monitoring configuration
        Frame(master, height=1, width=200, style="BW.TLabel").grid(row=4, column=3, columnspan=2) #separator
        
        Label(master, text="Trackers (mailbox config)", font = "Helvetica 10 bold").grid(row=5, column=3, columnspan=2)
        
        Label(master, text="Server:").grid(row=6, column=3, sticky=E)
        Label(master, text="User:").grid(row=7, column=3, sticky=E)
        Label(master, text="Password:").grid(row=8, column=3, sticky=E)
        Label(master, text="Filter:").grid(row=9, column=3, sticky=E)

        self.tr1 = Entry(master)
        self.tr2 = Entry(master)
        self.tr3 = Entry(master, show="*")
        self.tr4 = Entry(master)

        self.tr1.grid(row=6, column=4)
        self.tr2.grid(row=7, column=4)
        self.tr3.grid(row=8, column=4)
        self.tr4.grid(row=9, column=4)          
        
        try:
            with open('globals/' + 'authsms.pk', 'rb') as f:
                auth = pickle.load(f)
                
                username = auth['username']
                password = auth['password']
                provider = auth['provider']
                options = auth['options']

                email = auth['email']
                mobile = auth['mobile']
                errsms = auth['errsms']
                
            self.prb.icursor(1)
            self.pr.set(provider)
            self.e1.insert(0, username)
            self.e2.insert(0, password)
            self.cdate.set(options['date'])
            self.cname.set(options['name'])
            self.cEn.set(options['En'])
            self.cPR.set(options['PR'])
            self.ceuro.set(options['euro'])

            self.em.insert(0, email)
            self.mob.insert(0, mobile)
            self.ers.set(errsms)

            #Trackers
            self.tr1.insert(0, auth['trServer'])
            self.tr2.insert(0, auth['trUser'])
            self.tr3.insert(0, auth['trPass'])
            self.tr4.insert(0, auth['trFilter'])

        except IOError:
            pass
        except KeyError:
            pass


    def testemail(self):
        email = self.em.get()
        sendreport('testing...', 'PV Monitor test e-mail \nIt works fine!', email)
        tkMessageBox.showinfo ('E-mail sent!', 'Please, check ' + email + ' inbox for a testing E-mail')
        
    def testsms(self):
        mobile = self.mob.get()
        smsauth = {'provider': self.pr.get(),
                   'username':self.e1.get(),
                   'password': self.e2.get()}
        res, smscredits, success = send_sms(mobile, 'PV Monitor test SMS \nIt works fine!', smsauth)
        if success is True:
            tkMessageBox.showinfo ('SMS Sent', 'Test SMS succesfully sent!')
        else:
            tkMessageBox.showerror ('SMS Error', 'Could not send test SMS...')    
        
    def buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons
        
        box = Frame(self)

        w = Button(box, text="Save", width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=5)

        self.bind("&lt;Return>", self.ok)
        self.bind("&lt;Escape>", self.cancel)

        box.pack()

    #
    # standard button semantics

    def ok(self, event=None):

        if not self.validate():
            self.initial_focus.focus_set() # put focus back
            return

        self.withdraw()
        self.update_idletasks()

        self.apply()

        self.cancel()

    def cancel(self, event=None):

        # put focus back to the parent window
        self.parent.focus_set()
        self.destroy()

    #
    # command hooks

    def validate(self):

        return 1 # override

    def apply(self):
        # SMS
        provider = self.pr.get()
        username = self.e1.get()
        password = self.e2.get()
        options = {'date': self.cdate.get(),
                   'name': self.cname.get(),
                   'En': self.cEn.get(),
                   'PR': self.cPR.get(),
                   'euro': self.ceuro.get()}
        
        # Auto report
        email = self.em.get()
        mobile = self.mob.get()
        errsms = self.ers.get()

        # Trackers
        trServer = self.tr1.get()
        trUser = self.tr2.get()
        trPass = self.tr3.get()
        trFilter = self.tr4.get()
        
##        showdate = self.cdate.get()
        smsauth = {'provider':provider,
                   'username':username,
                   'password': password,
                   'options': options,
                   
                   'email': email,
                   'mobile': mobile,
                   'errsms': errsms,
                   
                   'trServer': trServer,
                   'trUser': trUser,
                   'trPass': trPass,
                   'trFilter': trFilter
                   }
        
##        print smsauth # or something
        with open('globals/' + 'authsms.pk', 'wb') as f:
            pickle.dump(smsauth, f)        
