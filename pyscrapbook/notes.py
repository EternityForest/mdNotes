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

import config, styles,util,calendar_entries


from html.parser import HTMLParser

def destyle_html(h):
    h = re.sub(r"<\/?span.*?>",'',h)
    h=h.replace("<p><br/><p>",'<br/>')
    return h

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
            #Replace the HTTP URL with a relative URL. It won't re-download next time because the URL is gone
            h = h.replace(i, os.path.relpath(fp, os.path.dirname(path)))
        except:
            logging.exception("Error getting image "+i)
    return h



def noteFromFile(path,notebook,raw=False):
        if os.path.isdir(path):
            raise ValueError("Path is directory")
        if not (raw or util.striptrailingnumbers(path).endswith(".txt") or util.striptrailingnumbers(path).endswith(".css")):
            edit = Note(path,notebook)
        else:
            edit = TxtNote(path,notebook)
        return edit



def fn_to_title(s):
    #Heuristic to detect intentional hyphen use rather than use to replace spaces.
    #If it contains a space, we assume any hyphens need to be there.
    if not " " in s:
        s=s.replace("-"," ")
    return s.replace("_"," ")

#todo: this should be i8n compatible
#main source: http://www.rasmusen.org/w/capitalization.htm
nocap = ["the","for","of","and",'in','a','but',
        'yet','so','from','to','of','with','without',
        'around','an','along','by','after','among','between', 'since','before','ago','past','till','until',
        'beside','over','under','above','across','against','throughout','underneath','within','except','beyond','despite','during',
        'behind','along','beneath']

def capitalize(s):
    #Capitalize all words not in the list or that are the fist
    l = s.split(" ")
    return ' '.join([i.title() if ((not i in nocap) or (v==0) or (v== (len(l)-1) )) else i for v,i in enumerate(l)])



