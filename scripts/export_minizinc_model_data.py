import numpy as np
import pandas as pd
import sys
import math
from dzn_export_functions import *

###########################################################
# Read in all input arguments
###########################################################
# 1) CSV path of generated workload jobs.
path =  str(sys.argv[1])
df = pd.read_csv(path)
# 2) Output path of exported DZN file
output_path = str(sys.argv[2])
# 3) Total SoC resource limits
total_power = int(sys.argv[3])
total_bandwidth = int(sys.argv[4])
total_memory = int(sys.argv[5]) # Remove this when possible
# 4) Workload schedule makespan limits
MAX_MAKESPAN = sys.argv[6]
MIN_MAKESPAN = sys.argv[7]
# 5) Num CPU cores on the SoC
n_cpus = sys.argv[8]
# 6) Whether or not resource constraints should be enforced (Useful for whatif? and debugging).
RESOURCE_CONSTRAINTS = sys.argv[9]
# 7) Energy consumption of DRAM
EXT_MEM_ENERGY=float(sys.argv[10])*1e-12 # pJ/bit
# 8) GPU profile data csv. Used when needing to turn off SMs.
GPU_CSV=sys.argv[11]
gpu_data_df = pd.read_csv(GPU_CSV)
# 9) Timestep resolution of the simulation
timestep_res=float(sys.argv[12])


###########################################################
# Print some basic system stats
###########################################################
# Get the task count
first_job_id = df['job_id'][0]
n_tasks = 0
for i in range(df.shape[0]):
    if df['job_id'][i] == first_job_id:
        n_tasks += 1
    else:
        break

n_jobs = int(df.shape[0]/n_tasks)
n_machines = int((df.shape[1] - 2) / 7) # The denominator here is the num of machine stats
print('=== DZN Export System Stats ===')
print('n_jobs',n_jobs)
print('num_columns', df.shape[1])
print('n_machines',n_machines)
print('total_power',total_power)
print('total_bandwidth',total_bandwidth)
print('total_memory',total_memory)
print('MAX_MAKESPAN',MAX_MAKESPAN)
print('MIN_MAKESPAN',MIN_MAKESPAN)
print('=== End System Stats ===')



###########################################################
# Add Basic Resrouce Quantities to DZN
###########################################################
dzn_output_data = []
dzn_output_data.append('n_jobs = ' + str(n_jobs) + ';')
dzn_output_data.append('n_tasks = ' + str(n_tasks) + ';')
dzn_output_data.append('n_machines = ' + str(n_machines) + ';')
dzn_output_data.append('total_bandwidth = ' + str(total_bandwidth) + ';')
dzn_output_data.append('total_power = ' + str(total_power) + ';')
dzn_output_data.append('total_memory = ' + str(total_memory) + ';')
dzn_output_data.append('MAX_MAKESPAN = ' + str(MAX_MAKESPAN) + ';')
dzn_output_data.append('MIN_MAKESPAN = ' + str(MIN_MAKESPAN) + ';')
dzn_output_data.append('total_cpus = ' + str(n_cpus) + ';')
dzn_output_data.append('total_gpus = ' + str(1) + ';')


###########################################################
# Format Per-phase Resrouce Usages
###########################################################
# Make adjustments if phases are going over global constraint limits.
scaled_data = scale_input_data(df, n_machines, RESOURCE_CONSTRAINTS, total_power, total_bandwidth, n_cpus, gpu_data_df, timestep_res, EXT_MEM_ENERGY, MAX_MAKESPAN)
# Create all Minizinc arrays containing per-phase resource usages
duration_data = build_dzn_3darray(scaled_data, n_jobs, n_tasks, n_machines, 'machine', '_time')
memory_data = build_dzn_3darray(scaled_data, n_jobs, n_tasks, n_machines, 'machine', '_memory')
bandwidth_data = build_dzn_3darray(scaled_data, n_jobs, n_tasks, n_machines, 'machine', '_bandwidth')
power_data = build_dzn_3darray(scaled_data,n_jobs, n_tasks, n_machines, 'machine', '_power')
compatibility_data = build_dzn_3darray(scaled_data, n_jobs, n_tasks, n_machines, 'machine', '_compatibility')
cpus_data = build_dzn_3darray(scaled_data, n_jobs, n_tasks, n_machines, 'machine', '_cpus')
gpus_data = build_dzn_3darray(scaled_data, n_jobs, n_tasks, n_machines, 'machine', '_gpus')


###########################################################
# Add Per-phase Resrouce Usages to DZN
###########################################################
dzn_output_data.append('task_duration_per_machine = array3d(1..n_jobs,1..n_machines,1..n_tasks,' 
                   + str(duration_data) + ');')
dzn_output_data.append('task_memory_per_machine = array3d(1..n_jobs,1..n_machines,1..n_tasks,' 
                   + str(memory_data) + ');')
dzn_output_data.append('task_bandwidth_per_machine = array3d(1..n_jobs,1..n_machines,1..n_tasks,' 
                   + str(bandwidth_data) + ');')
dzn_output_data.append('task_power_per_machine = array3d(1..n_jobs,1..n_machines,1..n_tasks,' 
                   + str(power_data) + ');')
dzn_output_data.append('task_compatibility_per_machine = array3d(1..n_jobs,1..n_machines,1..n_tasks,' 
                   + str(compatibility_data) + ');')
dzn_output_data.append('cpus_used_per_task = array3d(1..n_jobs,1..n_machines,1..n_tasks,' 
                   + str(cpus_data) + ');')
dzn_output_data.append('gpus_used_per_task = array3d(1..n_jobs,1..n_machines,1..n_tasks,' 
                   + str(gpus_data) + ');')



###########################################################
# Write DZN to disk.
###########################################################
with open(output_path, 'w') as fp:
    for data in dzn_output_data:
        fp.write("%s\n" % data)
    print('Done exporting DZN file.')