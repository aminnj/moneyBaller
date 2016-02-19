import os
import numpy as np
import datetime
from matplotlib.dates import date2num, num2date

def yearToSeason(year):
    return "%s-%s" % (str(year), str(year+1)[-2:])

def web(filename,user="namin"):
    os.system("scp %s %s@uaf-6.t2.ucsd.edu:~/public_html/dump/ >& /dev/null" % (filename, user))
    print "Copied to uaf-6.t2.ucsd.edu/~%s/dump/%s" % (user, filename.split("/")[-1])

    
def date2inum(dt):
    # takes datetime object
    # return #days+1 since 01-01-01
    return int(date2num(dt))
def date2tuple(dt):
    # takes datetime object
    # return (y,m,d) tuple
    return (dt.year, dt.month, dt.day)
def tuple2inum(dt):
    # takes (y,m,d) tuple
    # return #days+1 since 01-01-01
    dt = datetime.datetime(*dt)
    return int(date2num(dt))
def tuple2date(dt):
    # takes (y,m,d) tuple
    # return datetime object
    return datetime.datetime(*dt)
def inum2date(dt):
    # takes #days+1 since 01-01-01
    # return datetime object
    return num2date(dt)
def inum2tuple(dt):
    # takes #days+1 since 01-01-01
    # return (y,m,d) tuple
    dt = inum2date(dt)
    return (dt.year, dt.month, dt.day)
def tuple2string(dt):
    # takes (y,m,d) tuple
    # returns nice string like Jan 1, 2004
    dt = datetime.datetime(*dt)
    return dt.strftime("%b %d, %Y").replace(" 0"," ")
def inum2string(dt):
    dt = num2date(dt)
    return dt.strftime("%b %d, %Y").replace(" 0"," ")
def inum2stamp(dt):
    dt = num2date(dt)
    return dt.strftime("%Y%b%d")

'''
def ma(x, N):
    if len(x) < N:
        return [np.nan]*len(x)
    else:
        cumsum = np.cumsum(np.insert(x, 0, 0))
        ret_arr = (cumsum[N:] - cumsum[:-N]) / N
        return np.append([np.nan]*(N-1),ret_arr)
'''
def ma(x, N):
    if len(x) < N:
        return [np.nan]*len(x)
    else:
        y = np.zeros((len(x)-N+1,))
        for ctr in range(N,len(x)+1):
             z = x[ctr-N:ctr]
             valid_z = z[z == z]
             if len(valid_z) == 0:
                 y[ctr-N] = np.nan
             else:
                 y[ctr-N] = np.sum(valid_z)/len(valid_z)
        return np.append([np.nan]*(N-1),y)