class NoteToolBar(QWidget):
    "Represents the toolbar for a note. If richtext is false, will not have any fancy formatting buttons"
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
                #Return list of tuples of time, text of entry
                ce=calendar_entries.get_calendar_entries(None, self.note.to_gfm())
                #get the datetime of the last entry
                if ce and not (config.config.get("basic", "timestamp_button") == "basic"):
                    last = ce[-1][0]
                else:
                    t =datetime.datetime.now().strftime(config.config.get("basic", "strftime",raw=True))
                    self.edit.page().mainFrame().evaluateJavaScript('document.execCommand("insertHTML",false,"' +t+ '");' )
                    return


                now = datetime.datetime.now()
                d="\n"

                #Only put the time if we can help it, otherwise out the date on an l2 heading.
                if not(now.year==last.year and now.day==last.day and now.month==last.month):
                    #d is the data variable that always begins with a # indicating an MD heading and the current time.
                    d = "<h2>" +datetime.datetime.now().strftime('%B %d')+"</h2>"
                    d+= '<h3>' + datetime.datetime.now().strftime('%I:%M%p')+"</h3>"

                #Don't put another heading at all if the new entry is within 3 minutes of the last one
                elif (now-last)>datetime.timedelta(minutes=3):
                    d+=  "<h3>"+ datetime.datetime.now().strftime('%I:%M%p')+"</h3>"

                self.edit.page().mainFrame().evaluateJavaScript('document.execCommand("insertHTML",false,"' +d+ '");' )







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
                t =datetime.datetime.now().strftime(config.config.get("basic", "strftime",raw=True))
                self.edit.insertPlainText(t)
            self.ts = QPushButton("Timestamp")
            self.ts.clicked.connect(Timestamp)
            self.lo.addWidget(self.ts)

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
                if not os.path.relpath(droppedpath, config.notespath).startswith(".."):
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
            self.watcher.fileChanged.connect(self.onChanged)

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

    def to_gfm(self):
        doc = pandoc.Document()
        doc.html = destyle_html(self.edit.page().mainFrame().toHtml()).encode("utf-8")
        return doc.markdown_github.decode("utf-8")

    def save(self,name=None):
        name=name or self.path
        #Readonly html file support
        if name.endswith(".ro"):
            return
        if name.endswith(".html"):
            return
        "Save the file if it needs saving"
        if not self.edit.page().isModified():
            return

        #Back Up File
        buf =None
        #If the file exists, copy it to file~ first. If that exists, copy it to file4857475928345
        if os.path.exists(name):
            if not os.path.exists(name+"~"):
                buf=(name+"~")
                shutil.copy(name, name+"~")
            else:
                buf = name+str(time.time())
                shutil.copy(name,buf )

        #Again, pandoc to convert to the proper format
        doc = pandoc.Document()
        h = downloadAllImages(self.edit.page().mainFrame().toHtml(),name)
        doc.html = destyle_html(h).encode("utf-8")

        if  util.striptrailingnumbers(name).endswith(".md"):
            with open(name,"wb") as f:
                f.write(self.pre_bytes+doc.markdown_github)

        if  util.striptrailingnumbers(name).endswith(".rst"):
            with open(name,"wb") as f:
                f.write(self.pre_bytes+doc.rst)

        if buf and os.path.isfile(buf):
            os.remove(buf)

        #Reload to mark as saved, before the filesystem watcher ca get to it.
        self.reload()


    def onChanged(self):
        "Handle change in the filesystem"

        #Never let an external change completely destroy our work.
        self.save(self.path+str(time.time()))

        self.reload()
        #Three sleeps, really be sure the other process has put the file back.
        #See http://stackoverflow.com/questions/18300376/qt-qfilesystemwatcher-signal-filechanged-gets-emited-only-once
        time.sleep(0.01)
        time.sleep(0.01)
        time.sleep(0.01)

        self.watcher.addPath(self.path)


    def reload(self,dummy=True):
        "Reload the file from disk"
        if self.path.endswith('.jpg') or self.path.endswith('.svg') or  self.path.endswith('.png') or  self.path.endswith('.jpeg'):
            self.edit.setUrl(QUrl("file://"+self.path))
            self.edit.page().setContentEditable(False)
            return

        if os.path.isfile(self.path):
            with open(self.path,"rb") as f:
                s = f.read()
            #Be compatible with files made on a certain android text editor that puts those bytes there sometimes.
            if s.startswith(b"\xff\xfe"):
                s = s[2:]
                self.pre_bytes = b"\xff\xfe"
            elif s.startswith(b"\xfe\xff"):
                s = s[2:]
                self.pre_bytes = b"\xfe\xff"
            elif s.startswith(b"\xef\xbb\xbf"):
                s = s[3:]
                self.pre_bytes = b"\xef\xbb\xbf"
            else:
                self.pre_bytes = b''            #now we are going to use pandoc to convert to html
            doc = pandoc.Document()

            #Figure out the input format. We back things up and archive them by appenting a Timestamp
            #to the end or else a ~. That function strips both of those things.
            if util.striptrailingnumbers(self.path).endswith(".html"):
                doc.html = s
                self.edit.page().setContentEditable(False)

            #The special html.ro lets us have read only HTML used for handy calculators and stuff.
            elif util.striptrailingnumbers(self.path).endswith(".html.ro"):
                doc.html = s
                self.edit.page().setContentEditable(False)

            elif util.striptrailingnumbers(self.path).endswith(".md"):
                doc.markdown_github = s

            elif util.striptrailingnumbers(self.path).endswith(".rst"):
                doc.rst = s
            else:
                raise RuntimeError("Bad filetype")
            html = doc.html.decode("utf-8")

            #Add the CSS file before the HTML
            d="<style>"+styles.style+"</style>"
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
            f.write(self.pre_bytes+self.edit.toPlainText().encode("utf-8"))

        if buf and os.path.isfile(buf):
            os.remove(buf)

    def reload(self,dummy=True):
        "Reload the file from disk"
        if os.path.isfile(self.path):
            with open(self.path,"rb") as f:
                s = f.read()
            #Be compatible with files made on a certain android text editor that puts those bytes there sometimes.
            if s.startswith(b"\xff\xfe"):
                s = s[2:]
                self.pre_bytes = b"\xff\xfe"
            elif s.startswith(b"\xfe\xff"):
                s = s[2:]
                self.pre_bytes = b"\xfe\xff"
            elif s.startswith(b"\xef\xbb\xbf"):
                s = s[3:]
                self.pre_bytes = b"\xef\xbb\xbf"
            else:
                self.pre_bytes = b''
            self.edit.setPlainText(s.decode("utf-8"))


class VirtualNote(Note):
    def __init__(self,notebook,html=None,onclose=None, reloader = None,editable=False,reloadbutton=False):
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
        self.tools= NoteToolBar(self,reloadable=reloadbutton)
        self.lo.addWidget(self.tools)
        self.lo.addWidget(self.edit)

        #Add the CSS file before the HTML
        d="<style>"+styles.style+"</style>"
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
