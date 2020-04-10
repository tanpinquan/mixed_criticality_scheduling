import random
import numpy as np
import matplotlib.pyplot as plt


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


def check_EDF_cond(util_lo, util_hi_hi):
    return util_hi_hi + util_lo < 1


def generate_taskset_EDF_VD(min_period, max_period, min_util, max_util, min_ratio=0.3, max_ratio=0.5):
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
            lo_ratio = random.uniform(min_ratio, max_ratio)
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


def generate_taskset_ER_EDF(min_period, max_period, min_util, max_util, er_step=0.2, num_er=5):
    lo_periods = []
    lo_wcets = []
    lo_starts = []
    hi_periods = []
    hi_wcets = []
    hi_lo_wcets = []
    hi_starts = []
    total_util = 0
    util_lo = 0
    util_hi_hi = 0
    util_hi_lo = 0
    schedule_valid = True
    while schedule_valid:
        # print(util_lo, util_hi_lo, util_hi_hi)
        hi_test = random.uniform(0, 1) > 0.5
        if hi_test:
            task_util_hi = random.uniform(min_util, max_util)
            schedule_valid = (total_util + task_util_hi) < 1
            if schedule_valid:
                hi_periods.append(random.uniform(min_period, max_period))
                hi_wcets.append(task_util_hi * hi_periods[-1])
                hi_starts.append(0)
                total_util += task_util_hi
        else:
            desired_period = random.uniform(min_period, max_period)
            desired_util = random.uniform(min_util, max_util)
            wcet = desired_util * desired_period
            max_period_new = desired_period + er_step * desired_period * num_er
            # max_period = period_mult * desired_period
            task_util_lo = wcet / max_period_new
            # print(desired_period, max_period_new)
            schedule_valid = (total_util + task_util_lo) < 1
            if schedule_valid:
                lo_periods.append(np.linspace(desired_period, max_period_new, num_er + 1))
                lo_wcets.append(wcet)
                lo_starts.append(0)
                total_util += task_util_lo

    lo_tasks = list(zip(lo_starts, lo_periods, lo_wcets))
    hi_tasks = list(zip(hi_starts, hi_periods, hi_wcets))

    return lo_tasks, hi_tasks, total_util


def convert_VD_to_ER(lo_tasks, hi_tasks, utils, er_step, num_er=5):
    if len(hi_tasks):
        hi_tasks = list(zip(*hi_tasks))
        del hi_tasks[2]
        hi_tasks = list(zip(hi_tasks[0], hi_tasks[1], hi_tasks[2]))

    util_hi = utils[2]
    util = util_hi
    if len(lo_tasks):
        lo_tasks = list(zip(*lo_tasks))
        lo_starts = np.array(lo_tasks[0])
        lo_periods = np.array([lo_tasks[1]])
        lo_wcets = np.array(lo_tasks[2])
        util_lo = np.sum(lo_wcets / lo_periods)
        util = util_hi + util_lo
        # print(util_lo, util)

        for i in range(num_er):
            lo_periods = np.concatenate((lo_periods, [lo_periods[-1, :] + er_step * lo_periods[0, :]]), axis=0)
            util_lo = np.sum(lo_wcets / lo_periods[-1, :])
            util = util_hi + util_lo
            # print(util_lo, util)

        # while util > 1:
        #     lo_periods = np.concatenate((lo_periods, [lo_periods[-1, :] + er_step * lo_periods[0, :]]), axis=0)
        #     util_lo = np.sum(lo_wcets / lo_periods[-1, :])
        #     util = util_hi + util_lo
        #     print(util_lo, util)

        lo_tasks = list(zip(lo_starts.T, lo_periods.T, lo_wcets.T))

    return lo_tasks, hi_tasks, util


