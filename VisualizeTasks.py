import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
import numpy as np
from cycler import cycler


def plot_tasks_EDF_VD(task_arrivals, task_suppresses, task_start, task_end, task_complete, lo_task_names, hi_task_names,
                      hi_crit, lo_crit, xlim):
    total_tasks = len(lo_task_names) + len(hi_task_names)
    color = cm.get_cmap('tab10').colors
    plt.rc('axes', prop_cycle=(cycler('color', color)))
    bar_colors = cm.get_cmap('tab20').colors

    base_height = 1

    crit_data = get_crit_list(hi_crit, lo_crit)
    plt.broken_barh(crit_data, (0, (total_tasks + 1) * base_height), facecolors='lightgrey')

    for i, name in enumerate(lo_task_names):

        task_start[name], task_end[name] = clean_end_timing(task_start[name], task_end[name])

        task_duration = list(np.array(task_end[name]) - np.array(task_start[name]))
        plt_data = list(zip(task_start[name], task_duration))
        # c = next(color)
        # print(c)
        plt.broken_barh(plt_data, ((1 * i) * base_height, 0.8 * base_height), facecolors=bar_colors[i * 2 + 1])

        if len(task_arrivals[name]):
            markerline, _, _ = plt.stem(task_arrivals[name],
                                        (i + 0.9) * base_height * np.ones(len(task_arrivals[name])),
                                        bottom=i * base_height,
                                        use_line_collection=True,
                                        linefmt='C' + str(i) + ':',
                                        basefmt='C' + str(i) + '-',
                                        markerfmt='C' + str(i) + 'o')
            # markerline.set_marker(8)
            plt.setp(markerline, markersize=5, marker=8)
        if len(task_suppresses[name]):
            plt.stem(task_suppresses[name], (i + 0.9) * base_height * np.ones(len(task_suppresses[name])),
                     bottom=i * base_height,
                     use_line_collection=True,
                     basefmt='C' + str(i) + ':',
                     linefmt='C' + str(i) + ':',
                     markerfmt='C' + str(i) + 'x')
        if len(task_complete[name]):
            markerline, _, _ = plt.stem(task_complete[name],
                                        (i + 0.9) * base_height * np.ones(len(task_complete[name])),
                                        bottom=i * base_height,
                                        use_line_collection=True,
                                        basefmt='C' + str(i) + '-',
                                        linefmt='C' + str(i) + ':',
                                        markerfmt='C' + str(i) + ',')
            plt.setp(markerline, markersize=5, marker=9)

    for i, name in enumerate(hi_task_names):
        print(name)
        task_start[name], task_end[name] = clean_end_timing(task_start[name], task_end[name])

        task_duration = list(np.array(task_end[name]) - np.array(task_start[name]))
        plt_data = list(zip(task_start[name], task_duration))
        # c = next(color)
        plt.broken_barh(plt_data, ((1 * (i + len(lo_task_names)) + 1) * base_height, 0.8 * base_height),
                        facecolors=bar_colors[(i + len(lo_task_names)) * 2 + 1])

        if len(task_arrivals[name]):
            markerline, _, _ = plt.stem(task_arrivals[name],
                                        (i + len(lo_task_names) + 1.9) * base_height * np.ones(
                                            len(task_arrivals[name])),
                                        bottom=(i + len(lo_task_names) + 1) * base_height,
                                        use_line_collection=True,
                                        linefmt='C' + str(i + len(lo_task_names)) + ':',
                                        basefmt='C' + str(i + len(lo_task_names)) + '-',
                                        markerfmt='C' + str(i + len(lo_task_names)) + 'o')
            plt.setp(markerline, markersize=5, marker=8)

        if len(task_complete[name]):
            markerline, _, _ = plt.stem(task_complete[name],
                                        (i + len(lo_task_names) + 1.9) * base_height * np.ones(
                                            len(task_complete[name])),
                                        bottom=(i + len(lo_task_names) + 1) * base_height,
                                        use_line_collection=True,
                                        linefmt='C' + str(i + len(lo_task_names)) + ':',
                                        basefmt='C' + str(i + len(lo_task_names)) + '-',
                                        markerfmt='C' + str(i + len(lo_task_names)) + 'o')
            plt.setp(markerline, markersize=5, marker=9)

    plt.xlim(-0.5,xlim)
    plt.yticks([])
    plt.ylabel('LO-crit                                   HI-crit           ')
    plt.show()


