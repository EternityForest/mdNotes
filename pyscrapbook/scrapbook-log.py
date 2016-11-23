#!/usr/bin/python3

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


#Tell the function not to use the first arg as the notebook location, because this program
#has it's own entirely differnt way of using the args.
config.getConfiguredNotebook()

from calendar_entries import *


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
print(sys.argv)

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


if lf:
    #Return list of tuples of time, text of entry
    ce=get_calendar_entries(lf)
    #get the datetime of the last entry
    if ce:
        last = ce[-1][0]
    else:
        print("File invalid or missing header with year")
        exit()


    now = datetime.datetime.now()
    d="\n"

    #Only put the time if we can help it, otherwise out the date on an l2 heading.
    if not(now.year==last.year and now.day==last.day and now.month==last.month):
        #d is the data variable that always begins with a # indicating an MD heading and the current time.
        d = "\n## " +datetime.datetime.now().strftime('%B %d')
        d+= '\n\n### ' + datetime.datetime.now().strftime('%I:%M%p')+"\n\n"

    #Don't put another heading at all if the new entry is within 3 minutes of the last one
    elif (now-last)>datetime.timedelta(minutes=3):
        d+=  "### "+ datetime.datetime.now().strftime('%I:%M%p')+"\n\n"
    else:
        d+="\n"


    d+= sys.argv[-1]
    with open(lf, "a") as myfile:
        myfile.write(d)

    print("Appended to " + lf)
else:
    print("Could not find journal by that name")
