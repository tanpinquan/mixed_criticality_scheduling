import numpy as np
import simpy
import random
import TasksetGenerator
import VisualizeTasks
from scipy.stats import norm
import matplotlib.pyplot as plt

class Slack:
    def __init__(self):
        self.slack_queue = np.empty((0, 2))

    def add_slack(self, deadline, amt):
        self.slack_queue = np.append(self.slack_queue, np.array([[deadline, amt]]), axis=0)
        sort_ind = np.argsort(self.slack_queue[:, 0])
        self.slack_queue = self.slack_queue[sort_ind]
        # print(self.slack_queue)

        self.push_slack_backward()
        # print('slack added:\n', self.slack_queue)
        print(amt, 'slack added')
        # print('\n')

    def push_slack_backward(self):
        queue_length = len(self.slack_queue)
        for queue_ind in range(queue_length - 1, 0, -1):
            deadline_gap = self.slack_queue[queue_ind, 0] - self.slack_queue[queue_ind - 1, 0]
            excess_slack = self.slack_queue[queue_ind, 1] - deadline_gap

            # print('excess slack', excess_slack)
            if excess_slack > 0:
                self.slack_queue[queue_ind, 1] -= excess_slack
                self.slack_queue[queue_ind - 1, 1] += excess_slack
                # print(self.slack_queue)

    def reclaim_slack(self, deadline, amt):
        slack_totals = np.cumsum(slack.slack_queue[slack.slack_queue[:, 0] <= deadline, 1])
        reclaim_idx_list = np.where(slack_totals >= amt)
        if len(reclaim_idx_list[0]) > 0:
            reclaim_idx = reclaim_idx_list[0][0]
            # print('hello', reclaim_idx_list, reclaim_idx, slack_totals[reclaim_idx],)
            # print(list(range(reclaim_idx)))

            self.slack_queue = np.delete(self.slack_queue, list(range(reclaim_idx)), axis=0)
            self.slack_queue[0, 1] = slack_totals[reclaim_idx] - amt

            # print(amt, 'slack reclaimed:\n', self.slack_queue)
            print(amt, 'slack reclaimed:\n')

            return True

        # print('slack unchanged:\n', self.slack_queue)
        print('slack unchanged:\n')

        return False


def task_lo(env, name, proc, start_time, wcet, period):
    global deadline_met
    yield env.timeout(start_time)
    task_arrivals[name].append(env.now)

    while deadline_met:
        # execution_time = random.uniform(0, wcet)
        # execution_time = max(0.1, execution_time)
        execution_time = random.normalvariate(mu=wcet / 2, sigma=wcet / 8)
        execution_time = max(0.01, execution_time)
        execution_time = min(execution_time, wcet)
        # execution_time = wcet

        arrival_time = env.now
        deadline = arrival_time + period[-1]
        release_points = arrival_time + np.array(period)
        execution_time_left = execution_time
        print('%.2f:\t%s arrived,\t\t deadline %.2f,\t execution: %.2f' % (env.now, name, deadline, execution_time),
              ', release pts', release_points)
        # task_arrivals[name].append(env.now)

        while execution_time_left:
            try:
                with proc.request(priority=deadline) as req:

                    yield req

                    if deadline_met:
                        print('%.2f:\t%s executing,\t deadline %.2f,\t exec left: %.2f'
                              % (env.now, name, deadline, execution_time_left))
                        task_start[name].append(env.now)
                        yield env.timeout(execution_time_left)
                        print('%.2f:\t%s completed' % (env.now, name))
                        task_end[name].append(env.now)
                        task_complete[name].append(env.now)
                        execution_time_left = 0
            except simpy.Interrupt as interrupt:
                if interrupt.cause:
                    execution_time_left -= env.now - interrupt.cause.usage_since
                    task_end[name].append(env.now)
                    if execution_time_left:
                        print('%.2f:\t%s preempted, time left %.2f' % (env.now, name, execution_time_left))
                    else:
                        print('%.2f:\t%s completed' % (env.now, name))
                        task_complete[name].append(env.now)
                        task_complete[name].append(env.now)

        if env.now > deadline:
            print('%.2f:\t%s DEADLINE MISSED' % (env.now, name))
            deadline_met = False
        else:
            # slack.add_slack(deadline, wcet - execution_time)
            for i, release_point in enumerate(release_points):
                if (release_point > env.now):
                    yield env.timeout(release_point - env.now)
                    slack_demand = wcet - period[i] * wcet / period[-1]
                    slack_deadline = env.now + period[-1]
                    print('%.2f:\t%s ER point' % (env.now, name), "\t slack req ", slack_demand, ', slack deadline',
                          slack_deadline)
                    if slack.reclaim_slack(slack_deadline, slack_demand):
                        print('%.2f:\t%s EARLY RELEASED' % (env.now, name))
                        if i < len(release_points) - 1:
                            task_early_release[name].append(env.now)
                        # else:
                        # task_arrivals[name].append(env.now)
                        if i == len(release_points) - 1:
                            task_arrivals[name].append(env.now)
                        break


