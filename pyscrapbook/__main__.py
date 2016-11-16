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

import cgi,datetime,time,logging,io,sys,re,webbrowser,subprocess
import urllib.parse
import urllib.request

from PyQt5 import QtGui
from PyQt5.QtWebKit import QWebSettings
from PyQt5.QtWebKitWidgets import QWebPage, QWebView
from PyQt5.QtCore import QUrl, QFileSystemWatcher
import sys,os,atexit,time,pandoc,shutil
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5 import QtCore


import config,styles,notes,plugins


__version__ ="0.1.0"


# global lists of files that are open in any tab so we don't open them twice.
#Global instead of with the notebook so that we can later add more places a note can be open.
openfiletabs = {}

supportedTypes = ["*.md", "*.rst", "*.html", "*.html", "*.html.ro", "*.txt","*.css","*.jpg","*.png","*.svg"]

builtinsdir = os.path.dirname(os.path.realpath(__file__))


class Tool():
    def __init__(self,title, function):
        self.title = title
        self.function = function

plugins.addPluginType("tool",Tool)

import calendarnote

def searchDir(dir,pattern,all=False):
        for d, dirs,files in os.walk(dir):
            try:
                for i in files:
                        if not(i.endswith(".md") or i.endswith(".html") or i.endswith(".html.ro") or i.endswith(".txt") or i.endswith(".rst")):
                            continue
                        fn = os.path.join(d,i)
                        with open(fn) as f:
                            text = f.read(2*10**6)
                        x=None
                        if all:
                            x = re.findall(pattern, text, flags=re.MULTILINE)

                        else:
                            x = re.search(pattern, text, flags=re.MULTILINE)
                        if not all:
                            if x:
                                yield (fn, x.group(0) )
                        else:
                            if x:
                                yield (fn, [i[0] for i in x] )



            except:
                logging.exception("Searching "+i+" Failed")



def findTodos(dir):
    #r = searchDir(dir,"[ ( ?)]",all=True)
    r = searchDir(dir,"^([\-\=\* \t\#\_\`\~\`\/\.\,\[\]\$\%\^\&\(\)]*?(((TODO)|(Todo)|(todo)|(done)|(Done)|(DONE)):.*))$",all=True)
    return r


class Notebook(QTabWidget):
    """
    Class representing the tabbed area in which notes are viewed.
    """
    def __init__(self):
        QTabWidget.__init__(self)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.closehandler)
        atexit.register(self.onExit)


    def closehandler(self,i):
        "Handle a user clicking a close tab button"
        if self.widget(i).path in openfiletabs:
            del openfiletabs[self.widget(i).path]
        self.widget(i).save()
        self.removeTab(i)

    def open(self,path,raw=False,create=False):
        "Open a new tab given a path to a supported file"
        # if search:
        #     scrolljs ="""
        #         var walkDOM = function (node,func) {
        #                 func(node);                     //What does this do?
        #                 node = node.firstChild;
        #                 while(node) {
        #                     walkDOM(node,func);
        #                     node = node.nextSibling;
        #                 }
        #
        #             };
        #
        #          lookFor = function(str)
        #          {
        #
        #             var c = function(node)
        #                 {
        #                  if (node.innerText.indexOf(str) != -1)
        #                  {
        #                     window.scrollTo(0,node.offsetTop);
        #                  }
        #                 }
        #          }
        #
        #          walkDOM(document.body, lookFor("THING_TO_SEARCH_FOR"))
        #
        #     """.replace("THING_TO_SEARCH_FOR", search)

        if not path.startswith("mdnotes://"):
            pass
        else:
            path =path[len("mdnotes://"):]
            path = os.path.join(builtinsdir, path)
        try:
            #Don't allow the user to open a file that already is open
            #If they try, just go to that tab
            if  path in openfiletabs:
                for i in range(self.count()):
                    if self.widget(i).path == path:
                        self.setCurrentIndex(i)
            else:
                #If file exists, open it and jump to that tab
                edit = notes.noteFromFile(path,self,raw=raw)
                self.addTab(edit,os.path.basename(path))
                self.setCurrentIndex(self.count()-1)
                openfiletabs[path] = edit
                # if search:
                #     edit.edit.page().mainFrame().evaluateJavaScript(scrolljs)

        except:
            logging.exception("Could not open file "+path)


    def add(self,tab,path):
        self.addTab(tab,path)
        self.setCurrentIndex(self.count()-1)

    def openVirtual(self,html,title,onclose=None,reloader=None,reloadbutton=False):
        "Open a new tab and load some html"
        try:
            edit = notes.VirtualNote(self,html=html,onclose=onclose,reloader=reloader,reloadbutton=reloadbutton)
            self.addTab(edit,title)
            self.setCurrentIndex(self.count()-1)
            return edit
        except:
            logging.exception("Could not open virtual file "+title)

    def onExit(self):
        "Save everything on shutdown"
        for i in range(self.count()):
            self.widget(i).onClose()
            if self.widget(i).path in openfiletabs:
                del openfiletabs[self.widget(i).path]

