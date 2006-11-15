# (c) August 2006, Emin Gun Sirer
# Distributed under the GNU Public License, v2
# See the file COPYING for copyright info
#
#
# This file describes the object hierarchy in the bibliography itself
# 
import string

citeabletypes = ["article", "inproceedings", "phdthesis", "masterthesis", "book", "techreport", "rfc", "misc"]

def isobjref(str):
    return (str[0] != "\"" and str[0] != "{")
            
class objectfarm:
    # a namespace is a dictionary of dictionaries
    def __init__(self):
        self._namespaces = {}
        self._definitions = []

    # checks two objects to see if they are identical, useful for multiple defn check
    def objidentical(self, obj1, obj2):
        #XXX need to implement field by field check
        return 1
    
    # stores an object under its key in a namespace named by its type
    def putobject(self, obj, options, curpos):
        nsname = "%s" % obj.__class__
        nsname = nsname[len("crosstexobjects."):]        
        if self._namespaces.has_key(nsname):
            ns = self._namespaces[nsname]
        else:
            ns = {}
            self._namespaces[nsname] = ns
        for key in [obj.key] + obj.aliases:
            if ns.has_key(key):
                if options["strict"]:
                    print "%s: object with key %s of type %s already exists" % (curpos, key, nsname)
                if not self.objidentical(obj, ns[key]):
                    print "%s: different object with key %s of type %s already exists" % (curpos, key, nsname)
                return
            ns[key] = obj
            self._definitions += [(nsname, key)]
        
    # retrieves an object by a key from a namespace named by type
    def getobject(self, nsname, key):
        if self._namespaces.has_key(nsname):
            ns = self._namespaces[nsname]
            if ns.has_key(key):
                return ns[key]
            else:
                print "no object with key %s exists of type %s" % (key, nsname)
        else:
            print "no objects exist of type %s" % (nsname)

    # checks if specified object exists
    def checkobject(self, nsname, key):
        if self._namespaces.has_key(nsname):
            if self._namespaces[nsname].has_key(key):
                return 1
        return 0
    
# this is a sentinel object
class NoObject:
    def beginobj(self, curpos):
        print "NoObject is not a valid object name", curpos
        raise Exception, "should not happen"

    def endobj(self, curpos):
        print "Ill-formed object at", curpos

#an entry for a @string definition
class stringentry:
    def beginobj(self, curpos):
        self._beginline = curpos
    
    def myname(self):
        longclassname = "%s" % self.__class__
        return longclassname[len("crosstexobjects."):]

    def setkey(self, arg, curpos):
        self.key = arg

    def setaliases(self, arg, curpos):
        self.aliases = arg

    def setvalue(self, arg, curpos):
        self._value = arg

    def endobj(self, curpos):
        self._endline = curpos

    def tobibtex(self, options):
        pass

    def promote(self, db, intoobj, options):
        return self._value

# a person, for use in author lists, only the name is used for citations
class author:
    def beginobj(self, curpos):
        self._beginline = curpos
        self._name = ""
        self._email = ""
        self._phone = ""
        self._institution = ""

    def myname(self):
        longclassname = "%s" % self.__class__
        return longclassname[len("crosstexobjects."):]

    def setkey(self, arg, curpos):
        self.key = arg
    def setaliases(self, arg, curpos):
        self.aliases = arg

    def setname(self, arg, curpos):
        self._name = arg
    def setemail(self, arg, curpos):
        self._email = arg
    def setphone(self, arg, curpos):
        self._phone = arg
    def setinstitution(self, arg, curpos):
        self._institution = arg

    def endobj(self, curpos):
        self._endline = curpos

    def tobibtex(self, options):
        pass

    def promote(self, db, intoobj, options):
        return self._name

# an object with just a long and short name
class namedobject:
    def beginobj(self, curpos):
        self._beginline = curpos
        self._shortname = self._longname = ""

    def myname(self):
        longclassname = "%s" % self.__class__
        return longclassname[len("crosstexobjects."):]

    def setkey(self, arg, curpos):
        self.key = arg

    def setaliases(self, arg, curpos):
        self.aliases = arg

    def setname(self, arg, curpos):
        self._shortname = self._longname = arg

    def setlongname(self, arg, curpos):
        self._longname = arg

    def setshortname(self, arg, curpos):
        self._shortname = arg

    def endobj(self, curpos):
        self._endline = curpos
        if self._shortname == "":
            self._shortname = self._longname

    def promote(self, db, intoobj, options):
        if options["use-long-" + self.myname() + "names"]:
            return self._longname
        else:
            return self._shortname
    def tobibtex(self, options):
        pass
            
class journal(namedobject):
    pass

class country(namedobject):
    pass

class state(namedobject):
    pass

