import re,datetime, os

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


def get_calendar_entries(fn,s=None):
    """Given a file, return all of the calendar entries, which are simply text under a heading with the date.
       Headings are nestable,l1 should have a 4 digit year.
       l2 headings should contain the date and l3 the time, however this function ignore exactly what the headings are and tries
       it's best to infer things. You can put the full date on any level of heading and it will still work.
    """
    #Check for a 4-digit year at some point in the first 4096 characters of the file. If there is not at least one,
    #Then assume this is not actually a journal file.
    if fn:
        with open(fn,'rb') as f:
            s = f.read(4096).decode(errors="surrogateescape")

    if not re.search(r"\d\d\d\d",s):
        return([])
    if fn:
        #Limit files to 4MB, that really should be enough for any journal file.
        with open(fn,'rb') as f:
            s = f.read(4*10**6).decode(errors="surrogateescape")
            n = os.path.basename(fn).replace("\r","")

    s = s.lower()
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
        except( TypeError, ValueError) as e:
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
