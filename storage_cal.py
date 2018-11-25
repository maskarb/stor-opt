import csv

from ast import literal_eval

from lookup_elev import els_stor
from lookup_stor import stor_els
from lookup_area import els_area

def read_csv(file):
    with open(file, 'r', newline='') as f:
        data_reader = csv.reader(f)
        __ = next(data_reader) # remove headers
        data = [line for line in data_reader]
    return data



def start():
    data_file, demand_file = 'timeseries_0_0.8.csv', 'reservoir-shift_0.8-ts-0.csv'
    storage = 131394.5 # assume full lake to start
    data, demand_all = read_csv(data_file), read_csv(demand_file)
    for i in range(600):
        month = get_month(i)
        inflow, precip, evap = get_ipe(data[i])
        demand = get_withdrawn(get_demand(demand_all[i]), storage)

        days = days_in_month(month)
        outflow = release(storage, month, days)
        inflow *= 1.98347 * days
        precip = get_precip(precip, storage)
        evap = get_evap(evap, storage)
        perc_full = storage / 131394.5 * 100

        print(f'{month:2d}: {inflow:10.2f}, {precip:10.2f}, {evap:10.2f}, {outflow:10.2f}, {demand:10.2f}, {storage:10.2f}, {perc_full:3.1f}')
        storage = storage + inflow + precip - evap - outflow - demand


def get_month(i):
    mo = i + 1
    if mo % 12 == 0:
        month = 12
    else:
        month = mo % 12
    return month

def get_ipe(line):
    data = [literal_eval(val) for val in line[:3]]
    return data

def get_demand(line):
    return literal_eval(line[7])

def get_precip(precip_in, stor):
    return lookup(lookup(stor, stor_els), els_area) * (precip_in / 12)

def get_evap(evap_in, stor):
    return lookup(lookup(stor, stor_els), els_area) * (evap_in / 12)

def get_withdrawn(demand, storage):
    lowestStorage = lookup(236.5, els_stor)
    remainingWater = storage - lowestStorage
    actual = 0
    if (remainingWater >= demand):
        actual = demand
    elif (remainingWater > 0):
        actual = remainingWater
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
        for k, v in dic.items():
            if num < k:
                x1, y1 = k, v
                return (y1 - y0)/(x1 - x0) * (num - x0) + y0
            x0, y0 = k, v
    else:
        return val

if __name__ == "__main__":
    start()