class month(namedobject):
    def beginobj(self, curpos):
        self._monthno = 0
        
    def setmonthno(self, arg, curpos):
        self._monthno = int(arg)

    def promote(self, db, intoobj, options):
        intoobj._monthno = self._monthno
        return namedobject.promote(self, db, intoobj, options)

class location:
    def beginobj(self, curpos):
        self._beginline = curpos
        self._city = self._state = self._country = "\"\""
    def setkey(self, arg, curpos):
        self.key = arg
    def setaliases(self, arg, curpos):
        self.aliases = arg
    def setcity(self, arg, curpos):
        self._city = arg
    def setstate(self, arg, curpos):
        self._state = arg
    def setcountry(self, arg, curpos):
        self._country = arg
    def endobj(self, curpos):
        self._endline = curpos
    def tobibtex(self, options):
        pass
    def __str__(self):
        str = ""
        if self._city != "\"\"":
            str = self._city.strip("\"")
        if self._state != "\"\"":
            if str != "\"\"":
                str = "%s, " % str
            str = "%s%s" % (str, self._state.strip("\""))
        if self._country != "\"\"":
            if str != "":
                str = "%s, " % str
            str = "%s%s" % (str, self._country.strip("\""))
        return "\"%s\"" % str

    def promote(self, db, intoobj, options):
        # if a field is not an enclosed string, and there is an object
        # with that key, call on the promote method of that object to
        # promote this object reference to a string
        if isobjref(self._city) and db.checkobject("city", self._city):
            self._city = db.getobject("city", self._city).promote(db, self, options)
        if isobjref(self._state) and db.checkobject("state", self._state):
            self._state = db.getobject("state", self._state).promote(db, self, options)
        if isobjref(self._country) and db.checkobject("country", self._country):
            self._country = db.getobject("country", self._country).promote(db, self, options)
        return self.__str__()

class conference(namedobject):
    def beginobj(self, curpos):
        self._beginline = curpos
        self._address = {}
        self._month = {}
        self._editor = {}
        self._publisher = {}
        self._isbn = {}

    def endobj(self, curpos):
        self._endline = curpos

    def setkey(self, arg, curpos):
        self.key = arg

    def setaliases(self, arg, curpos):
        self.aliases = arg

    def setyearcontext(self, arg, curpos):
        self._year = arg

    # set a named field to a given value
    def setfield(self, fname, value, curpos):
        internalfname = '_%s' % fname
        if fname in set(["address", "month", "editor", "publisher", "isbn"]):
            dict = getattr(self, internalfname, value)
            if dict.has_key(self._year):
                print "%s: %s for conference %s already set for year %s" % (curpos, fname, self.key, self._year)
            dict[self._year] = value
            return
        print "%s: object of type %s does not have field named %s" % (curpos, self.myname(), fname)

    def promote(self, db, intoobj, options):
#        for fname in set(["address", "month", "editor", "publisher", "isbn"]):
#            dict = getattr(self, internalfname, value)
#            if dict.has_key(self._year):
#                dict[self._year] = value

        if self._address.has_key(intoobj._year):
            address = self._address[intoobj._year]
            if isobjref(address):
                if db.checkobject("location", address):
                    address = db.getobject("location", address).promote(db, intoobj, options)
                else:
                    print "Location %s is not defined, leaving it as is" % address
            try:
                if intoobj._address != address:
                    print "%s: object with key %s has address field %s in conflict with conference %s address %s" % (intoobj._beginline, intoobj.key, intoobj._address, self.key, address)
            except:
                pass
            intoobj._address = address
        if self._month.has_key(intoobj._year):
            month = self._month[intoobj._year]
            if isobjref(month) and db.checkobject("month", month):
                month = db.getobject("month", month).promote(db, intoobj, options)
            try:
                if intoobj._month != month:
                    print "%s: object with key %s has month field %s in conflict with conference %s month %s" % (intoobj._beginline, intoobj.key, intoobj._month, self.key, month)
            except:
                pass
            intoobj._month = month
        if options["use-long-conferencenames"]:
            return self._longname
        else:
            return self._shortname

    def __str__():
        return "Proceedings of the %s. " % self._longname

class workshop(conference):
    pass

