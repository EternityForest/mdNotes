# COPYRIGHT (c) 2016 Daniel DUnn
#
# GNU GENERAL PUBLIC LICENSE
#    Version 3, 29 June 2007
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import cgi,datetime,time,logging,io,sys,re,webbrowser,subprocess
import urllib.parse
import urllib.request
from configparser import ConfigParser

from PyQt5 import QtGui
from PyQt5.QtWebKit import QWebSettings
from PyQt5.QtWebKitWidgets import QWebPage, QWebView
from PyQt5.QtCore import QUrl, QFileSystemWatcher
import sys,os,atexit,time,pandoc,shutil
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5 import QtCore

import config, styles,util,notes,plugins
from html.parser import HTMLParser

months= {
"jan":1, "january":1,
"feb":2, "february":2,
"mar":3, "march":3,
"apr":4, "april":1,
"may":5,
"jun":6, "june":6,
"jul":7, "july":7,
"aug":8, "august":8,
"sep":9, "september":9,
"oct":10, "october":10,
"nov":11, "november":11,
"dec":12, "december":12
}

def has_time(s):
    s=s.lower()
    x = re.search(r"(\d\d?):(\d\d)(:\d\d)? *?((am)|(pm))?",s)
    if x:
        return((int(x.group(1))+ (12 if x.group(6) else 0))%24 ,int(x.group(2)))

    x = re.search(r"(\d\d?) *?((am)|(pm))",s)
    if x:
        return((int(x.group(1))+ (12 if x.group(4) else 0))%24, 0)

def has_date(s):
    s=s.lower()
    month = None
    year = None
    day = None

    hd=False

    for i in months:
        if i in s:
            month = months[i]

    x = re.search(r"\d\d\d\d",s)

    if x:
        year = int(x.group(0))


    x = re.search(r" \d\d?(?![^ ])",s)
    if x:
        day = int(x.group(0))

    x = re.search(r"(\d\d\d\d)-(\d\d)-(\d\d)",s)
    if x:
        year = int(x.group(1))
        month = int(x.group(2))
        day = int(x.group(3))

    if year or month or day:
        return year, month, day


def get_calendar_entries(fn):
    #Check for a 4-digit year at some point in the first 4096 characters of the file. If there is not at least one,
    #Then assume this is not actually a journal file.
    with open(fn,'rb') as f:
        s = f.read(4096).decode(errors="surrogateescape")
        if not re.search(r"\d\d\d\d",s):
            return([])

    #Limit files to 4MB, that really should be enough for any journal file.
    with open(fn,'rb') as f:
        s = f.read(4*10**6).decode(errors="surrogateescape")
    s = s.lower()
    n = os.path.basename(fn).replace("\r","")
    o =''
    t = s.split("\n")
    y=m=d=h=mm =None

    e = []
    this_entry=''
    is_entry=None
    while t:
        i = t.pop(False)
        if i.startswith("#") or (t and (t[0].startswith("--") or t[0].startswith("==="))):
            #If the last section was a cal entry
            if is_entry:
                try:
                    #Don't allow empty entries
                    if this_entry.replace("\n",''):
                        e.append((datetime.datetime(y,m,d,h,mm),this_entry,fn))
                except( TypeError, ValueError):
                    logging.exception("Bad entry "+repr(i)+" decoded as "+ str((y,m,d,h,mm)))
                #Start new blank entry
            this_entry=''

            #Unless it has a date or a time, this section is not a cal entry.
            is_entry = False
            ht=hd=None
            if has_date(i):
                hd=has_date(i)
                y= hd[0] if not hd[0]==None else y
                m= hd[1] if not hd[1]==None else m
                d= hd[2] if not hd[2]==None else d

                #Just assume dates without times are talking about midnight
                h=0
                mm=0

            if has_time(i):
                ht=has_time(i)
                h= ht[0] if not ht[0]==None else h
                mm= ht[1] if not ht[1]==None else mm

            #Only if we have a complete date either in the title or inferred from context of previous things.
            #And if the heading actually has some time-related thing in it.
            if(not y==None) and (not m==None) and (not d==None) and (ht or hd):
                is_entry=True
        elif i.startswith("---") or i.startswith("==="):
            pass
        else:
            #Just a normal ish line of text
            this_entry += i+"\n"
    #Catch the lat entry of a file
    if is_entry:
        try:
            if this_entry:
                e.append((datetime.datetime(y,m,d,h,mm),this_entry,fn))
        except( TypeError, ValueError):
            pass
    return e





def findAllCalenderEntries(path):
    entries = []
    for root,dirs,files in os.walk(path):
        if not ".stversions" in root :
            for i in files:
                if i.endswith(".md") and not (os.path.sep+"archive"+os.path.sep in root.lower()):
                    entries.extend(get_calendar_entries(os.path.join(root,i)))
    return entries

def q2p(d):
    return datetime.datetime(d.year(),d.month(),d.day())

class DatebookNote(notes.Note):
    def __init__(self,path,notebook):
        QWidget.__init__(self)
        self.path = path

        self.notebook = notebook
        self.lo = QVBoxLayout()
        self.t = QTextEdit()
        self.t.setReadOnly(True)
        self.setLayout(self.lo)
        self.list = QListWidget()
        self.entries = findAllCalenderEntries(config.notespath)
        self.entries= sorted(self.entries,key=lambda x: x[0])

        self.split = QSplitter(Qt.Vertical)

        self.selector = QSplitter()

        self.cal = QCalendarWidget()
        now = datetime.datetime.now()
        self.cal.setSelectedDate(QtCore.QDate.currentDate())
        self.cal.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Maximum)
        self.selector.addWidget(self.cal)
        self.selector.addWidget(self.list)

        self.lo.addWidget(self.split)
        self.split.addWidget(self.selector)

        self.split.addWidget(self.t)


        def f(y=None,m=None):
            z = datetime.datetime(year=self.cal.yearShown(),month=self.cal.monthShown(),day=1)
            e = z+datetime.timedelta(days=31)
            try:
                self.populate(z,e)
            except:
                raise
        self.cal.currentPageChanged.connect(f)
        self.list.itemDoubleClicked.connect(self.onDoubleClick)
        self.list.itemClicked.connect(self.onClick)
        f()

    def populate(self,min,max):
        self.list.clear()
        for i in reversed(self.entries):
            if   min  <=i[0]<=max:
                j = QListWidgetItem(i[0].strftime(config.config.get('basic',"strftime",raw=True))+
                "\n" +
                (("TODO:" if 'todo:' in i[1][80:].lower() else "   ")+ i[1][:80]).replace("\n",'')
                )
                j.notepath = i[2]
                j.e_txt = i[1]
                self.list.addItem(j)

    def onDoubleClick(self,item):
        self.notebook.open(item.notepath)
    def onClick(self,item):
        self.t.setPlainText(item.e_txt[:2000])

    def onClose(self):
        "Handle closing the tab or the whole program"
        pass
    def save(self):
        pass

def plugin(notebook):
        notebook.add(DatebookNote("mdnotes://calendar",notebook),"mdnotes://calendar")

c = plugins.pluginClasses['tool']("Show Calendar", plugin)
plugins.addPlugin("tool",c)
