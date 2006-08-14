#
# This file provides objects that can format the
# bibliography objects in the object hierarchy
# 

import string
import crosstexobjects

class plain:
    def __init__(self):
        self.citations = []
    
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
        if string[0] >= "a" and string[0] <= "z":
            str = string[0]
            for i in range(1, len(string)):
                if string[i] >= "A" and string[i] <= "Z":
                    str += string[i]
                    return str
        elif string[0] >= "A" and string[0] <= "Z":
            return string[0]
        else:
            #return the first usable character
            for i in range(0, len(string)):
                if (string[i] >= "a" and string[i] <= "z") or (string[i] >= "A" and string[i] <= "Z"):
                    return string[i]
        return "X"
   
    def processkey(self, authors, year, db, options):
        authors = authors.strip("\"")
        authlist = authors.split(" and ")
        
        # go over all the names
        keystr = ""
        if options["use-citebyinitial"]:
            for i in range(0, min(len(authlist), 3)):
                (fnames, lname, sname) = self.processauthor(authlist[i], db, options)
                keystr += self.makekeyinitial(lname, db, options)
            if len(authlist) > 2:
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
        
    def processauthors(self, authors, db, options):
        authors = authors.strip("\"")
        authlist = authors.split(" and ")
#        print "XXXXXXXXXXXXXXXX", authlist
        
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
    
    def cite(self, key, db, options):
        for type in crosstexobjects.citeabletypes:
            if db._namespaces.has_key(type) and db._namespaces[type].has_key(key):
                ref = db._namespaces[type][key]

                keystr = ""
                sortkey = ""
                try:
                    providedyear = ref._year
                except:
                    providedyear = ""
                try:
                    providedkey = ref._key
                except:
                    providedkey = ""
                if providedkey != "":
                    keystr = "[%s]" % providedkey.strip("\"")
                    sortkey = keystr.lower()
                elif options["use-citebyinitial"] or options["use-citebyfullname"]:
                    keystr = "[%s]" % self.processkey(ref._author, providedyear, db, options)
                    sortkey = keystr.lower()
                else:
                    try:
                        sortkey = self.processkey(ref._author, providedyear, db, options).lower()
                    except:
                        pass
                refstr = "\\bibitem%s{%s}\n" % (keystr, ref.key)
                try:
                    authstr = "%s.\n" % (self.processauthors(ref._author, db, options))
                except:
                    authstr = ""
                try:
                    titlestr = "\\newblock {%s}.\n" % (self.processtitle(ref._title, db, options))
                except:
                    titlestr = ""

                pubstr = ""
                datestr = ""
                locstr = ""
                if ref.myname() == "article":
                    if options["use-inforarticles"]:
                        pubstr = "\\newblock In {\\em %s}" % (ref._journal.strip("\""))
                    else:
                        pubstr = "\\newblock {\\em %s}" % (ref._journal.strip("\""))
                elif ref.myname() == "inproceedings":
                    procstr = ""
                    if options["add-proceedingsof"]:
                        procstr = "Proceedings of the "
                    if options["add-procof"]:
                        procstr = "Proc. of "
                    pubstr = "\\newblock In %s{\\em %s}" % (procstr, ref._booktitle.strip("\""))
                    try:
                        if ref._number:
                            pubstr += " " + ref._number
                    except:
                        pass
                    try:
                        if ref._number:
                            pubstr += "(" + ref._number + ")"
                    except:
                        pass
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
                elif ref.myname() == "book":
                    pass

                # TECHREPORT
                elif ref.myname() == "techreport":
                    try:
                        if ref._number:
                            pubstr = "\\newblock Technical Report %s, %s" % (ref._number.strip("\""), ref._institution.strip("\""))
                    except:
                        try:
                            if ref._institution:
                                pubstr = "\\newblock Technical Report, %s" % ref._institution.strip("\"")
                        except:
                            pubstr = "\\newblock Technical Report"
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
                citestr = refstr + authstr + titlestr + pubstr 
                if locstr != "":
                    citestr += ", " + locstr
                if datestr != "":
                    citestr += ", " + datestr
                citestr += "."
                self.citations.append((sortkey, citestr))

    def emitcites(self, fp, preambletbl, db, options):
        if options["use-sortcitations"]:
            self.citations.sort()

        fp.write("\\newcommand{\\etalchar}[1]{$^{#1}$}\n")
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

        fp.write("\\begin{thebibliography}{WWWW{\\etalchar{+}}00}\n")
        
        for (key, cite) in self.citations:
            fp.write(cite + "\n\n")

        fp.write("\\end{thebibliography}\n")

class alpha:
    pass

class abbrv:
    pass

