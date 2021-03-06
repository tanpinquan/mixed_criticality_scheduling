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
        # print(amt, 'slack added')

    def push_slack_backward(self):
        queue_length = len(self.slack_queue)
        for queue_ind in range(queue_length - 1, 0, -1):
            deadline_gap = self.slack_queue[queue_ind, 0] - self.slack_queue[queue_ind - 1, 0]
            excess_slack = self.slack_queue[queue_ind, 1] - deadline_gap

            if excess_slack > 0:
                self.slack_queue[queue_ind, 1] -= excess_slack
                self.slack_queue[queue_ind - 1, 1] += excess_slack

    def reclaim_slack(self, deadline, amt):
        slack_totals = np.cumsum(slack.slack_queue[slack.slack_queue[:, 0] <= deadline, 1])
        reclaim_idx_list = np.where(slack_totals >= amt)
        if len(reclaim_idx_list[0]) > 0:
            reclaim_idx = reclaim_idx_list[0][0]

            self.slack_queue = np.delete(self.slack_queue, list(range(reclaim_idx)), axis=0)
            self.slack_queue[0, 1] = slack_totals[reclaim_idx] - amt

            # print(amt, 'slack reclaimed:\n')
            return True
        # print('slack unchanged:\n')
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
        # print('%.2f:\t%s arrived,\t\t deadline %.2f,\t execution: %.2f' % (env.now, name, deadline, execution_time),
        #       ', release pts', release_points)

        while execution_time_left:
            try:
                with proc.request(priority=deadline) as req:

                    yield req

                    if deadline_met:
                        # print('%.2f:\t%s executing,\t deadline %.2f,\t exec left: %.2f'
                        #       % (env.now, name, deadline, execution_time_left))
                        task_start[name].append(env.now)
                        yield env.timeout(execution_time_left)
                        # print('%.2f:\t%s completed' % (env.now, name))
                        task_end[name].append(env.now)
                        task_complete[name].append(env.now)
                        execution_time_left = 0
            except simpy.Interrupt as interrupt:
                if interrupt.cause:
                    execution_time_left -= env.now - interrupt.cause.usage_since
                    task_end[name].append(env.now)
                    if not execution_time_left:
                        # print('%.2f:\t%s completed' % (env.now, name))
                        task_complete[name].append(env.now)

        if env.now > deadline:
            print('%.2f:\t%s DEADLINE MISSED' % (env.now, name))
            deadline_met = False
        else:
            for i, release_point in enumerate(release_points):
                if (release_point > env.now):
                    yield env.timeout(release_point - env.now)
                    task_er_points[name].append(env.now)
                    slack_demand = wcet - period[i] * wcet / period[-1]
                    slack_deadline = env.now + period[-1]
                    # print('%.2f:\t%s ER point' % (env.now, name), "\t slack req ", slack_demand, ', slack deadline',
                    #       slack_deadline)
                    if slack_demand == 0:
                        # print('%.2f:\t%s NORMAL RELEASED' % (env.now, name))
                        task_arrivals[name].append(env.now)
                    if slack.reclaim_slack(slack_deadline, slack_demand):
                        # print('%.2f:\t%s  RELEASED' % (env.now, name))

                        if i < len(release_points) - 1:
                            # print('%.2f:\t%s EARLY RELEASED' % (env.now, name))
                            task_early_release[name].append(env.now)

                        break


def task_hi(env, name, proc, start_time, wcet, period, min_ratio=0.3, max_ratio=0.5, prob_within=0.8):
    wcet_lo = random.uniform(min_ratio, max_ratio) * wcet
    mean = 3 * wcet_lo / 4
    ref_val = norm.ppf(prob_within)
    sigma = mean / (3 * ref_val)

    global deadline_met
    yield env.timeout(start_time)

    while deadline_met:

        execution_time = random.normalvariate(mu=mean, sigma=sigma)
        execution_time = max(0.01, execution_time)
        execution_time = min(execution_time, wcet)

        arrival_time = env.now
        deadline = arrival_time + period
        execution_time_left = execution_time
        # print('%.2f:\t%s arrived,\t\t deadline %.2f,\t execution: %.2f' % (env.now, name, deadline, execution_time))
        task_arrivals[name].append(env.now)

        while execution_time_left:
            try:
                with proc.request(priority=deadline) as req:

                    yield req

                    if deadline_met:
                        # print('%.2f:\t%s executing,\t deadline %.2f,\t exec left: %.2f'
                        #       % (env.now, name, deadline, execution_time_left))
                        task_start[name].append(env.now)
                        yield env.timeout(execution_time_left)
                        # print('%.2f:\t%s completed' % (env.now, name))
                        task_end[name].append(env.now)
                        task_complete[name].append(env.now)
                        execution_time_left = 0
            except simpy.Interrupt as interrupt:
                if interrupt.cause:
                    execution_time_left -= env.now - interrupt.cause.usage_since
                    task_end[name].append(env.now)
                    if not execution_time_left:
                        #     print('%.2f:\t%s preempted, time left %d' % (env.now, name, execution_time_left))
                        # else:
                        # print('%.2f:\t%s completed' % (env.now, name))
                        task_complete[name].append(env.now)

        if env.now > deadline:
            print('%.2f:\t%s DEADLINE MISSED' % (env.now, name))
            deadline_met = False
        else:
            slack.add_slack(deadline, wcet - execution_time)
            yield env.timeout(deadline - env.now)


