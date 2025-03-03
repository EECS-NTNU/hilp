import numpy as np
import pandas as pd
import sys
import math


# Scale input data to be in line with the system 
# e.g. If a task uses a lot of bandwidth then slow it down.
def scale_input_data(df, n_machines, RESOURCE_CONSTRAINTS, total_power, total_bandwidth, n_cpus, gpu_data_df, timestep_res, EXT_MEM_ENERGY, MAX_MAKESPAN):
    for i in range(n_machines):
        
        round_result = lambda x : round(x) if x>=1 else math.ceil(x)
        
        bandwidth_idx = 'machine' + str(i) + '_bandwidth'
        time_idx = 'machine' + str(i) + '_time'
        power_idx = 'machine' + str(i) + '_power'
        compatibility_idx = 'machine' + str(i) + '_compatibility'


        # Set things down for the resrouce constraints.
        for t in range(len(df)):
            bandwidth = df[bandwidth_idx][t]
            time = df[time_idx][t]
            power = df[power_idx][t]
            if int(RESOURCE_CONSTRAINTS) == 0:
                df.loc[t, bandwidth_idx] = 0
                df.loc[t, power_idx] = 0
        
        # Check Bandwidth
        for t in range(len(df)):
            max_sms = 128
            bandwidth = df[bandwidth_idx][t]
            time = df[time_idx][t]
            power = df[power_idx][t]
            
            if bandwidth > total_bandwidth:

                new_bandwidth = 1
                new_time = 1
                new_power = 1
                num_clocks = 11
                downclocked_machine_index = n_cpus
                current_machine_index = (i % (num_clocks)) # 11 is the number of clock steps
                
                if int(current_machine_index) == int(downclocked_machine_index):
                    bench_id = df['job_id'][t] * num_clocks
                    #print(bench_id,"Downclocking SMs from bandwidth")
                    
                    # If lowest clocked machine, then turn off SMs
                    # Read get the lowest clock slice from the gpu csv data
                    names = gpu_data_df['Config'][bench_id*max_sms:(bench_id+1)*max_sms].to_list()
                    sm_time_data = gpu_data_df['KernelTime (s)'][bench_id*max_sms:(bench_id+1)*max_sms].to_list()
                    sm_bandwidth_data = gpu_data_df['Bandwidth (GB/s)'][bench_id*max_sms:(bench_id+1)*max_sms].to_list()
                    sm_power_data = gpu_data_df['Power Usage (W)'][bench_id*max_sms:(bench_id+1)*max_sms].to_list()


                    # Find the next highest bandwidth within the limit.
                    for j in range(len(sm_bandwidth_data)):
                        index = len(sm_bandwidth_data)-1-j
                        lower_bandwidth = sm_bandwidth_data[index]
                        if lower_bandwidth < total_bandwidth:
                            print(names[index])
                            print(lower_bandwidth)
                            new_time = math.ceil(sm_time_data[index]/timestep_res)
                            new_bandwidth = math.ceil(sm_bandwidth_data[index])
                            new_power = math.ceil(sm_power_data[index]) + math.ceil(float(new_bandwidth)*1e9*EXT_MEM_ENERGY)
                            print('index',index,sm_bandwidth_data[index],sm_time_data[index])
                            print("SMs dropping","Bandwiths",bandwidth,'->',new_bandwidth,"     POWERS",power,'->',new_power,"     TIMES",time,'->',new_time)
                            break # We found a new bandwidth that fits, so stop now.
                    
                    df.loc[t, bandwidth_idx] = new_bandwidth
                    df.loc[t, time_idx] = new_time
                    df.loc[t, power_idx] = new_power
                
                # Slow down CPUs linear, cause we have no other data
                elif i < int(n_cpus):
                    slowdown = total_bandwidth / bandwidth
                    new_bandwidth = round_result(bandwidth * slowdown)
                    new_time = round_result(df[time_idx][t] / slowdown)
                    power_factor = (time / new_time)**2 # Working based on DVFS now
                    new_power = round_result(df[power_idx][t] * power_factor)
                    df.loc[t, time_idx] = new_time
                    df.loc[t, bandwidth_idx] = new_bandwidth
                    df.loc[t, power_idx] = new_power
                
                else:
                    df.loc[t, time_idx] = 1
                    df.loc[t, bandwidth_idx] = 1
                    df.loc[t, power_idx] = 1
                    df.loc[t, compatibility_idx] = 0


        # Check Power
        for t in range(len(df)):
            max_sms = 128
            bandwidth = df[bandwidth_idx][t]
            time = df[time_idx][t]
            power = df[power_idx][t]
            compatibility = df[compatibility_idx][t]

            new_bandwidth = 1
            new_time = 1
            new_power = 1

            # Add power of ext memory
            mem_power = math.ceil(float(bandwidth)*1e9*EXT_MEM_ENERGY)
            # Add memory power to the power.
            df.loc[t, power_idx] = power + mem_power
            power = df[power_idx][t]

            # Skip machines that are disabled.
            if compatibility == 0:
                continue

            # Power too high?
            if power > total_power:
                
                # First check if the machine is high clock or not, only turn off sms for lowest clock machine
                num_clocks = 11
                downclocked_machine_index = n_cpus
                current_machine_index = (i % (num_clocks)) # 11 is the number of clock steps
                
                if int(current_machine_index) == int(downclocked_machine_index):
                    print("Turning off SMs on Machine", i)
                    # New version, if power too high then assume device can't turn on.
                    # Hardcode clock to only select low clocked SMs
                    new_power = 0
                    print(t,downclocked_machine_index,"bandwidth",bandwidth)
                    bench_id = df['job_id'][t] * num_clocks
                                        
                    # Read get the lowest clock slice from the gpu csv data
                    names = gpu_data_df['Config'][bench_id*max_sms:(bench_id+1)*max_sms].to_list()
                    sm_time_data = gpu_data_df['KernelTime (s)'][bench_id*max_sms:(bench_id+1)*max_sms].to_list()
                    sm_bandwidth_data = gpu_data_df['Bandwidth (GB/s)'][bench_id*max_sms:(bench_id+1)*max_sms].to_list()
                    sm_power_data = gpu_data_df['Power Usage (W)'][bench_id*max_sms:(bench_id+1)*max_sms].to_list()
                    
                    # Find the next highest power within the limit.
                    for j in range(len(sm_power_data)):
                        index = len(sm_power_data)-1-j
                        lower_power = sm_power_data[index]
                        if lower_power < total_power - mem_power:
                            print("mem_power",mem_power)
                            print("lower_power",lower_power)
                            new_time = math.ceil(sm_time_data[index]/timestep_res)
                            new_bandwidth = math.ceil(sm_bandwidth_data[index])
                            new_mem_power =float(new_bandwidth)*1e9*EXT_MEM_ENERGY
                            new_power = math.ceil(lower_power + new_mem_power)
                            new_name = names[index]
                            print("new_mem_power",new_mem_power)
                            print(t,"SMs dropping to",new_name,"Bandwiths",bandwidth,new_bandwidth,"POWERS",power,new_power,"TIMES",time,new_time)
                            break # We found a new power that fits, so stop now.
                    df.loc[t, time_idx] = new_time
                    df.loc[t, bandwidth_idx] = new_bandwidth
                    df.loc[t, power_idx] = new_power
                
                # It is a higher clocked machine and thus should never be used in the power limited case.
                else:
                    df.loc[t, time_idx] = 1
                    df.loc[t, bandwidth_idx] = 1
                    df.loc[t, power_idx] = 1
                    df.loc[t, compatibility_idx] = 0
        
        
        # Check Large Times above the Max Makespan
        for t in range(len(df)):
            bandwidth = df[bandwidth_idx][t]
            time = df[time_idx][t]
            power = df[power_idx][t]
            compatibility = df[compatibility_idx][t]
            if time > int(MAX_MAKESPAN):
                df.loc[t, bandwidth_idx] = 1
                df.loc[t, time_idx] = 1
                df.loc[t, compatibility_idx] = 0
                
    return df


# Build array string in the Minizinc DZN format
def build_dzn_3darray(df, n_jobs, n_tasks, n_machines, start_idx_string, end_idx_string):
    array_data = []
    for j in range(n_jobs):
        for m in range(n_machines):
            for t in range(n_tasks):
                idx_string = start_idx_string + str(m) + end_idx_string
                data = df[idx_string][j*n_tasks + t]
                
                array_data.append(data)
    return array_data