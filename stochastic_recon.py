import random
import math

import matplotlib.pyplot as plt

from statistics import mean, stdev
from unittest import TestCase

import numpy as np

from scipy.stats import lognorm, norm, pearsonr
from scipy.interpolate import InterpolatedUnivariateSpline

from historical_data import h_data

def logn(mu, sig):
    return lambda x: 1 / ( math.sqrt(2*math.pi) * sig * x) * math.exp(-1/(2 * sig**2) * (math.log1p(x) - mu)**2)

shift = 0.5

shiftFactor = list(np.arange(1, shift, 600))
probs = list(np.linspace(0, 1, 21))

for i in range(1, 601):
    month = i % 12 # 0 is December
    flows = h_data[month][0]
    precip= h_data[month][1]
    evapor= h_data[month][2]

    precip_corr, __ = pearsonr(flows, precip)
    evapor_corr, __ = pearsonr(flows, evapor)

    if shiftFactor[i-1] < 1:
        precip_shift = 1 - (1 - shiftFactor[i-1]) * precip_corr
        evapor_shift = 1 - (1 - shiftFactor[i-1]) * evapor_corr
    else:
        precip_shift = (shiftFactor[i-1] - 1) * precip_corr + 1
        evapor_shift = (shiftFactor[i-1] - 1) * evapor_corr + 1

    flows_recon = 0
    precip_recon= 0
    evapor_recon= 0


def reconstruct(time, values, shift_factor, probs):
    return

values = sorted(flows)
shift_factor = 0.5
probs = probs

old_ave = mean(values)
std_dev = stdev(values)
new_ave = old_ave * shift_factor
old_dist = norm(old_ave, std_dev)
new_dist = norm(new_ave, std_dev)

ln_vals = [math.log1p(val) for val in values]
ln_old_ave = mean(ln_vals)
ln_std_dev = stdev(ln_vals)
ln_new_ave = ln_old_ave * shift_factor
ln_old_dist = lognorm(ln_old_ave, ln_std_dev)
ln_new_dist = lognorm(ln_new_ave, ln_std_dev)


ln2_vals = values
ln2_old_ave = math.log1p(old_ave / math.sqrt(1 + std_dev/old_ave**2))
ln2_std_dev = math.sqrt(math.log1p(1 + std_dev/old_ave**2))
ln2_new_ave = ln_old_ave * shift_factor
ln2_old_dist = lognorm(ln2_old_ave, scale=math.exp(ln2_old_ave))
ln2_new_dist = lognorm(ln2_new_ave, scale=math.exp(ln2_new_ave))

dist = logn(ln2_old_ave, ln2_std_dev)

y = [0] + values
x = list(np.linspace(0, 1, len(y)))
c_spline = InterpolatedUnivariateSpline(x, y)

ln_y = [0.00001] + ln_vals
ln_x = list(np.linspace(0, 1, len(ln_y)))
ln_c_spline = InterpolatedUnivariateSpline(ln_x, ln_y)

ln2_y = [0] + ln2_vals
ln2_x = list(np.linspace(0, 1, len(ln2_y)))
ln2_c_spline = InterpolatedUnivariateSpline(ln2_x, ln2_y)


new_probs = []
for p in probs:
    temp = new_dist.ppf(p)
    new_probs.append(old_dist.cdf(temp))

ln_new_probs = []
for p in probs:
    temp = ln_new_dist.ppf(p)
    ln_new_probs.append(ln_old_dist.cdf(temp))

ln2_new_probs = []
for p in probs:
    temp = ln2_new_dist.ppf(p)
    ln2_new_probs.append(ln2_old_dist.cdf(temp))


new_vals = list(c_spline(new_probs))
new_vals[0] = 0

ln_new_vals = list(ln_c_spline(ln_new_probs))
# ln_new_vals[0] = 0


ln2_new_vals = list(ln2_c_spline(ln2_new_probs))
ln2_new_vals[0] = 0

new_x = list( np.linspace(0, 1, len(new_vals)) )
n_spline = InterpolatedUnivariateSpline(new_x, new_vals)

ln_new_x = list( np.linspace(0, 1, len(ln_new_vals)) )
ln_n_spline = InterpolatedUnivariateSpline(ln_new_x, ln_new_vals)

ln2_new_x = list( np.linspace(0, 1, len(ln2_new_vals)) )
ln2_n_spline = InterpolatedUnivariateSpline(ln2_new_x, ln2_new_vals)


sample = random.uniform(0, 1)
sample = 0.5
val_for_timepoint = float(n_spline(sample))

ln_val_tp = float( ln_n_spline(sample) )
ln2_val_tp = float( ln2_n_spline(sample) )