import TasksetGenerator
import matplotlib.pyplot as plt
import numpy as np
task_length = []
for i in range(10000):
    tasks, util = TasksetGenerator.generate_taskset_EDF(min_period=1, max_period=10, min_util=0.02, max_util=0.2)
    task_length.append(len(tasks))


plt.figure(figsize=(6,3))
plt.hist(task_length, bins=list(range(5, 20)), density=True, )
plt.ylabel('Probability')
plt.xlabel('Number of tasks')
plt.title('Regular EDF')
plt.savefig('Taskset Length EDF', bbox_inches = 'tight')

plt.show()

min_ratio = 0.3
max_ratio = 0.5
task_length_edf_vd = []
for i in range(10000):
    lo_tasks, hi_tasks, utils, x = TasksetGenerator.generate_taskset_EDF_VD(min_period=1, max_period=10,
                                                                            min_util=0.02, max_util=0.2,
                                                                            min_ratio=min_ratio, max_ratio=max_ratio)
    task_length_edf_vd.append(len(lo_tasks)+len(hi_tasks))
plt.figure(figsize=(6,3))
plt.hist(task_length_edf_vd, bins=list(range(5, 20)), density=True, )
plt.ylabel('Probability')
plt.xlabel('Number of tasks')
plt.title(f'EDF-VD: r ∈ [{min_ratio},{max_ratio}]')
plt.savefig('Taskset Length EDF_VD', bbox_inches = 'tight')
plt.show()

print(np.mean(task_length), np.mean(task_length_edf_vd))