def task_hi(env, name, proc, start_time, wcet, period, min_ratio=0.3, max_ratio=0.5, prob_within=0.3):
    wcet_lo = random.uniform(min_ratio, max_ratio)*wcet
    mean = 3 * wcet_lo / 4
    ref_val = norm.ppf(prob_within)
    sigma = mean / (3 * ref_val)

    global deadline_met
    yield env.timeout(start_time)

    while deadline_met:
        # execution_time = random.uniform(0.1, wcet)
        # execution_time = random.normalvariate(mu=wcet / 2, sigma=wcet / 8)
        execution_time = random.normalvariate(mu=mean, sigma=sigma)
        execution_time = max(0.01, execution_time)
        execution_time = min(execution_time, wcet)

        arrival_time = env.now
        deadline = arrival_time + period
        execution_time_left = execution_time
        print('%.2f:\t%s arrived,\t\t deadline %.2f,\t execution: %.2f' % (env.now, name, deadline, execution_time))
        task_arrivals[name].append(env.now)

        while execution_time_left:
            try:
                with proc.request(priority=deadline) as req:

                    yield req
                    # print('test lo', crit_level_lo)

                    if deadline_met:
                        print('%.2f:\t%s executing,\t deadline %.2f,\t exec left: %.2f'
                              % (env.now, name, deadline, execution_time_left))
                        task_start[name].append(env.now)
                        yield env.timeout(execution_time_left)
                        print('%.2f:\t%s completed' % (env.now, name))
                        task_end[name].append(env.now)
                        task_complete[name].append(env.now)
                        execution_time_left = 0
            except simpy.Interrupt as interrupt:
                if interrupt.cause:
                    execution_time_left -= env.now - interrupt.cause.usage_since
                    task_end[name].append(env.now)
                    if execution_time_left:
                        print('%.2f:\t%s preempted, time left %d' % (env.now, name, execution_time_left))
                    else:
                        print('%.2f:\t%s completed' % (env.now, name))
                        task_complete[name].append(env.now)

        if env.now > deadline:
            print('%.2f:\t%s DEADLINE MISSED' % (env.now, name))
            deadline_met = False
        else:
            slack.add_slack(deadline, wcet - execution_time)
            yield env.timeout(deadline - env.now)


run_dur = 500

prob_within_arr = [0.6, 0.7, 0.8, 0.9, 0.999999]
num_er_arr = [1, 2, 3]
num_er = 3
max_period_mult = 2

for num_er in num_er_arr:
    avg_service_periods = []

    for prob_within in prob_within_arr:
        lo_task_periods = []

        service_periods = []
        er_step = (max_period_mult-1)/num_er

        for sched in range(5):

            slack = Slack()

            # random.seed(3)
            deadline_met = True

            task_arrivals = {}
            task_start = {}
            task_early_release = {}
            task_end = {}
            task_complete = {}
            lo_task_names = []
            hi_tasks_active = []
            hi_tasks_names = []

            env = simpy.Environment()
            processor = simpy.PreemptiveResource(env, capacity=1)

            lo_tasks_ER, hi_tasks_ER, util_ER = TasksetGenerator.generate_taskset_ER_EDF(min_period=1, max_period=10,
                                                                                         min_util=0.02, max_util=0.2,
                                                                                         er_step=er_step, num_er=num_er)

            lo_tasks_list = []

            for i, (start, period, wcet) in enumerate(lo_tasks_ER):
                task_name = 'Task LO ' + str(i)

                lo_task_names.append(task_name)
                task_arrivals[task_name] = []
                task_start[task_name] = []
                task_early_release[task_name] = []
                task_end[task_name] = []
                task_complete[task_name] = []
                print(task_name, period, wcet)

                lo_tasks_list.append(
                    env.process(task_lo(env, task_name, processor, start_time=start, wcet=wcet, period=period)))

            hi_start = [0, 0]
            hi_periods = [5, 7]
            hi_wcets = [2, 1]

            for i, (start, period, wcet) in enumerate(hi_tasks_ER):
                task_name = 'Task HI ' + str(i)

                hi_tasks_names.append(task_name)
                task_arrivals[task_name] = []
                task_start[task_name] = []
                task_end[task_name] = []
                task_complete[task_name] = []
                print(task_name, period, wcet)

                task3 = env.process(task_hi(env, task_name, processor, start_time=start, wcet=wcet, period=period, min_ratio=0.3, max_ratio=0.5, prob_within=prob_within))

            env.run(until=run_dur)

            # VisualizeTasks.plot_tasks_ER_EDF(task_arrivals=task_arrivals, task_early_release=task_early_release,
            #                                  task_start=task_start,
            #                                  task_end=task_end,
            #                                  task_complete=task_complete,
            #                                  lo_task_names=lo_task_names, hi_task_names=hi_tasks_names, xlim=30)

            for i, task in enumerate(lo_task_names):
                lo_task_completions = len(task_complete[task])
                lo_task_periods.append(lo_tasks_ER[i][1][0])
                if lo_task_completions:
                    service_periods.append(run_dur / lo_task_completions)
                else:
                    service_periods.append(run_dur)

        avg_service_periods.append(np.mean(service_periods))
        avg_period = np.mean(lo_task_periods)
        print('average serive period', avg_service_periods[-1], 'avg task period', avg_period)

    plt.plot(np.array(prob_within_arr), avg_service_periods)

plt.xlabel('Probability of HI-crit task exceeding LO-crit WCET')
plt.ylabel('Avg task period of LO-crit task')
plt.savefig('ER-EDF service_rate')
# plt.legend('ER-EDF:1','ER-EDF:1','ER-EDF:1')
plt.show()
