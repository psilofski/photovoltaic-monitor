from Tkinter import *
from ttk import *
import os
import datetime
import calendar

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
        Label(master, text = 'Date: ').grid(row=0, sticky=W)

        today = datetime.date.today()
        oneday = datetime.timedelta(days=1)
        onemonth = datetime.timedelta(days=30)
        startday = today - onemonth
        entryday = today
        entries = []
        while  entryday != startday:
            humanform = entryday.strftime('%d %b %y')
            entries.append(humanform)
##            dateobjlist.append(entryday)  # Create a calendar list
            entryday -= oneday           

        self.sp = StringVar()
        self.sp.set(entries[0])
        self.spb = Combobox(master, values = entries, textvariable = self.sp)
        self.spb.grid(row=0, column=1)

                    
    def buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons
        
        box = Frame(self)

        w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
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
        
        try:
            self.apply()
        except ValueError:  # nonsense in the box
            pass

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
        cdate = self.sp.get()
        cdate = datetime.datetime.strptime(cdate, '%d %b %y')
        cdate = cdate.date()
        self.result = cdate

## http://www.pythonware.com/library/tkinter/introduction/dialog-windows.htm      
