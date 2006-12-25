# This file provides utility functions.
#
#
# This file does domain-specific capitalization
#
# It's specialized for English, and Computer Science.

case_csacronyms = [ "DNS", "BGP", "WWW", "GC", "MANET", ]
case_days = [ "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
case_months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
case_names = ["Internet", "Java", "C++", "C", "Modula-3"]
# these are made lowercase in lower case mode, capitalized
# according to the folowing spec in titlecase mode
case_compoundwords = ["Peer-to-Peer", "Pub-Sub",]

titlecase_specialcases = case_days + case_months + case_names + case_csacronyms + case_compoundwords
lowercase_specialcases = case_days + case_months + case_names + case_csacronyms

titlecase_alwayscaps = set(sc.lower() for sc in titlecase_specialcases)
lowercase_alwayscaps = set(sc.lower() for sc in lowercase_specialcases)
smallwords = set(["the", "as", "of", "in", "on", "is", "a", "an", "and", "for", "from", "to", "upon", "with", "through"])
punctuation = set([":", "!", ".", "-"])

def citationcase(str, case):
    str = str.strip("\"")
    if len(str) >= 3 and str[0] == "{" and str[-1] == "}" and str[-2] != "\\":
        str = str[1:-1]
    newstr = ""
    words = str.split()
    needscaps = 1
    nestingdepth = 0
    for word in words:
        # XXX we should account for escaped braces here
        lcount = word.count("{")
        rcount = word.count("}")
        lowerword = word.lower()
        # all caps 
        if case == "upper":
            word = word.upper()
        # capitalize if it is the first word, follows punctuation,
        #  is a word that always needs capitalization, and is not
        #  one of the small words
        elif case =="title" and nestingdepth == 0:
            # if it's one of the special cases, replace with special case
            if lowerword in titlecase_alwayscaps:
                for sc in titlecase_specialcases:
                    if sc.lower() == lowerword:
                        word = sc
            #the word needs caps, but titlecase it only if it
            #begins with a lowercase letter. this preserves all
            #capitalized words in the input
            elif (needscaps or (lowerword not in smallwords)) and word[0].islower():
                word = word.title()
        # capitalize if it follows punctuation, or is a special word
        elif case =="lower" and nestingdepth == 0:
            # if it's one of the special cases, replace with special case
            if lowerword in lowercase_alwayscaps:
                for sc in lowercase_specialcases:
                    if sc.lower() == lowerword:
                        word = sc
            #the word needs caps, but titlecase it only if it
            #begins with a lowercase letter. this preserves all
            #capitalized words in the input
            elif needscaps:
                word = word.lower()
                word = word[0].title() + word[1:]
            else:
                word = word.lower()
        if newstr == "":
            sep = ""
        else:
            sep = " "
        needscaps = 0
        # if the word ends in punctuation, the next word needs capitalization
        if word[-1] in punctuation:
            needscaps = 1
        nestingdepth += (lcount - rcount)
        newstr = newstr + sep + word
    return newstr

