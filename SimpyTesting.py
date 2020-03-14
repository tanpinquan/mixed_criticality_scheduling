import numpy as np
import simpy


def resource_user(name, env, resource, wait, prio):
    yield env.timeout(wait)
    try:
        with resource.request(priority=prio) as req:
            print('%s requesting at %s with priority=%s' % (name, env.now, prio))
            yield req
            print('%s got resource at %s' % (name, env.now))
            try:
                print('%s executing at %s' % (name, env.now))
                yield env.timeout(3)
            except simpy.Interrupt as interrupt:
                by = interrupt.cause.by
                usage = env.now - interrupt.cause.usage_since
                print('%s got preempted by %s at %s after %s' %(name, by, env.now, usage))
    except simpy.Interrupt as interrupt:
        print('error')

env = simpy.Environment()
res = simpy.PreemptiveResource(env, capacity=1)
p1 = env.process(resource_user(1, env, res, wait=0, prio=1))
p2 = env.process(resource_user(2, env, res, wait=0, prio=0))
p3 = env.process(resource_user(3, env, res, wait=2, prio=-1))
env.run()
