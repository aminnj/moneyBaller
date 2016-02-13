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
            avg_strings = ['AVG_'  + s for s in np.array(self.t_fint).astype(str)]
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
            return_dict["FANT_TARGET"]       = len(headers)+len(avg_strings)
            return_dict["REST"]              = len(headers)+len(avg_strings) + 1
            return_dict["FANDUEL_SALARY"]    = len(headers)+len(avg_strings) +2
            return_dict["DRAFTKINGS_SALARY"] = len(headers)+len(avg_strings) + 3
            return_dict["FANT_PREDICTION"]   = len(headers)+len(avg_strings) + 4

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
            t_colnames, t_data = self.load_season_json(year, "T") # team data for matches
            t_data_init        = np.array(t_data)

            if iyear ==0:
                t_dict_init    = self.gen_dict(t_colnames,"None")
                t_sel_upp,t_opp_low,t_opp_high             = len(t_dict_init)+len(self.t_fint),t_dict_init["FGM"],len(t_dict_init)+len(self.t_fint)

                st_dict = self.gen_dict(t_colnames ,"T","_SEL")
                ot_dict = self.gen_dict(np.array(t_colnames)[range(t_opp_low,len(t_colnames))],"T","_OPP")

                self.t_dict                            = self.gen_dict(np.append([s[0] for s in sorted(st_dict.items(), key=operator.itemgetter(1))],
                                                                       [s[0] for s in sorted(ot_dict.items(), key=operator.itemgetter(1))])
                                                                       ,"None","",False)
            self.set_fant(t_dict_init,t_data_init)                                                   #maps final column to fantasy points
            t_data_init[:,t_dict_init["WL"]][t_data_init[:,t_dict_init["WL"]] == "W"]            = 1 #maps [W,L] to [0,1]
            t_data_init[:,t_dict_init["WL"]][t_data_init[:,t_dict_init["WL"]] == "L"]            = 0
            t_data_init[:,t_dict_init["MATCHUP"]] = np.array([int("@" not in s) for s in t_data_init[:,t_dict_init["MATCHUP"]]]) #maps [A,H] to [0,1]

            t_data_init[:,t_dict_init["GAME_DATE"]] =  np.array(map(lambda x: (datetime.datetime(*map(int,x.split("-"))) - \
                                                                     datetime.datetime(year=1970, month=1, day=1)).days, t_data_init[:,t_dict_init["GAME_DATE"]] ))
            t_data_init = t_data_init[t_data_init[:,t_dict_init["GAME_DATE"]].astype(int).argsort()]
            for tit_, team_id in enumerate(np.unique(t_data_init[:,t_dict_init['TEAM_ID']])):
                teams_  =    t_data_init[t_data_init[:,t_dict_init['TEAM_ID']] == team_id]
                teams_[:,t_dict_init["GAME_DATE"]] = teams_[:,t_dict_init["GAME_DATE"]].astype(int) - np.roll(teams_[:,t_dict_init["GAME_DATE"]],1).astype(int)
                opps_   =    t_data_init[t_data_init[:,t_dict_init['TEAM_ID']] != team_id]
                sel_res,opp_res = [],[]

                for git_,sel_team in enumerate(teams_):
                    gid      =  sel_team[t_dict_init["GAME_ID"]].astype(int)
                    opp_team = opps_[opps_[:,t_dict_init["GAME_ID"]].astype(int) == gid]

                    if len(sel_res) == 0:
                        sel_res  = sel_team
                        opp_res  = opp_team
                    else:
                        sel_res = np.vstack((sel_res,sel_team))
                        opp_res = np.vstack((opp_res,opp_team))

                    if git_ == len(teams_)-1:
                        for range_ in self.t_fint:
                            opp_res = np.c_[opp_res,u.ma(opp_res[:,t_dict_init["FANT"]].astype(float),range_)]
                            sel_res = np.c_[sel_res,u.ma(sel_res[:,t_dict_init["FANT"]].astype(float),range_)]

                stack    = np.c_[sel_res[:,range(t_sel_upp)],opp_res[:,range(t_opp_low,t_opp_high)]]
                if len(t_year) == 0:
                    t_year = stack
                else:
                    t_year = np.vstack((t_year,stack))
            if iyear == 0:
                t_total = t_year
            else:
                t_total = np.vstack((t_total,t_year))
        self.teams =  t_total

    def load_players(self):
        p_total = []
        for iyear,year in enumerate(self.years):
            p_year = []
            p_colnames, p_data = self.load_season_json(year, "P") # team data for matches
            p_data_init        = np.array(p_data)

            if iyear ==0:
                p_d    = self.gen_dict(p_colnames,"None")
                self.p_dict    =  self.gen_dict(p_colnames,"P")
            self.set_fant(p_d,p_data_init) #maps final column to fantasy points
            p_data_init[:,p_d["MATCHUP"]] = np.array([int("@" not in s) for s in p_data_init[:,p_d["MATCHUP"]]]) #maps [A,H] to [0,1]

            for tit_, player_id in enumerate(np.unique(p_data_init[:,p_d['PLAYER_ID']])):
                p_init  = p_data_init[p_data_init[:,p_d['PLAYER_ID']] == player_id]
                p_name  = str.split(self.clean_str(str(p_init[:,p_d['PLAYER_NAME']][0]))," ")

                if len(p_name) < 2:
                    continue

                p_init[:,p_d["GAME_DATE"]] =  np.array(map(lambda x: (datetime.datetime(*map(int,x.split("-"))) - \
                                                                     datetime.datetime(year=1970, month=1, day=1)).days, p_init[:,p_d["GAME_DATE"]] ))

                p_init = p_init[p_init[:,p_d["GAME_DATE"]].astype(int).argsort()]

                for range_ in self.p_fint:
                    p_init = np.c_[p_init,u.ma(p_init[:,p_d["FANT"]].astype(float),range_)]

                p_init = np.c_[p_init,np.append(np.roll(p_init[:,p_d["FANT"]],-1)[-1000000:-1],np.nan) ]

                p_init = np.c_[p_init,p_init[:,p_d["GAME_DATE"]].astype(int) - np.roll(p_init[:,p_d["GAME_DATE"]],1).astype(int)]

                key     = str(p_name[1] + ", " + p_name[0])
                if key in self.p_preds.keys():
                    key_s1 = self.p_preds[key]
                else:
                    continue

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

    def __init__(self, years=[2014], player_fant_int = [3,5,9,15,20],team_fant_int = [3,5,9,15,20], preds_file = '../data/pickle/fantcrunch_merged_nozip.pkl',debug=False):

        self.years        = years
        self.p_fint       = player_fant_int
        self.t_fint       = team_fant_int
        with open(preds_file, 'rb') as handle:
            preds = pickle.load(handle)

        self.p_preds      = preds
        t0 = time.time()
        self.load_teams()
        t1 = time.time()
        print 'The time to load teams was %s' %(t1 - t0)

        t0 = time.time()
        self.load_players()
        t1 = time.time()
        print 'The time to load players was %s' %(t1 - t0)
