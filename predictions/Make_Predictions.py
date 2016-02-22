import numpy as np
import datetime
import sys
sys.path.insert(0,"../")
import utils.utils as u
#import xgboost as xgb
from sklearn.preprocessing import StandardScaler,Imputer
from sklearn import datasets, linear_model
sys.path.append('../analyze')
import optimize_predictions

def gen_dict(header):
    splitter_ = header[2:].split(",")
    d_ = {}
    for id_,line in enumerate(splitter_):
        d_[line] = id_
    return d_

def pos_map(x):
        if x == 0:
            return 'SG'
        if x == 1:
            return 'PG'
        if x == 2:
            return 'SF'
        if x == 3:
            return 'C'
        if x == 4:
            return 'PF'

f_events      = '../data/parsed/events.csv'
events        = np.genfromtxt(f_events, delimiter=",", filling_values=-999999, skip_header=1)
events        = events.astype(float)
with open(f_events, 'r') as f:
    header = f.readline()
d_      = gen_dict(header)


f_lookup      = '../data/parsed/events_lookup.csv'
lookup        = np.genfromtxt(f_lookup, delimiter=",", names=True,dtype=["S20","i8"])


date          =  int((datetime.datetime(year=2016, month=2, day=06) - datetime.datetime(year=1970, month=1, day=1)).days)

X       = events[:,range(0,len(events[0])-1)].astype(float)
y       = events[:,-1].astype(float)

X       = Imputer(missing_values='NaN', strategy='mean', axis=0).fit_transform(X)

train   = X[lookup['GAME_DATE'] != date]
train_t = y[lookup['GAME_DATE'] != date]
test    = X[lookup['GAME_DATE'] == date]
test_t  = y[lookup['GAME_DATE'] == date]

regr    = linear_model.Lasso (alpha = 3.2).fit(train,train_t)#LinearRegression()
preds   = regr.predict(test)

events  = events[lookup['GAME_DATE'] == date]
lookup  = lookup[lookup['GAME_DATE'] == date]

#TODO~ Find out why the nba database is missing so many players...
print len(lookup['PLAYER_NAME'])
#print len(fanduel)



f_fanduel      = 'FanDuel-NBA-2016-02-06-14627-players-list.csv'
fanduel       = np.genfromtxt(f_fanduel, delimiter=",", names=True,dtype=["S20","S20","S20","S20","S20","S20","S20"
                                                                         ,"S20","S20","S20","S20","S20","S20"])

fanduel['Salary']     = np.array([int(x.replace("\"","")) for x in fanduel['Salary']])
fanduel['First_Name'] = np.array([fanduel['First_Name'][x].replace("\"","") + " " + fanduel['Last_Name'][x].replace("\"","")
                                  for x in range(len(fanduel))])


name_c  = 0
r_events = []
for id_,name in enumerate(lookup['PLAYER_NAME']):
    t_event = []
    #if events[:,d_['FANT_PREDICTION']][id_] < 23:
    #    continue
    fid_ = np.where(fanduel['First_Name'] == name)
    if len(fid_[0]) == 0:
        name_c = name_c + 1
        print 'The player %s is not contained in the fanduel list and the counter is up to %s '% (name,name_c)
        continue
    if fanduel['Position'][fid_][0] != pos_map(events[:,d_['POSITION']][id_].astype(int)):
        print 'position error %s' % (name)
        print fanduel['Position'][fid_][0]
        print events[:,d_['POSITION']][id_].astype(int)
        print pos_map(events[:,d_['POSITION']][id_].astype(int))
    t_event.append(id_)
    t_event.append(lookup['PLAYER_NAME'][id_])
    t_event.append(fanduel['Position'][fid_][0])#pos_map(events[:,d_['POSITION']][id_].astype(int)))
    t_event.append(int(events[:,d_['FANDUEL_SALARY']][id_]))
    t_event.append(preds[id_])
    t_event.append(float(events[:,d_['FANT_TARGET']][id_]))
    r_events.append(t_event)

print len(r_events)
r_events = np.array(r_events)

d_ = {'Id':0, 'Name' : 1, 'Position' : 2,'Salary':3,'Predictions':4,'Actual':5 }
optimize_predictions.optimize_predictions(r_events,d_,.5)