class CustomTreeView(QTreeView):
    "A modified tree view that can move md files and fix the llinks so they still work"
    def dropEvent(self,e):
        #Get the place it's being dropped at
        try:
            i=self.indexAt(e.pos())
            target= self.model().filePath(i)
            #If not at a folder, get the folder

            if not os.path.isdir(target):
                target = os.path.dirname(target)

            if e.mimeData().hasUrls():
                n = e.mimeData().urls()[0].toString()
                if n.startswith("file://"):
                    n=n[len("file://"):]
                    if os.path.isfile(n):
                        self.moveFile(n,target)
        except:
            logging.exception("Could not move file or folder.")

    def moveFile(self,old, newdir):
        """
        Move a markdown file from path old to newdir
        Modify every relative link in md so that if the file is moved from oldlocation to newlocation the links still work.
        Actually, don't implement that quite yet, it might be useless
        """
        # #Can't overwrite stuff.

        #
        # if old.endswith('.md'):
        #     oldlocation = os.path.dirname(old)
        #     with open(old) as f:
        #         md = f.read()
        #
        #     for i in re.finditer("\[(.*?)\](:?)\((.*?)\)",md):
        #             link = os.path.join(oldlocation,i.group(3))
        #             link = os.path.relpath(link, newdir)
        #             #i[0] being the entire regex, we replace it with a new modified one that we build up from pieces of the old one.
        #             md = md.replace(i.group(0), "["+i.group(1)+"]" +i.group(2)+  "("+link+")"   )
        #
        #     #Write the new modified file in the new location
        #     with open(os.path.join(newdir,os.path.basename(old)),'w') as f:
        #         f.write(md)
        #     #Delete the copy in the old location after we have out new modified one.
        #     os.remove(old)
        # else:

        if os.path.exists(os.path.join(newdir,os.path.basename(old))):
            raise RuntimeError("Refusing to overwrite existing file or directory")
        os.rename(old,os.path.join(newdir,os.path.basename(old))  )

    #todo: refactor this to emit a custom signal? s
    def mouseDoubleClickEvent(self, e):
        "We reimplement this to prevent the double click from renaming on double clicks"
        i=self.indexAt(e.pos())
        target= self.model().filePath(i)
        self.nb.open(target)


