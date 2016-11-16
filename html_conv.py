from HTMLParser import HTMLParser
from os import linesep


#Modified from a SO answer by samaspin
#http://stackoverflow.com/questions/15608555/python-convert-html-to-text-and-mimic-formatting




def render_gfm(md):
    out = ""
    tagstack = []

    while(md):
        x = md.pop()
        if x in ["\n","\r"]:
            out+= "<br>"
            if tagstack and tagstack[-1] in["h1","h1","h3","h4","h5","h6"]
            
class MyHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.quoting=False
        self.listcount = 0
        self.divert = False

    def feed(self, in_html):
        self.output = ""
        HTMLParser.feed(self, in_html)
        return self.output

    def handle_data(self, data):
        if self.divert:
            return
        if self.quoting:
            for i in data.split("\n"):
                self.output+= ">"+data
        else:
            self.output += data

    def handle_starttag(self, tag, attrs):
        if tag =="style":
            self.divert = True
        if tag == 'ul':
            self.listcount = 0
        if tag=="ol":
            self.listcount = 1

        if tag == 'li':
            if self.listcount:
                self.output += linesep + '* '
            else:
                self.output += linesep+str(self.listcount)+"."
                self.listcount+= 1

        elif tag == 'blockquote' :
            self.output += linesep+linesep + ">"
            self.quoting = True

        elif tag =="code":
            self.output += linesep+linesep + "```"

        elif tag == 'br' :
            if self.quoting:
                self.output += linesep
            else:
                self.output +=">"+ linesep

        elif tag == 'p' :
            if self.quoting:
                for i in data.split("\n"):
                    output+= linesep+">"+linesep+">"
            else:
                self.output += linesep +linesep

        elif tag == 'div' :
            self.output += linesep +linesep
        elif tag == 'h1' :
            self.output += linesep +"# "
        elif tag == 'h2' :
            self.output += linesep +"## "
        elif tag == 'h3' :
            self.output += linesep +"### "
        elif tag == 'h4' :
            self.output += linesep +"#### "
        elif tag == 'h5' :
            self.output += linesep +"##### "
        elif tag == 'h6' :
            self.output += linesep +"###### "

    def handle_endtag(self, tag):
        if tag =="style":
            self.divert = False
        if tag == 'blockquote':
            self.output += linesep + linesep
            self.quoting = False

        elif tag =="code":
            self.output += linesep+linesep + "```"
            self.quoting = True

def html_to_md(h):
    p = MyHTMLParser()
    return p.feed(h)
