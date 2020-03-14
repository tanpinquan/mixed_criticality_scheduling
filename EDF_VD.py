import numpy as np
import simpy


def task(env, name, proc, start_time, execution_time, period):
    yield env.timeout(start_time)
    while True:
        arrival_time = env.now
        deadline = arrival_time + period
        execution_time_left = execution_time
        print('%s:\t%s arrived, deadline %s' % (env.now, name, deadline))

        while execution_time_left:
            with proc.request(priority=deadline) as req:
                yield req
                try:
                    start = env.now
                    print('%s:\t%s executing' % (env.now, name))
                    yield env.timeout(execution_time_left)
                    execution_time_left = 0
                    print('%s:\t%s completed' % (env.now, name))
                except simpy.Interrupt:
                    print('%s:\t%s preempted' % (env.now, name))
                    execution_time_left -= env.now - start

        if env.now > deadline:
            print('%s:\tDeadline missed' % env.now)
        else:
            yield env.timeout(deadline - env.now)


env = simpy.Environment()
processor = simpy.PreemptiveResource(env, capacity=1)
env.process(task(env, 'Task 1', processor, 0, 1, 2))
env.process(task(env, 'Task 2', processor, 0, 1, 10))

env.run(until=20)
