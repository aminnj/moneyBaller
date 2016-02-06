import Games
import requests, json, sys, pprint
sys.path.insert(0,"../")
import utils.utils as u
import numpy as np
import pickle, gzip
from tqdm import tqdm 

np.set_printoptions(linewidth=205,formatter={'float_kind':lambda x: "%.2f" % x })

def getData(season="2014-15", pid=201166,thetype="common"):
    if thetype in ["common"]: 
        requrl="http://stats.nba.com/stats/commonplayerinfo?LeagueID=00&PlayerID=%i" % (pid)
    elif thetype in ["stats"]: 
        requrl="http://stats.nba.com/stats/playerdashptshots?DateFrom=&DateTo=&GameSegment=&LastNGames=0&LeagueID=00&Location=&Month=0&OpponentTeamID=0&Outcome=&PerMode=PerGame&Period=0&PlayerID=%i&Season=%s&SeasonSegment=&SeasonType=Regular+Season&TeamID=0&VsConference=&VsDivision=" % (pid,season)
    else:
        return

    # print requrl

    headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36"}
    req = requests.get(requrl, headers=headers, timeout=30)
    return req.json()

years = [2013, 2014, 2015]
g = Games.Games(years=years, debug=False)

seaspids = g.get_player_ids()


general_player_info = {} # give it pid as key
for year, pids in zip(years,seaspids):

    player_season_stats = {} # give it (pid,year) as key

    season = u.yearToSeason(year)
    filename = "../data/pickle/player_stats_%i.pkl" % (year)



    print "doing season:", season
    for pid in tqdm(pids):
        try:
            if pid not in general_player_info:
                json = getData(season=season, pid=pid, thetype="common")
                height = json['resultSets'][0]['rowSet'][0][10]
                weight = json['resultSets'][0]['rowSet'][0][11]
                position = json['resultSets'][0]['rowSet'][0][14]
                if len(weight) > 0: weight = int(weight)
                if len(height) > 0: height = 12*int(height.split("-")[0])+int(height.split("-")[1])
                general_player_info[pid] = {"height": height, "weight": weight, "position": position}

            json = getData(season=season, pid=pid, thetype="stats")
            discardFirst = 5 #discard first n since we don't care about playerid, playername, sortorder, gamesplayed
            colnames = json['resultSets'][0]['headers']
            dtype = [(str(col), 'S21') if "SHOT_TYPE" in col else (str(col), 'f8') for col in colnames]
            colnames = colnames[discardFirst:]
            dtype = dtype[discardFirst:]
            rows = []
            for stat in json['resultSets']:
                for row in stat['rowSet']:
                    rows.append(row)
            rows = np.array(rows)[:,discardFirst:]
            rows = np.array([tuple(r) for r in rows], dtype=dtype)
            player_season_stats[(pid,year)] = {'stats': rows}
            for k,v in general_player_info[pid].items():
                player_season_stats[(pid,year)][k] = v
        except:
            print "error!"

    with gzip.open(filename, "wb") as fh:
        pickle.dump(player_season_stats, fh)

# print general_player_info
# print player_season_stats
