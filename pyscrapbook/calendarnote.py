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

from calendar_entries import *
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
