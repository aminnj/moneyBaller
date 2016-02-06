import os

def yearToSeason(year):
    return "%s-%s" % (str(year), str(year+1)[-2:])

def web(filename,user="namin"):
    os.system("scp %s %s@uaf-6.t2.ucsd.edu:~/public_html/dump/ >& /dev/null" % (filename, user))
    print "Copied to uaf-6.t2.ucsd.edu/~%s/dump/%s" % (user, filename.split("/")[-1])

    
