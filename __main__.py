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
from configparser import ConfigParser

from PyQt5 import QtGui
from PyQt5.QtWebKit import QWebSettings
from PyQt5.QtWebKitWidgets import QWebPage, QWebView
from PyQt5.QtCore import QUrl, QFileSystemWatcher
import sys,os,atexit,time,pandoc,shutil
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5 import QtCore

from html.parser import HTMLParser

#The absolute path to the current notebook folder, or None if there is none.
notespath = None

# global lists of diles that are open in any tab so we don't open them twice.
#Global instead of with the notebook so that we can later add more places a note can be open.
openfiletabs = {}

supportedTypes = ["*.md", "*.rst", "*.html", "*.html", "*.html.ro", "*.txt","*.css"]

builtinsdir = os.path.dirname(__file__)

defaultstyle="""
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

#These functions work based on looking in a file called .mdnotes/notebooks.txt, which is just a list of filenames, one per line.
#The first is the default notebooks directory.

def getNotebookLocation():
        "Get the notebook file either from a config file or from the command line arg"
        p=None
        if os.path.exists(os.path.expanduser("~/.mdnotes/notebooks.txt")):
            p = os.path.expanduser("~/.mdnotes/notebooks.txt")
        else:
            if os.path.exists(os.path.expanduser("~/.mdnotes/notebooks.txt")+"~"):
                p= os.path.expanduser("~/.mdnotes/notebooks.txt")+"~"


        if not len(sys.argv)>1:
            #If no config file and also no shell arg
            if not p:
                print("No notebooks.txt found")
                return os.getcwd()

            #Read the config
            with open(p) as f:
                t = f.read()

            #Get the lines, but handle bizzare newline formats
            t= t.replace("\r","").split("\n")

            #Expand the user in the first line to get the absolute pathto the default notebook
            np= os.path.join(os.path.expanduser(t[0]))

            if np.endswith("/"):
                return np[:-1]
            else:
                return np
        else:
            return sys.argv[1] if os.path.exists(sys.argv[1]) else os.getcwd()


def setNotebookLocation(l):
        "Set the default notebook file"

        #Ensure that there is actually a folder in which to store the default notebooks
        if not os.path.exists(os.path.expanduser("~/.mdnotes/")):
            os.mkdir(os.path.expanduser("~/.mdnotes/"))

        if os.path.isfile(os.path.expanduser("~/.mdnotes/notebooks.txt")):
            with open(os.path.expanduser("~/.mdnotes/notebooks.txt")) as f:
                t = f.read()

            #Make it into a list, handle odd newlines
            t= t.replace("\r","").split("\n")

            #If there's already an entry, get rid of it
            if l in t:
                t.remove(l)
        else:
            t= []

        #Put it right at the top so it's the default notebook
        t = [l]+t

        #Write it to a file
        with open(os.path.expanduser("~/.mdnotes/notebooks.txt"),"w") as f:
            f.write("\n".join(t))



def destyle_html(h):
    h = re.sub(r"<\/?span.*?>",'',h)
    h=h.replace("<p><br/><p>",'<br/>')
    return h

class cssreloader():
    def __init__(self,csspath):

        self.path = csspath
        #Watch the file so we can auto reload
        self.csswatcher = QFileSystemWatcher()
        self.csswatcher.addPath(csspath)
        self.csswatcher.fileChanged.connect(self.rlcss)
        print("Watching "+self.path)

    #Handle auto reloading the CSS theme
    def rlcss(self,*args):
        global style
        #Read the notebook specific style.css which overrides that if it exists
        if os.path.exists(self.path):
            print("reloaded "+self.path)
            with open(self.path) as f:
                style=f.read()

def initCSS(notespath,config):
    "Setup the CSS reloader watcher ad load the CSS. Requires the notes path and the config object. and returns the css text"
    #Kinda hacky having style as a  global
    global csswatcher,style
    css =interpretcnfpath(config.get("theme","css"))
    style=defaultstyle
    csspath = None
    #Read the user's donfigured CSS if it exists
    if os.path.exists(css):
        with open(css) as f:
            style=f.read()
        csspath = css

    if notespath:
        #Read the notebook specific style.css which overrides that if it exists
        if os.path.exists(os.path.join(notespath,"style.css")):
            with open(os.path.join(notespath,"style.css")) as f:
                style=f.read()
            csspath = os.path.join(notespath,"style.css")

    if csspath:
        csswatcher = cssreloader(csspath)

    return style

def initConfig(notespath):
    "Given the notes path, attempt to loaf a config object from that notes path and the user's configured notes file"

    default="""
    [basic]
    strftime = %b %d %I:%M%p %G
    [theme]
    css = ~/.mdnotes/style.css

    """
    # Maybe add this?
    # [todolist]
    # regex = ^(.*((TODO)|(Todo)|(todo)|(done)|(Done)|(DONE)):.*)$
    # ^.*((done)|(Done)|(DONE)):

    config = ConfigParser(allow_no_value=True)
    config.read_string(default)
    config.read([os.path.expanduser("~/.mdnotes/mdnotes.conf")])
    if notespath:
        config.read([os.path.join(notespath, 'notebook.conf')])
    return config

def html_resolve_paths(h):
    "Let html.ro stuff acess builtinsdir"
    return h.replace('$MDEDITBUILTINS', builtinsdir)

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
    r = searchDir(dir,"^(.*((TODO)|(Todo)|(todo)|(done)|(Done)|(DONE)):.*)$",all=True)
    return r

class NoteToolBar(QWidget):
    "Represents the toolbar for a note."
    def __init__(self,note,savable=True, reloadable=False, richtext=True):
        QWidget.__init__(self)
        self.edit = note.edit
        self.note = note
        self.lop= QVBoxLayout()

        self.lo= QHBoxLayout()
        self.lo2= QHBoxLayout()
        self.w= QWidget()
        self.w2= QWidget()
        self.w.setLayout(self.lo)
        self.w2.setLayout(self.lo2)

        self.setLayout(self.lop)
        self.lop.addWidget(self.w)
        self.lop.addWidget(self.w2)

        if savable:
            def save(d):
                self.note.save()
            self.save = QPushButton("Save")
            self.save.clicked.connect(save)
            self.lo.addWidget(self.save)

        if reloadable:
            def reload(d):
                self.note.reload()
            self.reload = QPushButton("Refresh")
            self.reload.clicked.connect(reload)
            self.lo.addWidget(self.reload)

        if richtext:
            def bold(d):
                self.edit.page().mainFrame().evaluateJavaScript("document.execCommand('bold');")
            self.boldbutton = QPushButton("Bold")
            self.boldbutton.clicked.connect(bold)
            self.lo.addWidget(self.boldbutton)

            def ital(d):
                self.edit.page().mainFrame().evaluateJavaScript("document.execCommand('italic');")
            self.ital = QPushButton("Italic")
            self.ital.clicked.connect(ital)
            self.lo.addWidget(self.ital)


            def strike(d):
                self.edit.page().mainFrame().evaluateJavaScript("document.execCommand('strikethrough');")
            self.strike = QPushButton("Strike")
            self.strike.clicked.connect(strike)
            self.lo.addWidget(self.strike)

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

            def code(d):
                self.edit.page().mainFrame().evaluateJavaScript("document.execCommand('formatBlock',false,'PRE');")
            self.code = QPushButton("Code")
            self.code.clicked.connect(code)
            self.lo2.addWidget(self.code)

            def quote(d):
                self.edit.page().mainFrame().evaluateJavaScript("document.execCommand('formatBlock',false,'BLOCKQUOTE');")
            self.quote = QPushButton("Quote")
            self.quote.clicked.connect(quote)
            self.lo2.addWidget(self.quote)

            def normal(d):
                self.edit.page().mainFrame().evaluateJavaScript('document.execCommand("removeFormat");')
            self.normal = QPushButton("Normal")
            self.normal.clicked.connect(normal)
            self.lo2.addWidget(self.normal)

            def ol(d):
                self.edit.page().mainFrame().evaluateJavaScript('document.execCommand("insertOrderedList");')
            self.ol = QPushButton("ol")
            self.ol.setToolTip("Create Ordered List")
            self.ol.clicked.connect(ol)
            self.lo2.addWidget(self.ol)

            def ul(d):
                self.edit.page().mainFrame().evaluateJavaScript('document.execCommand("insertUnorderedList");')
            self.ul = QPushButton("ul")
            self.ul.setToolTip("Create Unordered List")
            self.ul.clicked.connect(ul)
            self.lo2.addWidget(self.ul)

            def Timestamp(d):
                t =datetime.datetime.now().strftime(config.get("basic", "strftime",raw=True))
                self.edit.page().mainFrame().evaluateJavaScript('document.execCommand("insertHTML",false,"' +t+ '");' )
            self.ts = QPushButton("Timestamp")
            self.ts.clicked.connect(Timestamp)
            self.lo2.addWidget(self.ts)

            def Image(d):
                text, ok = QInputDialog.getText(self, 'New Image', 'Location(URL or file:/// address):')
                if ok:
                    self.edit.page().mainFrame().evaluateJavaScript('document.execCommand("insertImage",false,"' +text+ '");' )
            self.img = QPushButton("Image")
            self.img.clicked.connect(Image)
            self.lo2.addWidget(self.img)

            def Link(d):
                text, ok = QInputDialog.getText(self, 'New Link', 'Location(URL or file:/// address):')
                if ok:
                    self.edit.page().mainFrame().evaluateJavaScript('document.execCommand("createLink",false,"' +text+ '");' )
            self.link = QPushButton("Selection>Link")
            self.link.clicked.connect(Link)
            self.lo2.addWidget(self.link)

        else:
            def Timestamp(d):
                t =datetime.datetime.now().strftime(config.get("basic", "strftime",raw=True))
                self.edit.insertPlainText(t)
            self.ts = QPushButton("Timestamp")
            self.ts.clicked.connect(Timestamp)
            self.lo.addWidget(self.ts)


def fn_to_title(s):
    #Heuristic to detect intentional hyphen use rather than use to replace spaces.
    #If it contains a space, we assume any hyphens need to be there.
    if not " " in s:
        s=s.replace("-"," ")
    return s.replace("_"," ")

#todo: this should be i8n compatible
#source: http://www.rasmusen.org/w/capitalization.htm
nocap = ["the","for","of","and",'in','a','but',
        'yet','so','from','to','of','with','without',
        'around','an','along','by','after','among','between', 'since','before','ago','past','till','until',
        'beside','over','under','above','across','against','throughout','underneath','within','except','beyond','despite','during',
        'behind','along','beneath']

def capitalize(s):
    #Capitalize all words not in the list or that are the fist
    l = s.split(" ")
    return ' '.join([i.title() if ((not i in nocap) or (v==0) or (v== (len(l)-1) )) else i for v,i in enumerate(l)])

class WebkitNoteEditor(QWebView):
    "The actual box used for displaying and editing notes"""
    def dropEvent(self,e):
        "Modify incoming drag and dropped urls to use a relative path."
        try:
            #The startswith thing witll only filter out some of the annoying exception logs but it's better than nothing
            #todo: only modify things that actuall
            if e.mimeData().hasUrls() and e.mimeData().urls()[0].toString().startswith("file://"):
                droppedpath = e.mimeData().urls()[0].toString()[len("file://"):]
                here = self.url().toString()[len("file://"):]
                print(here, droppedpath)
                #Don't modify absolute paths to anything outside the notes directory.
                if not os.path.relpath(droppedpath, notespath).startswith(".."):
                #e.mimeData().setUrls([QtCore.QUrl(os.path.relpath(self.url().toString(), e.mimeData().urls()[0].toString()))])

                    #Create a link as Html that looks the way we want it to.
                    e.mimeData().setHtml('<a href="'+
                    urllib.parse.quote_plus(os.path.relpath(droppedpath, os.path.dirname(here)  )    )+
                    '">'+capitalize(fn_to_title(
                    '.'.join(
                            os.path.basename(droppedpath).split(".")[:-1]))) +"</a>")
        except:
            logging.exception("Failed to modify to relative path")
        QWebView.dropEvent(self,e)