class Browser(QWidget):
    "Class representing the file browser tree and associated command buttons and menus"
    def __init__(self, book):
        "Book must be an associated notebook that this Browser is 'controlling'"
        self.nb = book
        QWidget.__init__(self)
        self.lo = QVBoxLayout()
        self.setLayout(self.lo)
        #SEtup file system model
        self.files = QFileSystemModel()
        self.files.setReadOnly(False)
        self.files.setNameFilters(supportedTypes)
        if config.notespath:
            self.files.setRootPath(config.notespath)

        #Setup the view over that
        self.fv = CustomTreeView()
        self.fv.setModel(self.files)
        self.fv.hideColumn(2)
        self.fv.hideColumn(3)
        self.fv.hideColumn(1)
        self.fv.resizeColumnToContents(0)
        self.fv.setAutoScroll(True)
        #We pass it a reference so it can open things in the notebook
        self.fv.nb=book
        #I don't know what that line does, but it's important!!!!
        self.fv.setRootIndex(self.files.setRootPath("/Users"))

        #self.fv.doubleClicked.connect(self.dblclk)
        self.fv.expanded.connect(lambda x:     self.fv.resizeColumnToContents(0))
        self.fv.clicked.connect(lambda x:     self.fv.resizeColumnToContents(0))
        self.fv.setDragEnabled(True)
        self.fv.setDragDropMode(QAbstractItemView.DragDrop)
        self.fv.setAcceptDrops(True)
        self.lo.addWidget(self.fv)


        #Credit to vahancho http://stackoverflow.com/questions/22198427/adding-a-right-click-menu-for-specific-items-in-qtreeview
        self.fv.setContextMenuPolicy(Qt.CustomContextMenu);
        self.fv.customContextMenuRequested.connect(self.onCustomContextMenu);


    def onCustomContextMenu(self, point):
        if not config.notespath:
            return
        i=self.fv.indexAt(point)
        #Build the menu itself.
        menu = QMenu()
        delete = QAction("Delete",self)
        archive = QAction("Archive",self)
        newmd = QAction("New Note(md)",self)
        newf= QAction("New Folder",self)
        newfile= QAction("New File",self)
        search= QAction("Search",self)
        editr= QAction("Edit Raw",self)

        menu.addAction(newf)
        menu.addAction(newmd)
        menu.addAction(newfile)
        menu.addAction(delete)
        menu.addAction(archive)
        menu.addAction(search)
        menu.addAction(editr)

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
                newp = os.path.join(archive, os.path.relpath(path, config.notespath))
                if not os.path.isdir(os.path.dirname(newp)):
                    os.makedirs(os.path.dirname(newp), '700')
                if not os.path.exists(newp):
                    os.rename(path,newp)
                else:
                    os.rename(path,os.path.dirname(newp)+"."+str(time.time())+os.path.basename(newp))

        #User has chosen to create note
        if k == newmd:
                path = self.files.filePath(i) or config.notespath
                if not os.path.isdir(path):
                    path = os.path.dirname(path)
                text, ok = QInputDialog.getText(self, 'New Note', 'Name(no extension needed):')
                newp = os.path.join(path,text+".md")
                if ok and not os.path.exists(newp):
                    with open(newp, "w") as f:
                        f.write("# Heading\ntext content")
                self.nb.open(newp)

        #User has chosen to create file
        if k == newfile:
                path = self.files.filePath(i) or config.notespath
                if not os.path.isdir(path):
                    path = os.path.dirname(path)
                text, ok = QInputDialog.getText(self, 'New File', 'Name(including extension):')
                newp = os.path.join(path,text)
                if ok and not os.path.exists(newp):
                    with open(newp, "w") as f:
                        f.write("")
                self.nb.open(newp)

        #Uer has chosen to create one folder
        if k == newf:
                path = self.files.filePath(i) or config.notespath
                if not os.path.isdir(path):
                    path = os.path.dirname(path)
                text, ok = QInputDialog.getText(self, 'New Folder', 'Name:')
                newp = os.path.join(path,text)
                if ok and not os.path.exists(newp):
                    os.mkdir(newp)

        #Uer has chosen to create one folder
        if k == search:
            path = self.files.filePath(i) or config.notespath
            if not os.path.isdir(path):
                path = os.path.dirname(path)
            text, ok = QInputDialog.getText(self, 'Search', 'Pattern')
            x=[0]

            #Allow the user to stop the search by closing the search results tab.
            def stop(o):
                x[0]=True
            if ok:
                html = "<style>"+styles.style+'</style>'+"<h1>Search Results</h2><dl>"
                tab = self.nb.openVirtual(html=html,title="Search Results",onclose=stop)
                for f,c in (searchDir(path,"^.*?"+text.replace(".","\\")+".*?$")):
                    app.processEvents()
                    if x[0]:
                        break
                    html=html+'<dt><a href="'+f+'">'+f+'</a></dt><dd>'+str(c)+'</dd>'
                html+= '</dl>'
                tab.setHtml(html)

        #Uer has chosen to create one folder
        if k == editr:
            if  os.path.isfile(path):
                self.nb.open(path,raw=True)








