import requests, bs4, sys
import json, copy
import pickle, gzip
import numpy as np
import Games

seasons = [2014,2015]
sources = ['fantasyfeud','fanduel','draftkings','fantasyaces','yahoo']
###Modified to pick up all sources on fantcrunch.  This makes the other scraper pretty obsolete.
g = Games.Games(years=seasons, debug=False)
for source in sources:
    for year in seasons:
        datesToFetch = np.unique(np.array(map(g.get_date_from_gameid, g.get_game_ids(years=[year])))) # integers
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

        with gzip.open("../data/pickle/%s_%i.pkl" % (source,year), "wb") as fh: pickle.dump(d, fh)
