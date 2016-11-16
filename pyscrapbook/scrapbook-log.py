#!/usr/bin/python

#This file is a very simple shell utility for maintaining journals in md format
#usage
#log blah
#Add an entry with text blah to ~/notes/journal.md

#log n "text here"
#Log that to ~/home/notes/n.md

#log -here "text"
#log that to a file named journal.md in the wording dir which will be created if it does not exist.

#Text will be inserted as is after a top level heading of the current date.

import sys,os,datetime, getpass

import config

config.loadConfigFiles()

#d is the data variable that always begins with a # indicating an MD heading and the current time.
d = "\n## " +datetime.datetime.now().strftime('%b %d %I:%M%p %G')

lf = None

def get_name():
    if os.path.isfile(os.path.join(os.path.expanduser("~"),".mdnotes/name.txt")):
        with open(os.path.join(os.path.expanduser("~"),".mdnotes/name.txt")) as f:
            return f.read(64)
    else:
        return ""

def set_name(n):
    if not os.path.exists(os.path.join(config.no,".mdnotes")):
        os.mkdir(os.path.join(os.path.expanduser("~"),".mdnotes"))
    with open(os.path.join(os.path.expanduser("~"),".mdnotes/name.txt"),"w") as f:
        f.write(n)

#If there is only one argument, assume it goes notespath/journal.md
if len(sys.argv)==2:
    lf = os.path.join(config.notespath,"journal.md")
else:

    #If there is a file in the user's notes folder that matches the pattern, then we append there.
    #Note files must end in .md, but you don't type the .md
    if os.path.isfile(os.path.join(config.notespath, sys.argv[1]+".md")):
        lf = os.path.join(config.notespath, sys.argv[1]+".md")

    #If the user explicitly specifies an md file.
    elif sys.argv[1].endswith(".md"):
        if os.path.isfile(os.path.join(sys.argv[1])):
            lf = os.path.join(sys.argv[1])

    #-project appents to a file named journal.md in the current directory, and also adds your configured name
    elif sys.argv[1] == "-project":
        n = get_name()
        if n:
            d+= " by " +n
        lf = os.path.join(os.getcwd(),"journal.md")

    #-project appends to a file named journal.md in the current directory.
    elif sys.argv[1] == "-here":
        lf = os.path.join(os.getcwd(),"journal.md")

    #To set your name
    elif sys.argv[1] == "-set":
        if sys.argv[2] == "name":
            set_name(sys.argv[3])

        else:
            print("Invalid property")
        exit(0)

    else:
        print("error")
        exit(0)



d+= "\n "+sys.argv[-1]+"\n"

if lf:
    with open(lf, "a") as myfile:
        myfile.write(d)
        pass

    print("Appended to " + lf)
else:
    print("Could not find journal by that name")
