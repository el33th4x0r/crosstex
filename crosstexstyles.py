#
# This file provides objects that can format the
# bibliography objects in the object hierarchy
# 

import math
import string
import crosstexobjects

class formatter:
    def __init__(self):
        # list of cited object, initially in order of citation, later sorted
        self.citations = []
        # dictionary of cited objects, by refkey
        self.citationsbykey = {}
        # list of used keys
        self.usedkeys = {}
        
    def processauthor(self, name, db, options):

        # check to see if this is a reference to an object
        if name.find(" ") < 0 and db.checkobject("author", name):
            auth = db.getobject("author", name)
            name = auth.promote(db, self, options).strip("\" ")
            
        # first tokenize the name into components
        str = ""
        lastchar = ' '
        names = []
        nesting = 0
        for i in range(0,len(name)):
            charc = name[i]
            if lastchar != '\\' and lastchar != ' ' and charc == " ":
                names.append(str)
                str =""
            elif lastchar != '\\' and charc == "}":
                if nesting == 0:
                    names.append(str)
                    str =""
                else:
                    nesting -= 1
            elif lastchar != '\\' and charc == "{":
                nesting += 1
            elif lastchar != '\\' and charc == ",":
                pass
            else:
                str += charc
            lastchar = charc
        names.append(str)

        # extract lastname, check suffixes and last name modifiers
        # extract also a list of first names
        sname = ""
        lnameoffset = len(names)-1
        if names[lnameoffset] in set(["Jr.", "Sr.", "Jr", "Sr", "III", "IV"]):
            sname = names[lnameoffset]
            lnameoffset -= 1
        mnameoffset = lnameoffset-1
        lname = names[lnameoffset]
        if names[mnameoffset] in set(["van", "von", "de", "bin", "ibn"]):
            lname = names[mnameoffset] + " " + lname
            mnameoffset -= 1

        # return the person info as a 3-tuple
        return (names[0:mnameoffset+1], lname, sname)


    def makeauthref(self, fnames, lname, sname, db, options):
        # create author name based on the options
        namestr = ""
        for n in fnames:
            pad = ""
            if options["use-initials"]:
                if namestr != "":
                    pad = "~"
                namestr += pad + n[0] + "."
            else:
                if namestr != "":
                    pad = " "
                namestr += pad + n
        if namestr != "":
            namestr += " "
        if sname != "":
            namestr += lname + ", " + sname
        else:
            namestr += lname
        return namestr
            
    def makekeyinitial(self, string, db, options):
        lastchar = ' '
        str = ""
        
        for i in range(0, len(string)):
            if (lastchar == ' ' or lastchar == '-') and ((string[i] >= "a" and string[i] <= "z") or (string[i] >= "A" and string[i] <= "Z")):
                str += string[i]
            lastchar = string[i]
        return str

    # determine the cite key (the key used to cite the paper by)
    def processcitekey(self, authors, year, db, options):
        authors = authors.strip("\"")
        authlist = authors.split(" and ")
        
        # go over all the names
        keystr = ""
        if options["use-citebyinitial"]:
            if len(authlist) == 1:
                (fnames, lname, sname) = self.processauthor(authlist[0], db, options)
                keystr = lname[0:3]
            elif len(authlist) <= 4:
                for i in range(0, min(len(authlist), 4)):
                    (fnames, lname, sname) = self.processauthor(authlist[i], db, options)
                    keystr += self.makekeyinitial(lname, db, options)
            else:
                for i in range(0, min(len(authlist), 3)):
                    (fnames, lname, sname) = self.processauthor(authlist[i], db, options)
                    keystr += self.makekeyinitial(lname, db, options)
                keystr += "{\etalchar{+}}"
        elif options["use-citebyfullname"]:
            if len(authlist) == 1:
                (fnames, lname, sname) = self.processauthor(authlist[0], db, options)
                keystr = lname
            elif len(authlist) == 2:
                (fnames1, lname1, sname1) = self.processauthor(authlist[0], db, options)
                (fnames2, lname2, sname2) = self.processauthor(authlist[1], db, options)
                keystr = lname1 + " \& " + lname2
            if len(authlist) > 2:
                (fnames, lname, sname) = self.processauthor(authlist[0], db, options)
                keystr = lname + " et al."
            keystr += " "
        else:
            for i in range(0, len(authlist)):
                (fnames, lname, sname) = self.processauthor(authlist[i], db, options)
                keystr += lname
            keystr += " "
        if year != "":
            keystr += ("%02d" % (int(year) % 100))
        return keystr
        
    # determine the sort key (the key used to sort the bib entries by)
    def processsortkey(self, authors, year, monthno, db, options):
        return self.processcitekey(authors, year, db, options).lower() + str(monthno)

    def processauthors(self, authors, db, options):
        authors = authors.strip("\"")
        authlist = authors.split(" and ")
        
        # go over all the names
        authstr = ""
        for i in range(0, len(authlist)):
            name = authlist[i]
            pad = ""
            if authstr != "":
                if i != len(authlist)-1:
                    pad = ", "
                else:
                    pad = " and "
            (fnames, lname, sname) = self.processauthor(name, db, options)
            authstr += pad + self.makeauthref(fnames, lname, sname, db, options)
        return authstr
        
    def processtitle(self, title, db, options):
        title = title.strip("\"")
        if title[0] == "{" and title[len(title)-1] == "}":
            title = title[1:len(title)-1]
        return title
    
    def prepcite(self, refkey, db, options):
        for type in crosstexobjects.citeabletypes:
            if db._namespaces.has_key(type) and db._namespaces[type].has_key(refkey):
                ref = db._namespaces[type][refkey]

                keystr = ""
                sortkey = ""
                try:
                    providedyear = ref._year
                except:
                    providedyear = ""
                try:
                    providedkey = ref._key.strip("\"")
                except:
                    providedkey = ""
                try:
                    providedmonth = ref._monthno
                except:
                    providedmonth = 1
                try:
                    providedauthor = ref._author
                except:
                    providedauthor = ""

                if providedkey != "":
                    citekey = self.processcitekey(providedkey, providedyear, db, options)
                elif options["use-citebyinitial"] or options["use-citebyfullname"]:
                    citekey = self.processcitekey(providedauthor, providedyear, db, options)
                else:
                    citekey = ""
                sortkey = self.processsortkey(providedkey, providedyear, providedmonth, db, options)
                    
                obj = [sortkey, citekey, refkey, ref, providedauthor, providedyear, 0, ""]
                self.citations.append(obj)
                self.citationsbykey[refkey] = obj
                return
        else:
            print "citation %s not found" % refkey

    def finduniquekey(self, obj, db, options):
        #if we have processed this entry, do not redo it
        if obj[6]:
            return

        # find a new suffix
        suffixstr = "abcdefghijklmnopqrstuvwxyz"
        citekey = obj[1]
        for i in range(0, len(suffixstr)):
            suffix = suffixstr[i:][0]
            if not self.usedkeys.has_key(citekey + suffix):
                citekey = citekey + suffix
                obj[1] = citekey
                obj[6] = 1
                self.usedkeys[citekey] = obj
                return
        print "too many citations with the same key (%s) in the same year" % obj[1]
                      
    def fixupkeys(self, db, options):
        if options["use-sortcitations"]:
            self.citations.sort()

        # if the entries are cited by initial or name, they are not guaranteed
        # to be unique. need to check and uniquify them.
        if options["use-citebyinitial"] or options["use-citebyfullname"]:

            for obj in self.citations:
                citekey = obj[1]
                if citekey in self.usedkeys:
                    # first find a unique name for the old object
                    oldobj = self.usedkeys[citekey]
                    self.finduniquekey(oldobj, db, options)
                    # then find a unique name for the new object
                    self.finduniquekey(obj, db, options)
                else:
                    self.usedkeys[citekey] = obj


    def cite(self, key, db, options):
        try:
            obj = self.citationsbykey[key]
        except:
            return

        citekey = obj[1]
        refkey = obj[2]
        ref = obj[3]
        providedauthor = obj[4]
        providedyear = obj[5]

        citestr = authstr = titlestr = pubstr = datestr = locstr = ""
        if citekey != "":
            citestr = "[%s]" % citekey
        refstr = "\\bibitem%s{%s}\n" % (citestr, refkey)
        if providedauthor != "":
            authstr = "%s.\n" % (self.processauthors(providedauthor, db, options))
        try:
            titlestr = "\\newblock {%s}.\n" % (self.processtitle(ref._title, db, options))
        except:
            titlestr = ""

        # ARTICLE
        if ref.myname() == "article":
            if options["use-inforarticles"]:
                pubstr = "\\newblock In {\\em %s}" % (ref._journal.strip("\""))
            else:
                pubstr = "\\newblock {\\em %s}" % (ref._journal.strip("\""))
            try:
                if ref._volume:
                    pubstr += " " + ref._volume
            except:
                pass
            try:
                if ref._number:
                    pubstr += "(" + ref._number + ")"
            except:
                pass
            try:
                if ref._pages:
                    pubstr += ":" + ref._pages
            except:
                pass

        # INPROCEEDINGS
        elif ref.myname() == "inproceedings":
            procstr = ""
            if options["add-proceedingsof"]:
                procstr = "Proceedings of the "
            if options["add-procof"]:
                procstr = "Proc. of "
            pubstr = "\\newblock In %s{\\em %s}" % (procstr, ref._booktitle.strip("\""))

        # THESES
        elif ref.myname() == "phdthesis":
            try:
                pubstr = "\\newblock Ph.D. Thesis, %s" % ref._school.strip("\"")
            except:
                pubstr = "\\newblock Ph.D. Thesis"
        elif ref.myname() == "masterthesis":
            try:
                pubstr = "\\newblock Masters Thesis, %s" % ref._school.strip("\"")
            except:
                pubstr = "\\newblock Masters Thesis"

        # BOOK
        elif ref.myname() == "book":
            try:
                pubstr = "\\newblock {\em %s}" % ref._title
            except:
                pass
            print "TODO: book citations are broken"

        # TECHREPORT
        elif ref.myname() == "techreport":
            try:
                if ref._number and ref._institution:
                    pubstr = "\\newblock Technical Report %s, %s" % (ref._number.strip("\""), ref._institution.strip("\""))
            except:
                try:
                    if ref._institution:
                        pubstr = "\\newblock Technical Report, %s" % ref._institution.strip("\"")
                except:
                    pubstr = "\\newblock Technical Report"

        # RFC
        elif ref.myname() == "rfc":
            try:
                pubstr = "\\newblock IETF Request for Comments RFC-%s" % ref._number.strip("\"")
            except:
                pubstr = ""

        # MISC
        elif ref.myname() == "misc":
            try:
                if ref._howpublished:
                    pubstr = "\\newblock %s" % ref._howpublished.strip("\"")
            except:
                try:
                    if ref._note:
                        pubstr = "\\newblock %s" % ref._note.strip("\"")
                except:
                    pass
        try:
            datestr = "%s %s" % (ref._month.strip("\""), ref._year.strip("\""))
        except:
            try:
                datestr = ref._year.strip("\"")
            except:
                pass
        try:
            locstr = ref._address.strip("\"")
        except:
            pass
        bibstr = refstr + authstr + titlestr + pubstr 
        if locstr != "":
            bibstr += ", " + locstr
        if datestr != "":
            bibstr += ", " + datestr
        bibstr += "."

        obj[7] = bibstr
            
    def emitcites(self, fp, preambletbl, db, options):

        # in case we need this
        fp.write("\\newcommand{\\etalchar}[1]{$^{#1}$}\n")

        # dump preambles
        for i in preambletbl:
            preamble = preambletbl[i]
            preamble = preamble[len("@PREAMBLE")+1:]
            preamble = preamble.strip()
            if preamble[0] == '{' and preamble[-1:] == "}":
                preamble = preamble[1:len(preamble)-1]
            if preamble[0] == '\"' and preamble[-1:] == "\"":
                preamble = preamble[1:len(preamble)-1]
            fp.write(preamble)
            fp.write("\n")

        # find the longest string to ref a citation by
        maxstr = ""
        for obj in self.citations:
            citekey = obj[1]
            citekey = citekey.replace("{\\etalchar{+}}", "X")
            if len(citekey) > len(maxstr):
                maxstr = citekey

        strlen = int(math.ceil(math.log(len(self.citations), 10)))
        if maxstr == "":
            maxstr = "00000000000"[0:strlen]
        elif len(maxstr) >= 13:
            print "------------------->", maxstr
            maxstr = "XXXXXXXXXXXXX"
            
        fp.write("\\begin{thebibliography}{" + maxstr + "}\n")
        
        for obj in self.citations:
            fp.write(obj[7] + "\n\n")

        fp.write("\\end{thebibliography}\n")

    def style(self, sname, options):
        if options["ignore-doc-style"] == 1:
            return

        # order is shorten-firstnames, cite-by-initials, cite-byfullname, sort, proceedingsof, procof, in-for-articles
        if sname == "abbrv":
            choices = [1, 0, 0, 1, 0, 0, 0]
        elif sname == "alpha":
            choices = [0, 1, 0, 1, 0, 0, 0]
        elif sname == "full":
            choices = [0, 0, 1, 1, 1, 0, 1]
        else:
            if sname != "plain":
                print "style %s not found, using plain instead" % sname
            choices = [0, 0, 0, 1, 0, 0, 0]

        options["use-initials"] = choices[0]
        options["use-citebyinitial"] = choices[1]
        options["use-citebyfullname"] = choices[2]
        options["use-sortcitations"] = choices[3]
        options["add-proceedingsof"] = choices[4]
        options["add-procof"] = choices[5]
        options["use-inforarticles"] = choices[6]
