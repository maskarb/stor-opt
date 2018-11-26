import gurobipy as gu
from lookup_stor import stor_els as se
from report import lindo
from storage_cal import binary_search_iterative, lookup

ACRE_FT_TO_CF = 435560
SEC_PER_DAY = 86400

def get_min_release(month):
    return 100 if month in range(4, 9) else 60



def stickerrythinginafunc(days, month, storage, demand, inflow, precip, evap, drought_stage):
    m = gu.Model('ooffff') # pylint: disable=E1101

    min_release = get_min_release(month) * days * SEC_PER_DAY / ACRE_FT_TO_CF
    max_release = 8000 * days * SEC_PER_DAY / ACRE_FT_TO_CF

    min_storage = 25073     # at MSL = 236.5 ft - top of sediment storage
    max_storage = 972610    # at MSL = 291.5 ft - top of dam

    release = m.addVar(name="release")
    dem_fac = m.addVar(name="dem_fac")

    m.update()
    m.setObjective(storage + inflow + precip - evap - release - demand*dem_fac - max_storage, sense=gu.GRB.MAXIMIZE) # pylint: disable=E1101


    m.addConstr(release >= min_release)
    m.addConstr(release <= max_release)

    if drought_stage == 0:
        m.addConstr(dem_fac >= 0.85)
        m.addConstr(dem_fac <= 1.00)
    elif drought_stage == 1:
        m.addConstr(dem_fac >= 0.55)
        m.addConstr(dem_fac <= 0.85)
    elif drought_stage == 2:
        m.addConstr(dem_fac >= 0.45)
        m.addConstr(dem_fac <= 0.55)
    elif drought_stage == 3:
        m.addConstr(dem_fac >= 0.0)
        m.addConstr(dem_fac <= 0.45)

    m.update()
    m.optimize()
    lindo(m)

    rel_val = release.X
    dem_val = demand * dem_fac.X
    stor_val = m.ObjVal + max_storage
    elevation = lookup(stor_val, se)


    print()
    print(f'{elevation:10.2f} {stor_val:10.2f} {dem_val:10.2f} {dem_fac.X:10.2f} {rel_val:10.2f}')

    return rel_val, dem_val

days = 30
month = 6
storage = 128186.48743337806
demand = 6005.484226694337
inflow = 4980.411049100027
precip = 1853.357137054525
evap = 3772.3573564026738
drought_stage = 0

stickerrythinginafunc(days, month, storage, demand, inflow, precip, evap, drought_stage)