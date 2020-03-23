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
                # print('loop')
                try:
                    with proc.request(priority=deadline) as req:
                        # print('req')

                        yield req
                        # print('test lo', crit_level_lo)

                        if deadline_met & crit_level_lo:
                            print('%.2f:\t%s executing,\t deadline %.2f,\t exec left: %.2f'
                                  % (env.now, name, deadline, execution_time_left))
                            yield env.timeout(execution_time_left)
                            print('%.2f:\t%s completed' % (env.now, name))
                            execution_time_left = 0
                # Preemt interrupt
                except simpy.Interrupt as interrupt:
                    # print('interrupt')
                    if interrupt.cause:
                        execution_time_left -= env.now - interrupt.cause.usage_since
                        if execution_time_left:
                            print('%.2f:\t%s preempted, time left %.2f' % (env.now, name, execution_time_left))
                        else:
                            print('%.2f:\t%s completed' % (env.now, name))
                    else:
                        execution_time_left = 0
                        print('%.2f:\t%s interrupted by hi crit' % (env.now, name))

            if env.now > deadline:
                print('%.2f:\t%s DEADLINE MISSED' % (env.now, name))
                deadline_met = False
            else:
                yield env.timeout(deadline - env.now)
        # Interrupt outside loop if waiting for next task
        except simpy.Interrupt as interrupt:
            if interrupt.cause:
                execution_time_left -= env.now - interrupt.cause.usage_since
                if execution_time_left:
                    print('%.2f:\t%s preempted, time left %.2f' % (env.now, name, execution_time_left))
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
        execution_time = random.uniform(0.1, wcet_hi)
        # execution_time = wcet_hi
        arrival_time = env.now
        deadline = arrival_time + period
        # execution_time_left = execution_time

        if execution_time > wcet_lo:
            execution_time_lo = wcet_lo
            execution_time_hi = execution_time - wcet_lo
        else:
            execution_time_lo = execution_time
            execution_time_hi = 0

        print('%.2f:\t%s arrived,\t deadline %.2f,\t execution: %.2f,\t lo crit: %s'
              % (env.now, name, deadline, execution_time, crit_level_lo))

        while execution_time_lo > 0:
            try:
                with proc.request(priority=deadline) as req:

                    yield req
                    if deadline_met:
                        print('%.2f:\t%s executing,\t deadline %.2f,\t lo left: %.2f'
                              % (env.now, name, deadline, execution_time_lo))
                        yield env.timeout(execution_time_lo)
                        execution_time_lo = execution_time_lo - execution_time_lo

                        print('%.2f:\t%s completed LO execution' % (env.now, name))

            except simpy.Interrupt as interrupt:
                execution_time_lo -= env.now - interrupt.cause.usage_since
                if execution_time_lo:
                    print('%.2f:\t%s preempted,\t lo left: %.2f' % (env.now, name, execution_time_lo))
                else:
                    print('%.2f:\t%s completed2' % (env.now, name))

        # HI execution part
        while execution_time_hi > 0:
            try:
                with proc.request(priority=deadline) as req:

                    yield req
                    # print('test hi')

                    if deadline_met:

                        if crit_level_lo:
                            crit_level_lo = False
                            for task in lo_tasks:
                                task.interrupt()
                            # lo_tasks.interrupt()
                            # crit_level_lo = False
                        print('%.2f:\t%s continue,\t deadline %.2f,\t hi left: %.2f,\t HI CRIT LEVEL'
                              % (env.now, name, deadline, execution_time_hi))
                        yield env.timeout(execution_time_hi)
                        execution_time_hi = 0

                        print('%.2f:\t%s completed' % (env.now, name))

            except simpy.Interrupt as interrupt:
                execution_time_hi -= env.now - interrupt.cause.usage_since
                if execution_time_hi:
                    print('%.2f:\t%s preempted,\t hi left %.2f' % (env.now, name, execution_time_hi))
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
lo_start = [1, 0]
lo_periods = [3, 8]
lo_wcets = [1, 2]
lo_tasks = []
for i, (start, period, wcet) in enumerate(zip(lo_start, lo_periods, lo_wcets)):
    task_name = 'Task LO ' + str(i)
    print(task_name, period, wcet)
    lo_tasks.append(env.process(task_lo(env, task_name, processor, start_time=start, wcet=wcet, period=period)))


task3 = env.process(
    task_hi(env, 'Task HI 3', processor, start_time=1., wcet_lo=2., wcet_hi=3., period=5., lo_tasks=lo_tasks))

env.run(until=30)
