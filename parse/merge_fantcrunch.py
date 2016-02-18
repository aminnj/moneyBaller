import matplotlib as mpl
mpl.use('Agg')
import numpy as np
import pickle, gzip, sys
import datetime
sys.path.insert(0,"../")

np.set_printoptions(linewidth=205,formatter={'float_kind':lambda x: "%.2f" % x })

# some vars
outfname = "../data/parsed/fantcrunch_merged.pkl"
years    = [2014,2015]
types    = ["fanduel", "draftkings", "fantasyaces", "fantasyfeud","yahoo"]
d_       = {}
for typ in types:
    for year in years:
        try:
            with gzip.open("../data/pickle/%s_%i.pkl" % (typ,year),"rb") as fh: data = pickle.load(fh)
        except:
            print 'Failed for file ../data/pickle/%s_%i.pkl' % (typ,year)
            continue
        #Pick a primary dataset.

        m1,m2 = [],[]
        for key_1 in data.keys():
            m1.append(key_1)
            date = str( (datetime.datetime(int(str(key_1)[0:4]),int(str(key_1)[4:6]),int(str(key_1)[6:8])) - \
            datetime.datetime(year=1970, month=1, day=1)).days)
            for key_2 in data[key_1].keys():
                m2.append(key_2)
                p_nam = str.split(str(data[key_1][key_2]['PlayerName'])," ")
                p_nam = p_nam[1] + ", " + p_nam[0]

                if p_nam not in d_.keys() and typ == types[0]:
                    d_[p_nam] = {}
                elif p_nam not in d_.keys():
                    continue
                if date not in d_[p_nam].keys():
                    if typ == types[0]:
                        d_[p_nam][date] = {}
                    else:
                        continue

                d_[p_nam][date][typ] = data[key_1][key_2]
print d_
with open(outfname , "wb") as fh: pickle.dump(d_, fh)