class Note(QWidget):
    def __init__(self,path,notebook):
        """
        Class representing the actual tab pane for a note file, including the editor,
        the toolbar and the save/load logic.

        path is the path to the file(which does not need to exist yet)
        notebook must be the Notebook instance the note will be a part of

        """
        QWidget.__init__(self)
        self.notebook = notebook
        self.path = path

        #Set up the embedded webkit
        self.edit = WebkitNoteEditor()
        self.edit.page().setContentEditable(True)
        self.edit.settings().setAttribute(QWebSettings.JavascriptEnabled,True)

        def openLink(url):
            decoded_url = urllib.parse.unquote_plus(url.toString())
            try:
                if decoded_url.startswith("http"):
                    #Note that we just pass the unmodifed url and assume the browser will handle that better
                    webbrowser.open_new_tab(url.toString())
                    return
                if decoded_url.startswith("file://"):
                    self.notebook.open(decoded_url[len("file://"):])
                elif not decoded_url.startswith("mdnotes://"):
                    self.notebook.open(os.path.join(os.path.dirname(self.path),decoded_url ))
                else:
                    #Open knows how to handle these directly
                    self.notebook.open(decoded_url)
            except:
                logging.exception("Failed to open link "+ str(url.toString()))

        self.edit.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.edit.page().linkClicked.connect(openLink)

        #set up the toolbar
        self.tools = QWidget()
        self.tools.lo = QHBoxLayout()
        self.tools.setLayout(self.tools.lo)

        if self.path:
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

        self.reload()

    def onClose(self):
        "Handle closing the tab or the whole program"
        self.watcher.removePath(self.path)
        self.save()

    def save(self):
        #Readonly html file support
        if self.path.endswith(".ro"):
            return
        if self.path.endswith(".html"):
            return
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
        h = downloadAllImages(self.edit.page().mainFrame().toHtml(),self.path)
        doc.html = destyle_html(h).encode("utf-8")

        if  striptrailingnumbers(self.path).endswith("md"):
            with open(self.path,"wb") as f:
                f.write(doc.markdown_github)

        if  striptrailingnumbers(self.path).endswith("rst"):
            with open(self.path,"wb") as f:
                f.write(doc.rst)

        if buf and os.path.isfile(buf):
            os.remove(buf)

    def reload(self,dummy=True):
        "Reload the file from disk"
        if os.path.isfile(self.path):
            with open(self.path,"rb") as f:
                s = f.read()
            #now we are going to use pandoc to convert to html
            doc = pandoc.Document()

            #Figure out the input format. We back things up and archive them by appenting a Timestamp
            #to the end or else a ~. That function strips both of those things.
            if striptrailingnumbers(self.path).endswith(".html"):
                doc.html = s
                self.edit.page().setContentEditable(False)

            #The special html.ro lets us have read only HTML used for handy calculators and stuff.
            elif striptrailingnumbers(self.path).endswith(".html.ro"):
                doc.html = s
                self.edit.page().setContentEditable(False)

            elif striptrailingnumbers(self.path).endswith(".md"):
                doc.markdown_github = s

            elif striptrailingnumbers(self.path).endswith(".rst"):
                doc.rst = s
            else:
                raise RuntimeError("Bad filetype")
            html = doc.html.decode("utf-8")

            #Add the CSS file before the HTML
            d="<style>"+style+"</style>"
            self.header_size = len(d)
            d += html

            self.edit.setHtml(d, QUrl("file://"+self.path) if self.path else QUrl("file:///"))

