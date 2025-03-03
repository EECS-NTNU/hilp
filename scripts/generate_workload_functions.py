import numpy as np
import pandas as pd
import math
import csv
import random
import sys

# Sort benchmarks based on longest executing kernel according to the CPU. 
# When assigning DSAs they are in order of most expensive kernel first.
def get_dsa_compatibility(machine_id, performance_dicts, benchmark_names, n_cpus, n_gpus, gpu_clocks):
    
    # Get a ranked array of longest exe time cpu kernels.
    single_core_items = []
    for i in range(len(benchmark_names)):
        cpu_dict_key = benchmark_names[i] + '_' + str(n_cpus) + 'cores'
        single_core_items.append((cpu_dict_key,performance_dicts[0][cpu_dict_key]))

    sorted_items = sorted(single_core_items, key=lambda x: x[1]['KernelTime (s)'],reverse=True)
    ranked_keys = []
    
    for i in range(len(benchmark_names)):
       ranked_keys.append(sorted_items[i][0])

    names = []
    for i in range(len(benchmark_names)):
       names.append(ranked_keys[i].split('_')[0])

    positions = []
    for i in range(len(benchmark_names)):
       positions.append(benchmark_names.index(names[i]))

    dsa_comp_arr = []
    dsa_comp_arr = np.zeros(len(benchmark_names),dtype=int)
    dsa_type_id = (machine_id - n_cpus - n_gpus) // len(gpu_clocks)
    dsa_comp_arr[positions[dsa_type_id]] = 1
    
    return dsa_comp_arr


# Generate compatibility numbers for non-DSA devices
def generate_compatibility_array(n_cpus, n_machines, WLP_TEST):
    compatibility_array = []
    
    # Task ID 0
    tmp = []
    for i in range(n_machines):
        if i < n_cpus:
            tmp.append(1)
        else:
            tmp.append(0)
    compatibility_array.append(tmp)

    # Task ID 1
    tmp = []
    for i in range(n_machines):
        if i == 0:
            # Don't allow CPUs to execute kernels for WLP Tests.
            if WLP_TEST:
                tmp.append(0)
            else:
                tmp.append(1)
        elif i < n_cpus:
            tmp.append(0)
        else:
            tmp.append(1)
        #tmp.append(1)
    compatibility_array.append(tmp)

    # Task ID 2
    tmp = []
    for i in range(n_machines):
        if i < n_cpus:
            tmp.append(1)
        else:
            tmp.append(0)
    compatibility_array.append(tmp)
    
    return compatibility_array


