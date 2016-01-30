import json
from pprint import pprint
import numpy as np

year = 2014
season = "%s-%s" % (str(year), str(year+1)[-2:])
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
