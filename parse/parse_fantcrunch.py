import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pickle, gzip, sys
from collections import Counter
from sklearn import cluster
sys.path.insert(0,"../")
import utils.utils as u

np.set_printoptions(linewidth=205,formatter={'float_kind':lambda x: "%.2f" % x })

# some vars
outfname = "../data/parsed/fantcrunch.txt"
years = [2014,2015]
types = ["yahoo","draftkings", "fanduel", "fantasyaces", "fantasyfeud"]

with open(outfname,"w") as fhout:
    # MAKE CHANGES ON LINES MARKED WITH XXX
    header = "PlayerName|Date|PlayerID|Site|IsHome|\
              Injured|InjuryType|InjuryStatement|\
              LastSalary|Salary|GameCount|\
              AveragePoints|SigmaPoints|\
              ProjectedMins|ProjectedScore|\
              ProjectedCeiling|ProjectedFloor|\
              ActualPoints".replace(" ","")
    fhout.write("%s\n" % header)

first = True
for year in years:
# for year in years[:1]:
    for typ in types:
    # for typ in types[:2]:
        try:
            with gzip.open("../data/pickle/fantcrunch_%s_%i.pkl" % (typ,year),"rb") as fh: data = pickle.load(fh)
        except: continue

        Xtot = []
        for date in data.keys():
        # for date in data.keys()[:2]:
            for pid in data[date].keys():
            # for pid in data[date].keys()[:2]:
                try:
                    player = data[date][pid]

                    injured = 0
                    injuryType = ""
                    injuryStatement = ""
                    if "Injury_status" in player and player["Injury_status"] == "P":
                        injured = 1
                        injuryType = player["Injury_desc"]
                        injuryStatement = player["Injury_details"]

                    # XXX
                    Xtot.append( [player["PlayerName"], date, int(pid), typ, player["Team"]==player["HomeTeam"], \
                                  injured, injuryType, injuryStatement, \
                                  float(player["Last_Sal"] or "nan"),float(player["Salary"] or "nan"),float(player["gameCount"] or "nan"),\
                                  float(player["Avg_Pts"] or "nan"),float(player["stddev"] or "nan"),\
                                  float(player["Proj_Mins"] or "nan"),float(player["Proj_Score"] or "nan"),\
                                  float(player["Proj_Ceiling"] or "nan"),float(player["Proj_Floor"] or "nan"),\
                                  float(player["Actual_Pts"] or "nan")] )
                except:
                    print "ERROR WITH",year,typ,date,pid

        with open(outfname,"a") as fhout:
            for line in Xtot:
                # XXX
                fmtstr = "%s|%i|%i|%s|%i|\
                             %i|%s|%s|\
                             %.1f|%.1f|%.0f|\
                             %.2f|%.2f|\
                             %.1f|%.2f|\
                             %.2f|%.2f|\
                             %.2f\n".replace(" ","")
                fhout.write(fmtstr % tuple(line))

        print "wrote data for %s %i" % (typ, year)

