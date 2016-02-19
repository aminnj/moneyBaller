import numpy as np
import datetime
import sys
sys.path.insert(0,"../")
import utils.utils as u
import xgboost as xgb
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


f_events      = '../data/parsed/events.csv'
events        = np.genfromtxt(f_events, delimiter=",", filling_values=np.nan, skip_header=1)
with open(f_events, 'r') as f:
    header = f.readline()
d_      = gen_dict(header)
X       = events[:,range(0,len(events[0])-1)].astype(float)
y       = events[:,-1].astype(float)

X = Imputer(missing_values=np.nan, strategy='mean', axis=0).fit_transform(X)
X = StandardScaler().fit_transform(X)

f_lookup      = '../data/parsed/events_lookup.csv'
lookup        = np.genfromtxt(f_lookup, delimiter=",", names=True,dtype=["S20","i8"])


f_fanduel     = 'FanDuel-NBA-2016-01-29-14555-players-list.csv'
fanduel       = np.genfromtxt(f_fanduel, delimiter=",", names=True,dtype=["S20","S20","S20","S20","S20","S20","S20"
                                                                         ,"S20","S20","S20","S20","S20","S20"])

fanduel['Salary']     = np.array([int(x.replace("\"","")) for x in fanduel['Salary']])
fanduel['First_Name'] = np.array([fanduel['First_Name'][x].replace("\"","") + " " + fanduel['Last_Name'][x].replace("\"","")
                                  for x in range(len(fanduel))])

date          =  int((datetime.datetime(year=2016, month=1, day=29) - datetime.datetime(year=1970, month=1, day=1)).days)

train   = X[lookup['GAME_DATE'] != date]
train_t = y[lookup['GAME_DATE'] != date]
test    = X[lookup['GAME_DATE'] == date]
test_t  = y[lookup['GAME_DATE'] == date]

regr    = linear_model.Lasso (alpha = 3.2).fit(train,train_t)#LinearRegression()
preds  = regr.predict(test)
print np.mean( np.abs(test_t - preds))
print np.mean( np.abs(test_t - events[lookup['GAME_DATE'] == date][:,d_['FANT_PREDICTION']]))

lookup  = lookup[lookup['GAME_DATE'] == date]

#TODO~ Find out why the nba database is missing so many players...
print len(lookup['PLAYER_NAME'])
print len(fanduel)





name_c  = 0
r_events = []
for id_,name in enumerate(lookup['PLAYER_NAME']):
    t_event = []
    fid_ = np.where(fanduel['First_Name'] == name)
    if len(fid_[0]) == 0:
        name_c = name_c + 1
        print 'The player %s is not contained in the fanduel list and the counter is up to %s '% (name,name_c)
        continue
    else:
        t_event.append(fanduel['Id'][fid_][0].replace("\"",""))
        t_event.append(fanduel['First_Name'][fid_][0].replace("\"",""))
        t_event.append(fanduel['Position'][fid_][0].replace("\"",""))
        t_event.append(int( fanduel['Salary'][fid_][0].replace("\"","") ))

        #t_event.append(preds[id_])
        t_event.append(events[:,d_['FANT_PREDICTION']][id_])
        t_event.append(events[:,d_['FANT_TARGET']][id_])
    r_events.append(t_event)
r_events = np.array(r_events)
d_ = {'Id':0, 'Name' : 1, 'Position' : 2,'Salary':3,'Predictions':4,'Actual':5 }
optimize_predictions.optimize_predictions(r_events,d_,.5)

