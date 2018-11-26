import csv
from ast import literal_eval

from tabulate import tabulate

# import gurobipy as g

from lookup_area import els_area
from lookup_drought_stage import drought_stages as ds
from lookup_drought_stage import mo_data as md
from lookup_elev import els_stor
from lookup_stor import stor_els

ACRE_FT_TO_GAL = 325850.943
ACRE_FT_TO_CF = 435560

# m = g.Model() # pylint: disable=E1101

# rel = m.addVar(name='release')


def read_csv(file):
    with open(file, 'r', newline='') as f_in:
        data_reader = csv.reader(f_in)
        __ = next(data_reader) # remove headers
        data = [line for line in data_reader]
    return data

def write_csv(file, data, headers):
    with open(file, 'w', newline='') as f_out:
        data_writer = csv.writer(f_out, delimiter=',')
        data_writer.writerow(headers)
        data_writer.writerows(data)
    print(file, 'write complete.\n')


def start():
    table_list = []
    drought_stages = False
    ts_file = 'timeseries_0_0.2.csv'
    rs_file = 'reservoir-shift_0.2-ts-0.csv'
    csv_file = 'rs-0.2-ts-0-droughts-f.csv'
    storage = lookup(251.5, els_stor) # assume full lake to start (el. 251.5 ft, MSL)
    ipe_data, model_output = read_csv(ts_file), read_csv(rs_file)
    for i in range(600):
        month = get_month(i)
        days = days_in_month(month)
        if month in [4, 5, 6, 7, 8]: # summer
            stor_comp = lookup(251.5, els_stor)
        else:
            stor_comp = lookup(250.1, els_stor)

        storage0 = storage # previous storage
        if drought_stages:
            demand_reduction = get_drought_restriction(month, storage, storage0, stor_comp)
        else:
            demand_reduction = 1.00

        inflow, precip, evap = get_ipe(ipe_data[i])
        raw_demand, population = get_dp(model_output[i])
        demand = get_withdrawn(raw_demand, storage) * demand_reduction
        deficit = 100 - (demand / raw_demand * 100)

        outflow = release(storage, month, days)
        # outflow = simple_release(storage, month, days)
        inflow *= days * 3600*24 / ACRE_FT_TO_CF
        precip = get_vol_delta(precip, storage)
        evap = get_vol_delta(evap, storage)


        storage = storage + inflow + precip - evap - outflow - demand
        perc_full = storage / stor_comp

        table_list.append([month, inflow, precip, evap, outflow, demand,
                           storage, perc_full, demand_reduction, deficit])

    headers = ['mo', 'inflow', 'precip', 'evap', 'outlow', 'demand',
               'storage', '% full', '% redu', 'deficit']
    print(tabulate(table_list, headers=headers, floatfmt=".2f"))
    write_csv(csv_file, table_list, headers)

def get_drought_restriction(month1, level0, level1, level_comp):
    level0 /= level_comp
    level1 /= level_comp
    month0 = get_prev_month(month1)
    if check_drought(month0, level0) is not None:
        drought = check_rescission(month1, level1)
    else:
        drought = check_drought(month1, level1)
    return ds[drought]

def get_prev_month(month):
    if month == 1:
        month0 = 12
    else:
        month0 = month - 1
    return month0


def check_drought(month, level):
    return check_percentage(month, level, 0)

def check_rescission(month, level):
    # conservative check. if level == rescission, stays in drought stage
    return check_percentage(month, level, 1)

def check_percentage(month, level, index):
    stages = md[month][index]
    for i, stage in enumerate(stages):
        if level > stage:
            return i
    return 3


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
    lowest_storage = lookup(236.5, els_stor) # top of sediment storage (el. 236.5 ft, MSL)
    remaining_water = storage - lowest_storage
    if remaining_water >= demand:
        actual = demand
    elif remaining_water > 0:
        actual = remaining_water
    else:
        actual = 0
    return actual

