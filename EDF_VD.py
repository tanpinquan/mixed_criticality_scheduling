import numpy as np
import simpy
import random


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
        print('%.2f:\t%s arrived, deadline %s, execution: %.2f' % (env.now, name, deadline, execution_time))

        while execution_time_left > 0:
            try:
                with proc.request(priority=deadline) as req:

                    yield req
                    if deadline_met:
                        max_execution = deadline - env.now
                        actual_execution_time = min(max_execution, execution_time_left)
                        print('%.2f:\t%s executing, execution left: %.2f, deadline %.2f, max execution: %.2f'
                              % (env.now, name, execution_time_left, deadline, max_execution))
                        yield env.timeout(actual_execution_time)
                        if max_execution < execution_time_left:
                            print('%.2f:\t%s DEADLINE MISSED' % (env.now, name))
                            deadline_met = False
                        else:
                            print('%.2f:\t%s completed' % (env.now, name))
                        execution_time_left = 0

            except simpy.Interrupt as interrupt:
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


deadline_met = True

env = simpy.Environment()
processor = simpy.PreemptiveResource(env, capacity=1)
env.process(task_lo(env, 'Task 1', processor, start_time=0., wcet=1., period=2.))
env.process(task_lo(env, 'Task 2', processor, start_time=0., wcet=2., period=2.))

env.run(until=20)
