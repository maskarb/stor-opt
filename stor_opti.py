import gurobipy as gu

import lookup_constants as c
from lookup_stor import stor_els as se
from report import lindo
from storage_cal import binary_search_iterative, lookup


def get_min_release(month):
    return 100 if month in range(4, 9) else 60

def stickerrythinginafunc(days, month, storage, inflow, precip, evap, demand, drought_stage):
    name = 'ooffff'
    stor_init = storage + inflow + precip - evap
    m = gu.Model(name) # pylint: disable=E1101

    min_release = get_min_release(month) * days * c.SEC_PER_DAY / c.ACRE_FT_TO_CF
    max_release = 8000 * days * c.SEC_PER_DAY / c.ACRE_FT_TO_CF

    min_storage = 25073     # at MSL = 236.5 ft - top of sediment storage
    ful_storage= 131394.5  # at MSL = 251.5 ft - normal operating level
    max_storage = 972610    # at MSL = 291.5 ft - top of dam

    release = m.addVar(name="release")
    dem_fac = m.addVar(name="dem_fac")
    s1_mins = m.addVar(name="s1_minus")
    s1_plus = m.addVar(name="s1_plus")
    d1_mins = m.addVar(name="d1_minus")
    d1_plus = m.addVar(name="d1_plus")

    m.update()

    w = 0.005
    m.setObjective( w*(s1_plus + d1_mins) + (1 - w)*(d1_plus + s1_mins), sense=gu.GRB.MINIMIZE) # pylint: disable=E1101


    m.addConstr(release >= min_release)
    m.addConstr(release <= max_release)

    m.addConstr(stor_init - release - demand*dem_fac + s1_mins - s1_plus == ful_storage)
    m.addConstr(demand*dem_fac + d1_mins - d1_plus == demand)

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
    m.setParam('OutputFlag', False)
    m.optimize()
    m.write(name+'.lp')
    lindo(m)

    released = release.X
    supplied = demand * dem_fac.X
    stor_val = stor_init - released - supplied
    elevation = lookup(stor_val, se)


    print()
    print(f'{elevation:10.2f} {stor_val:10.2f} {supplied:10.2f} {dem_fac.X:10.2f} {released:10.2f}')

    return released, supplied, dem_fac

def main():
    days = 30
    month = 6
    storage = 135891.3285775884
    demand = 6005.484226694337
    inflow = 4980.411049100027
    precip = 1853.357137054525
    evap = 3772.3573564026738
    drought_stage = 0

    stickerrythinginafunc(days, month, storage, inflow, precip, evap, demand, drought_stage)

if __name__ == "__main__":
    main()