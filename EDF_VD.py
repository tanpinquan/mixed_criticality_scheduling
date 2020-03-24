import numpy as np
import simpy
import random
import TasksetGenerator


def task_lo(env, name, proc, start_time, wcet, period):
    global deadline_met
    yield env.timeout(start_time)

    while deadline_met:
        # execution_time = random.uniform(0, wcet)
        # execution_time = max(0.1, execution_time)
        execution_time = wcet
        arrival_time = env.now
        deadline = arrival_time + period
        execution_time_left = execution_time

        if not crit_level_lo:
            try:
                print('%.2f:\t%s SUPPRESSED,\t deadline %.2f,\t execution: %.2f' % (env.now, name, deadline, execution_time))
                yield env.timeout(deadline - env.now)
            except simpy.Interrupt as interrupt:
                print(interrupt)
                yield env.timeout(deadline - env.now)

        else:
            print('%.2f:\t%s ARRIVED,\t\t deadline %.2f,\t execution: %.2f' % (env.now, name, deadline, execution_time))
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
                        execution_time_left = interrupt_lo(env, interrupt, execution_time_left, deadline, name)

                if env.now > deadline:
                    print('%.2f:\t%s DEADLINE MISSED' % (env.now, name))
                    deadline_met = False
                else:
                    # if crit_level_lo:
                    print(env.now, 'wait after exec', name)
                    yield env.timeout(deadline - env.now)
            # Interrupt outside loop if waiting for next task
            except simpy.Interrupt as interrupt:
                execution_time_left = interrupt_lo(env, interrupt, execution_time_left, deadline, name)
                if not interrupt.cause:
                    print(env.now, 'wait after int', name)
                    yield env.timeout(deadline - env.now)

    print(env.now, 'END ', name)


def interrupt_lo(env, interrupt, execution_time_left, deadline, name):
    if interrupt.cause:
        execution_time_left -= env.now - interrupt.cause.usage_since
        if execution_time_left:
            print('%.2f:\t%s preempted, time left %.2f' % (env.now, name, execution_time_left))
        else:
            print('%.2f:\t%s completed' % (env.now, name))
    else:
        print('%.2f:\t%s interrupted by hi crit' % (env.now, name))
        # yield env.timeout(deadline - env.now)
        execution_time_left = 0

    return execution_time_left


def task_hi(env, name, proc, start_time, wcet_lo, wcet_hi, period, lo_tasks, x):
    global deadline_met
    global crit_level_lo
    global hi_tasks_active

    yield env.timeout(start_time)

    while deadline_met:
        execution_time = random.uniform(0.1, wcet_hi)
        # execution_time = wcet_hi
        arrival_time = env.now
        actual_deadline = arrival_time + period
        virtual_deadline = arrival_time + x * period
        if crit_level_lo:
            active_deadline = virtual_deadline
        else:
            active_deadline = actual_deadline
        # execution_time_left = execution_time

        if execution_time > wcet_lo:
            execution_time_lo = wcet_lo
            execution_time_hi = execution_time - wcet_lo
        else:
            execution_time_lo = execution_time
            execution_time_hi = 0

        print('%.2f:\t%s arrived,\t\t deadline %.2f,\t execution: %.2f,\t vir deadline: %2f,\t lo crit: %s'
              % (env.now, name, actual_deadline, execution_time, virtual_deadline, crit_level_lo))
        hi_tasks_active.append(name)
        # print(hi_tasks_active)
        while execution_time_lo > 0:
            try:
                with proc.request(priority=active_deadline) as req:

                    yield req
                    if deadline_met:
                        print('%.2f:\t%s executing,\t deadline %.2f,\t lo left: %.2f'
                              % (env.now, name, active_deadline, execution_time_lo))
                        yield env.timeout(execution_time_lo)
                        execution_time_lo = execution_time_lo - execution_time_lo

                        if execution_time_hi > 0:
                            print('%.2f:\t%s completed LO execution' % (env.now, name))
                        else:
                            print('%.2f:\t%s completed' % (env.now, name))

            except simpy.Interrupt as interrupt:
                execution_time_lo -= env.now - interrupt.cause.usage_since
                if execution_time_lo:
                    print('%.2f:\t%s preempted,\t lo left: %.2f' % (env.now, name, execution_time_lo))
                else:
                    print('%.2f:\t%s completed2' % (env.now, name))

        # HI execution part
        while execution_time_hi > 0:
            try:
                with proc.request(priority=active_deadline) as req:

                    yield req
                    # print('test hi')

                    if deadline_met:

                        if crit_level_lo:
                            crit_level_lo = False
                            for task in lo_tasks:
                                task.interrupt()
                            # lo_tasks.interrupt()
                            # crit_level_lo = False
                        print('%.2f:\t%s continue,\t\t deadline %.2f,\t hi left: %.2f,\t HI CRIT LEVEL'
                              % (env.now, name, active_deadline, execution_time_hi))
                        yield env.timeout(execution_time_hi)
                        execution_time_hi = 0

                        print('%.2f:\t%s completed' % (env.now, name))

            except simpy.Interrupt as interrupt:
                execution_time_hi -= env.now - interrupt.cause.usage_since
                if execution_time_hi:
                    print('%.2f:\t%s preempted,\t hi left %.2f' % (env.now, name, execution_time_hi))
                else:
                    print('%.2f:\t%s completed2' % (env.now, name))

        if env.now > actual_deadline:
            print('%.2f:\t%s DEADLINE MISSED' % (env.now, name))
            deadline_met = False
        else:
            hi_tasks_active.remove(name)
            # print(hi_tasks_active)
            if len(hi_tasks_active) == 0:
                print(env.now, 'LO CRIT')
                crit_level_lo = True

            yield env.timeout(actual_deadline - env.now)



