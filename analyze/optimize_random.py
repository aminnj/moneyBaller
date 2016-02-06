import numpy as np
import random, copy
from tqdm import tqdm
from io import StringIO

# load data
fname = "fanduel.csv"
with open(fname, "r") as fh: filestr = unicode(fh.read().replace('"',''))
data = np.genfromtxt(StringIO(filestr),delimiter=",", names=True, dtype="S15,S5,S10,S10,f4,i8,i8,S7,S3,S3", usecols=[0,1,2,3,4,5,6])

# convert Id to integer because this fanduel is stupid
convert = np.vectorize(lambda x: int(x.replace("-","")))
ids = np.array(convert(data["Id"]))

# make some LUTs to get any info if given a player id
d_id_to_position = dict(zip(ids,data["Position"]))
d_id_to_points = dict(zip(ids,data["FPPG"])) # we will want to replace these "points" with our predicted score
d_id_to_salary = dict(zip(ids,data["Salary"]))
d_id_to_name = dict(zip(ids,np.array(map(lambda x: " ".join(x), data[["First_Name","Last_Name"]]))))

# group players by position
d_group_by_pos = {} # key is position and value is a list of player ids
for pos in np.unique(data["Position"]): d_group_by_pos[pos] = []
for pid in ids: d_group_by_pos[d_id_to_position[pid]].append(pid)
for pos in d_group_by_pos.keys(): d_group_by_pos[pos] = np.array(d_group_by_pos[pos])

# select lineup randomly (remember, only 1 player if position is "C")
max_points = -1
salary = 0
best_lineup = {}
for i in tqdm(range(100000)):
    lineup = {}
    for pos,pids in d_group_by_pos.items():
        lineup[pos] = np.random.choice( pids,size=2 if not "C" in pos else 1,replace=False )

    # take a flattened list of the player ids in lineup and use these as keys to get salary/points, then sum
    init_salary = np.sum(np.vectorize(d_id_to_salary.get)(np.concatenate(lineup.values())))
    init_points = np.sum(np.vectorize(d_id_to_points.get)(np.concatenate(lineup.values())))

    # print init_salary, init_points
    if init_points > max_points and init_salary <= 60000:
        max_points = init_points
        salary = init_salary
        best_lineup = copy.deepcopy(lineup)

print max_points, salary
for pos in best_lineup:
    print 
    print ("%s: " %pos),
    for pid in best_lineup[pos]:
        print ("%s," % d_id_to_name[pid]),
