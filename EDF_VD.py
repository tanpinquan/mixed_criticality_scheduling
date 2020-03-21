import numpy as np
import simpy
import random


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

        try:
            while execution_time_left:
                with proc.request(priority=deadline) as req:

                    yield req
                    # print('test lo', crit_level_lo)

                    if deadline_met & crit_level_lo:
                        print('%.2f:\t%s executing,\t deadline %.2f,\t exec left: %.2f'
                              % (env.now, name, deadline, execution_time_left))
                        yield env.timeout(execution_time_left)
                        print('%.2f:\t%s completed' % (env.now, name))
                        execution_time_left = 0

            if env.now > deadline:
                print('%.2f:\t%s DEADLINE MISSED' % (env.now, name))
                deadline_met = False
            else:
                yield env.timeout(deadline - env.now)
        except simpy.Interrupt as interrupt:
            if interrupt.cause:
                execution_time_left -= env.now - interrupt.cause.usage_since
                if execution_time_left:
                    print('%.2f:\t%s preempted, time left %d' % (env.now, name, execution_time_left))
                else:
                    print('%.2f:\t%s completed' % (env.now, name))
            else:
                execution_time_left = 0
                print('%.2f:\t%s interrupted by hi crit' % (env.now, name))


def task_hi(env, name, proc, start_time, wcet_lo, wcet_hi, period, lo_tasks):
    global deadline_met
    global crit_level_lo

    yield env.timeout(start_time)

    while deadline_met:
        # execution_time = random.uniform(0, wcet)
        # execution_time = max(0.1, execution_time)
        execution_time = wcet_hi
        arrival_time = env.now
        deadline = arrival_time + period
        execution_time_left = execution_time

        if (execution_time > wcet_lo):

            execution_time_lo = wcet_lo
            execution_time_hi = execution_time-wcet_lo
        else:
            execution_time_lo = execution_time

        print('%.2f:\t%s arrived,\t\t deadline %.2f,\t execution: %.2f,\t crit: %s'
              % (env.now, name, deadline, execution_time, crit_level_lo))

        while execution_time_left > 0:
            try:
                with proc.request(priority=deadline) as req:

                    yield req
                    # print('test hi')

                    if deadline_met:
                        print('%.2f:\t%s executing,\t deadline %.2f,\t exec left: %.2f'
                              % (env.now, name, deadline, execution_time_lo))
                        yield env.timeout(execution_time_lo)
                        execution_time_left = execution_time-execution_time_hi
                        if execution_time_left:
                            if crit_level_lo:
                                for task in lo_tasks:
                                    task.interrupt()
                                    crit_level_lo = False
                                # lo_tasks.interrupt()
                                # crit_level_lo = False
                            print('%.2f:\t%s continue,\t deadline %.2f,\t exec left: %.2f,\t HI CRIT LEVEL'
                                  % (env.now, name, deadline, execution_time_hi))
                            yield env.timeout(execution_time_hi)
                        print('%.2f:\t%s completed' % (env.now, name))

            except simpy.Interrupt as interrupt:
                execution_time_left -= env.now - interrupt.cause.usage_since
                if execution_time_left:
                    print('%.2f:\t%s preempted, time left %d' % (env.now, name, execution_time_left))
                else:
                    print('%.2f:\t%s completed2' % (env.now, name))

        if env.now > deadline:
            print('%.2f:\t%s DEADLINE MISSED' % (env.now, name))
            deadline_met = False
        else:
            yield env.timeout(deadline - env.now)


deadline_met = True
crit_level_lo = True

env = simpy.Environment()
processor = simpy.PreemptiveResource(env, capacity=1)
task1 = env.process(task_lo(env, 'Task 1', processor, start_time=0., wcet=1., period=4.))
# task2 = env.process(task_lo(env, 'Task 2', processor, start_time=0., wcet=1., period=6.))

lo_tasks = [task1]
task3 = env.process(task_hi(env, 'Task 3', processor, start_time=0., wcet_lo=1., wcet_hi=3., period=4., lo_tasks=lo_tasks))

env.run(until=20)
