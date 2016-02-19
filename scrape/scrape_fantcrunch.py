import requests, bs4, sys
import json, copy
import pickle, gzip
import numpy as np
import Games
import os.path
merged_dict = "../data/parsed/fantcrunch_merged.pkl"
pass_       = os.path.exists(merged_dict)

if pass_:
  existing_dates = []
  with open(merged_dict, 'rb') as handle:
    preds = pickle.load(handle)
  for key_1 in preds.keys():
    for key_2 in preds[key_1].keys():
      date = int(preds[key_1][key_2]['draftkings']['DateTime'][0:10].replace("-",""))
      if date not in existing_dates:
      	existing_dates.append(date)
print existing_dates
seasons = [2014,2015]
sources = ['fantasyfeud','fanduel','draftkings','fantasyaces','yahoo']
###Modified to pick up all sources on fantcrunch.  This makes the other scraper pretty obsolete.
g = Games.Games(years=seasons, debug=False)
for source in sources:
    for year in seasons:
        datesToFetch = np.unique(np.array(map(g.get_date_from_gameid, g.get_game_ids(years=[year])))).astype(int) # integers
        print "Before filtering" + len(datesToFetch)
        if len(existing_dates) > 0:
        	print "After filtering" + len(list(set(datesToFetch) - set(existing_dates)))
	break
        d = {}
        for date in datesToFetch:
            datestr = "%s-%s-%s" % (str(date)[:4], str(date)[4:6], str(date)[6:]) # convert to 2013-01-09
            try:
                data = requests.get("https://www.fantasycruncher.com/lineup-rewind/%s/NBA/%s" % (source,datestr))
                bs = bs4.BeautifulSoup(data.text,"html.parser")
                rawjson = None
                for script in bs.findAll("script", {"src":""}):
                    if "var playerlist = {" in script.text:
                        rawjson = script.text
                        break
                rawjson = "{"+rawjson.split("\n")[1].split("{",1)[1][:-2].replace("\\","")
                js = json.loads(rawjson)
                d[date] = copy.deepcopy(js)
                print "fetched %s: %s" % (source,datestr)
            except: print "ERROR fetching %s: %s" % (source,datestr)

        with gzip.open("../data/pickle/fantcrunch_%s_%i.pkl" % (source,year), "wb") as fh: pickle.dump(d, fh)
