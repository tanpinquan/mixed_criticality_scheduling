# Mixed Criticality Scheduling: EDF-VD and ER-EDF 

Two mixed-criticality algortihms are implemented
- EDF-VD
- ER-EDF

The packages required to run the code are:
- python 3.7
- simpy 3.0.11		https://pypi.org/project/simpy/
- numpy 1.18.1		https://numpy.org/
- scipy 1.4.1		https://www.scipy.org/
- matplotlib 3.1.3	https://matplotlib.org/
- cycler 0.10.0		https://pypi.org/project/Cycler/

The files are structed in this way:

EDF-VD.py - This generates a random EDF-VD taskset and schedule according to the parameters in the report. Run to generate a random taskset and plot its schedule

EDF-VD_service_rate.py - This measures the service rate for EDF-VD. Run to measure and plot service rate

ER-EDF.py - This generates a random ER-EDF taskset and schedule according to the parameters in the report. Run to generate a random taskset and plot its schedule

ER-EDF_service_rate.py - This measures the service rate for ER-EDF. Run to measure and plot service rate

TasksetCompare.py - This generates the distribution of taskset lengths for regular EDF, EDF-VD, and ER-EDF

TasksetGenerator.py - This contains functions to generate EDF-VD and ER-EDF tasksets. Not used directly

VisualizeTasks.py - This contains functions to plot out generated schedules. Not used directly
