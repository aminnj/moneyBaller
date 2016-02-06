import numpy as np
import random, copy, pprint, math, sys
from tqdm import tqdm
from io import StringIO

MAX_SALARY = 60000

# np.random.seed(420)
alpha = 0.01
if len(sys.argv) > 1: alpha = float(sys.argv[-1])

# load data
fname = "fanduel.csv"
with open(fname, "r") as fh: filestr = unicode(fh.read().replace('"',''))
data = np.genfromtxt(StringIO(filestr),delimiter=",", names=True, dtype="S15,S5,S10,S10,f4,i8,i8,S7,S3,S3,S1,S3") #, usecols=[0,1,2,3,4,5,6])

data = data[np.vectorize(len)(data["Injury_Indicator"]) == 0] # Throw out people who are injured
# data = data[data["FPPG"] > 10] # Throw out people who have no chance of being in the lineup

# convert Id to integer because this fanduel is stupid
convert = np.vectorize(lambda x: int(x.replace("-","")))
ids = np.array(convert(data["Id"]))

# make some LUTs to get any info if given a player id
positions = np.unique(data["Position"]) # list of positions
d_id_to_position = dict(zip(ids,data["Position"]))
d_id_to_points = dict(zip(ids,data["FPPG"])) # we will want to replace these "points" with our predicted score
d_id_to_salary = dict(zip(ids,data["Salary"]))
d_id_to_name = dict(zip(ids,np.array(map(lambda x: " ".join(x), data[["First_Name","Last_Name"]]))))

# group players by position
d_group_by_pos = {} # key is position and value is a list of player ids
for pos in np.unique(data["Position"]): d_group_by_pos[pos] = []
for pid in ids: d_group_by_pos[d_id_to_position[pid]].append(pid)
for pos in d_group_by_pos.keys(): d_group_by_pos[pos] = np.array(d_group_by_pos[pos])

# make functions for hamiltonian and delta energy
def H(salary, points): return -points + (alpha*(salary-MAX_SALARY))*int(salary>MAX_SALARY)
def dE(pid_out, pid_in, salary, points):
    return H(salary+d_id_to_salary[pid_in] -d_id_to_salary[pid_out],
             points+d_id_to_points[pid_in] -d_id_to_points[pid_out]) - H(salary,points)

# construct initial lineup
lineup = {}
for pos,pids in d_group_by_pos.items(): lineup[pos] = np.random.choice( pids,size=2 if not "C" in pos else 1,replace=False )

# take a flattened list of the player ids in lineup and use these as keys to get salary/points, then sum
salary = np.sum(np.vectorize(d_id_to_salary.get)(np.concatenate(lineup.values())))
points = np.sum(np.vectorize(d_id_to_points.get)(np.concatenate(lineup.values())))
energy = H(salary, points)

best_points = -1
best_salary = -1
best_lineup = {}

T = 30.0
for it in range(1,150+1):
    T -= 0.2
    nSweeps = 100*it

    vpoints = []
    for isweep in range(nSweeps):
        # get position to swap (e.g., "C"), and index of player in that position (e.g., 0)
        pos_swap = np.random.choice(positions)
        isC = int(pos_swap=="C")
        pidx_swap_out = np.random.randint(low=0, high=2-isC)
        pid_swap_out = lineup[pos_swap][pidx_swap_out]
        other_pid = lineup[pos_swap][1-isC-pidx_swap_out]
        pid_swap_in = np.random.choice(d_group_by_pos[pos_swap])
        deltaE = dE(pid_swap_out, pid_swap_in, salary, points)
        if(deltaE < 0 or random.random() < math.exp(-1.0*deltaE/T)):
            if pid_swap_in != other_pid: # don't swap if we end up putting in a duplicate
                energy += deltaE
                points += d_id_to_points[pid_swap_in]-d_id_to_points[pid_swap_out]
                salary += d_id_to_salary[pid_swap_in]-d_id_to_salary[pid_swap_out]

                lineup[pos_swap][pidx_swap_out] = pid_swap_in
                vpoints.append(points)

                if points > best_points and salary <= MAX_SALARY:
                    best_points = points
                    best_salary = salary
                    best_lineup = copy.deepcopy(lineup)

    vpoints = np.array(vpoints)
    print T, salary, points, vpoints.mean(), vpoints.std()/np.sqrt(len(vpoints)), len(vpoints)

print best_points, best_salary
for pos in best_lineup:
    print 
    print ("%s: " %pos),
    for pid in best_lineup[pos]:
        print ("%s," % d_id_to_name[pid]),