def get_machine_time(job_id, task_id, machine_id, performance_dfs, benchmark_names, n_cpus, n_gpus, n_gpu_sms, gpu_clocks, n_dsas, n_dsa_cus, dsa_speedup,setup_teardown_scaling):

    benchmark_name = benchmark_names[job_id%10]
    cpu_dict_key = benchmark_name + '_' + str(n_cpus) + 'cores'
    
    gpu_dict_key = 'default-gpu_dict_key'
    if machine_id >= n_cpus and  machine_id < n_cpus + n_gpus:
        gpu_dict_key = benchmark_name + str(gpu_clocks[machine_id-n_cpus]) + 'clk_' + str(n_gpu_sms) + 'sms'
    
    dsa_dict_key = 'default-dsa_dict_key'
    dsa_type_id = (machine_id - n_cpus - n_gpus) // len(gpu_clocks)
    
    if machine_id >= n_cpus + n_gpus:
        dsa_dict_key = benchmark_name + str(gpu_clocks[machine_id-n_cpus-n_gpus-dsa_type_id*len(gpu_clocks)]) + 'clk_' + str(int(n_dsa_cus*dsa_speedup)) + 'sms'
    
    # Default numbers
    time = 1
    bandwidth = 1
    power = 1
    
    # Setup
    if task_id == 0:
        if machine_id < n_cpus:
            time = performance_dfs[0][cpu_dict_key]['SetupTime (s)'] * setup_teardown_scaling
            bandwidth = performance_dfs[0][cpu_dict_key]['SetupBandwidth (GB/s)']
    
    # Kernel
    elif task_id == 1:
        
        # CPU
        if machine_id == 0:
            time = performance_dfs[0][cpu_dict_key]['KernelTime (s)']
            bandwidth = performance_dfs[0][cpu_dict_key]['KernelBandwidth (GB/s)']
        elif machine_id < n_cpus: # If executing kernel on CPUs, assign to core 0
            time = 1
            bandwidth = 1
        
        # GPU
        elif machine_id < n_cpus + n_gpus:
            time = performance_dfs[1][gpu_dict_key]['KernelTime (s)']
            bandwidth = performance_dfs[1][gpu_dict_key]['Bandwidth (GB/s)']
            power = performance_dfs[1][gpu_dict_key]['Power Usage (W)']
            
        # DSA
        elif machine_id < n_cpus + n_gpus + n_dsas:
            #print('Getting DSA time')
            time = performance_dfs[1][dsa_dict_key]['KernelTime (s)']
            bandwidth = performance_dfs[1][dsa_dict_key]['Bandwidth (GB/s)']
            power = performance_dfs[1][dsa_dict_key]['Power Usage (W)']
    
    # Teardown
    elif task_id == 2:
        if machine_id < n_cpus:
            time = performance_dfs[0][cpu_dict_key]['TeardownTime (s)'] * setup_teardown_scaling
            bandwidth = performance_dfs[0][cpu_dict_key]['TeardownBandwidth (GB/s)']
    else:
        print("Error! TASK ID Incorrect.")
        return 0
    
    # Catch NAN errors
    if math.isnan(time):
        print('NAN time found:',job_id, task_id, machine_id)
    
    # Round up to nearest int for ILP model
    time = math.ceil(time)
    bandwidth = math.ceil(bandwidth)
    power = math.ceil(power)

    return time, bandwidth, power


def get_machine_stats(job_id, task_id, n_machines, performance_dicts, benchmark_names, n_cpus, n_gpus, n_gpu_sms, gpu_clocks, n_dsas, n_dsa_cus, dsa_speedup, setup_teardown_scaling, power_array, compatibility_array):
    
    # Default values
    memory = 1
    power = 1
    stats_array = []
    
    # Time
    for m in range(n_machines):
        #time, bandwidth, power = get_machine_time(job_id, task_id, m, performance_dicts)
        time, bandwidth, power = get_machine_time(job_id, task_id, m, performance_dicts, benchmark_names, n_cpus, n_gpus, n_gpu_sms, gpu_clocks, n_dsas, n_dsa_cus, dsa_speedup,setup_teardown_scaling)

        stats_array.append(time)
    # Memory 
    for m in range(n_machines):
        stats_array.append(memory)
    # Bandwidth
    for m in range(n_machines):
        #time, bandwidth, power = get_machine_time(job_id, task_id, m, performance_dicts)
        time, bandwidth, power = get_machine_time(job_id, task_id, m, performance_dicts, benchmark_names, n_cpus, n_gpus, n_gpu_sms, gpu_clocks, n_dsas, n_dsa_cus, dsa_speedup,setup_teardown_scaling)
        stats_array.append(bandwidth)
    # Power
    for m in range(n_machines):
        #time, bandwidth, power = get_machine_time(job_id, task_id, m, performance_dicts)
        time, bandwidth, power = get_machine_time(job_id, task_id, m, performance_dicts, benchmark_names, n_cpus, n_gpus, n_gpu_sms, gpu_clocks, n_dsas, n_dsa_cus, dsa_speedup,setup_teardown_scaling)
        # In the case of the CPU running the kernel it uses all cores, so the power needs to go up accordingly.
        if task_id == 1 and m < n_cpus:
            stats_array.append(power_array[m]*n_cpus)
        elif task_id == 1 and m >= n_cpus: # Kernel on accel
            stats_array.append(power)
        else: # Setup and teardown on CPU
            stats_array.append(power_array[m])
    # Compatibility
    for m in range(n_machines):
        if m >= n_cpus + n_gpus:
            dsa_comp_arr = get_dsa_compatibility(m, performance_dicts, benchmark_names, n_cpus, n_gpus, gpu_clocks)
            if task_id == 1:
                stats_array.append(dsa_comp_arr[job_id])
            else:
                stats_array.append(0)
        else:
            stats_array.append(compatibility_array[task_id][m])

    # N CPUs used
    for m in range(n_machines):

        if m < n_cpus:
            if task_id == 1:
                stats_array.append(n_cpus)
            else:
                stats_array.append(1)
        else:
            stats_array.append(0)

    # N GPUs used
    for m in range(n_machines):

        if m >= n_cpus and m < n_gpus+n_cpus:
            if task_id == 1:
                stats_array.append(1)
            else:
                stats_array.append(0)
        else:
            stats_array.append(0)

    return stats_array