class pub(namedobject):
    def __init__(self):
        self._mfields = set([])
        self._dfields = set(["author", "title", "month", "year", "address", "pages", "url", "doi", "isbn", "issn", "note", "editor"])

    # return the name of the class
    def myname(self):
        longclassname = "%s" % self.__class__
        return longclassname[len("crosstexobjects."):]

    # return the name of the bibtex record for this object
    def bibtexname(self):
        return self.myname()

    def beginobj(self, curpos):
        self._beginline = curpos

    def endobj(self, curpos):
        self._endline = curpos

    # check to see if all mandatory fields have been defined
    def check(self, options):
        for fname in self._mfields:
            internalfname = '_%s' % fname
            try:
                f = getattr(self, internalfname)
            except:
                print "%s: object of type %s is missing mandatory field <%s>" % (self._beginline, self.myname(), fname)

    def setkey(self, arg, curpos):
        self.key = arg

    def setaliases(self, arg, curpos):
        self.aliases = arg

    # set a named field to a given value
    def setfield(self, fname, value, curpos):
        internalfname = '_%s' % fname
        for i in (self._dfields | self._mfields):
            if i == fname:
                setattr(self, internalfname, value)
                return
        print "%s: object of type %s does not have field named %s" % (curpos, self.__class__, fname)

    # promote values associated with subobjects (conferences, etc) up to the parent
    def promote(self, db, intoobj, options):
        # ignore any exceptions thrown when month or address are not defined
        try:
            if isobjref(self._month) and db.checkobject("month", self._month):
                self._month = db.getobject("month", self._month).promote(db, self, options)
        except:
            pass
        try:
            if isobjref(self._address) and db.checkobject("location", self._address):
                self._address = db.getobject("location", self._address).promote(db, self, options)
        except:
            pass
    
    # convert object to bibtex format
    def tobibtex(self, options):
        print "@%s{%s," % (self.bibtexname(), self.key)
        fieldorder = ["key", "author", "title", "booktitle", "journal", "institution", "school", "volume", "number", "month", "year", "address", "pages", "publisher", "editor", "howpublished", "issn", "isbn", "doi", "url", "note"]
        for field in fieldorder:
            if field in (self._dfields | self._mfields):
                fname = '_%s' % (field)
                try:
                    f = getattr(self, fname)
                    print "\t%s=%s%s," % (field, "\t\t"[min(len(field)/7,1):], f)
                except:
                    pass
        print "}"
        
class inproceedings(pub):
    def __init__(self):
        pub.__init__(self)
        self._mfields = set(["author", "title", "booktitle", "address", "month", "year"])
        self._dfields = set(["pages", "publisher", "editor", "issn", "isbn", "doi", "url", "key", "note"])

    # promote values associated with subobjects (conferences, etc) up to the parent
    def promote(self, db, intoobj, options):
        # promote month and address first
        pub.promote(self, db, intoobj, options)
        # now pick up info from the conference
        if isobjref(self._booktitle):
            if db.checkobject("conference", self._booktitle):
                conf = db.getobject("conference", self._booktitle)
                self._booktitle = conf.promote(db, self, options)
            elif db.checkobject("workshop", self._booktitle):
                conf = db.getobject("workshop", self._booktitle)
                self._booktitle = conf.promote(db, self, options)
            else:
                if options["check"]:
                    print "conference %s is not defined, leaving it as is" % self._booktitle

class article(pub):
    def __init__(self):
        pub.__init__(self)
        self._mfields = set(["author", "title", "journal", "volume", "number", "year"])
        self._dfields = set(["address", "month", "pages", "publisher", "editor", "issn", "isbn", "doi", "url", "key", "note"])

    def promote(self, db, intoobj, options):
        # promote month and address first
        pub.promote(self, db, intoobj, options)
        # now pick up info from the conference
        if isobjref(self._journal):
            if db.checkobject("journal", self._journal):
                journal = db.getobject("journal", self._journal)
                self._journal = journal.promote(db, self, options)
            else:
                if options["check"]:
                    print "journal %s is not defined, leaving it as is" % self._journal

class misc(pub):
    def __init__(self):
        pub.__init__(self)
        self._mfields = set([])
        self._dfields = set(["key", "author", "title", "howpublished", "volume", "number", "month", "year", "address", "pages", "institution", "publisher", "editor", "issn", "isbn", "doi", "url", "key", "note"])

class techreport(pub):
    def __init__(self):
        pub.__init__(self)
        self._mfields = set(["author", "title", "institution", "number", "month", "year"])
        self._dfields = set(["address", "publisher", "editor", "issn", "isbn", "doi", "url", "key", "note"])
        
class book(pub):
    def __init__(self):
        pub.__init__(self)
        self._mfields = set(["author", "title", "publisher", "year"])
        self._dfields = set(["month", "address", "publisher", "editor", "issn", "isbn", "doi", "url", "key", "note"])
        
class rfc(pub):
    def __init__(self):
        pub.__init__(self)
        self._mfields = set(["author", "title", "number", "month", "year"])
        self._dfields = set(["howpublished", "issn", "isbn", "doi", "url", "key", "note"])

    # override default with misc
    def bibtexname(self):
        return "misc"

    def tobibtex(self, options):
        self._howpublished = "\"Request for Comments RFC-" + self._number.strip("\"") + "\""
        pub.tobibtex(self, options)

class thesis(pub):
    def __init__(self):
        pub.__init__(self)
        self._mfields = set(["author", "title", "school", "year"])
        self._dfields = set(["month", "address", "publisher", "editor", "issn", "isbn", "doi", "url", "key", "note"])

class phdthesis(thesis):
    pass

class masterthesis(thesis):
    pass

