#!/usr/bin/python3
# -*- coding: utf-8 -*-

# COPYRIGHT (c) 2016 Daniel Dunn
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


#Many thanks to the ZetCode PyQt5 tutorial

import cgi,datetime,time,logging,io,sys
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

from html.parser import HTMLParser

class MyHTMLParser(HTMLParser):
    "Class used in downloadAllImages"
    def __init__(self):
        HTMLParser.__init__(self)
        self.images = []

    def handle_data(self, data):
        pass

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            src = [i for i in attrs if i[0] =='src']
            src = src[0][1] if src else None
            self.images.append(src)

    def handle_endtag(self, tag):
        pass

count = int(time.time())

def downloadAllImages(h,path):
    """
    Given an html string h and a path to a file, download all images into a folder in the same dir as path,
    and modify the HTML itself to point to our new local copy. Return the modified HTML.
    """
    global count
    p = MyHTMLParser()
    p.feed(h)
    for i in p.images:
        try:
            if not (i.startswith("http") or i.startswith("file")):
                continue
            if not(os.path.exists(path+"_img")):
                os.mkdir(path+"_img")
            fp = os.path.join(path+"_img", "img_"+str(count)+"."+('png' if '.png' in i else 'jpg' if '.jpg' in i else 'svg' if '.svg' in i else 'image')  )
            count+=1
            urllib.request.urlretrieve(i, filename=fp)
            h = h.replace(i, os.path.relpath(fp, os.path.dirname(path)))
        except:
            logging.exception("Error getting image "+i)
    return h


def interpretcnfpath(p):
    return os.path.join(os.path.dirname(__file__),os.path.expanduser(p))


def striptrailingnumbers(t):
    while t and t[-1] in '~1234567890.':
        t = t[:-1]
    return t



def onClose():
    "Save everything on shutdown"
    for i in range(tabs.count()):
        tabs.widget(i).onClose()
        if tabs.widget(i).path in openfiletabs:
            del openfiletabs[tabs.widget(i).path]
atexit.register(onClose)


class NoteToolBar(QWidget):
    "Represents the toolbar for a note."
    def __init__(self,note):
        QWidget.__init__(self)
        self.edit = note.edit
        self.note = note
        self.lo= QHBoxLayout()
        self.setLayout(self.lo)

        def save(d):
            self.note.save()
        self.save = QPushButton("Save")
        self.save.clicked.connect(save)
        self.lo.addWidget(self.save)

        def bold(d):
            self.edit.page().mainFrame().evaluateJavaScript("document.execCommand('bold');")
        self.boldbutton = QPushButton("Bold")
        self.boldbutton.clicked.connect(bold)
        self.lo.addWidget(self.boldbutton)


        def h1(d):
            if(len(self.edit.selectedText())< 80):
                self.edit.page().mainFrame().evaluateJavaScript("document.execCommand('formatBlock',false,'h1');")
        self.h1button = QPushButton("H1")
        self.h1button.clicked.connect(h1)
        self.lo.addWidget(self.h1button)

        def h2(d):
            if(len(self.edit.selectedText())< 80):
                self.edit.page().mainFrame().evaluateJavaScript("document.execCommand('formatBlock',false,'h2');")
        self.h2button = QPushButton("H2")
        self.h2button.clicked.connect(h2)
        self.lo.addWidget(self.h2button)

        def h3(d):
            if(len(self.edit.selectedText())< 80):
                self.edit.page().mainFrame().evaluateJavaScript("document.execCommand('formatBlock',false,'h3');")
        self.h3button = QPushButton("H3")
        self.h3button.clicked.connect(h3)
        self.lo.addWidget(self.h3button)

        def h4(d):
            if(len(self.edit.selectedText())< 80):
                self.edit.page().mainFrame().evaluateJavaScript("document.execCommand('formatBlock',false,'h4');")
        self.h3button = QPushButton("H4")
        self.h3button.clicked.connect(h4)
        self.lo.addWidget(self.h3button)

        def normal(d):
            self.edit.page().mainFrame().evaluateJavaScript('document.execCommand("removeFormat");')
        self.normal = QPushButton("Normal")
        self.normal.clicked.connect(normal)
        self.lo.addWidget(self.normal)

        def Timestamp(d):
            t =datetime.datetime.now().strftime('%b %d %I:%M%p %G')
            self.edit.page().mainFrame().evaluateJavaScript('document.execCommand("insertHTML",false,"' +t+ '");' )
        self.ts = QPushButton("Timestamp")
        self.ts.clicked.connect(Timestamp)
        self.lo.addWidget(self.ts)

        def Image(d):
            text, ok = QInputDialog.getText(self, 'New Image', 'Location(URL or file:/// address):')
            if ok:
                self.edit.page().mainFrame().evaluateJavaScript('document.execCommand("insertImage",false,"' +text+ '");' )


        self.img = QPushButton("Image")
        self.img.clicked.connect(Image)
        self.lo.addWidget(self.img)


