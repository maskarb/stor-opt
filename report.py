
# report-v91.py (for Python 2 and 3)

# Read a Gurobi LP file, optimize it, & write a Lindo-style report

# Author: John Baugh (jwb@ncsu.edu)
# Version: 0.91

# LP format
#   http://www.gurobi.com/documentation/7.5/refman/lp_format.html

# Attributes:
#   http://www.gurobi.com/documentation/7.5/refman/attributes.html

from __future__ import print_function     # Python 2 and 3

import gurobipy
import os, sys, time

renumber = True                           # number rows from 1 instead of 0

def solve(infile):
    print('Reading ' + infile)
    m = gurobipy.read(infile)             # read and solve a model
    m.ModelName = infile
    m.optimize()                          # optimize it
    echo_model(m)
    int_constraints = dict()              # for MIPs: added integer constraints
    if m.isMIP == 1:                      # set integer values as found and
        for v in m.getVars():             #   convert to a pure LP
            if v.getAttr('VType') in ['B', 'I']:
                int_constraints[v.VarName] = m.addConstr(v == v.X)
                v.vtype = gurobipy.GRB.CONTINUOUS
                v.ub = gurobipy.GRB.INFINITY
        with open(outfile(m), 'a') as f:
            f.write('\n RE-INSTALLING BEST SOLUTION...\n')
        m.optimize()                      # re-solve as a pure LP
    lindo(m, int_constraints)

# echo the model formulation
def echo_model(m):
    m.write('temp.lp')
    print('Writing ' + outfile(m))
    copy_file('temp.lp', outfile(m))
    os.remove('temp.lp')

def copy_file(i, o):
    with open(i) as fi:
        with open(o, "w") as fo:
            for s in fi:
                if len(s) > 6 and s[0:2] == ' R':
                    sa = s.split()
                    if len(sa[0]) > 0:
                        cnum = str(int(sa[0][1:-1]) + 1)
                        fo.write(' ' + cnum + ')')
                        for x in sa[1:]:
                            fo.write(' ' + x)
                        fo.write('\n')
                else:
                    fo.write(s)

# write a Lindo style report
def lindo(m, int_constraints=dict()):
    with open(outfile(m), 'w') as f:      # write a standard report
        f.write('\nreport.py v.0.91 output from %s at %s:\n' % \
                (m.ModelName, time.strftime('%I:%M %p on %m/%d/%Y')))
        if m.Status == 4:                 # infeasible or unbounded
            m.params.DualReductions = 0
            m.optimize()                  # resolve to figure out which it is
        if m.Status == 2:                 # optimal
            write(f, m, int_constraints)
        elif m.Status == 3:               # infeasible
            m.computeIIS()
            m.write(outfile(m, '.ilp'))
            print('File %s written to help identify source of infeasibility' % \
                outfile(m, '.ilp'))
        else:                             # other than optimal or infeasible
            f.write('\n%s\n\n' % codes[m.Status])

# so that constraints are numbered starting at 1 instead of 0
def constr_name(c):
    s = c.getAttr('ConstrName')
    if renumber and s[0] == 'R' and s[1:].isdigit():
        return str(int(s[1:]) + 1)
    else:
        return s

def write(f, m, int_constraints):
    fmt = ' %9s %16.8g %17.8g\n'
    fmt2 = ' %8s %15.8g %16.8g %16.8g\n'
    f.write('\n        OBJECTIVE FUNCTION VALUE\n\n')
    f.write(' %9s %13.8g\n\n' % ('0)', m.ObjVal))
    f.write('  VARIABLE        VALUE          REDUCED COST\n')
    for v in m.getVars():
        value = v.X
        if value == 0.0:               # remove "negative" zeros
            value = 0.0
        if v.VarName in int_constraints:
            rc = int_constraints[v.VarName].getAttr('PI')
        else:
            rc = v.getAttr('RC')
        if rc == 0.0:                  # remove "negative" zeros
            rc = 0.0
        if rc != 0:                    # Lindo sign convention
            rc = m.ModelSense * rc
        f.write(fmt % (v.VarName, value, rc))
    f.write('\n       ROW   SLACK OR SURPLUS     DUAL PRICES\n')
    for c in m.getConstrs():
        if c not in int_constraints.values():
            slack = c.getAttr('Slack')
            if slack == 0.0:               # remove "negative" zeros
                slack = 0.0
            if slack != 0 and c.getAttr('Sense') == '>':
                slack = -slack             # Lindo sign convention
            dp = c.getAttr('PI')
            if dp == 0.0:                  # remove "negative" zeros
                dp = 0.0
            if dp != 0:                    # Lindo sign convention
                dp = -m.ModelSense * dp
            f.write(fmt % (constr_name(c) + ')', slack, dp))
    f.write('\n NO. ITERATIONS=%8d\n\n' % m.IterCount)
    if len(int_constraints) == 0:
        f.write(' RANGES IN WHICH THE BASIS IS UNCHANGED:\n\n')
        f.write('                           OBJ COEFFICIENT RANGES\n')
        f.write(' VARIABLE         CURRENT        ALLOWABLE        ALLOWABLE\n')
        f.write('                   COEF          INCREASE         DECREASE\n')
        for v in m.getVars():
            coef = v.getAttr('Obj')
            up = num_or_infinity(v.getAttr('SAObjUp'))
            low =  num_or_infinity(v.getAttr('SAObjLow'))
            f.write(fmt2 % (v.VarName, coef, up - coef, coef - low))
        f.write('\n                           RIGHTHAND SIDE RANGES\n')
        f.write('      ROW         CURRENT        ALLOWABLE        ALLOWABLE\n')
        f.write('                    RHS          INCREASE         DECREASE\n')
        for c in m.getConstrs():
            rhs = c.getAttr('RHS')
            up = num_or_infinity(c.getAttr('SARHSUp'))
            low =  num_or_infinity(c.getAttr('SARHSLow'))
            f.write(fmt2 % (constr_name(c), rhs, up - rhs, rhs - low))

def num_or_infinity(x):
    if x == gurobipy.GRB.INFINITY:
        return float('inf')
    elif x == -gurobipy.GRB.INFINITY:
        return float('-inf')
    return x

# create a filename for output files by using a '.log' extension (default)
def outfile(m, new_extension='.log'):
    name, ext = os.path.splitext(m.ModelName)
    return name + new_extension

codes = {1: 'LOADED', 2: 'OPTIMAL', 3: 'INFEASIBLE', 4: 'INF_OR_UNBD',
         5: 'UNBOUNDED', 6: 'CUTOFF', 7: 'ITERATION_LIMIT', 8: 'NODE_LIMIT',
         9: 'TIME_LIMIT', 10: 'SOLUTION_LIMIT', 11: 'INTERRUPTED',
         12: 'NUMERIC', 13: 'SUBOPTIMAL', 14: 'INPROGRESS'}

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('usage: gurobi.sh report.py file.lp [file2.lp ...]')
    else:
        for i in range(1, len(sys.argv)):
            solve(sys.argv[i])