def release(storage, month: int, days: int):
    elevation = lookup(storage, stor_els)
    norm_el = 0
    release_ = 0
    max_discharge = 8000 # (cfs) approximate at elevation 250 m.s.l.
    # freeOverflowing = lookup(elevation, els_stor) - lookup(268, els_stor)

    min_release_summer = 100
    min_release_winter = 60

    counter = 0
    total_release = 0
    if (4 <= month <= 8):
        release_ = min_release_summer
        norm_el = 251.5
        if elevation <= norm_el:
            storage -= release_ * 3600 * 24 * days / ACRE_FT_TO_CF
            total_release = release_ * 3600 * 24 * days / ACRE_FT_TO_CF
        else:
            while (elevation > norm_el and counter < days):
                if elevation <= 258:
                    release_ = 3000
                elif elevation <= 264:
                    release_ = 4000
                else:
                    release_ = max_discharge
                storage -= (release_ * 3600 * 24) / ACRE_FT_TO_CF
                elevation = lookup(storage, stor_els)
                counter += 1
                total_release += (release_ * 3600 * 24 / ACRE_FT_TO_CF)
    elif (month >= 9 or month <= 3):
        release_ = min_release_winter
        norm_el = 250.1
        if elevation <= norm_el:
            storage -= release_ * 3600 * 24 * days / ACRE_FT_TO_CF
            total_release += (release_ * 3600 * 24 * days / ACRE_FT_TO_CF)
        else:
            while (elevation > norm_el and counter < days):
                if elevation <= 258:
                    release_ = 1000
                elif elevation <= 264:
                    release_ = 2000
                else:
                    release_ = max_discharge
                storage -= release_ * 3600 * 24 / ACRE_FT_TO_CF
                elevation = lookup(storage, stor_els)
                counter += 1
                total_release += (release_ * 3600 * 24 / ACRE_FT_TO_CF)
    return total_release



def simple_release(storage, month: int, days: int):
    max_discharge = 6000 # (cfs) approximate at elevation 250 m.s.l.
    # freeOverflowing = lookup(elevation, els_stor) - lookup(268, els_stor)

    min_release_summer = 100
    min_release_winter = 60

    if month in [4, 5, 6, 7, 8]: # summer
        norm_el = 251.5
        total_release = release_that_water(norm_el, days, min_release_summer, max_discharge, storage)
    else: # winter
        norm_el = 250.1
        total_release = release_that_water(norm_el, days, min_release_winter, max_discharge, storage)
    return total_release

def release_that_water(norm_el, days, min_, max_, storage):
    counter, total_release = 0, 0
    elevation = lookup(storage, stor_els)
    if elevation <= norm_el:
        total_release = min_ * 3600 * 24 * days / ACRE_FT_TO_CF
    else:
        while elevation > norm_el or counter < days:
            if elevation > norm_el:
                release = max_
            else:
                release = min_
            storage -= (release * 3600 * 24) / ACRE_FT_TO_CF
            elevation = lookup(storage, stor_els)
            counter += 1
            total_release += (release * 3600 * 24 / ACRE_FT_TO_CF)
    return total_release

def days_in_month(month: int) -> int:
    if month == 2:
        days = 28
    elif month in [4, 6, 9, 11]:
        days = 30
    else:
        days = 31
    return days


def lookup(num, dic):
    x_0, y_0 = 0, 0
    val = dic.get(num)
    if val is None:
        keys = list(dic)
        x_0, x_1 = binary_search_iterative(keys, num)
        y_0, y_1 = dic[x_0], dic[x_1]
        val = (y_1 - y_0)/(x_1 - x_0) * (num - x_0) + y_0
    return val


def binary_search_iterative(arr, elem):
    start, end = 0, (len(arr) - 1)
    while start <= end:
        mid = (start + end) // 2
        if elem < arr[mid]:
            end = mid - 1
        else:  # elem > arr[mid]
            start = mid + 1
    if arr[mid] < elem:
        mid += 1
    return (arr[mid-1], arr[mid])





if __name__ == "__main__":
    start()
