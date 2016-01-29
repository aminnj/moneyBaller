import requests, json, urllib2, urllib
import datetime, ast, sys
import pprint, itertools


playersOrTeams = "P" # "T"
season = "2008-09"
requrl="http://stats.nba.com/stats/leaguegamelog?Direction=DESC&LeagueID=00&PlayerOrTeam=%s&Season=%s&SeasonType=Regular+Season&Sorter=PTS" % (playersOrTeams, season)
print requrl


page = urllib2.urlopen(requrl)
json = json.loads(page.read())
print json

# req = requests.get(requrl)
# print req.json()
# print req.content
# json = json.loads(req.content)


# print json

# data = req.content[14:-3]
# js = ast.literal_eval(data)

