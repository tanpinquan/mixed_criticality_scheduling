import TasksetGenerator
import matplotlib.pyplot as plt

task_length = []
for i in range(10000):
    tasks, util = TasksetGenerator.generate_taskset_EDF(min_period=10, max_period=100, min_util=0.02, max_util=0.2)
    task_length.append(len(tasks))

plt.hist(task_length, bins=list(range(5, 30)), density=True, )
plt.ylabel('Probability')
plt.xlabel('Number of tasks')
plt.show()

task_length_edf_vd = []
for i in range(10000):
    lo_tasks, hi_tasks, utils, x = TasksetGenerator.generate_taskset_EDF_VD(min_period=10, max_period=100, min_util=0.02, max_util=0.2)
    task_length_edf_vd.append(len(lo_tasks)+len(hi_tasks))

plt.hist(task_length_edf_vd, bins=list(range(5, 30)), density=True, )
plt.ylabel('Probability')
plt.xlabel('Number of tasks')
plt.show()