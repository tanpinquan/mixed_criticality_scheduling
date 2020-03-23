import random


def generate_taskset_EDF(min_period, max_period, min_util, max_util):
    periods = []
    wcets = []
    starts = []
    total_util = 0
    while True:
        util = random.uniform(min_util, max_util)
        if total_util + util < 1:
            periods.append(random.uniform(min_period, max_period))
            wcets.append(util * periods[-1])
            starts.append(0)
            total_util += util
        else:
            break

    return list(zip(starts, periods, wcets)), total_util


def generate_taskset_EDF_VD(min_period, max_period, min_util, max_util):
    lo_periods = []
    lo_wcets = []
    lo_starts = []
    hi_periods = []
    hi_hi_wcets = []
    hi_lo_wcets = []
    hi_starts = []
    util_lo = 0
    util_hi_hi = 0
    util_hi_lo = 0
    schedule_valid = True
    while schedule_valid:
        # print(util_lo, util_hi_lo, util_hi_hi)
        hi_test = random.uniform(0, 1) > 0.5
        if hi_test:
            task_util_hi = random.uniform(min_util, max_util)
            lo_ratio = random.uniform(0.3, 0.5)
            task_util_lo = lo_ratio * task_util_hi
            schedule_valid = check_EDF_VD_cond(util_lo, util_hi_hi + task_util_hi, util_hi_lo + task_util_lo)
            if schedule_valid:
                hi_periods.append(random.uniform(min_period, max_period))
                hi_hi_wcets.append(task_util_hi * hi_periods[-1])
                hi_lo_wcets.append(lo_ratio * hi_hi_wcets[-1])
                hi_starts.append(0)
                util_hi_lo += task_util_lo
                util_hi_hi += task_util_hi
        else:
            task_util_lo = random.uniform(min_util, max_util)
            schedule_valid = check_EDF_VD_cond(util_lo + task_util_lo, util_hi_hi, util_hi_lo)
            if schedule_valid:
                lo_periods.append(random.uniform(min_period, max_period))
                lo_wcets.append(task_util_lo * lo_periods[-1])
                lo_starts.append(0)
                util_lo += task_util_lo

    x = util_hi_lo / (1 - util_lo)
    lo_tasks = list(zip(lo_starts, lo_periods, lo_wcets))
    hi_tasks = list(zip(hi_starts, hi_periods, hi_lo_wcets, hi_hi_wcets))
    utils = (util_lo, util_hi_lo, util_hi_hi)

    return lo_tasks, hi_tasks, utils, x


def check_EDF_VD_cond(util_lo, util_hi_hi, util_hi_lo):
    cond1 = util_lo + util_hi_lo < 1
    x = util_hi_lo / (1 - util_lo)
    cond2 = x * util_lo + util_hi_hi < 1

    return cond1 & cond2
