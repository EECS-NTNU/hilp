import numpy as np
import pandas as pd
import math
import csv
import random
import sys
from generate_workload_functions import *

###########################################################
# Read in all input arguments
###########################################################
# 1) Num of basic SoC components
n_cpus = int(sys.argv[1])
n_gpu_sms = int(sys.argv[2])
gpu_clocks = ['210','240','300','360','420','480','540','600','660','705','765'] # For GPU DVFS
n_gpus = len(gpu_clocks)
if n_gpu_sms == 0:
    n_gpus = 0
n_dsas = int(sys.argv[3]) * len(gpu_clocks) # DSAs DVFS in the same way as GPUs
n_dsa_cus = int(sys.argv[4])
n_machines = n_cpus + n_gpus + n_dsas
# 2) SoC power characteristics
cpu_tdp = int(sys.argv[5])
gpu_sm_tdp = int(sys.argv[6])
dsa_cu_tdp = int(sys.argv[7])
gpu_tdp = n_gpu_sms * gpu_sm_tdp
dsa_tdp = n_dsa_cus * dsa_cu_tdp
tdp_scaling = 1 # Power resolution in watts (Raise this for better solver perf.)
# 3) Perf. advantage vs GPU for same power and area.
dsa_speedup = float(sys.argv[8])
# 4) Num. times to duplicate each app in the workload (easy way to increase work if desired)
n_dups = int(sys.argv[9])
# 5) Output folder for tmp CSV used for making the DZN
output_folder = str(sys.argv[10])
# 6) Profiled CPU and GPU data
cpu_df_path = str(sys.argv[11])
gpu_df_path = str(sys.argv[12])
cpu_df = pd.read_csv(cpu_df_path)
gpu_df = pd.read_csv(gpu_df_path)
benchmark_names = ['bfs',
 'heartwall',
 'hotspot3D',
 'hotspot',
 'lavaMD',
 'lud',
 'myocyte',
 'nn',
 'pathfinder',
 'sc'] # Used for indexing the profiled data
n_tasks = 3
n_benchmarks = len(benchmark_names)
# 7) Time step res of the model. (Can increase this to improve solver perf.)
timestep_res = float(sys.argv[13])
# 8) Calculated total workload job count after duplication possible of apps
n_jobs = int(sys.argv[14]) * (n_dups+1)
# 9) Amount to scale setup and teardown phases if desired
setup_teardown_scaling = float(sys.argv[15])
# 10) Flag for debugging WLP metric. If 1, CPUs cannot execute kernel phases (default 0).
WLP_TEST = 0


###########################################################
# Scale profiled performance data based on timestep res
###########################################################
cpu_df['SetupTime (s)'] = cpu_df['SetupTime (s)'] / timestep_res
cpu_df['KernelTime (s)'] = cpu_df['KernelTime (s)'] / timestep_res
cpu_df['TeardownTime (s)'] = cpu_df['TeardownTime (s)'] / timestep_res
gpu_df['KernelTime (s)'] = gpu_df['KernelTime (s)'] / timestep_res

# Convert to dictionaries
cpu_df.set_index('Config',inplace=True)
gpu_df.set_index('Config',inplace=True)
cpus_dict = cpu_df.to_dict(orient='index')
gpus_dict = gpu_df.to_dict(orient='index')
performance_dicts = [cpus_dict,gpus_dict]

# Multamdahl conversion, if emulating MA
multiamdahl = False
if multiamdahl:
    performance_dicts = emulate_multiamdahl(performance_dicts, benchmark_names, n_cpus, n_gpus, n_gpu_sms, gpu_clocks, n_dsas, n_dsa_cus, dsa_speedup, n_machines)
    n_machines = 1


###########################################################
# Power array stucture to be filled out later
###########################################################
power_array = []
for c in range(n_cpus):
    power_array.append(int(cpu_tdp/tdp_scaling))
for i in range(n_gpus):
    power_array.append(int(gpu_tdp/tdp_scaling))
for d in range(n_dsas):
    power_array.append(int(dsa_tdp/tdp_scaling))


###########################################################
# Create basic compatibility array, to be adjusted later
###########################################################
compatibility_array = generate_compatibility_array(n_cpus, n_machines, WLP_TEST)


###########################################################
# Create list with per-machine stats
###########################################################
# Output defined here before possible MA adjustments to job count
output_name = str(timestep_res) + 'ts_' + str(setup_teardown_scaling) + 's_' + str(n_jobs) +'jobs_'+ str(n_cpus) + 'cpus' + str(cpu_tdp) +'W_'+ str(n_gpu_sms) + 'sms'+ str(gpu_sm_tdp) +'W_' +str(n_dsas//len(gpu_clocks))+'dsas' + str(n_dsa_cus) + 'cus' + str(dsa_cu_tdp) +'W.csv'
output_path = output_folder + output_name

# Adjusted from proper indexing when emulating MA
if multiamdahl:
    n_jobs = 1

# The list that will be used to write out the CSV
jobs_array = []
header = ['job_id','task_id']
job_attributes = ['time','memory','bandwidth','power','compatibility','cpus','gpus']

# Create all of the column names for the CSV
for i in range(len(job_attributes)):
    for j in range(n_machines):
        header_string = 'machine' + str(j) + '_' + job_attributes[i]
        header.append(header_string)
jobs_array.append(header)

# Start getting all of the per-phase data for each CSV row
for j in range(n_jobs):
    for t in range(n_tasks):
        task_array = []
        # Job and task id
        task_array.append(j)
        task_array.append(t)
        
        # Rest of machine stats
        machine_stats = get_machine_stats(j, t, n_machines, performance_dicts, benchmark_names, n_cpus, n_gpus, n_gpu_sms, gpu_clocks, n_dsas, n_dsa_cus, dsa_speedup, setup_teardown_scaling, power_array, compatibility_array)
        task_array = task_array + machine_stats
        jobs_array.append(task_array)

# Find worst case scenario execution time, useful for setting the max makespan.
time_sum = 0
for i in range(1,len(jobs_array)):
    time_sum += int(jobs_array[i][2])
print('Worst case makespan:',time_sum) 

###########################################################
# Write CSV to disk
###########################################################
with open(output_path, 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
    for i in range(len(jobs_array)):
        csvwriter.writerow(jobs_array[i])