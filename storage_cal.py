import csv
from ast import literal_eval

from tabulate import tabulate

# import gurobipy as g

from lookup_area import els_area
from lookup_drought_stage import drought_stages as ds
from lookup_elev import els_stor
from lookup_stor import stor_els

ACRE_FT_TO_GAL = 325850.943
ACRE_FT_TO_CF = 43559.9

# m = g.Model() # pylint: disable=E1101

# rel = m.addVar(name='release')


def read_csv(file):
    with open(file, 'r', newline='') as f:
        data_reader = csv.reader(f)
        __ = next(data_reader) # remove headers
        ipe_data = [line for line in data_reader]
    return ipe_data



def start():
    table_list = []
    ts_file, rs_file = 'timeseries_0_0.8.csv', 'reservoir-shift_0.8-ts-0.csv'
    storage = lookup(251.5, els_stor) # assume full lake to start (el. 251.5 ft, MSL)
    ipe_data, model_output = read_csv(ts_file), read_csv(rs_file)
    for i in range(600):
        month = get_month(i)
        days = days_in_month(month)
        if month in [4, 5, 6, 7, 8]: # summer
            stor_comp = lookup(251.5, els_stor)
        else:
            stor_comp = lookup(250.1, els_stor)

        inflow, precip, evap = get_ipe(ipe_data[i])
        raw_demand, population = get_dp(model_output[i])
        demand = get_withdrawn(raw_demand, storage)

        outflow = release(storage, month, days)
        inflow *= days * 3600*24 / ACRE_FT_TO_CF
        precip = get_vol_delta(precip, storage)
        evap = get_vol_delta(evap, storage)


        storage = storage + inflow + precip - evap - outflow - demand
        perc_full = storage / stor_comp

        table_list.append([month, inflow, precip, evap, outflow, demand, storage, perc_full])
    print(tabulate(table_list, headers=['mo', 'inflow', 'precip', 'evap', 'outlow', 'demand', 'storage', '% full'], floatfmt=".2f"))



def get_month(i):
    mo = i + 1
    if mo % 12 == 0:
        month = 12
    else:
        month = mo % 12
    return month

def get_ipe(line):
    ipe_data = [literal_eval(val) for val in line[:3]]
    return ipe_data

def get_dp(line):
    return literal_eval(line[7]), literal_eval(line[13])

def get_vol_delta(inches, storage):
    init_el = lookup(storage, stor_els)
    final_el = init_el + inches/12
    return lookup(final_el, els_stor) - storage


def get_withdrawn(demand, storage):
    lowestStorage = lookup(236.5, els_stor) # top of sediment storage (el. 236.5 ft, MSL)
    remainingWater = storage - lowestStorage
    if (remainingWater >= demand):
        actual = demand
    elif (remainingWater > 0):
        actual = remainingWater
    else:
        actual = 0
    return actual

def release(storage, month: int, days: int):
    elevation = lookup(storage, stor_els)
    normalElavation = 0
    release = 0
    maxDischarge = 8000 # (cfs) approximate at elevation 250 m.s.l.
    # freeOverflowing = lookup(elevation, els_stor) - lookup(268, els_stor)

    minimumReleaseSummer = 100
    minimumReleaseWinter = 60

    counter = 0
    totalRelease = 0
    if (month >= 4 and month <= 8):
        release = minimumReleaseSummer
        normalElavation = 251.5
        if (elevation <= normalElavation):
            storage -= release * 3600 * 24 * days / 43560
            totalRelease = release * 3600 * 24 * days / 43560
        else:
            while (elevation > normalElavation and counter < days):
                if (elevation <= 258):
                    release = 3000
                elif (elevation <= 264):
                    release = 4000
                else:
                    release = maxDischarge
                storage -= (release * 3600 * 24) / 43560
                elevation = lookup(storage, stor_els)
                counter += 1
                totalRelease += (release * 3600 * 24 / 43560)
    elif (month >= 9 or month <= 3):
        release = minimumReleaseWinter
        normalElavation = 250.1
        if (elevation <= normalElavation):
            storage -= release * 3600 * 24 * days / 43560
            totalRelease += (release * 3600 * 24 * days / 43560)
        else:
            while (elevation > normalElavation and counter < days):
                if (elevation <= 258):
                    release = 1000
                elif (elevation <= 264):
                    release = 2000
                else:
                    release = maxDischarge
                storage -= release * 3600 * 24 / 43560
                elevation = lookup(storage, stor_els)
                counter += 1
                totalRelease += (release * 3600 * 24 / 43560)
    return totalRelease


def days_in_month(month: int) -> int:
    if month == 2:
        days = 28
    elif month in [4, 6, 9, 11]:
        days = 30
    else:
        days = 31
    return days

def lookup(num, dic):
    x0, y0 = 0, 0
    val = dic.get(num)
    if val is None:
        keys = list(dic) # idk why this works
        x0, x1 = binary_search_iterative(keys, num)
        y0, y1 = dic[x0], dic[x1]
        return (y1 - y0)/(x1 - x0) * (num - x0) + y0
    else:
        return val



def binary_search_iterative(arr, elem):
    start, end = 0, (len(arr) - 1)
    while start <= end:
        mid = (start + end) // 2
        if elem < arr[mid]:
            end = mid - 1
        else:  # elem > arr[mid]
            start = mid + 1
    return (arr[mid-1], arr[mid])





if __name__ == "__main__":
    start()