random.seed(0)
deadline_met = True
crit_level_lo = True

env = simpy.Environment()
processor = simpy.PreemptiveResource(env, capacity=1)

lo_start = [0, 0]
lo_periods = [3, 8]
lo_wcets = [1, 2]
lo_tasks = []
hi_tasks_active = []

for i, (start, period, wcet) in enumerate(zip(lo_start, lo_periods, lo_wcets)):
    task_name = 'Task LO ' + str(i)
    print(task_name, ':', period, wcet)
    lo_tasks.append(env.process(task_lo(env, task_name, processor, start_time=start, wcet=wcet, period=period)))

hi_start = [0, 0]
hi_periods = [5, 6]
hi_wcets_lo = [2, 1]
hi_wcets_hi = [3, 2]
hi_x = 0.8
hi_tasks = []
for i, (start, period, wcet_lo, wcet_hi) in enumerate(zip(hi_start, hi_periods, hi_wcets_lo, hi_wcets_hi)):
    task_name = 'Task HI ' + str(len(lo_tasks) + i)
    print(task_name, ':', period, wcet_lo, wcet_hi)
    hi_tasks.append(env.process(
        task_hi(env, task_name, processor, start_time=start, wcet_lo=wcet_lo, wcet_hi=wcet_hi, period=period,
                lo_tasks=lo_tasks, x=hi_x)))

env.run(until=300)

# lo_tasks, hi_tasks, utils, x = TasksetGenerator.generate_taskset_EDF_VD(min_period=1, max_period=10, min_util=0.1,
#                                                                         max_util=0.2)
#
# lo_tasks_list = []
# hi_tasks_list = []
#
# for i, (start, period, wcet) in enumerate(lo_tasks):
#     task_name = 'Task LO ' + str(i)
#     print(task_name, ':', period, wcet)
#     lo_tasks_list.append(env.process(task_lo(env, task_name, processor, start_time=start, wcet=wcet, period=period)))
#
# for i, (start, period, wcet_lo, wcet_hi) in enumerate(hi_tasks):
#     task_name = 'Task HI ' + str(i)
#     print(task_name, ':', period, wcet_lo, wcet_hi)
#     hi_tasks_list.append(env.process(
#         task_hi(env, task_name, processor, start_time=start, wcet_lo=wcet_lo, wcet_hi=wcet_hi, period=period,
#                 lo_tasks=lo_tasks_list, x=x)))
#
# print('\n')
#
# env.run(until=30)