class TxtNote(Note):
    def __init__(self,path,notebook):
        """
        Class representing the actual tab pane for a plain .txt note file, including the editor,
        the toolbar and the save/load logic.

        path is the path to the file(which does not need to exist yet)
        notebook must be the Notebook instance the note will be a part of

        """
        QWidget.__init__(self)
        self.notebook = notebook
        self.path = path

        #Set up the embedded webkit
        self.edit = QTextEdit()

        #set up the toolbar
        self.tools = QWidget()
        self.tools.lo = QHBoxLayout()
        self.tools.setLayout(self.tools.lo)

        if self.path:
            #Watch the file so we can auto reload
            self.watcher = QFileSystemWatcher()
            self.watcher.addPath(self.path)
            self.watcher.fileChanged.connect(self.reload)


        #Put the widgets together
        self.lo = QVBoxLayout()
        self.setLayout(self.lo)
        self.tools= NoteToolBar(self,richtext=False)
        self.lo.addWidget(self.tools)
        self.lo.addWidget(self.edit)

        self.reload()

    def save(self):
        #Readonly html file support
        if self.path.endswith(".ro"):
            return
        #
        # "Save the file if it needs saving"
        # if not self.edit.page().isModified():
        #     return

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

        with open(self.path,"wb") as f:
            f.write(self.edit.toPlainText().encode("utf-8"))

        if buf and os.path.isfile(buf):
            os.remove(buf)

    def reload(self,dummy=True):
        "Reload the file from disk"
        if os.path.isfile(self.path):
            with open(self.path,"rb") as f:
                s = f.read().decode("utf-8")
            self.edit.setPlainText(s)