def generate_taskset_ubound(min_period, max_period, min_util, max_util, min_ratio, max_ratio, ubound):
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
    util_lo_er = 0
    schedule_valid = True
    while schedule_valid:
        # print(util_lo, util_hi_lo, util_hi_hi)
        hi_test = random.uniform(0, 1) > 0.5
        if hi_test:
            task_util_hi = random.uniform(min_util, max_util)
            lo_ratio = random.uniform(min_ratio, max_ratio)
            task_util_lo = lo_ratio * task_util_hi
            hi_periods.append(random.uniform(min_period, max_period))
            hi_hi_wcets.append(task_util_hi * hi_periods[-1])
            hi_lo_wcets.append(lo_ratio * hi_hi_wcets[-1])
            hi_starts.append(0)
            util_hi_lo += task_util_lo
            util_hi_hi += task_util_hi

            schedule_valid = check_ubound_cond(util_lo, util_hi_hi, util_hi_lo, ubound)
            # if schedule_valid:

        else:
            task_util_lo = random.uniform(min_util, max_util)
            lo_periods.append(random.uniform(min_period, max_period))
            lo_wcets.append(task_util_lo * lo_periods[-1])
            lo_starts.append(0)
            util_lo += task_util_lo
            util_lo_er += lo_wcets[-1]/(2*lo_periods[-1])
            schedule_valid = check_ubound_cond(util_lo, util_hi_hi, util_hi_lo, ubound)
            # if schedule_valid:

    lo_tasks = list(zip(lo_starts, lo_periods, lo_wcets))
    hi_tasks = list(zip(hi_starts, hi_periods, hi_lo_wcets, hi_hi_wcets))
    utils = (util_lo, util_hi_lo, util_hi_hi, util_lo_er)

    return lo_tasks, hi_tasks, utils


def check_ubound_cond(util_lo, util_hi_hi, util_hi_lo, ubound):
    u1 = util_hi_hi
    u2 = util_lo + util_hi_lo
    # print(u1, u2)
    return max(u1, u2) < ubound

    # return cond1 & cond2


if __name__ == "__main__":

    ubound_arr = np.linspace(0.3, 1.3)
    # ubound_arr = [1]
    accep_arr_vd = np.zeros([len(ubound_arr)])
    accep_ratio_edf = np.zeros([len(ubound_arr)])

    k_arr = [2, 3, 5]
    accep_ratio_er = np.zeros([len(ubound_arr), len(k_arr)])

    min_ratio = 0.3
    max_ratio = 0.5
    n_tasks = 1000

    util_hi_hi_arr = []
    util_lo_arr = []
    for i, ubound in enumerate(ubound_arr):
        for j in range(n_tasks):
            lo_tasks, hi_tasks, utils = generate_taskset_ubound(min_period=1, max_period=10,
                                                                min_util=0.02, max_util=0.2,
                                                                min_ratio=min_ratio, max_ratio=max_ratio,
                                                                ubound=ubound)
            util_lo = utils[0]
            util_hi_lo = utils[1]
            util_hi_hi = utils[2]
            util_lo_er = utils[3]

            util_hi_hi_arr.append(util_hi_hi)
            util_lo_arr.append(util_lo)

            if check_EDF_VD_cond(util_lo, util_hi_hi, util_hi_lo):
                accep_arr_vd[i] += 1
            if check_EDF_cond(util_lo, util_hi_hi):
                accep_ratio_edf[i] += 1
            for k_ind, k in enumerate(k_arr):
                if check_EDF_cond(util_lo / k, util_hi_hi):
                    accep_ratio_er[i, k_ind] += 1

    accep_arr_vd = accep_arr_vd / n_tasks
    accep_ratio_edf = accep_ratio_edf / n_tasks
    accep_ratio_er = accep_ratio_er / n_tasks

    plt.figure(figsize=(6, 4))
    plt.plot(ubound_arr, accep_ratio_edf, ':')
    plt.plot(ubound_arr, accep_arr_vd, '--k')
    plt.plot(ubound_arr, accep_ratio_er)

    plt.xlabel('Ubound')
    plt.ylabel('Acceptance Ratio')
    plt.legend(['Regular EDF', 'EDF-VD', 'ER-EDF:2', 'ER-EDF:3', 'ER-EDF:5'])
    plt.title(f'r ∈ [{min_ratio},{max_ratio}]')
    # plt.savefig('EDF_VD_acceptance ratio', bbox_inches='tight')
    plt.savefig('ER-EDF_acceptance ratio', bbox_inches='tight')
    plt.show()

    print('LO util:', np.mean(np.array(util_lo_arr)))
    print('HI util:', np.mean(np.array(util_hi_hi_arr)))
