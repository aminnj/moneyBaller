import urllib2
from bs4 import BeautifulSoup
import re
import numpy as np
import Games
import datetime
import pickle
dict_ = {'10': 'oct','11': 'nov','12': 'dec','01' : 'jan','02' : 'feb'}
d_    = {}
seasons = [2014,2015]
g = Games.Games(years=seasons, debug=False)
filename = '../data/parsed/backtest.pkl'
for year in seasons:
    datesToFetch = np.unique(np.array(map(g.get_date_from_gameid, g.get_game_ids(years=[year])))) # integers
    for date in datesToFetch[:2]:
        numDate =  (datetime.datetime(int(str(date)[:4]), int(str(date)[4:6]), int(str(date)[6:])) - datetime.datetime(year=1970, month=1, day=1)).days
        datestr = "%s-%s-%s" % ( dict_[str(date)[4:6]], str(date)[6:],str(date)[:4]) # convert to 2013-01-09
        print datestr
        page = urllib2.urlopen('http://www.dfsgold.com/nba/fanduel-daily-fantasy-recap-' + datestr)
        soup = BeautifulSoup(page)
        t = soup.findAll('a')
        win = []
        for row in t:
            row = str(row)
            if 'modalLineup' in str(row):
                fixd_ = re.sub(r'<.*?>', '', str(row))
                win.append(float(fixd_))

        t = soup.findAll('td')
        cash = []
        for row in t:
            row = str(row)
            if 'hidden-sm hidden-xs' in row and 'PM' not in row and '$' not in row:
                fixd_ = re.sub(r'<.*?>', '', str(row))
                cash.append(float(fixd_))

        d_[str(numDate)] = {'win':np.mean(win),'cash':np.mean(cash)}
with open(filename, "wb") as fh: pickle.dump(d_, fh)
print d_