class Note(QWidget):
    def __init__(self,path,notebook):
        """
        Class representing the actual tab pane for a note file, and the save/load logic
        path is the path to the file(which does not need to exist yet)
        notebook must be the Notebook instance the note will be a part of

        """
        QWidget.__init__(self)
        self.notebook = notebook
        self.path = path

        #Set up the embedded webkit
        self.edit = QWebView()
        self.edit.page().setContentEditable(True)
        self.edit.settings().setAttribute(QWebSettings.JavascriptEnabled,True)
        def openLink(url):
            self.notebook.open(os.path.join(os.path.dirname(self.path),url.toString() ))
        self.edit.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.edit.page().linkClicked.connect(openLink)

        #set up the toolbar
        self.tools = QWidget()
        self.tools.lo = QHBoxLayout()
        self.tools.setLayout(self.tools.lo)

        #Watch the file so we can auto reload
        self.watcher = QFileSystemWatcher()
        self.watcher.addPath(self.path)
        self.watcher.fileChanged.connect(self.reload)

        #from http://ralsina.me/weblog/posts/BB948.html
        #Add a search feature
        self.search = QLineEdit(returnPressed = lambda: self.edit.findText(self.search.text()))
        self.search.hide()
        self.showSearch = QShortcut("Ctrl+F", self, activated = lambda: (self.search.show() , self.search.setFocus()))

        #Put the widgets together
        self.lo = QVBoxLayout()
        self.setLayout(self.lo)
        self.tools= NoteToolBar(self)
        self.lo.addWidget(self.tools)
        self.lo.addWidget(self.edit)
        if os.path.isfile(self.path):
            with open(self.path,"rb") as f:
                s = f.read()

        #now we are going to use pandoc to convert to html
        doc = pandoc.Document()

        #Figure out the input format. We back things up and archive them by appenting a Timestamp
        #to the end or else a ~. That function strips both of those things.
        if striptrailingnumbers(self.path).endswith(".html"):
            doc.html = s

        if striptrailingnumbers(self.path).endswith(".md"):
            doc.markdown = s

        elif striptrailingnumbers(self.path).endswith(".rst"):
            doc.rst = s
        else:
            raise RuntimeError("Bad filetype")

        #Add the CSS file before the HTML
        d="<style>"+style+"</style>"
        d += doc.html.decode("utf-8")

        self.edit.setHtml(d,QUrl("file://"+self.path))


    def onClose(self):
        "Handle closing the tab or the whole program"
        self.watcher.removePath(self.path)
        self.save()

    def save(self):
        "Save the file if it needs saving"
        if not self.edit.page().isModified():
            return

        #Back Up File
        buf =None
        #If the file exists, copy it to file~ first. If that exists, copy it to file4857475928345
        if os.path.exists(self.path):
            if not os.path.exists(self.path+"~"):
                buf=(self.path+"~")
                shutil.copy(self.path, self.path+"~")
            else:
                buf = self.path+str(time.time())
                shutil.copy(self.path,buf )

        #Again, pandoc to convert to the proper format
        doc = pandoc.Document()
        doc.html = downloadAllImages(self.edit.page().mainFrame().toHtml(),self.path).encode("utf-8")

        if  striptrailingnumbers(self.path).endswith("md"):
            with open(self.path,"wb") as f:
                f.write(doc.markdown_github)

        if  striptrailingnumbers(self.path).endswith("rst"):
            with open(self.path,"wb") as f:
                f.write(doc.rst)

        if  striptrailingnumbers(self.path).endswith("html"):
            with open(self.path,"wb") as f:
                f.write(doc.html)

        if buf and os.path.isfile(buf):
            os.remove(buf)

    #TODO: un-duplicate the load code. Also, this doesn't check format. bad.
    def reload(self,dummy=True):
        "Reload the file from disk"
        if os.path.isfile(self.path):
            with open(self.path,"rb") as f:
                s = f.read()
            doc = pandoc.Document()
            doc.markdown = s
        d="<style>"+style+"</style>"
        d += doc.html.decode("utf-8")
        self.edit.setHtml(d,QUrl("file://"+self.path))