# random.seed(1)
plot_schd = False
run_dur = 200
num_runs = 100
num_er_arr = [1, 2, 4, 6, 8, 10, 12]
max_period_arr = [3, 5, 7]
edf_vd_ref = 6.78
edf_vd_ref = 5.98
prob_within = 0.9

for max_period_mult in max_period_arr:
    print('Generating for k:', max_period_mult)
    avg_service_periods = []
    total_completions = []
    lo_task_periods = [[] for i in range(len(num_er_arr))]
    service_periods = [[] for i in range(len(num_er_arr))]
    task_completions = [[] for i in range(len(num_er_arr))]
    avg_completions = np.zeros((len(num_er_arr), num_runs))
    for sched in range(num_runs):
        print('Run:', sched, 'of', num_runs)

        lo_tasks_ref, hi_tasks_ER, util_ER = TasksetGenerator.generate_taskset_ER_EDF(min_period=1, max_period=10,
                                                                                      min_util=0.02, max_util=0.2,
                                                                                      er_step=(max_period_mult - 1),
                                                                                      num_er=1)
        for num_er_ind, num_er in enumerate(num_er_arr):
            er_step = (max_period_mult - 1) / num_er

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
            task_er_points = {}

            env = simpy.Environment()
            processor = simpy.PreemptiveResource(env, capacity=1)

            lo_tasks_ER = TasksetGenerator.change_ER_points(lo_tasks_ref, num_er=num_er)

            lo_tasks_list = []

            for i, (start, period, wcet) in enumerate(lo_tasks_ER):
                task_name = 'Task LO ' + str(i)

                lo_task_names.append(task_name)
                task_arrivals[task_name] = []
                task_start[task_name] = []
                task_early_release[task_name] = []
                task_end[task_name] = []
                task_complete[task_name] = []
                task_er_points[task_name] = []

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

                task3 = env.process(
                    task_hi(env, task_name, processor, start_time=start, wcet=wcet, period=period,
                            min_ratio=0.3, max_ratio=0.5, prob_within=prob_within)
                )

            env.run(until=run_dur)

            if plot_schd:
                VisualizeTasks.plot_tasks_ER_EDF(task_arrivals=task_arrivals, task_early_release=task_early_release,
                                                 task_er_points=task_er_points,
                                                 task_start=task_start,
                                                 task_end=task_end,
                                                 task_complete=task_complete,
                                                 lo_task_names=lo_task_names, hi_task_names=hi_tasks_names,
                                                 xlim=30)

            for i, task in enumerate(lo_task_names):
                task_completions[num_er_ind].append(len(task_complete[task]))
                lo_task_completions = len(task_complete[task])
                lo_task_periods[num_er_ind].append(lo_tasks_ER[i][1][0])
                if lo_task_completions:
                    service_periods[num_er_ind].append(run_dur / lo_task_completions)
                else:
                    service_periods[num_er_ind].append(run_dur)

            avg_completions[num_er_ind, sched] = 0
            for task in lo_task_names:
                avg_completions[num_er_ind, sched] += len(task_complete[task]) / len(lo_task_names)

    avg_service_periods = run_dur / np.mean(avg_completions, 1)
    # print(total_completions)

    plt.plot(np.array(num_er_arr), avg_service_periods)

plt.plot([1, 12], [edf_vd_ref, edf_vd_ref], ':k')

plt.xlabel('Number of ER Points')
plt.ylabel('Avg task period of LO-crit task')
plt.legend(['ER-EDF:3', 'ER-EDF:5', 'ER-EDF:7', 'EDF-VD'])
plt.title(f'Avg period with prob exceed LO WCET = {prob_within}')
plt.savefig('ER-EDF service_rate')

plt.show()
