import numpy as np
import simpy
import random
import TasksetGenerator
import VisualizeTasks


class Slack:
    def __init__(self):
        self.slack_queue = np.empty((0, 2))

    def add_slack(self, deadline, amt):
        self.slack_queue = np.append(self.slack_queue, np.array([[deadline, amt]]), axis=0)
        sort_ind = np.argsort(self.slack_queue[:, 0])
        self.slack_queue = self.slack_queue[sort_ind]

        self.push_slack_backward()
        print(amt, 'slack added')

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

            print('slack reclaimed')

            return True
        print('slack unchanged:')

        return False


def task_lo(env, name, proc, start_time, wcet, period):
    global deadline_met
    yield env.timeout(start_time)
    task_arrivals[name].append(env.now)

    while deadline_met:

        execution_time = random.normalvariate(mu=wcet / 2, sigma=wcet / 8)
        execution_time = max(0.01, execution_time)
        execution_time = min(execution_time, wcet)

        arrival_time = env.now
        deadline = arrival_time + period[-1]
        release_points = arrival_time + np.array(period)
        execution_time_left = execution_time
        print('%.2f:\t%s arrived,\t\t deadline %.2f,\t execution: %.2f' % (env.now, name, deadline, execution_time),
              ', release pts', release_points)

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
                    print('%.2f:\t%s ER point' % (env.now, name), "\t slack req ", slack_demand, ', slack deadline',
                          slack_deadline)
                    if slack_demand == 0:
                        print('%.2f:\t%s NORMAL RELEASED' % (env.now, name))
                        task_arrivals[name].append(env.now)
                    if slack.reclaim_slack(slack_deadline, slack_demand):
                        print('%.2f:\t%s EARLY RELEASED' % (env.now, name))
                        if i < len(release_points) - 1:
                            task_early_release[name].append(env.now)

                        break


def task_hi(env, name, proc, start_time, wcet, period):
    global deadline_met
    yield env.timeout(start_time)

    while deadline_met:
        execution_time = random.normalvariate(mu=wcet / 2, sigma=wcet / 8)
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


slack = Slack()
# random.seed(8)
# random.seed(10)
# random.seed(11)

run_dur = 50
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


lo_tasks_VD, hi_tasks_VD, utils_VD, x = TasksetGenerator.generate_taskset_EDF_VD(min_period=1, max_period=10,
                                                                                 min_util=0.02, max_util=0.2)

num_er = 1
max_period = 2
er_step = (max_period - 1) / num_er

lo_tasks_ER, hi_tasks_ER, util_ER = TasksetGenerator.convert_VD_to_ER(lo_tasks=lo_tasks_VD, hi_tasks=hi_tasks_VD,
                                                                      utils=utils_VD,
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

    task_er_points[task_name] = []

    print(task_name, period, wcet)

    lo_tasks_list.append(env.process(task_lo(env, task_name, processor, start_time=start, wcet=wcet, period=period)))

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

    task3 = env.process(task_hi(env, task_name, processor, start_time=start, wcet=wcet, period=period))

env.run(until=run_dur)

VisualizeTasks.plot_tasks_ER_EDF(task_arrivals=task_arrivals, task_early_release=task_early_release, task_er_points=task_er_points,
                                 task_start=task_start,task_end=task_end, task_complete=task_complete,
                                 lo_task_names=lo_task_names, hi_task_names=hi_tasks_names,
                                 xlim=30, title=f'ER-EDF Schedule with {num_er} early release points')


