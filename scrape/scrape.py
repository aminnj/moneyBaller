import requests, json, sys
sys.path.insert(0,"../")
import utils.utils as u

def getData(season, thetype="P"):
    if thetype in ["P", "T"]: # [P]layer or [T]eam stats for games per season
        requrl="http://stats.nba.com/stats/leaguegamelog?Direction=DESC&LeagueID=00&PlayerOrTeam=%s&Season=%s&SeasonType=Regular+Season&Sorter=PTS" % (thetype, season)
    elif thetype in ["G"]: # [G]eneral player stats per season
        requrl="http://stats.nba.com/stats/leaguedashplayerstats?College&Conference&Country&DateFrom&DateTo&Division&DraftPick&DraftYear&GameScope&GameSegment&Height&LastNGames=0&LeagueID=00&Location&MeasureType=Base&Month=0&OpponentTeamID=0&Outcome&PORound=0&PaceAdjust=N&PerMode=PerGame&Period=0&PlayerExperience&PlayerPosition=&PlusMinus=N&Rank=N&Season=%s&SeasonSegment&SeasonType=Regular+Season&ShotClockRange&StarterBench&TeamID=0&VsConference&VsDivision&Weight" % (season)
    else:
        return

    headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36"}
    req = requests.get(requrl, headers=headers, timeout=30)
    return req.json()

if __name__=='__main__':

    for year in range(2015,2016):
        season = u.yearToSeason(year)
        for ptg in ["P", "T", "G"]:
            try:
                data = getData(season, thetype=ptg)
                outname = "../data/json/data_%s_%i.json" % (ptg, year)
                with open(outname,"w") as fh:
                    json.dump(data, fh)
                print "[scraper] Got %s data for %s" % (ptg, season)
            except:
                print "[scraper] ERROR getting %s data for %s" % (ptg, season)



