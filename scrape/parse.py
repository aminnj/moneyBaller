import json, sys
import numpy as np
sys.path.insert(0,"../")
import utils.utils as u

year = 2014
season = u.yearToSeason(year)
pt = "P"

filename = "../data/json/data_%s_%i.json" % (pt, year)
print filename

with open(filename,"r") as fh:
    data = json.loads(fh.read())

colnames = data['resultSets'][0]['headers']
rows = data['resultSets'][0]['rowSet']

print len(rows)

print colnames
print rows[0:10]



print np.array(rows)
