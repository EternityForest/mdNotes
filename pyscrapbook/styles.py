from PyQt5.QtCore import QUrl, QFileSystemWatcher
import os
import config


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

def loadCSS():
    "Setup the CSS reloader watcher ad load the CSS. Requires the notes path and the config object from config. and returns the css text"
    #Kinda hacky having style as a  global
    global csswatcher,style
    style=defaultstyle
    csspath = None

    if config.notespath and os.path.exists(os.path.join(config.notespath,"style.css")):
        #Read the notebook specific style.css which has the highest precedence
        with open(os.path.join(config.notespath,"style.css")) as f:
            style=f.read()
        csspath = os.path.join(config.notespath,"style.css")

    #Read the user's donfigured CSS if it exists
    elif os.path.exists(config.interpretPath(config.config.get("theme","css"))):
        with open(config.interpretPath(config.config.get("theme","css"))) as f:
            style=f.read()
        csspath = config.interpretPath(config.config.get("theme","css"))
    else:
        #Read the default
         if os.path.isfile(os.path.join(os.path.realpath(__file__),"style.css")):
            with open(os.path.join(os.path.realpath(__file__),"style.css")) as f:
                style=f.read()
            csspath = css




    if csspath:
        csswatcher = cssreloader(csspath)

    return style
