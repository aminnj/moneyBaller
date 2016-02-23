import numpy as np
import random, copy, pprint, math, sys
from tqdm import tqdm
from io import StringIO

class optimize_predictions:
    def H(self,salary, points):
        return -points + (self.alpha*(salary-self.MAX_SALARY))*int(salary>self.MAX_SALARY)

    # make functions for hamiltonian and delta energy
    def dE(self,pid_out, pid_in, salary, points):
        return self.H(salary+self.d_id_to_salary[pid_in] -self.d_id_to_salary[pid_out],
                 points+self.d_id_to_points[pid_in] -self.d_id_to_points[pid_out]) - self.H(salary,points)

    def __init__(self,data,d_,alpha = .5, backtest = True):
        self.MAX_SALARY = 60000
        self.alpha = alpha
        # convert Id to integer because this fanduel is stupid
        #convert = np.vectorize(lambda x: int(x.replace("-","")))
        ids     = (data[:,d_["Id"]])

        # make some LUTs to get any info if given a player id
        positions             = np.unique(data[:,d_["Position"]]) # list of positions
        self.d_id_to_position = dict(zip(ids,data[:,d_["Position"]]))
        self.d_id_to_points   = dict(zip(ids,data[:,d_["Predictions"]].astype(float)))
        self.d_id_to_salary   = dict(zip(ids,data[:,d_["Salary"]].astype(int)))
        self.d_id_to_name     = dict(zip(ids,data[:,d_["Name"]]))
        if backtest:
            self.d_id_to_actual   = dict(zip(ids,data[:,d_["Actual"]].astype(float)))

        # group players by position
        d_group_by_pos = {} # key is position and value is a list of player ids
        for pos in np.unique(data[:,d_["Position"]]): d_group_by_pos[pos] = []
        for pid in ids: d_group_by_pos[self.d_id_to_position[pid]].append(pid)
        for pos in d_group_by_pos.keys(): d_group_by_pos[pos] = np.array(d_group_by_pos[pos])


        # construct initial lineup
        lineup = {}
        for pos,pids in d_group_by_pos.items(): lineup[pos] = np.random.choice( pids,size=2 if not "C" in pos else 1,replace=False )
        # take a flattened list of the player ids in lineup and use these as keys to get salary/points, then sum
        salary = np.sum(np.vectorize(self.d_id_to_salary.get)(np.concatenate(lineup.values())))
        points = np.sum(np.vectorize(self.d_id_to_points.get)(np.concatenate(lineup.values())))
        energy = self.H(salary, points)

        best_points = -1
        best_salary = -1
        best_lineup = {}

        T = 5.0
        lineups = []

        for it in range(1,150+1):
            T -= 0.2
            if T < 0: continue
            nSweeps = 20000*it

            vpoints = []

            for isweep in range(nSweeps):
                # get position to swap (e.g., "C"), and index of player in that position (e.g., 0)
                pos_swap = np.random.choice(positions)
                isC = int(pos_swap=="C")
                pidx_swap_out = np.random.randint(low=0, high=2-isC)
                pid_swap_out = lineup[pos_swap][pidx_swap_out]
                other_pid = lineup[pos_swap][1-isC-pidx_swap_out]
                pid_swap_in = np.random.choice(d_group_by_pos[pos_swap])
                deltaE = self.dE(pid_swap_out, pid_swap_in, salary, points)
                if(deltaE < 0 or random.random() < math.exp(-1.0*deltaE/T)):
                    if pid_swap_in != other_pid: # don't swap if we end up putting in a duplicate
                        energy += deltaE
                        points += self.d_id_to_points[pid_swap_in]-self.d_id_to_points[pid_swap_out]
                        salary += self.d_id_to_salary[pid_swap_in]-self.d_id_to_salary[pid_swap_out]

                        lineup[pos_swap][pidx_swap_out] = pid_swap_in
                        vpoints.append(points)

                        if points > best_points + 2.5 and salary <= self.MAX_SALARY:
                            best_points = points
                            best_salary = salary
                            best_lineup = copy.deepcopy(lineup)
                            if len(lineups) < 10:
                                lineups.append(best_lineup)
                            else:
                                lineups = np.append(lineups[1:10],best_lineup)
            vpoints = np.array(vpoints)
            print T, salary, points, vpoints.mean(), vpoints.std()/np.sqrt(len(vpoints)), len(vpoints)

        print best_points, best_salary
        for line in lineups:
            for pos in line:
                print
                for pid in line[pos]:
                    print ("%s: %s w/ Predicted: %s, Actual %s " % (pos,self.d_id_to_name[pid],self.d_id_to_points[pid],self.d_id_to_actual[pid]))
            print 'The team salary was ' + str(np.sum(np.vectorize(self.d_id_to_salary.get)(np.concatenate(line.values()))))
            print 'The predicted points were ' + str(np.sum(np.vectorize(self.d_id_to_points.get)(np.concatenate(line.values()))))
            if backtest:
                print 'The actual points were ' + str(np.sum(np.vectorize(self.d_id_to_actual.get)(np.concatenate(line.values()))))