class VirtualNote(Note):
    def __init__(self,notebook,html=None,onclose=None, reloader = None,editable=False):
        """
        Class representing the actual tab pane for a note file that is really an html string in memory, including the editor,
        the toolbar and the save/load logic.

        path is the path to the file(which does not need to exist yet)
        notebook must be the Notebook instance the note will be a part of

        """
        QWidget.__init__(self)
        self.notebook = notebook
        self.path="file:///"
        #Set up the embedded webkit
        self.edit = QWebView()
        if editable:
            self.edit.page().setContentEditable(True)
        self.edit.settings().setAttribute(QWebSettings.JavascriptEnabled,True)
        self.closeCallback=onclose
        self.reloader=reloader

        def openLink(url):
            try:
                if url.toString().startswith("http"):
                    webbrowser.open_new_tab(url.toString())
                    return

                elif url.toString().startswith("file://"):
                    self.notebook.open(url.toString()[len("file://"):])
                elif not url.toString().startswith("mdnotes://"):
                    self.notebook.open(os.path.join(os.path.dirname(self.path),url.toString() ))
                else:
                    #Open knows how to handle these directly
                    self.notebook.open(url.toString())
            except:
                logging.exception("Failed to open link "+ str(url))

        self.edit.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.edit.page().linkClicked.connect(openLink)

        #set up the toolbar
        self.tools = QWidget()
        self.tools.lo = QHBoxLayout()
        self.tools.setLayout(self.tools.lo)

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

        #Add the CSS file before the HTML
        d="<style>"+style+"</style>"
        self.header_size = len(d)
        d += html

        self.edit.setHtml(d, QUrl(self.path))

    def setHtml(self,html):
        self.edit.setHtml(html, QUrl(self.path))

    def onClose(self):
        "Handle closing the tab or the whole program"
        if self.closeCallback:
            self.closeCallback(self)
    def save(self):
        pass

    def reload(self,dummy=True):
        if self.reloader:
            self.reloader(self)

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
        "Open a new tab given a path to a supported file"\

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
                #If the file exists, open it and go to the tab.
                if not (raw or striptrailingnumbers(path).endswith(".txt") or striptrailingnumbers(path).endswith(".css")):
                    edit = Note(path,self)
                else:
                    edit = TxtNote(path,self)
                self.addTab(edit,os.path.basename(path))
                self.setCurrentIndex(self.count()-1)
                openfiletabs[path] = edit

        except:
            logging.exception("Could not open file "+path)


    def openVirtual(self,html,title,onclose=None,reloader=None):
        "Open a new tab and load some html"
        try:
            edit = VirtualNote(self,html=html,onclose=onclose,reloader=reloader)
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
        self.files.setNameFilters(supportedTypes)
        if notespath:
            self.files.setRootPath(notespath)

        #Setup the view over that
        self.fv = QTreeView()
        self.fv.setModel(self.files)
        self.fv.hideColumn(2)
        self.fv.hideColumn(3)
        self.fv.hideColumn(1)
        self.fv.resizeColumnToContents(0)

        #I don't know what that line does, but it's important!!!!
        self.fv.setRootIndex(self.files.setRootPath("/Users"))

        self.fv.doubleClicked.connect(self.dblclk)
        self.fv.expanded.connect(lambda x:     self.fv.resizeColumnToContents(0))
        self.fv.clicked.connect(lambda x:     self.fv.resizeColumnToContents(0))
        self.fv.setDragEnabled(True)
        self.lo.addWidget(self.fv)


        #Credit to vahancho http://stackoverflow.com/questions/22198427/adding-a-right-click-menu-for-specific-items-in-qtreeview
        self.fv.setContextMenuPolicy(Qt.CustomContextMenu);

        def onCustomContextMenu(point):
            if not notespath:
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
                    newp = os.path.join(archive, os.path.relpath(path, notespath))
                    if not os.path.isdir(os.path.dirname(newp)):
                        os.makedirs(os.path.dirname(newp), '700')
                    if not os.path.exists(newp):
                        os.rename(path,newp)
                    else:
                        os.rename(path,os.path.dirname(newp)+"."+str(time.time())+os.path.basename(newp))

            #User has chosen to create note
            if k == newmd:
                    path = self.files.filePath(i) or notespath
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
                    path = self.files.filePath(i) or notespath
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
                    path = self.files.filePath(i) or notespath
                    if not os.path.isdir(path):
                        path = os.path.dirname(path)
                    text, ok = QInputDialog.getText(self, 'New Folder', 'Name:')
                    newp = os.path.join(path,text)
                    if ok and not os.path.exists(newp):
                        os.mkdir(newp)

            #Uer has chosen to create one folder
            if k == search:
                path = self.files.filePath(i) or notespath
                if not os.path.isdir(path):
                    path = os.path.dirname(path)
                text, ok = QInputDialog.getText(self, 'Search', 'Pattern')
                x=[0]

                #Allow the user to stop the search by closing the search results tab.
                def stop(o):
                    x[0]=True
                if ok:
                    html = "<style>"+style+'</style>'+"<h1>Search Results</h2><dl>"
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


        self.fv.customContextMenuRequested.connect(onCustomContextMenu);



    def dblclk(self, ind):
        self.nb.open(self.files.filePath(ind))






