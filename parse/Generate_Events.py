import operator
import numpy as np
import pickle
import sys
sys.path.insert(0,"../")
import Load_Games

def gen_key(g_,p_,m):
    d_ = {}
    vars = np.append( g_,
                      np.append(["AVG_" + str(s) for s in m.p_fint],p_) )
    for id_,line in enumerate(vars):
        d_[line] = id_
    return d_

np.random.seed(0)
m      = Load_Games.Load_Games(years=[2014])

teams   = m.teams
players = m.players
t_d =  m.t_d
p_d =  m.p_d


print 'The sorted team items are ' + str(sorted( t_d.items(), key=operator.itemgetter(1)))
print 'The sorted player items are ' + str(sorted(p_d.items(), key=operator.itemgetter(1)))

events = []

g_vars = np.append(np.append(['AVG_' + s + "_SEL" for s in np.array(m.t_inclusive).astype(str)],
                             ['AVG_' + s + "_OPP" for s in np.array(m.t_inclusive).astype(str)]),
                             ["AVG_" + str(s) + "_" +"POSITION_OPP" for s in m.t_fint])

p_vars = [['REST'],['FANDUEL_SALARY'],['DRAFTKINGS_SALARY'],['MATCHUP'],['FANT_PREDICTION'],['POSITION'],['FANT_TARGET']]
d_ = gen_key(g_vars,p_vars,m)

print sorted(d_.items(), key=operator.itemgetter(1))

p_ = [p_d['REST'],p_d['FANDUEL_SALARY'],p_d['DRAFTKINGS_SALARY'],p_d['MATCHUP'],p_d["FANT_PREDICTION"],p_d["POSITION"],p_d['FANT_TARGET']]


for t_name in np.unique(teams[:,t_d['TEAM_NAME_SEL']].astype(str)):
    team_players = players[players[:,p_d['TEAM_NAME']].astype(str) == t_name]
    team_games   = teams[teams[:,t_d["TEAM_NAME_SEL"]].astype(str) == t_name]

    for game in team_games:
        gid = game[t_d['GAME_ID_SEL']]
        for player in team_players[team_players[:,p_d['GAME_ID']] == gid]:
            event = []
            g_vars = np.append( np.append(map(lambda x: t_d[x], ['AVG_' + s + "_SEL" for s in np.array(m.t_inclusive).astype(str)]) ,
                                          map(lambda x: t_d[x], ['AVG_' + s + "_OPP" for s in np.array(m.t_inclusive).astype(str)]) ),
                               map(lambda x: t_d[x] ,["AVG_" + str(s) + "_" + player[p_d['POSITION']] + "_OPP" for s in m.t_fint]))

            p_vars = np.append(map(lambda x: p_d[x],["AVG_" + str(s) for s in m.p_fint]),p_)

            for line in g_vars:
                event.append(game[line])

            for line in p_vars:
                event.append(player[line])
            events.append(event)

events        = np.array(events)
events        = events[events[:,d_['AVG_9']].astype(float) == events[:,d_['AVG_9']].astype(float)]
events        = events[events[:,d_['FANT_TARGET']].astype(float) == events[:,d_['FANT_TARGET']].astype(float)]

pos_ = {}
for id_,line in enumerate(m.positions):
   pos_[line] = id_

events[:,d_['POSITION']] = map(lambda x: pos_[x] ,events[:,d_['POSITION']])
head = ''
for line in sorted(d_.items(), key=operator.itemgetter(1)): head = head + str(line[0]) + ','
np.savetxt('../data/events.csv',events.astype(float),delimiter=',',header = head)
