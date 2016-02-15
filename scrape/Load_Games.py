import numpy as np
import pickle, gzip
import gzip
from tqdm import tqdm
import json, sys, time
sys.path.insert(0,"../")
import utils.utils as u
import operator
import datetime
import time
import string
np.set_printoptions(linewidth=205,formatter={'float_kind':lambda x: "%.1f" % x })
class Load_Games:

    def clean_str(self,string_):
        bad_chars = '@^(){}[]<>\''
        return string_.translate(string.maketrans("", "", ), bad_chars)

    def gen_dict(self,headers,type = "P",suffix = "",do_fant = True):
        return_dict = {}
        avg_strings = []
        if type == "P":
            avg_strings = ['AVG_'  + s for s in np.array(self.p_fint).astype(str)]
        if type == "T":
            avg_strings = []
            for line in self.positions:
                temp = ['AVG_'  + s +'_' +line for s in np.array(self.t_fint).astype(str)]
                if len(avg_strings) == 0:
                    avg_strings = temp
                else:
                    avg_strings = np.append(avg_strings,temp)

        for line in range(len(headers)):
            if line < (len(headers)-1):
                return_dict[str(headers[line]+suffix)] = line
            elif do_fant:
                return_dict['FANT'+suffix] = line
            else:
                return_dict[str(headers[line]+suffix)] = line

        for line in range(len(avg_strings)):
            return_dict[avg_strings[line]+suffix] = line + len(headers)

        if type == "P":
            return_dict["POSITION"]              = len(headers)+len(avg_strings) + 2
            return_dict["FANT_TARGET"]       = len(headers)+len(avg_strings)
            return_dict["REST"]              = len(headers)+len(avg_strings) + 1
            return_dict["FANDUEL_SALARY"]    = len(headers)+len(avg_strings) + 3
            return_dict["DRAFTKINGS_SALARY"] = len(headers)+len(avg_strings) + 4
            return_dict["FANT_PREDICTION"]   = len(headers)+len(avg_strings) + 5

        return return_dict

    def set_fant(self,dict_,stats_):
        stats_[:,dict_['FANT']] = 3.0 * np.nan_to_num(stats_[:,dict_['FG3M']].astype(float))\
                                  + 2.0 *   np.nan_to_num(stats_[:,dict_['FGM']].astype(float))\
                                  + 1.0 *  np.nan_to_num(stats_[:,dict_['FTM']].astype(float))\
                                  + 1.2 *  np.nan_to_num(stats_[:,dict_['REB']].astype(float))\
                                  + 1.5 *  np.nan_to_num(stats_[:,dict_['AST']].astype(float))\
                                  + 2.0 *  np.nan_to_num(stats_[:,dict_['BLK']].astype(float))\
                                  + 2.0 *  np.nan_to_num(stats_[:,dict_['STL']].astype(float))\
                                  - 1.0 *   np.nan_to_num(stats_[:,dict_['TOV']].astype(float))

    def load_season_json(self, year, ptg):
        season = u.yearToSeason(year)
        filename = "../data/json/data_%s_%i.json" % (ptg, year)
        print 'Trying to load %s' %(filename)
        with open(filename,"r") as fh:
            data = json.loads(fh.read())
        colnames = data['resultSets'][0]['headers']
        rows = data['resultSets'][0]['rowSet']
        return colnames,rows

    def load_teams(self):
        for iyear,year in enumerate(self.years):
            t_year = []

            #Load up team data
            t_colnames, t_data = self.load_season_json(year, "T") # team data for matches
            t_data = np.array(t_data)
            
            #Load up player data
            p_colnames, p_data = self.load_season_json(year, "P") # team data for matches
            p_data = np.array(p_data)
            
            #Open player stats file
            with gzip.open("../data/pickle/player_stats_%i.pkl" % year,"rb") as fh:
                data_raw = pickle.load(fh)


            if iyear ==0:
                #Create initial dictionaries
                t_d    = self.gen_dict(t_colnames,"None")
                p_d    = self.gen_dict(p_colnames,"None")

                t_sel_upp,t_opp_low,t_opp_high             = len(t_d)+len(self.t_fint),t_d["FGM"],len(t_d)+len(self.t_fint)

                #Create final dictionaries for individual teams
                st_dict = self.gen_dict(t_colnames ,"T","_SEL")
                ot_dict = self.gen_dict(np.array(t_colnames)[range(t_opp_low,len(t_colnames))],"T","_OPP")

                #Merge these dictionaries for composite team info
                self.t_d                            = self.gen_dict(np.append([s[0] for s in sorted(st_dict.items(), key=operator.itemgetter(1))],
                                                                       [s[0] for s in sorted(ot_dict.items(), key=operator.itemgetter(1))]),"None","",False)
            #Map final columns to fantasy points
            self.set_fant(p_d,p_data)
            self.set_fant(t_d,t_data)

            #Loads up the player positions
            temp_arr,temp_lines   = [],[]
            for id_,line in enumerate(p_data):
                pid = line[p_d['PLAYER_ID']]
                if (pid,year) not in data_raw:
                    print 'failed player %s with pid %s for id_ %s' % (line[p_d["PLAYER_NAME"]],pid,id_)
                    continue
                else:
                    temp_arr.append(np.append(line,str(data_raw[(pid,year)]['position'])))
                    temp_lines.append(id_)
            p_data = np.c_[p_data[temp_lines],temp_arr]



            #maps [W,L] to [0,1]
            t_data[:,t_d["WL"]][t_data[:,t_d["WL"]] == "W"]            = 1
            t_data[:,t_d["WL"]][t_data[:,t_d["WL"]] == "L"]            = 0

            #maps [A,H] to [0,1]
            t_data[:,t_d["MATCHUP"]] = np.array([int("@" not in s) for s in t_data[:,t_d["MATCHUP"]]])

            #maps game date to number of days rest
            t_data[:,t_d["GAME_DATE"]] =  np.array(map(lambda x: (datetime.datetime(*map(int,x.split("-"))) - \
                                                                     datetime.datetime(year=1970, month=1, day=1)).days, t_data[:,t_d["GAME_DATE"]] ))
            #sort to make time ordering
            t_data = t_data[t_data[:,t_d["GAME_DATE"]].astype(int).argsort()]

            for tit_, team_id in enumerate(np.unique(t_data[:,t_d['TEAM_ABBREVIATION']])):
                #Subset the teams and players
                teams_  =    t_data[t_data[:,t_d['TEAM_ABBREVIATION']] == team_id]
                players =    p_data[p_data[:,p_d['TEAM_ABBREVIATION']] == team_id]
                team_p  = []

                for git_,sel_team in enumerate(teams_):
                    #Cycle through games and find the scores by this team at each position
                    gid      =  sel_team[t_d["GAME_ID"]].astype(int)
                    psub     = players[players[:,p_d["GAME_ID"]].astype(int) == gid]
                    out_ = []
                    for line in self.positions:
                        sum_ = np.sum(psub[psub[:,-1] == line][:,p_d["FANT"]])
                        if sum_ != False:
                            out_.append(sum_)
                        else:
                            out_.append(np.nan)
                    sel_team = np.append(sel_team,out_)
                    if len(team_p) == 0:
                        team_p  = sel_team
                    else:
                        team_p = np.vstack((team_p,sel_team))


                if len(t_year) == 0:
                    t_year = team_p
                else:
                    t_year = np.vstack((t_year,team_p))

            if iyear == 0:
                t_total = t_year
            else:
                t_total = np.vstack((t_total,t_year))

        merged = []
        for team_id in np.unique(t_total[:,t_d['TEAM_ABBREVIATION']]):
            temp_merge = []
            teams_  =    t_total[t_total[:,t_d['TEAM_ABBREVIATION']] == team_id]
            opps_   =    t_total[t_total[:,t_d['TEAM_ABBREVIATION']] != team_id]

            #Merge team statistics with opponent statistics (select columns)
            for g_id,game_id in enumerate(np.unique(teams_[:,t_d['GAME_ID']])):
                opp_team    = opps_[opps_[:,t_d['GAME_ID']] == game_id][0]
                temp_merge.append(np.append(teams_[g_id][0:t_sel_upp+len(self.positions)],opp_team[t_opp_low:t_opp_high+len(self.positions)]))
            temp_merge = np.array(temp_merge)

            #Insert moving averages into the array
            for pos in self.positions:
                for range_ in self.t_fint:
                    if range_ == 1: continue
                    index_ = int(self.t_d['AVG_' + str(range_) + '_' + pos + '_SEL'])
                    base_  = int(self.t_d['AVG_1_' + pos + '_SEL'])
                    temp_merge = np.insert(temp_merge,index_,
                                     u.ma(temp_merge[:,base_].astype(float),range_),1)

            #Insert moving averages into the array
            for pos in self.positions:
                for range_ in self.t_fint:
                    if range_ == 1: continue
                    index_ = self.t_d['AVG_' + str(range_) + '_' + pos + '_OPP']
                    base_  = int(self.t_d['AVG_1_' + pos + '_OPP'])
                    temp_merge = np.insert(temp_merge,index_,
                                     u.ma(temp_merge[:,base_].astype(float),range_),1)

            if len(merged) == 0:
                merged = temp_merge
            else:
                merged = np.vstack((merged,np.array(temp_merge)))

        self.teams =  np.array(merged)

    def load_players(self):
        p_total = []
        for iyear,year in enumerate(self.years):
            #Load up player data
            p_year = []
            p_colnames, p_data = self.load_season_json(year, "P") # team data for matches
            p_data        = np.array(p_data)

            #Open player stats file
            with gzip.open("../data/pickle/player_stats_%i.pkl" % year,"rb") as fh:
                data_raw = pickle.load(fh)

            if iyear ==0:
                #Create initial dictionary
                p_d    = self.gen_dict(p_colnames,"None")

                #Create final dictionary
                self.p_d    =  self.gen_dict(p_colnames,"P")

            #maps final column to fantasy points
            self.set_fant(p_d,p_data)

            #maps [A,H] to [0,1]
            p_data[:,p_d["MATCHUP"]] = np.array([int("@" not in s) for s in p_data[:,p_d["MATCHUP"]]])

            #maps date to days since 1970
            p_data[:,p_d["GAME_DATE"]] =  np.array(map(lambda x: (datetime.datetime(*map(int,x.split("-"))) - \
                                                                     datetime.datetime(year=1970, month=1, day=1)).days, p_data[:,p_d["GAME_DATE"]] ))
            temp_arr,temp_lines   = [],[]
            for id_,line in enumerate(p_data):
                pid = line[p_d['PLAYER_ID']]
                if (pid,year) not in data_raw:
                    print 'failed player %s with pid %s for id_ %s' % (line[p_d["PLAYER_NAME"]],pid,id_)
                    continue
                else:
                    temp_arr.append(np.append(line,str(data_raw[(pid,year)]['position'])))
                    temp_lines.append(id_)
            p_data = np.c_[p_data[temp_lines],temp_arr]



            #sorts by this game date
            p_data = p_data[p_data[:,p_d["GAME_DATE"]].astype(int).argsort()]


            for tit_, player_id in enumerate(np.unique(p_data[:,p_d['PLAYER_ID']])):
                #Load up a player
                p_init  = p_data[p_data[:,p_d['PLAYER_ID']] == player_id]
                p_name  = str.split(self.clean_str(str(p_init[:,p_d['PLAYER_NAME']][0]))," ")

                #Check that the name loaded correctly
                if len(p_name) < 2:
                    print 'An error occured while trying to load the player named %s' % (p_name)
                    continue


                #Appending the players moving averages
                for range_ in self.p_fint:
                    p_init = np.c_[p_init,u.ma(p_init[:,p_d["FANT"]].astype(float),range_)]

                #Appending the target
                p_init = np.c_[p_init,np.append(np.roll(p_init[:,p_d["FANT"]],-1)[-1000000:-1],np.nan) ]

                #Appending the players rest
                p_init = np.c_[p_init,p_init[:,p_d["GAME_DATE"]].astype(int) - np.roll(p_init[:,p_d["GAME_DATE"]],1).astype(int)]

                #Load up the fantcrunch data
                key     = str(p_name[1] + ", " + p_name[0])
                if key in self.p_preds.keys():
                    key_s1 = self.p_preds[key]
                else:
                    print 'An error occured while trying to load the player named %s' % (p_name)
                    continue

                #Append the crucial fantcrunch datasets
                p_final = []
                for g in np.unique(p_init[:,p_d['GAME_DATE']]):
                    if g in np.array(key_s1.keys()).astype(int):
                        key_s2  = key_s1[str(g)]
                        if 'draftkings' not in key_s2.keys() :
                            continue
                        if 'fanduel' not in key_s2.keys() :
                            continue
                        p_temp                             = np.append(p_init[p_init[:,p_d['GAME_DATE']] == g],key_s2['fanduel']['Salary'])
                        p_temp                             = np.append(p_temp,key_s2['draftkings']['Salary'])
                        p_temp                             = np.append(p_temp,key_s2['fanduel']['Default_Proj_Score'])
                        if len(p_final) == 0:
                            p_final = np.array(p_temp)
                        else:
                            p_final = np.vstack((p_final,p_temp))

                if len(p_final) == 0:
                    continue

                if len(p_year) == 0:
                    p_year = p_final

                else:
                    p_year = np.vstack((p_year,p_final))
            if len(p_total) == 0:
                p_total = p_year
            else:
                p_total = np.vstack((p_total,p_year))
        print 'THe length of p_total is ' + str(len(p_total))
        self.players =  p_total

        pc_colnames, pc_data = self.load_season_json(year, "G") # team data for matches
        print pc_colnames
        self.player_cards = np.array(pc_data)

    def __init__(self, years=[2014], player_fant_int = [3,5,9,15,20],team_fant_int = [1,5,10,20], preds_file = '../data/pickle/fantcrunch_merged_nozip.pkl',debug=False):
    #Keep 1 in team_fant_int or face an error ~-_-~

        #Years to perform analysis on
        self.years        = years

        #Intervals for player fantasy points
        self.p_fint       = player_fant_int

        #Intervals for team fantasy pts allowed
        self.t_fint       = team_fant_int

        #Position key
        self.positions    = ['Forward', '', 'Center', 'Center-Forward', 'Guard', 'Guard-Forward', 'Forward-Center', 'Forward-Guard']

        #Scraped fantcrunch data
        with open(preds_file, 'rb') as handle:
            preds = pickle.load(handle)
        self.p_preds      = preds

        #Load up the teams first
        t0 = time.time()
        self.load_teams()
        t1 = time.time()
        print 'The time to load teams was %s' %(t1 - t0)

        #Load up the players second
        t0 = time.time()
        self.load_players()
        t1 = time.time()
        print 'The time to load players was %s' %(t1 - t0)
