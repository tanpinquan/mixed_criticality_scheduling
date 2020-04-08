import numpy as np
import simpy
import random
import TasksetGenerator
import VisualizeTasks
import matplotlib.pyplot as plt
import pickle


def task_lo(env, name, proc, start_time, wcet, period):
    global deadline_met
    yield env.timeout(start_time)
    deadline = env.now
    while deadline_met:
        while (deadline - env.now) > 0:
            try:
                # print(name, 'WAITING', deadline-env.now)
                print('%.3f:\t%s WAITING,\t deadline %.2f,\t wait dur: %.2f' % (
                    env.now, name, deadline, deadline - env.now))
                yield env.timeout(deadline - env.now)
            except simpy.Interrupt as interrupt:
                print('%.3f:\t%s INTERRUPTED, going back to wait' % (env.now, name,))

        # execution_time = random.uniform(0, wcet)
        # execution_time = max(0.1, execution_time)
        # execution_time = wcet
        execution_time = random.normalvariate(mu=wcet / 2, sigma=wcet / 2)
        execution_time = max(0.01, execution_time)
        execution_time = min(execution_time, wcet)

        arrival_time = env.now
        deadline = arrival_time + period
        execution_time_left = execution_time

        if not crit_level_lo:
            print('%.3f:\t%s SUPPRESSED,\t deadline %.2f,\t execution: %.2f' % (
                env.now, name, deadline, execution_time))
            task_suppresses[name].append(env.now)

        if crit_level_lo:
            print('%.3f:\t%s ARRIVED,\t\t deadline %.2f,\t execution: %.2f' % (env.now, name, deadline, execution_time))
            task_arrivals[name].append(env.now)
            try:
                while execution_time_left:
                    # print('loop')
                    try:
                        with proc.request(priority=deadline) as req:
                            # print('req')
                            yield req
                            # print('test lo', crit_level_lo)

                            if deadline_met & crit_level_lo:
                                print('%.3f:\t%s executing,\t deadline %.2f,\t exec left: %.2f'
                                      % (env.now, name, deadline, execution_time_left))
                                task_start[name].append(env.now)
                                yield env.timeout(execution_time_left)
                                print('%.3f:\t%s completed' % (env.now, name))
                                task_end[name].append(env.now)
                                task_complete[name].append(env.now)
                                execution_time_left = 0
                    # Preemt interrupt
                    except simpy.Interrupt as interrupt:
                        execution_time_left = interrupt_lo(env, interrupt, execution_time_left, deadline, name)

                        # if (len(task_start[name]) > 0) & (env.now != arrival_time):
                        #     if env.now != task_start[name][-1]:
                        #         print(name, 'add', env.now, task_start[name][-1])
                        #         task_end[name].append(env.now)

                if env.now > deadline:
                    print('%.3f:\t%s DEADLINE MISSED' % (env.now, name))
                    deadline_met = False
                # else:
                #     print(env.now, 'wait after exec', name)
                #     yield env.timeout(deadline - env.now)
            # Interrupt outside loop if waiting for next task
            except simpy.Interrupt as interrupt:
                execution_time_left = interrupt_lo(env, interrupt, execution_time_left, deadline, name)

    print(env.now, 'END ', name)


def interrupt_lo(env, interrupt, execution_time_left, deadline, name):
    task_end[name].append(env.now)
    if interrupt.cause:
        execution_time_left -= env.now - interrupt.cause.usage_since
        if execution_time_left:
            print('%.3f:\t%s preempted, time left %.2f' % (env.now, name, execution_time_left))
        else:
            print('%.3f:\t%s completed' % (env.now, name))
            task_complete[name].append(env.now)

    else:
        print('%.3f:\t%s interrupted by hi crit' % (env.now, name))

        # yield env.timeout(deadline - env.now)
        execution_time_left = 0

    return execution_time_left


def wait_lo(env, duration):
    yield env.timeout(duration)