class Notebook(QTabWidget):
    "Class representing the tabbed area in which notes are viewed"
    def __init__(self):
        QTabWidget.__init__(self)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.closehandler)

    def closehandler(self,i):
        "Handle a user clicking a close tab button"
        if self.widget(i).path in openfiletabs:
            del openfiletabs[self.widget(i).path]
        self.widget(i).save()
        self.removeTab(i)

    def open(self,path):
        "Open a new tab given a path to a supported file"
        try:
            #Don't allow the user to open a file that already is open
            #If they try, just go to that tab
            if  path in openfiletabs:
                for i in range(self.count()):
                    if self.widget(i).path == path:
                        self.setCurrentIndex(i)
            else:
                #If the file exists, open it and go to the tab.
                if os.path.isfile(path):
                    edit = Note(path,self)
                    self.addTab(edit,os.path.basename(path))
                    self.setCurrentIndex(tabs.count()-1)
                    openfiletabs[path] = edit
        except:
            logging.exception("Could not open file "+path)

openfiletabs = {}

class Browser(QWidget):
    "Class representing the file browser tree and associated command buttons and menus"
    def __init__(self, book):
        self.nb = book
        QWidget.__init__(self)
        self.lo = QVBoxLayout()
        self.setLayout(self.lo)

        #SEtup file system model
        self.files = QFileSystemModel()
        self.files.setNameFilters(["*.md", "*.rst"])
        self.files.setRootPath(notespath)

        #Setup the view over that
        self.fv = QTreeView()
        self.fv.setModel(self.files)
        self.fv.hideColumn(2)
        self.fv.hideColumn(3)
        self.fv.hideColumn(1)
        self.fv.resizeColumnToContents(0)
        self.fv.setRootIndex(self.files.setRootPath("/Users"))
        self.fv.doubleClicked.connect(self.dblclk)
        self.fv.expanded.connect(lambda x:     self.fv.resizeColumnToContents(0))
        self.fv.clicked.connect(lambda x:     self.fv.resizeColumnToContents(0))

        self.lo.addWidget(self.fv)


        #Credit to vahancho http://stackoverflow.com/questions/22198427/adding-a-right-click-menu-for-specific-items-in-qtreeview
        self.fv.setContextMenuPolicy(Qt.CustomContextMenu);

        def onCustomContextMenu(point):
            i=self.fv.indexAt(point)
            #Build the menu itself.
            menu = QMenu()
            delete = QAction("Delete",self)
            archive = QAction("Archive",self)
            newmd = QAction("New Note",self)
            newf= QAction("New Folder",self)

            menu.addAction(newf)
            menu.addAction(newmd)
            menu.addAction(delete)
            menu.addAction(archive)

            t = time.time()
            k =menu.exec_(self.mapToGlobal(point))

            #If the menu hasn't been open for more than 0.6s,
            #assume user did not have time to properly react to it opening
            if time.time()-t <0.6:
                return
            #Get the path that this menu is for
            path = self.files.filePath(i)

            #User wants to delete something. We use send2trash to do that.
            if k == delete:
                msg =QMessageBox()
                msg.setText("Send "+path+" to trash?");
                msg.setStandardButtons(QMessageBox.Yes| QMessageBox.Cancel);

                r=msg.exec_()
                if r== QMessageBox.Yes:
                    try:
                        import send2trash
                        send2trash.send2trash(path)
                    except:
                        logging.exception("Cold not send "+path+" to the trash can")

            #User wants to send it to the archive. This seriously needs to be improved.
            if k == archive:
                msg =QMessageBox()
                msg.setText("Archive "+path+" ?");
                msg.setStandardButtons(QMessageBox.Yes| QMessageBox.Cancel);

                r=msg.exec_()
                if r== QMessageBox.Yes:
                    archive = os.path.join("/home/danny/Projects/notesapp/","archive")
                    if not os.path.isdir(archive):
                        os.mkdir(archive)
                    newp = os.path.join(archive, os.path.relpath(path, notespath))
                    if not os.path.isdir(os.path.dirname(newp)):
                        os.makedirs(os.path.dirname(newp), '700')
                    if not os.path.exists(newp):
                        os.rename(path,newp)
                    else:
                        os.rename(path,os.path.dirname(newp)+"."+str(time.time())+os.path.basename(newp))

            #User has chosen to create file
            if k == newmd:
                    path = self.files.filePath(i) or notespath
                    if os.path.isdir(path):
                        text, ok = QInputDialog.getText(self, 'New Note', 'Name:')
                        newp = os.path.join(path,text+".md")
                        if ok and not os.path.exists(newp):
                            with open(newp, "w") as f:
                                f.write("# Heading\ntext content")
                        tabs.open(newp)

            #Uer has chosen to create one folder
            if k == newf:
                    path = self.files.filePath(i) or notespath
                    if os.path.isdir(path):
                        text, ok = QInputDialog.getText(self, 'New Folder', 'Name:')
                        newp = os.path.join(path,text)
                        if ok and not os.path.exists(newp):
                            os.mkdir(newp)


        self.fv.customContextMenuRequested.connect(onCustomContextMenu);



    def dblclk(self, ind):
        self.nb.open(self.files.filePath(ind))