class App(QMainWindow):
    "Class representinf the main app window"
    def __init__(self):
        QMainWindow.__init__(self)
        self.setWindowTitle('mdNotes')
        self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), "W_Book01.png" )))
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
            subprocess.Popen([__file__, b], close_fds=True)
        opennotebook.triggered.connect(opennb)
        self.fileMenu.addAction(opennotebook)


        setnotebook = QAction('Set as Default Notebook', self)


        def setnb(*a):
            if notespath:
                setNotebookLocation(notespath)
        setnotebook.triggered.connect(setnb)
        self.fileMenu.addAction(setnotebook)

        showabout = QAction('About', self)
        def f(*a):
            self.tabs.open("mdnotes://about.html")
        showabout.triggered.connect(f)
        self.help.addAction(showabout)

        #Make a folder for each of our builtins in the builtins folder. Right now it's just an example though
        for i in [i for i in os.listdir(os.path.join(os.path.dirname(__file__),'builtins')) if os.path.isfile(os.path.join(os.path.dirname(__file__),'builtins',i))]:
            a = QAction(i[:-8], self)
            def f(*a):
                self.tabs.open(os.path.join(os.path.dirname(__file__),'builtins',i))
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
            if not notespath:
                return
            html = "<style>"+style+'</style>'+"""<h1>Todos in this notebook</h2><p>Add todo entries by putting todo: something, Todo: A thing, or TODO: this thing
            anywhere in the notebook folder, with one todo per line.
              Change them to done: to indicate you have done them.<dl>"""
            tab = self.tabs.openVirtual(html=html,title="Todo List")
            for f,c in (findTodos(notespath)):
                #Keep the program responsive
                app.processEvents()
                if x[0]:
                    break
                html=html+'<dt>In <a href="'+f+'">'+f+'</a>:</dt><dd><ul>'
                for i in c:
                    todo = str(i)
                    if re.match("^.*((done)|(Done)|(DONE)):",todo):
                        html+=("<li><s>"+todo.replace("done:","")+"</s></li>")
                    else:
                        html+=("<li>"+todo+"</li>")
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
    notespath =getNotebookLocation()
    #Find and get the config file
    config= initConfig(notespath)
    #Find and get the CSS
    style=initCSS(notespath,config)

     #Set up the top level UI
    app = QApplication(sys.argv)
    app.setStyleSheet(style)

    w = App()
    w.showMaximized()

    sys.exit(app.exec_())