def plot_tasks_ER_EDF(task_arrivals, task_early_release, task_start, task_end, task_complete, lo_task_names, hi_task_names):
    total_tasks = len(lo_task_names) + len(hi_task_names)
    color = cm.get_cmap('tab10').colors
    plt.rc('axes', prop_cycle=(cycler('color', color)))
    bar_colors = cm.get_cmap('tab20').colors

    base_height = 1

    for i, name in enumerate(lo_task_names):

        task_start[name], task_end[name] = clean_end_timing(task_start[name], task_end[name])

        task_duration = list(np.array(task_end[name]) - np.array(task_start[name]))
        plt_data = list(zip(task_start[name], task_duration))
        # c = next(color)
        # print(c)
        plt.broken_barh(plt_data, ((1 * i) * base_height, 0.8 * base_height), facecolors=bar_colors[i*2+1])

        if len(task_arrivals[name]):
            markerline, _, _ = plt.stem(task_arrivals[name],
                                        (i + 0.9) * base_height * np.ones(len(task_arrivals[name])),
                                        bottom=i * base_height,
                                        use_line_collection=True,
                                        linefmt='C' + str(i) + ':',
                                        basefmt='C' + str(i) + '-',
                                        markerfmt='C' + str(i) + 'o')
            # markerline.set_marker(8)
            plt.setp(markerline, markersize=5, marker=8)
        if len(task_early_release[name]):
            markerline, _, _ = plt.stem(task_early_release[name], (i + 0.9) * base_height * np.ones(len(task_early_release[name])),
                     bottom=i * base_height,
                     use_line_collection=True,
                     linefmt='C' + str(i) + ':',
                     basefmt='C' + str(i) + '-',
                     markerfmt='C' + str(i) + 'd')
            plt.setp(markerline, markersize=5, marker='s')

        if len(task_complete[name]):
            markerline, _, _ = plt.stem(task_complete[name],
                                        (i + 0.9) * base_height * np.ones(len(task_complete[name])),
                                        bottom=i * base_height,
                                        use_line_collection=True,
                                        basefmt='C' + str(i) + '-',
                                        linefmt='C' + str(i) + ':',
                                        markerfmt='C' + str(i) + ',')
            plt.setp(markerline, markersize=5, marker=9)

    for i, name in enumerate(hi_task_names):
        print(name)
        task_start[name], task_end[name] = clean_end_timing(task_start[name], task_end[name])

        task_duration = list(np.array(task_end[name]) - np.array(task_start[name]))
        plt_data = list(zip(task_start[name], task_duration))
        # c = next(color)
        plt.broken_barh(plt_data, ((1 * (i + len(lo_task_names)) + 1) * base_height, 0.8 * base_height),
                        facecolors=bar_colors[(i + len(lo_task_names))*2+1])

        if len(task_arrivals[name]):
            markerline, _, _ = plt.stem(task_arrivals[name],
                                        (i + len(lo_task_names) + 1.9) * base_height * np.ones(
                                            len(task_arrivals[name])),
                                        bottom=(i + len(lo_task_names) + 1) * base_height,
                                        use_line_collection=True,
                                        linefmt='C' + str(i + len(lo_task_names)) + ':',
                                        basefmt='C' + str(i + len(lo_task_names)) + '-',
                                        markerfmt='C' + str(i + len(lo_task_names)) + 'o')
            plt.setp(markerline, markersize=5, marker=8)
            markerline, _, _ = plt.stem(task_complete[name],
                                        (i + len(lo_task_names) + 1.9) * base_height * np.ones(
                                            len(task_complete[name])),
                                        bottom=(i + len(lo_task_names) + 1) * base_height,
                                        use_line_collection=True,
                                        linefmt='C' + str(i + len(lo_task_names)) + ':',
                                        basefmt='C' + str(i + len(lo_task_names)) + '-',
                                        markerfmt='C' + str(i + len(lo_task_names)) + 'o')
            plt.setp(markerline, markersize=5, marker=9)

    plt.show()


def clean_end_timing(task_start, task_end):
    task_start = np.array(task_start)
    task_end = np.array(task_end)
    task_end_new = []

    for test_idx, time in enumerate(task_end):
        start_vals = task_start[task_start < time]
        end_vals = task_end[task_end < time]
        # print(start_vals)
        # print(end_vals)
        if len(start_vals):
            if len(end_vals) == 0:
                task_end_new.append(time)
            elif end_vals[-1] < start_vals[-1]:
                task_end_new.append(time)
    task_end_new = np.unique(task_end_new)
    if len(task_end_new) < len(task_start):
        task_start = task_start[:-1]
        # task_end_new = np.append(task_end_new, task_start[-1] + 1)
    return task_start, np.unique(task_end_new)


def get_crit_list(hi_crit, lo_crit):
    if len(lo_crit) < len(hi_crit):
        lo_crit.append(hi_crit[-1] + 1)

    crit_duration = list(np.array(lo_crit) - np.array(hi_crit))

    return list(zip(hi_crit, crit_duration))


start_test = [8, 11, 13, 40]
end_test = [3, 9, 12, 13.5, 18, 42]

# task_start = np.array(start_test)
# task_end = np.array(end_test)
# task_end_new = []
#
# for test_idx, time in enumerate(task_end):
#     start_vals = task_start[task_start < time]
#     end_vals = task_end[task_end < time]
#     print(start_vals)
#     print(end_vals)
#     if len(start_vals):
#         if len(end_vals) == 0:
#             task_end_new.append(time)
#         elif end_vals[-1] < start_vals[-1]:
#             task_end_new.append(time)
#
#
#     print('\n')
# # end_test2 = clean_end_timing(start_test, end_test)