if __name__ == '__main__':
    #Get the notebook file either from a config file or from the command line arg
    if not len(sys.argv)>1:
        with open(os.path.expanduser("~/.mdnotes/notebooks.txt")) as f:
            t = f.read()

        t= t.replace("\r","").split("\n")

        notespath = os.path.join(os.path.expanduser(t[0]))

        if notespath.endswith("/"):
            notespath=notespath[:-1]
    else:
        notespath=sys.argv[1]



    style="""
    img
    {
    max-width:96%;
    max-height:45em;
    }
    h1
    {
    text-align:center;
    }
    h2
    {
    text-align:center;
    }
    h3
    {
    text-align:center;
    }
    h4
    {
    text-align:center;
    }
    """



    default="""
    [theme]
    css = ~/.mdnotes/style.css
    """

    config = ConfigParser(allow_no_value=True)
    config.read_string(default)
    config.read([os.path.expanduser("~/.mdnotes/default.conf"),os.path.join(notespath, 'notebook.conf')])

    css =interpretcnfpath(config.get("theme","css"))


    #Read the user's donfigured CSS if it exists
    if os.path.exists(css):
        with open(css) as f:
            style=f.read()

    #Read the notebook specific style.css which overrides that if it exists
    if os.path.exists(os.path.join(notespath,"style.css")):
        with open(os.path.join(notespath,"style.css")) as f:
            style=f.read()

     #Set up the top level UI
    app = QApplication(sys.argv)
    w = QMainWindow()

    w.resize(600, 400)
    w.move(300, 300)


    w.setWindowTitle('mdNotes')
    menubar = w.menuBar()
    fileMenu = menubar.addMenu('&File')
    w.show()


    split = QSplitter()
    w.setCentralWidget(split)
    tabs = Notebook()
    browser = Browser(tabs)
    split.addWidget(browser)

    split.addWidget(tabs)
    split.setSizes([250,900])
    sys.exit(app.exec_())