# This is used to sum all jobs together into a single serialized job for MultiAmdahl behavior.
def emulate_multiamdahl(performance_dicts, benchmark_names, n_cpus, n_gpus, n_gpu_sms, gpu_clocks, n_dsas, n_dsa_cus, dsa_speedup, n_machines):

    setup_sum = 0
    teardown_sum = 0
    cpu_kernel_sum = 0


    for i in range(len(benchmark_names)):
        benchmark_name = benchmark_names[i]
        # Get Setup and teardown times.
        cpu_dict_key = benchmark_name + '_' + str(n_cpus) + 'cores'
        setup_sum += performance_dicts[0][cpu_dict_key]['SetupTime (s)']
        teardown_sum += performance_dicts[0][cpu_dict_key]['TeardownTime (s)']

        machine_kernel_times = []


        for machine_id in range(0,n_machines):
            time = 1
            bandwidth = 1
            power = 1
            #cpu_kernel_time = performance_dicts[0][cpu_dict_key]['KernelTime (s)']

            # CPU
            if machine_id < n_cpus:
                time = performance_dicts[0][cpu_dict_key]['KernelTime (s)']
                bandwidth = performance_dicts[0][cpu_dict_key]['KernelBandwidth (GB/s)']
                machine_kernel_times.append(time)
            # GPU
            elif machine_id < n_cpus + n_gpus:
                gpu_dict_key = benchmark_name + str(gpu_clocks[machine_id-n_cpus]) + 'clk_' + str(n_gpu_sms) + 'sms'
                time = performance_dicts[1][gpu_dict_key]['KernelTime (s)']
                bandwidth = performance_dicts[1][gpu_dict_key]['Bandwidth (GB/s)']
                power = performance_dicts[1][gpu_dict_key]['Power Usage (W)']
                machine_kernel_times.append(time)
                
            # DSA
            elif machine_id < n_cpus + n_gpus + n_dsas:
                dsa_type_id = (machine_id - n_cpus - n_gpus) // len(gpu_clocks)
                dsa_dict_key = benchmark_name + str(gpu_clocks[machine_id-n_cpus-n_gpus-dsa_type_id*len(gpu_clocks)]) + 'clk_' + str(int(n_dsa_cus*dsa_speedup)) + 'sms'
                dsa_compatibility_array = list(get_dsa_compatibility(machine_id, performance_dicts, benchmark_names, n_cpus, n_gpus, gpu_clocks))
                dsa_type = dsa_compatibility_array.index(1)
                if dsa_type == i:
                    time = performance_dicts[1][dsa_dict_key]['KernelTime (s)']
                    bandwidth = performance_dicts[1][dsa_dict_key]['Bandwidth (GB/s)']
                    power = performance_dicts[1][dsa_dict_key]['Power Usage (W)']
                
                    machine_kernel_times.append(time)

        best_kernel_time = min(machine_kernel_times)
        cpu_kernel_sum += best_kernel_time

    for key, value in performance_dicts[0].items():
        performance_dicts[0][key]['SetupTime (s)'] = setup_sum
        performance_dicts[0][key]['KernelTime (s)'] = cpu_kernel_sum
        performance_dicts[0][key]['TeardownTime (s)'] = teardown_sum


    return performance_dicts