class App(QMainWindow):
    "Class representinf the main app window"
    def __init__(self):
        QMainWindow.__init__(self)
        self.setWindowTitle('Scrapbook ('+config.notespath+')')
        self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(os.path.realpath(__file__)), "W_Book01.png" )))
        #Setup menu bar
        self.menubar = self.menuBar()
        self.fileMenu = self.menubar.addMenu('&File')
        self.tools = self.menubar.addMenu('&Tools')
        self.help = self.menubar.addMenu('&Help')

        opennotebook = QAction('Open Notebok Folder', self)
        def opennb(*a):
            b = QFileDialog.getExistingDirectory(self, "Open Directory",
                                                os.path.expanduser("~"),
                                                QFileDialog.ShowDirsOnly
                                                | QFileDialog.DontResolveSymlinks)
            subprocess.Popen([os.path.realpath(__file__), b], close_fds=True)
        opennotebook.triggered.connect(opennb)
        self.fileMenu.addAction(opennotebook)


        setnotebook = QAction('Set as Default Notebook', self)


        def setnb(*a):
            if config.notespath:
                config.setNotebookLocation(config.notespath)
        setnotebook.triggered.connect(setnb)
        self.fileMenu.addAction(setnotebook)

        showabout = QAction('About', self)
        def f(*a):
            self.tabs.open("mdnotes://about.html")
        showabout.triggered.connect(f)
        self.help.addAction(showabout)

        #Make a folder for each of our builtins in the builtins folder. Right now it's just an example though
        for i in [i for i in os.listdir(os.path.join(os.path.dirname(os.path.realpath(__file__)),'builtins')) if os.path.isfile(os.path.join(os.path.dirname(os.path.realpath(__file__)),'builtins',i))]:
            a = QAction(i[:-8], self)
            def f(*a):
                self.tabs.open(os.path.join(os.path.dirname(os.path.realpath(__file__)),'builtins',i))
            a.triggered.connect(f)
            self.tools.addAction(a)

        for i in plugins.getPlugins("tool"):
            a = QAction(i.title, self)
            def f(*a):
                i.function(self.tabs)
            a.triggered.connect(f)
            self.tools.addAction(a)
        #
        # editcss = QAction('Edit User CSS Theme', self)
        # def f(*a):
        #     self.tabs.open(os.expanduser("~/.mdnotes/style.css"))
        # editcss.triggered.connect(f)

        showtodos = QAction('Todo List', self)

        #Use x[0] as a mutable flag to stop the search
        x=[0]
        def stop(o):
            x[0]=1

        def f(*a):
            if not config.notespath:
                return
            html = "<style>"+styles.style+'</style>'+"""<h1>Todos in this notebook</h2><p>Add todo entries by putting todo: something, Todo: A thing, or TODO: this thing
            anywhere in any .md note in the notebook folder, with one todo per line. There should not be any letters of numbers before the todo: marker.
              Change them to done: to indicate you have done them.<dl>"""
            tab = self.tabs.openVirtual(html=html,title="Todo List")
            for f,c in (findTodos(config.notespath)):
                #Keep the program responsive
                app.processEvents()
                if x[0]:
                    break
                html=html+'<dt>In <a href="'+f+'">'+f+'</a>:</dt><dd><ul>'
                for i in c:
                    todo = str(i)
                    text = re.search("((TODO)|(Todo)|(todo)|(done)|(Done)|(DONE)):(.*)", todo).group(8)
                    if re.match("^.*((done)|(Done)|(DONE)):",todo):
                        html+=("<li><s>"+text+"</s></li>")
                    else:
                        #Exclamation points make it bold.
                        if "!" in todo:
                            html+=("<li><b>"+text+"</b></li>")
                        else:
                            html+=("<li>"+text+"</li>")
                html+=("</li></dd>")
            html+= '</dl>'
            tab.setHtml(html)

        showtodos.triggered.connect(f)
        self.tools.addAction(showtodos)

        self.split = QSplitter()
        self.setCentralWidget(self.split)
        self.tabs = Notebook()
        self.browser = Browser(self.tabs)
        self.split.addWidget(self.browser)

        self.split.addWidget(self.tabs)
        self.split.setSizes([250,900])

if __name__ == '__main__':

    #Get the user's chosen notebook folder
    config.getNotebookLocation()
    #Find and get the config file
    config.loadConfigFiles()

    styles.loadCSS()

     #Set up the top level UI
    app = QApplication(sys.argv)
    app.setStyleSheet(styles.style)

    w = App()
    w.showMaximized()

    sys.exit(app.exec_())
