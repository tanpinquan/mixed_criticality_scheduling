import numpy as np
import simpy
import random


class Slack:
    def __init__(self):
        self.slack_queue = np.empty((0, 2))

    def add_slack(self, deadline, amt):
        self.slack_queue = np.append(self.slack_queue, np.array([[deadline, amt]]), axis=0)
        sort_ind = np.argsort(self.slack_queue[:, 0])
        self.slack_queue = self.slack_queue[sort_ind]
        print(self.slack_queue)

        self.push_slack_backward()
        print('\n')

    def push_slack_backward(self):
        queue_length = len(self.slack_queue)
        for queue_ind in range(queue_length - 1, 0, -1):
            deadline_gap = self.slack_queue[queue_ind, 0] - self.slack_queue[queue_ind - 1, 0]
            excess_slack = self.slack_queue[queue_ind, 1] - deadline_gap

            print('excess slack', excess_slack)
            if excess_slack > 0:
                self.slack_queue[queue_ind, 1] -= excess_slack
                self.slack_queue[queue_ind - 1, 1] += excess_slack
                print(self.slack_queue)


def task_lo(env, name, proc, start_time, wcet, period):
    global deadline_met
    yield env.timeout(start_time)

    while deadline_met & crit_level_lo:
        # execution_time = random.uniform(0, wcet)
        # execution_time = max(0.1, execution_time)
        execution_time = wcet
        arrival_time = env.now
        deadline = arrival_time + period
        execution_time_left = execution_time
        print('%.2f:\t%s arrived,\t\t deadline %.2f,\t execution: %.2f' % (env.now, name, deadline, execution_time))

        while execution_time_left:
            try:
                with proc.request(priority=deadline) as req:

                    yield req
                    # print('test lo', crit_level_lo)

                    if deadline_met & crit_level_lo:
                        print('%.2f:\t%s executing,\t deadline %.2f,\t exec left: %.2f'
                              % (env.now, name, deadline, execution_time_left))
                        yield env.timeout(execution_time_left)
                        print('%.2f:\t%s completed' % (env.now, name))
                        execution_time_left = 0
            except simpy.Interrupt as interrupt:
                if interrupt.cause:
                    execution_time_left -= env.now - interrupt.cause.usage_since
                    if execution_time_left:
                        print('%.2f:\t%s preempted, time left %d' % (env.now, name, execution_time_left))
                    else:
                        print('%.2f:\t%s completed' % (env.now, name))

        if env.now > deadline:
            print('%.2f:\t%s DEADLINE MISSED' % (env.now, name))
            deadline_met = False
        else:
            yield env.timeout(deadline - env.now)


slack = Slack()
slack.add_slack(5, 1)
slack.add_slack(15, 5)
slack.add_slack(30, 6)
slack.add_slack(25, 2)
slack.add_slack(10, 6)
slack.add_slack(35, 7)

deadline_met = True
crit_level_lo = True

env = simpy.Environment()
processor = simpy.PreemptiveResource(env, capacity=1)
lo_start = [1, 0]
lo_periods = [3, 5]
lo_wcets = [1, 2]
lo_tasks = []
for i, (start, period, wcet) in enumerate(zip(lo_start, lo_periods, lo_wcets)):
    task_name = 'Task LO ' + str(i)
    print(task_name, period, wcet)
    lo_tasks.append(env.process(task_lo(env, task_name, processor, start_time=start, wcet=wcet, period=period)))

env.run(until=1)
