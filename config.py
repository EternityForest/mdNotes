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

from configparser import ConfigParser
import sys,os
notespath = None

def loadConfigFiles():
    "Given the notes path, attempt to loaf a config object from that notes path and the user's configured notes file"
    global config
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



def interpretPath(p):
    "Expand user and correectly resolve a path found in a config file"
    return os.path.join(os.path.dirname(__file__),os.path.expanduser(p))

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

notespath = getNotebookLocation()

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