def task_hi(env, name, proc, start_time, wcet_lo, wcet_hi, period, lo_tasks, x):
    global deadline_met
    global crit_level_lo
    global hi_tasks_active

    yield env.timeout(start_time)
    actual_deadline = env.now

    while deadline_met:
        while (actual_deadline - env.now) > 0:
            try:
                # print(name, 'WAITING', deadline-env.now)
                print('%.3f:\t%s WAITING,\t deadline %.2f,\t wait dur: %.2f' % (
                    env.now, name, actual_deadline, actual_deadline - env.now))
                yield env.timeout(actual_deadline - env.now)
            except simpy.Interrupt as interrupt:
                print('%.3f:\t%s INTERRUPTED, going back to wait' % (env.now, name,))

        # execution_time = random.uniform(0.1, wcet_hi)
        execution_time = random.normalvariate(mu=3 * wcet_lo / 4, sigma=2 * wcet_lo / 2)
        execution_time = max(0.01, execution_time)
        execution_time = min(execution_time, wcet_hi)
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

        print('%.3f:\t%s arrived,\t\t deadline %.2f,\t execution: %.2f,\t vir deadline: %2f,\t lo crit: %s'
              % (env.now, name, actual_deadline, execution_time, virtual_deadline, crit_level_lo))
        hi_tasks_active.append(name)
        task_arrivals[name].append(env.now)

        # print(hi_tasks_active)
        while execution_time_lo > 0:
            try:
                with proc.request(priority=active_deadline) as req:

                    yield req
                    if deadline_met:
                        print('%.3f:\t%s executing,\t deadline %.2f,\t lo left: %.2f'
                              % (env.now, name, active_deadline, execution_time_lo))
                        task_start[name].append(env.now)
                        yield env.timeout(execution_time_lo)
                        execution_time_lo = execution_time_lo - execution_time_lo

                        if execution_time_hi > 0:
                            print('%.3f:\t%s completed LO execution' % (env.now, name))
                        else:
                            print('%.3f:\t%s completed' % (env.now, name))
                            task_end[name].append(env.now)
                            task_complete[name].append(env.now)

            except simpy.Interrupt as interrupt:
                execution_time_lo -= env.now - interrupt.cause.usage_since
                task_end[name].append(env.now)

                if execution_time_lo:
                    print('%.3f:\t%s preempted,\t lo left: %.2f' % (env.now, name, execution_time_lo))
                else:
                    print('%.3f:\t%s completed2' % (env.now, name))
                    task_complete[name].append(env.now)

        # HI execution part
        while execution_time_hi > 0:
            try:
                with proc.request(priority=active_deadline) as req:

                    yield req
                    # print('test hi')

                    if deadline_met:

                        if crit_level_lo:
                            crit_level_lo = False
                            hi_crit.append(env.now)
                            # print('-----------', env.now, 'HI CRIT caused  by', name)
                            print('%.3f:\tHI CRIT by %s-------------------' % (env.now, name))

                            for task in lo_tasks:
                                task.interrupt()
                            # lo_tasks.interrupt()
                            # crit_level_lo = False
                        print('%.3f:\t%s continue,\t\t deadline %.2f,\t hi left: %.2f'
                              % (env.now, name, active_deadline, execution_time_hi))
                        yield env.timeout(execution_time_hi)
                        execution_time_hi = 0

                        print('%.3f:\t%s completed' % (env.now, name))
                        task_end[name].append(env.now)
                        task_complete[name].append(env.now)

            except simpy.Interrupt as interrupt:
                task_end[name].append(env.now)
                execution_time_hi -= env.now - interrupt.cause.usage_since
                if execution_time_hi:
                    print('%.3f:\t%s preempted,\t hi left %.2f' % (env.now, name, execution_time_hi))
                else:
                    print('%.3f:\t%s completed2' % (env.now, name))
                    task_complete[name].append(env.now)

        if env.now > actual_deadline:
            print('%.3f:\t%s DEADLINE MISSED' % (env.now, name))
            deadline_met = False
        else:
            hi_tasks_active.remove(name)
            # print(hi_tasks_active)
            if (len(hi_tasks_active) == 0) & (not crit_level_lo):
                print('%.3f: LO CRIT-----------------------' % env.now)
                # print('-----------', env.now, 'LO CRIT')
                crit_level_lo = True
                lo_crit.append(env.now)

            # yield env.timeout(actual_deadline - env.now)


# random.seed(2)
# random.seed(1)
avg_service_periods = []
lo_task_periods = []
run_dur = 100

for sched in range(1000):
    deadline_met = True
    crit_level_lo = True

    env = simpy.Environment()
    processor = simpy.PreemptiveResource(env, capacity=1)
    task_arrivals = {}
    task_suppresses = {}
    task_start = {}
    task_end = {}
    task_complete = {}
    hi_crit = []
    lo_crit = []
    lo_task_names = []
    hi_tasks_active = []
    hi_tasks_names = []

    lo_tasks, hi_tasks, utils, x = TasksetGenerator.generate_taskset_EDF_VD(min_period=1, max_period=10, min_util=0.02,
                                                                            max_util=0.2, min_ratio=0.3, max_ratio=0.5)

    lo_tasks_list = []
    hi_tasks_list = []

    for i, (start, period, wcet) in enumerate(lo_tasks):
        task_name = 'Task LO ' + str(i)
        lo_task_names.append(task_name)
        task_arrivals[task_name] = []
        task_suppresses[task_name] = []
        task_start[task_name] = []
        task_end[task_name] = []
        task_complete[task_name] = []
        print(task_name, ':', period, wcet)
        lo_tasks_list.append(
            env.process(task_lo(env, task_name, processor, start_time=start, wcet=wcet, period=period)))

    for i, (start, period, wcet_lo, wcet_hi) in enumerate(hi_tasks):
        task_name = 'Task HI ' + str(i)
        hi_tasks_names.append(task_name)
        task_arrivals[task_name] = []
        task_start[task_name] = []
        task_end[task_name] = []
        task_complete[task_name] = []
        print(task_name, ':', period, wcet_lo, wcet_hi)
        hi_tasks_list.append(env.process(
            task_hi(env, task_name, processor, start_time=start, wcet_lo=wcet_lo, wcet_hi=wcet_hi, period=period,
                    lo_tasks=lo_tasks_list, x=x)))

    print('\n')
    env.run(until=run_dur)
    # VisualizeTasks.plot_tasks_EDF_VD(task_arrivals=task_arrivals, task_suppresses=task_suppresses,
    #                                  task_start=task_start,
    #                                  task_end=task_end, task_complete=task_complete, lo_task_names=lo_task_names,
    #                                  hi_task_names=hi_tasks_names,
    #                                  hi_crit=hi_crit, lo_crit=lo_crit, xlim=30)
    lo_task_completions = 0
    for i, task in enumerate(lo_task_names):
        print(task, len(task_complete[task]), task_complete[task])
        lo_task_completions = len(task_complete[task])
        lo_task_periods.append(lo_tasks[i][1])
        if lo_task_completions:
            avg_service_periods.append(run_dur / lo_task_completions)
        else:
            avg_service_periods.append(run_dur)



avg_service_period = np.mean(avg_service_periods)
avg_period = np.mean(lo_task_periods)
print('average serive period', avg_service_period, 'avg task period', avg_period)
