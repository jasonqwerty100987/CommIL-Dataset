import json
import os
from statistics import mean, mode
import numpy as np
import scipy.stats
from itertools import product
import random 

def read_data(filepath):
    with open(filepath, 'r') as fp:
        data = json.load(fp)
    return data

def parse_params_from_path(folder_path):
    folder_name = os.path.basename(folder_path)
    feature_size, packet_size, max_time = folder_name.split('_')
    feature_size = float(feature_size)
    packet_size = float(packet_size)
    max_time = float(max_time)
    return feature_size, packet_size, max_time

def get_number_of_CAV(scenario_folder_path):
    cav_count = 0
    for cav_folder_name in os.listdir(scenario_folder_path):
        cav_folder_path = os.path.join(scenario_folder_path, cav_folder_name)
        if os.path.isdir(cav_folder_path):
            cav_count+=1
    
    return cav_count

def get_min_max_of_transmission(data, reduction=None):
    # Given a scenario, return the start time and end time of transmission process at each time stamp

    list_min_time = []
    list_max_time = []

    for time_stamp in data:
        min_time = None
        max_time = None
        for cav in data[time_stamp]:
            sent_times = [float(time[0]) for time in data[time_stamp][cav]['sent']]
            receive_times = [float(time[0]) for peer_num in data[time_stamp][cav]['receive'] for time in data[time_stamp][cav]['receive'][peer_num]]
            this_min_sent_time = min(sent_times) if sent_times else None
            this_max_sent_time = max(sent_times) if sent_times else None
            this_min_receive_time = min(receive_times) if receive_times else None
            this_max_receive_time = max(receive_times) if receive_times else None
            if min_time is None:
                if this_min_sent_time is None and not this_min_receive_time is None:
                    min_time = this_min_receive_time
                elif not this_min_sent_time is None and this_min_receive_time is None:
                    min_time  = this_min_sent_time
                else:
                    min_time = min(this_min_sent_time, this_min_receive_time)
            else:
                if this_min_sent_time is None and not this_min_receive_time is None:
                    min_time = min(this_min_receive_time, min_time)
                elif not this_min_sent_time is None and this_min_receive_time is None:
                    min_time  = min(this_min_sent_time, min_time)
                else:
                    min_time = min(this_min_sent_time, this_min_receive_time, min_time)
            if max_time is None:
                if this_max_sent_time is None and not this_max_receive_time is None:
                    max_time = this_max_receive_time
                elif not this_max_sent_time is None and this_max_receive_time is None:
                    max_time  = this_max_sent_time
                else:
                    max_time = max(this_max_sent_time, this_max_receive_time)
            else:
                if this_max_sent_time is None and not this_max_receive_time is None:
                    max_time = max(this_max_receive_time, max_time)
                elif not this_max_sent_time is None and this_max_receive_time is None:
                    max_time  = min(this_max_sent_time, max_time)
                else:
                    max_time = max(this_max_sent_time, this_max_receive_time, max_time)
        if not min_time is None and not max_time is None:
            list_min_time.append(min_time)
            list_max_time.append(max_time)
    
    if reduction is not None:
        list_min_time = reduction(list_min_time)
        list_max_time = reduction(list_max_time)
    
    return list_min_time, list_max_time

def get_duration_of_transmission(data, reduction=None):
    min_time, max_time = get_min_max_of_transmission(data)
    if min_time and max_time:
        if reduction:
            return reduction(np.asarray(max_time) - np.asarray(min_time))
        else:
            return np.asarray(max_time) - np.asarray(min_time)
    else:
        return None

def get_ratio(data, n_cav, packet_size, feature_size, cav_select = "max", reduction = mean):
    num_pk_cav = feature_size/packet_size
    total_num_pk = num_pk_cav * (n_cav-1) # exclude ego vehicle

    ratios = []

    if cav_select == "max":
        cav_select = np.argmax
    elif cav_select == "min":
        cav_select = np.argmin
    else:
        cav_select = None
    
    
    for time_stamp in data:
        selected_cav_ratio = []
        for cav in data[time_stamp]:
            n_received_packet = 0
            for peer_num in data[time_stamp][cav]['receive']:
                n_received_packet += len(data[time_stamp][cav]['receive'][peer_num])

            selected_cav_ratio.append(n_received_packet/(total_num_pk)*100)

        if selected_cav_ratio and cav_select:
            # only recode either the best or worst ratio at each time stamp
            selected_cav_index = cav_select(selected_cav_ratio)
            ratios.append(selected_cav_ratio[selected_cav_index])
        elif selected_cav_ratio and cav_select is None:
            # Calucate average ratio cross all cav
            ratios.append(mean(selected_cav_ratio))
        else:
            # No vehicle can either send or receive any data
            ratios.append(0.)
    
    if reduction is not None:
        ratios = reduction(ratios)

    return ratios

# def _post_procfess_ratios()

def mean_confidence_interval(data, confidence=0.95):
    a = 1.0 * np.array(data)
    n = len(a)
    m, se = np.mean(a), scipy.stats.sem(a)
    h = se * scipy.stats.t.ppf((1 + confidence) / 2., n-1)
    return (m, h)

import matplotlib.pyplot as plt
from tqdm import tqdm
# One set of figures: x = number of CAV, y = ratio of avg received packets / total number of packets transmitted
# To show with the number of CAV increased, the ratio is lower, each line can be different config (maybe fix feature size and change packet size)
def plot_set_1(root, dataset_folder = 'train/', feature_size_select = None, cav_select = "min", distances:list = [40, 60]):
    print("Plotting nCAV VS. Ratio of received packets")
    distances.sort()
    distance_dict = get_average_distance_scenario_dataset(root, dataset_folder)
    base_folder_name = "comm_sim"
    filename = "comm_sim.json"
    base_folder_path = os.path.join(root, base_folder_name)
    final_data = {}
    for distance in distances:
        final_data[distance] = {}
    final_data['others'] = {}
    # plot_data = {}

    if os.path.isdir(base_folder_path):
        for sub_folder_name in tqdm(os.listdir(base_folder_path)):
            sub_folder_path = os.path.join(base_folder_path, sub_folder_name)
            if os.path.isdir(sub_folder_path):
                feature_size, packet_size, max_time = parse_params_from_path(sub_folder_path)
                if not feature_size_select is None:
                    if feature_size not in feature_size_select:
                        continue
                if packet_size > 65507:
                    continue
                # if feature_size not in plot_data:
                #     plot_data[feature_size] = []

                for scenario_folder_name in os.listdir(sub_folder_path):
                    scenario_folder_path = os.path.join(sub_folder_path, scenario_folder_name)
                    if os.path.isdir(scenario_folder_path):
                        dataset_scenario_folder_path = os.path.join(root, dataset_folder, scenario_folder_name)
                        filepath = os.path.join(scenario_folder_path, filename)
                        data = read_data(filepath)
                        ncav = get_number_of_CAV(dataset_scenario_folder_path)
                        ratio = get_ratio(data, ncav, packet_size, feature_size, cav_select=cav_select, reduction=None)
                        avg_distance = mean(distance_dict[scenario_folder_name])
                        if avg_distance >= distances[-1]:
                            plot_data = final_data['others']
                        else:
                            for distance_threshold in distances:
                                if avg_distance<distance_threshold:
                                    plot_data = final_data[distance_threshold]
                                    break
                        
                        if feature_size not in plot_data:
                            plot_data[feature_size] = {}
                        
                        total_ratio = plot_data[feature_size]
                        if packet_size not in total_ratio:
                            total_ratio[packet_size] = {}
                        if ncav not in total_ratio[packet_size]:
                            total_ratio[packet_size][ncav] = []
                        total_ratio[packet_size][ncav].extend(ratio)

    print(final_data.keys())
    for key in final_data:
        print(f"final_data[{key}] has keys {final_data[key].keys()}")
        for feature_size in final_data[key]:
            print(f"    final_data[{key}][{feature_size}] has keys {final_data[key][feature_size].keys()}")
            for packet_size in final_data[key][feature_size]:
                print(f"        final_data[{key}][{feature_size}][{packet_size}] has keys {final_data[key][feature_size][packet_size].keys()}")

                # x_sorted_ncavs = [ele for ele in total_ratio.keys()]
                # x_sorted_ncavs.sort()
                # # y_ratios = [mean_confidence_interval(total_ratio[ele]) for ele in x_sorted_ncavs]
                # y_ratios = [mean(total_ratio[ele]) for ele in x_sorted_ncavs]
                # plot_data[feature_size].append((x_sorted_ncavs, y_ratios, f"pk_size={format(packet_size, '.0e')}"))
    figure_path = os.path.join(root, "image/", "cav_ratio/")
    
    for distance_thresh in final_data:
        this_distance_path = os.path.join(figure_path, f"{distance_thresh}/")
        os.makedirs(this_distance_path, exist_ok=True)
        plot_data = {}
        for feature_size in final_data[distance_thresh]:
            plot_data[feature_size] = []
            for packet_size in final_data[distance_thresh][feature_size]:
                total_ratio = final_data[distance_thresh][feature_size][packet_size]
                x_sorted_ncavs = [ele for ele in total_ratio.keys()]
                x_sorted_ncavs.sort()
                y_ratios = [mean_confidence_interval(total_ratio[ele]) for ele in x_sorted_ncavs]
                plot_data[feature_size].append((x_sorted_ncavs, y_ratios, f"pl_size={format(packet_size, '.0e')}"))
        for feature_size in plot_data:
            plt.figure()
            iterator = get_next_line(bar_plot=True)
            multiline_data = plot_data[feature_size]
            xss = [len(ele[0]) for ele in multiline_data]
            x_ticks = []
            # xticklabels = [f"ncav={ele}" for ele in x_ticks]
            n_bins = len(multiline_data)
            total_width = 0.9
            each_bin_width = total_width/n_bins
            offsets = [each_bin_width/2 + each_bin_width * i - total_width/2 for i in range(n_bins)]
            for i, (xs, ys, label) in enumerate(multiline_data):
                x_ticks.extend(xs)
                hatch, color = next(iterator)
                yerr = [ele[1] for ele in ys]
                yss = [ele[0] for ele in ys]
                offset = offsets[i]
                new_xs = [offset + ele for ele in xs]
                plt.bar(new_xs, yss, width = each_bin_width, fill=False, hatch=hatch, label=label)
                plt.errorbar(new_xs, yss, yerr=yerr, color="r", ls='none', capsize=10)




            # if sum(xss) == len(xss):
            #     bar_plot = True
            # else:
            #     bar_plot = False
            # if not bar_plot:
            #     for xs, ys, label in multiline_data:
            #         if len(xs) == 1:
            #             continue
            #         marker, ls, color = next(iterator)
            #         plt.plot(xs, ys, label=label, linestyle= ls, color=color, marker=marker)
            # else:
            #     bars = {}
            #     for xs, ys, label in multiline_data:
            #         bars[float(label.split('=')[-1])] = ys[0]
            #     sorted_key = sorted(bars.keys())
            #     for i_plot, key in enumerate(sorted_key):
            #         plt.bar(i_plot, bars[key])
                
            # plt.title(f"Number of CAV VS. Received Packet Ratio. Feature Size = {feature_size}")
            # if not bar_plot:
                # plt.xlabel("Number of CAV")
            #     plt.xticks(xs)
            # else:
            plt.xlabel("Number of CAV")
            plt.ylabel("Received Packet Rate")
            plt.legend()
            
            
            # if bar_plot:
            ax = plt.gca()
                # axis_ticks = list(range(len(sorted_key)))
            x_ticks = sorted(list(set(x_ticks)))
            ax.set_xticks(x_ticks)
                # print(sorted_key)
                # ax.set_xticklabels([format(ele, '.0e') for ele in sorted_key])
            plt.tight_layout()
            this_figure_path = os.path.join(this_distance_path, f"fs_{feature_size}.pdf")
            plt.savefig(this_figure_path, format="pdf", dpi = 400.)
            plt.cla()
            plt.clf()
            plt.close('all')

# One set of figures: x = number of CAV, y = duration of transmission
# To show with the number of CAV increased, the duration is longer, each line can be different config (maybe fix feature size and change packet size)
def plot_set2(root, dataset_folder = 'train/', feature_size_select = None, distances:list = [40, 60]):
    print("Plotting nCAV VS. Duration of Transmission")
    distances.sort()
    distance_dict = get_average_distance_scenario_dataset(root, dataset_folder)
    base_folder_name = "comm_sim"
    filename = "comm_sim.json"
    base_folder_path = os.path.join(root, base_folder_name)
    final_data = {}
    for distance in distances:
        final_data[distance] = {}
    final_data['others'] = {}
    # plot_data = {}

    if os.path.isdir(base_folder_path):
        for sub_folder_name in tqdm(os.listdir(base_folder_path)):
            sub_folder_path = os.path.join(base_folder_path, sub_folder_name)
            if os.path.isdir(sub_folder_path):
                feature_size, packet_size, max_time = parse_params_from_path(sub_folder_path)
                if not feature_size_select is None:
                    if feature_size not in feature_size_select:
                        print("skip")
                        continue
                if packet_size > 65507:
                    continue
                # if feature_size not in plot_data:
                #     plot_data[feature_size] = []

                for scenario_folder_name in os.listdir(sub_folder_path):
                    scenario_folder_path = os.path.join(sub_folder_path, scenario_folder_name)
                    if os.path.isdir(scenario_folder_path):
                        dataset_scenario_folder_path = os.path.join(root, dataset_folder, scenario_folder_name)
                        filepath = os.path.join(scenario_folder_path, filename)
                        data = read_data(filepath)
                        ncav = get_number_of_CAV(dataset_scenario_folder_path)
                        durantion = get_duration_of_transmission(data)
                        if durantion is None:
                            continue
                        else:
                            durantion = durantion.tolist()
                        # ratio = get_ratio(data, ncav, packet_size, feature_size, cav_select=cav_select, reduction=None)
                        avg_distance = mean(distance_dict[scenario_folder_name])
                        if avg_distance >= distances[-1]:
                            plot_data = final_data['others']
                        else:
                            for distance_threshold in distances:
                                if avg_distance<distance_threshold:
                                    plot_data = final_data[distance_threshold]
                                    break
                        
                        if feature_size not in plot_data:
                            plot_data[feature_size] = {}
                        
                        total_ratio = plot_data[feature_size]
                        if packet_size not in total_ratio:
                            total_ratio[packet_size] = {}
                        if ncav not in total_ratio[packet_size]:
                            total_ratio[packet_size][ncav] = []
                        total_ratio[packet_size][ncav].extend(durantion)

    print(final_data.keys())
    for key in final_data:
        print(f"final_data[{key}] has keys {final_data[key].keys()}")
        for feature_size in final_data[key]:
            print(f"    final_data[{key}][{feature_size}] has keys {final_data[key][feature_size].keys()}")
            for packet_size in final_data[key][feature_size]:
                print(f"        final_data[{key}][{feature_size}][{packet_size}] has keys {final_data[key][feature_size][packet_size].keys()}")

                # x_sorted_ncavs = [ele for ele in total_ratio.keys()]
                # x_sorted_ncavs.sort()
                # # y_ratios = [mean_confidence_interval(total_ratio[ele]) for ele in x_sorted_ncavs]
                # y_ratios = [mean(total_ratio[ele]) for ele in x_sorted_ncavs]
                # plot_data[feature_size].append((x_sorted_ncavs, y_ratios, f"pk_size={format(packet_size, '.0e')}"))
    figure_path = os.path.join(root, "image/", "cav_duration/")
    for distance_thresh in final_data:
        this_distance_path = os.path.join(figure_path, f"{distance_thresh}/")
        os.makedirs(this_distance_path, exist_ok=True)
        plot_data = {}
        for feature_size in final_data[distance_thresh]:
            plot_data[feature_size] = []
            for packet_size in final_data[distance_thresh][feature_size]:
                total_ratio = final_data[distance_thresh][feature_size][packet_size]
                x_sorted_ncavs = [ele for ele in total_ratio.keys()]
                x_sorted_ncavs.sort()
                y_ratios = [mean_confidence_interval(total_ratio[ele]) for ele in x_sorted_ncavs]
                plot_data[feature_size].append((x_sorted_ncavs, y_ratios, f"pl_size={format(packet_size, '.0e')}"))
        for feature_size in plot_data:
            plt.figure()
            iterator = get_next_line(bar_plot=True)
            multiline_data = plot_data[feature_size]
            # xss = [len(ele[0]) for ele in multiline_data]
            # xss = [len(ele[0]) for ele in multiline_data]
            x_ticks = []
            # xticklabels = [f"ncav={ele}" for ele in x_ticks]
            n_bins = len(multiline_data)
            total_width = 0.9
            each_bin_width = total_width/n_bins
            offsets = [each_bin_width/2 + each_bin_width * i - total_width/2 for i in range(n_bins)]
            for i, (xs, ys, label) in enumerate(multiline_data):
                x_ticks.extend(xs)
                hatch, color = next(iterator)
                yerr = [ele[1] for ele in ys]
                yss = [ele[0] for ele in ys]
                offset = offsets[i]
                new_xs = [offset + ele for ele in xs]
                plt.bar(new_xs, yss, width = each_bin_width, fill=False, hatch=hatch, label=label)
                plt.errorbar(new_xs, yss, yerr=yerr, color="r", ls='none', capsize=10)
            # if sum(xss) == len(xss):
            #     bar_plot = True
            # else:
            #     bar_plot = False

            # if not bar_plot:
            #     for xs, ys, label in multiline_data:
            #         if len(xs) == 1:
            #             continue
            #         marker, ls, color = next(iterator)
            #         plt.plot(xs, ys, label=label, linestyle= ls, color=color, marker=marker)
            #         # plt.plot(xs, ys, label=label)
            # else:
            #     bars = {}
            #     for xs, ys, label in multiline_data:
            #         bars[float(label.split('=')[-1])] = ys[0]
            #     sorted_key = sorted(bars.keys())
            #     for i_plot, key in enumerate(sorted_key):
            #         plt.bar(i_plot, bars[key])
                
                
            # if not bar_plot:
            #     plt.xlabel("Number of CAV")
            #     plt.xticks(xs)
            # else:
            #     plt.xlabel("Payload Size")
            # plt.ylabel("Duration of Transmission")
            # plt.legend()

            plt.xlabel("Number of CAV")
            plt.ylabel("Duration of Transmission")
            plt.legend()
            
            
            # if bar_plot:
            ax = plt.gca()
                # axis_ticks = list(range(len(sorted_key)))
            x_ticks = sorted(list(set(x_ticks)))
            ax.set_xticks(x_ticks)
            
            
            # if bar_plot:
            #     ax = plt.gca()
            #     axis_ticks = list(range(len(sorted_key)))
            #     ax.set_xticks(axis_ticks)
            #     print(sorted_key)
            #     ax.set_xticklabels([format(ele, '.0e') for ele in sorted_key])
            plt.tight_layout()
            this_figure_path = os.path.join(this_distance_path, f"fs_{feature_size}.pdf")
            plt.savefig(this_figure_path, format="pdf", dpi = 400.)
            plt.cla()
            plt.clf()
            plt.close('all')

# One set of figures: x = feature size, y = duration of transmission
# To show with the size of feature increase, the duration of transmission is longer, each line can be different packet size and number of CAV
def plot_set3(root, dataset_folder = 'train/', feature_size_select = None, distances:list = [40, 60]):
    print("Plotting Feature Size VS. Duration of Transmission")
    distances.sort()
    distance_dict = get_average_distance_scenario_dataset(root, dataset_folder)
    base_folder_name = "comm_sim"
    filename = "comm_sim.json"
    base_folder_path = os.path.join(root, base_folder_name)
    final_data = {}
    for distance in distances:
        final_data[distance] = {}
    final_data['others'] = {}
    # plot_data = {}

    if os.path.isdir(base_folder_path):
        for sub_folder_name in tqdm(os.listdir(base_folder_path)):
            sub_folder_path = os.path.join(base_folder_path, sub_folder_name)
            if os.path.isdir(sub_folder_path):
                feature_size, packet_size, max_time = parse_params_from_path(sub_folder_path)
                if feature_size_select and feature_size not in feature_size_select:
                    print("skip")
                    continue
                if packet_size > 65507:
                    continue
                # if feature_size not in plot_data:
                #     plot_data[feature_size] = []

                for scenario_folder_name in os.listdir(sub_folder_path):
                    scenario_folder_path = os.path.join(sub_folder_path, scenario_folder_name)
                    if os.path.isdir(scenario_folder_path):
                        dataset_scenario_folder_path = os.path.join(root, dataset_folder, scenario_folder_name)
                        filepath = os.path.join(scenario_folder_path, filename)
                        data = read_data(filepath)
                        ncav = get_number_of_CAV(dataset_scenario_folder_path)
                        durantion = get_duration_of_transmission(data)
                        if durantion is None:
                            continue
                        else:
                            durantion = durantion.tolist()
                        # ratio = get_ratio(data, ncav, packet_size, feature_size, cav_select=cav_select, reduction=None)
                        avg_distance = mean(distance_dict[scenario_folder_name])
                        if avg_distance >= distances[-1]:
                            plot_data = final_data['others']
                        else:
                            for distance_threshold in distances:
                                if avg_distance<distance_threshold:
                                    plot_data = final_data[distance_threshold]
                                    break
                        
                        if ncav not in plot_data:
                            plot_data[ncav] = {}
                        
                        total_durations = plot_data[ncav]
                        if packet_size not in total_durations:
                            total_durations[packet_size] = {}
                        if feature_size not in total_durations[packet_size]:
                            total_durations[packet_size][feature_size] = []
                        total_durations[packet_size][feature_size].extend(durantion)

    print(final_data.keys())
    for key in final_data:
        print(f"final_data[{key}] has keys {final_data[key].keys()}")
        for ncav in final_data[key]:
            print(f"    final_data[{key}][{ncav}] has keys {final_data[key][ncav].keys()}")
            for packet_size in final_data[key][ncav]:
                print(f"        final_data[{key}][{ncav}][{packet_size}] has keys {final_data[key][ncav][packet_size].keys()}")

                # x_sorted_ncavs = [ele for ele in total_ratio.keys()]
                # x_sorted_ncavs.sort()
                # # y_ratios = [mean_confidence_interval(total_ratio[ele]) for ele in x_sorted_ncavs]
                # y_ratios = [mean(total_ratio[ele]) for ele in x_sorted_ncavs]
                # plot_data[feature_size].append((x_sorted_ncavs, y_ratios, f"pk_size={format(packet_size, '.0e')}"))
    figure_path = os.path.join(root, "image/", "feature_duration/")
    for distance_thresh in final_data:
        this_distance_path = os.path.join(figure_path, f"{distance_thresh}/")
        os.makedirs(this_distance_path, exist_ok=True)
        plot_data = {}
        for ncav in final_data[distance_thresh]:
            plot_data[ncav] = []
            for packet_size in final_data[distance_thresh][ncav]:
                total_durations = final_data[distance_thresh][ncav][packet_size]
                x_sorted_feature_size = [ele for ele in total_durations.keys()]
                x_sorted_feature_size.sort()
                y_durations = [mean_confidence_interval(total_durations[ele]) for ele in x_sorted_feature_size]
                plot_data[ncav].append((x_sorted_feature_size, y_durations, f"pl_size={format(packet_size, '.0e')}"))
        for ncav in plot_data:
            plt.figure()
            plt.xscale("log")
            iterator = get_next_line()
            multiline_data = plot_data[ncav]
            # xss = [len(ele[0]) for ele in multiline_data]
            x_ticks = {}
            # xticklabels = [f"ncav={ele}" for ele in x_ticks]
            # n_bins = len(multiline_data)
            # total_width = 0.9
            # each_bin_width = total_width/n_bins
            # offsets = [each_bin_width/2 + each_bin_width * i - total_width/2 for i in range(n_bins)]
            for i, (xs, ys, label) in enumerate(multiline_data):
                if len(xs) == 1:
                        continue
                marker, ls, color = next(iterator)
                # plt.plot(xs, ys, label=label, linestyle= ls, color=color, marker=marker)
                # plt.plot(xs, ys, label=label)
                for temp in xs:
                    if temp not in x_ticks:
                        x_ticks[temp] = 1

                marker, ls, color = next(iterator)
                yerr = [ele[1] for ele in ys]
                yss = [ele[0] for ele in ys]
                plt.plot(xs, yss, label=label, linestyle= ls, color=color, marker=marker)
                plt.errorbar(xs, yss, yerr=yerr, color=color, ls='none', capsize=10)
            # if sum(xss) == len(xss):
            #     bar_plot = True
            # else:
            #     bar_plot = False
            #     x_ticks = {}

            # if not bar_plot:
            #     for xs, ys, label in multiline_data:
                    # if len(xs) == 1:
                    #     continue
                    # marker, ls, color = next(iterator)
                    # plt.plot(xs, ys, label=label, linestyle= ls, color=color, marker=marker)
                    # # plt.plot(xs, ys, label=label)
                    # for temp in xs:
                    #     if temp not in x_ticks:
                    #         x_ticks[temp] = 1
            # else:
            #     bars = {}
            #     for xs, ys, label in multiline_data:
            #         bars[float(label.split('=')[-1])] = ys[0]
            #     sorted_key = sorted(bars.keys())
            #     for i_plot, key in enumerate(sorted_key):
            #         plt.bar(i_plot, bars[key])
                
                
            # if not bar_plot:
                # plt.xlabel("Feature Size")
            #     x_ticks = sorted(list(x_ticks.keys()))
            #     plt.xticks(x_ticks)
            #     ax = plt.gca()
            #     ax.set_xticklabels([format(ele, '.0e') for ele in x_ticks], rotation = 50)
            # else:
            #     plt.xlabel("Payload Size")
            plt.xlabel("Feature Size")
            plt.ylabel("Duration of Transmission")
            plt.legend()
            
            
            # if bar_plot:
            #     ax = plt.gca()
            #     axis_ticks = list(range(len(sorted_key)))
            #     ax.set_xticks(axis_ticks)
            #     print(sorted_key)
            #     ax.set_xticklabels([format(ele, '.0e') for ele in sorted_key])
            plt.tight_layout()
            this_figure_path = os.path.join(this_distance_path, f"fs_{ncav}.pdf")
            plt.savefig(this_figure_path, format="pdf", dpi = 400.)
            plt.cla()
            plt.clf()
            plt.close('all')

# One set of figures: x = packet size, y = ratio of avg received packets / total number of packets transmitted
# To show with the packet size increase, the ratio is lower. Each line can be different feature size and number of CAV
def plot_set_4(root, dataset_folder = 'train/', feature_size_select = None, cav_select = "min", distances:list = [40, 60]):
    print("Plotting Packet Size VS. Ratio of received packets")
    distances.sort()
    distance_dict = get_average_distance_scenario_dataset(root, dataset_folder)
    base_folder_name = "comm_sim"
    filename = "comm_sim.json"
    base_folder_path = os.path.join(root, base_folder_name)
    final_data = {}
    for distance in distances:
        final_data[distance] = {}
    final_data['others'] = {}
    # plot_data = {}

    if os.path.isdir(base_folder_path):
        for sub_folder_name in tqdm(os.listdir(base_folder_path)):
            sub_folder_path = os.path.join(base_folder_path, sub_folder_name)
            if os.path.isdir(sub_folder_path):
                feature_size, packet_size, max_time = parse_params_from_path(sub_folder_path)
                print(feature_size)
                if feature_size_select and feature_size not in feature_size_select:
                        print("skip")
                        continue
                print(f"after skip: {feature_size}")
                if packet_size > 65507:
                    continue
                # if feature_size not in plot_data:
                #     plot_data[feature_size] = []

                for scenario_folder_name in os.listdir(sub_folder_path):
                    scenario_folder_path = os.path.join(sub_folder_path, scenario_folder_name)
                    if os.path.isdir(scenario_folder_path):
                        dataset_scenario_folder_path = os.path.join(root, dataset_folder, scenario_folder_name)
                        filepath = os.path.join(scenario_folder_path, filename)
                        data = read_data(filepath)
                        ncav = get_number_of_CAV(dataset_scenario_folder_path)
                        ratio = get_ratio(data, ncav, packet_size, feature_size, cav_select=cav_select, reduction=None)
                        avg_distance = mean(distance_dict[scenario_folder_name])
                        if avg_distance >= distances[-1]:
                            plot_data = final_data['others']
                        else:
                            for distance_threshold in distances:
                                if avg_distance<distance_threshold:
                                    plot_data = final_data[distance_threshold]
                                    break
                        
                        if ncav not in plot_data:
                            plot_data[ncav] = {}
                        
                        total_ratios = plot_data[ncav]
                        if feature_size not in total_ratios:
                            total_ratios[feature_size] = {}
                        if packet_size not in total_ratios[feature_size]:
                            total_ratios[feature_size][packet_size] = []
                        total_ratios[feature_size][packet_size].extend(ratio)

    print(final_data.keys())
    for key in final_data:
        print(f"final_data[{key}] has keys {final_data[key].keys()}")
        for feature_size in final_data[key]:
            print(f"    final_data[{key}][{feature_size}] has keys {final_data[key][feature_size].keys()}")
            for packet_size in final_data[key][feature_size]:
                print(f"        final_data[{key}][{feature_size}][{packet_size}] has keys {final_data[key][feature_size][packet_size].keys()}")

                # x_sorted_ncavs = [ele for ele in total_ratio.keys()]
                # x_sorted_ncavs.sort()
                # # y_ratios = [mean_confidence_interval(total_ratio[ele]) for ele in x_sorted_ncavs]
                # y_ratios = [mean(total_ratio[ele]) for ele in x_sorted_ncavs]
                # plot_data[feature_size].append((x_sorted_ncavs, y_ratios, f"pk_size={format(packet_size, '.0e')}"))
    figure_path = os.path.join(root, "image/", "packet_ratio/")
    for distance_thresh in final_data:
        this_distance_path = os.path.join(figure_path, f"{distance_thresh}/")
        os.makedirs(this_distance_path, exist_ok=True)
        plot_data = {}
        for ncav in final_data[distance_thresh]:
            plot_data[ncav] = []
            for feature_size in final_data[distance_thresh][ncav]:
                total_ratio = final_data[distance_thresh][ncav][feature_size]
                x_sorted_packet_size = [ele for ele in total_ratio.keys()]
                x_sorted_packet_size.sort()
                y_ratios = [mean_confidence_interval(total_ratio[ele]) for ele in x_sorted_packet_size]
                plot_data[ncav].append((x_sorted_packet_size, y_ratios, f"feat_size={format(feature_size, '.0e')}"))

        for ncav in plot_data:
            plt.figure()
            iterator = get_next_line()
            plt.xscale("log")
            multiline_data = plot_data[ncav]
            x_ticks = {}
            # xticklabels = [f"ncav={ele}" for ele in x_ticks]
            # n_bins = len(multiline_data)
            # total_width = 0.9
            # each_bin_width = total_width/n_bins
            # offsets = [each_bin_width/2 + each_bin_width * i - total_width/2 for i in range(n_bins)]
            for i, (xs, ys, label) in enumerate(multiline_data):
                if len(xs) == 1:
                        continue
                marker, ls, color = next(iterator)
                # plt.plot(xs, ys, label=label, linestyle= ls, color=color, marker=marker)
                # plt.plot(xs, ys, label=label)
                for temp in xs:
                    if temp not in x_ticks:
                        x_ticks[temp] = 1

                marker, ls, color = next(iterator)
                yerr = [ele[1] for ele in ys]
                yss = [ele[0] for ele in ys]
                plt.plot(xs, yss, label=label, linestyle= ls, color=color, marker=marker)
                plt.errorbar(xs, yss, yerr=yerr, color=color, ls='none', capsize=10)
                
            # plt.title(f"Number of CAV VS. Received Packet Ratio. Feature Size = {feature_size}")
            # if not bar_plot:
            #     plt.xlabel("Payload Size")
            #     plt.xticks(sorted(list(set(xs_list))))
            # else:
            #     plt.xlabel("Feature Size")
            plt.xlabel("Payload Size")
            plt.xticks(sorted(list(x_ticks.keys())))
            plt.ylabel("Received Packet Rate")
            plt.legend()
            
            
            # if bar_plot:
            #     ax = plt.gca()
            #     axis_ticks = list(range(len(sorted_key)))
            #     ax.set_xticks(axis_ticks)
            #     print(sorted_key)
            #     ax.set_xticklabels([format(ele, '.0e') for ele in sorted_key])
            plt.tight_layout()
            this_figure_path = os.path.join(this_distance_path, f"fs_{ncav}.pdf")
            plt.savefig(this_figure_path, format="pdf", dpi = 400.)
            plt.cla()
            plt.clf()
            plt.close('all')

# One set of figures: x = packet size, y = duration of transmission
# To show with the packet size increase, the duration is longer. Each line can be feature size and number of CAV
def plot_set_5(root, dataset_folder = 'train/', feature_size_select = None, cav_select = "min", distances:list = [40, 60]):
    print("Plotting Packet Size VS. Duration of Transmission")
    distances.sort()
    distance_dict = get_average_distance_scenario_dataset(root, dataset_folder)
    base_folder_name = "comm_sim"
    filename = "comm_sim.json"
    base_folder_path = os.path.join(root, base_folder_name)
    final_data = {}
    for distance in distances:
        final_data[distance] = {}
    final_data['others'] = {}
    # plot_data = {}

    if os.path.isdir(base_folder_path):
        for sub_folder_name in tqdm(os.listdir(base_folder_path)):
            sub_folder_path = os.path.join(base_folder_path, sub_folder_name)
            if os.path.isdir(sub_folder_path):
                feature_size, packet_size, max_time = parse_params_from_path(sub_folder_path)
                if feature_size_select and feature_size not in feature_size_select:
                    print("skip")
                    continue
                if packet_size > 65507:
                    continue
                # if feature_size not in plot_data:
                #     plot_data[feature_size] = []

                for scenario_folder_name in os.listdir(sub_folder_path):
                    scenario_folder_path = os.path.join(sub_folder_path, scenario_folder_name)
                    if os.path.isdir(scenario_folder_path):
                        dataset_scenario_folder_path = os.path.join(root, dataset_folder, scenario_folder_name)
                        filepath = os.path.join(scenario_folder_path, filename)
                        data = read_data(filepath)
                        ncav = get_number_of_CAV(dataset_scenario_folder_path)

                        durantion = get_duration_of_transmission(data)
                        if durantion is None:
                            continue
                        else:
                            durantion = durantion.tolist()

                        avg_distance = mean(distance_dict[scenario_folder_name])
                        if avg_distance >= distances[-1]:
                            plot_data = final_data['others']
                        else:
                            for distance_threshold in distances:
                                if avg_distance<distance_threshold:
                                    plot_data = final_data[distance_threshold]
                                    break
                        
                        if ncav not in plot_data:
                            plot_data[ncav] = {}
                        
                        total_ratios = plot_data[ncav]
                        if feature_size not in total_ratios:
                            total_ratios[feature_size] = {}
                        if packet_size not in total_ratios[feature_size]:
                            total_ratios[feature_size][packet_size] = []
                        total_ratios[feature_size][packet_size].extend(durantion)

    print(final_data.keys())
    for key in final_data:
        print(f"final_data[{key}] has keys {final_data[key].keys()}")
        for feature_size in final_data[key]:
            print(f"    final_data[{key}][{feature_size}] has keys {final_data[key][feature_size].keys()}")
            for packet_size in final_data[key][feature_size]:
                print(f"        final_data[{key}][{feature_size}][{packet_size}] has keys {final_data[key][feature_size][packet_size].keys()}")

                # x_sorted_ncavs = [ele for ele in total_ratio.keys()]
                # x_sorted_ncavs.sort()
                # # y_ratios = [mean_confidence_interval(total_ratio[ele]) for ele in x_sorted_ncavs]
                # y_ratios = [mean(total_ratio[ele]) for ele in x_sorted_ncavs]
                # plot_data[feature_size].append((x_sorted_ncavs, y_ratios, f"pk_size={format(packet_size, '.0e')}"))
    figure_path = os.path.join(root, "image/", "packet_duration/")
    for distance_thresh in final_data:
        this_distance_path = os.path.join(figure_path, f"{distance_thresh}/")
        os.makedirs(this_distance_path, exist_ok=True)
        plot_data = {}
        for ncav in final_data[distance_thresh]:
            plot_data[ncav] = []
            for feature_size in final_data[distance_thresh][ncav]:
                total_durations = final_data[distance_thresh][ncav][feature_size]
                x_sorted_packet_size = [ele for ele in total_durations.keys()]
                x_sorted_packet_size.sort()
                y_durations = [mean_confidence_interval(total_durations[ele]) for ele in x_sorted_packet_size]
                plot_data[ncav].append((x_sorted_packet_size, y_durations, f"feat_size={format(feature_size, '.0e')}"))

        for ncav in plot_data:
            plt.figure()
            iterator = get_next_line()
            plt.xscale("log")
            multiline_data = plot_data[ncav]
            x_ticks = {}
            for i, (xs, ys, label) in enumerate(multiline_data):
                if len(xs) == 1:
                        continue
                marker, ls, color = next(iterator)
                for temp in xs:
                    if temp not in x_ticks:
                        x_ticks[temp] = 1
                marker, ls, color = next(iterator)
                yerr = [ele[1] for ele in ys]
                yss = [ele[0] for ele in ys]
                plt.plot(xs, yss, label=label, linestyle= ls, color=color, marker=marker)
                plt.errorbar(xs, yss, yerr=yerr, color=color, ls='none', capsize=10)

            # if not bar_plot:
            #     plt.xlabel("Payload Size")
            #     plt.xticks(sorted(list(set(xs_list))))
            # else:
            #     plt.xlabel("Feature Size")
            plt.xlabel("Payload Size")
            plt.xticks(sorted(list(x_ticks.keys())))
            plt.ylabel("Duration of Transmission")
            plt.legend()
            
            
            # if bar_plot:
            #     ax = plt.gca()
            #     axis_ticks = list(range(len(sorted_key)))
            #     ax.set_xticks(axis_ticks)
            #     print(sorted_key)
            #     ax.set_xticklabels([format(ele, '.0e') for ele in sorted_key])
            plt.tight_layout()
            this_figure_path = os.path.join(this_distance_path, f"fs_{ncav}.pdf")
            plt.savefig(this_figure_path, format="pdf", dpi = 400.)
            plt.cla()
            plt.clf()
            plt.close('all')

# One set of figures: x = feature size, y = Recievd Packet Ratio
# To show with the size of feature increase, the Recievd Packet Ratio is lower, each line can be different packet size and number of CAV
def plot_set_6(root, dataset_folder = 'train/', feature_size_select = None, cav_select = None, distances:list = [40, 60]):
    print("Plotting Feature Size VS. Received Packet Ratio")
    distances.sort()
    distance_dict = get_average_distance_scenario_dataset(root, dataset_folder)
    base_folder_name = "comm_sim"
    filename = "comm_sim.json"
    base_folder_path = os.path.join(root, base_folder_name)
    final_data = {}
    for distance in distances:
        final_data[distance] = {}
    final_data['others'] = {}

    if os.path.isdir(base_folder_path):
        for sub_folder_name in tqdm(os.listdir(base_folder_path)):
            sub_folder_path = os.path.join(base_folder_path, sub_folder_name)
            if os.path.isdir(sub_folder_path):
                feature_size, packet_size, max_time = parse_params_from_path(sub_folder_path)
                if not feature_size_select is None:
                    if feature_size not in feature_size_select:
                        continue
                if packet_size > 65507:
                    continue

                for scenario_folder_name in os.listdir(sub_folder_path):
                    scenario_folder_path = os.path.join(sub_folder_path, scenario_folder_name)
                    if os.path.isdir(scenario_folder_path):
                        dataset_scenario_folder_path = os.path.join(root, dataset_folder, scenario_folder_name)
                        filepath = os.path.join(scenario_folder_path, filename)
                        data = read_data(filepath)
                        ncav = get_number_of_CAV(dataset_scenario_folder_path)
                        ratio = get_ratio(data, ncav, packet_size, feature_size, cav_select=cav_select, reduction=None)
                        avg_distance = mean(distance_dict[scenario_folder_name])
                        if avg_distance >= distances[-1]:
                            plot_data = final_data['others']
                        else:
                            for distance_threshold in distances:
                                if avg_distance<distance_threshold:
                                    plot_data = final_data[distance_threshold]
                                    break
                        
                        if ncav not in plot_data:
                            plot_data[ncav] = {}
                        
                        total_durations = plot_data[ncav]
                        if packet_size not in total_durations:
                            total_durations[packet_size] = {}
                        if feature_size not in total_durations[packet_size]:
                            total_durations[packet_size][feature_size] = []
                        total_durations[packet_size][feature_size].extend(ratio)
                        

    print(final_data.keys())
    for key in final_data:
        print(f"final_data[{key}] has keys {final_data[key].keys()}")
        for ncav in final_data[key]:
            print(f"    final_data[{key}][{ncav}] has keys {final_data[key][ncav].keys()}")
            for packet_size in final_data[key][ncav]:
                print(f"        final_data[{key}][{ncav}][{packet_size}] has keys {final_data[key][ncav][packet_size].keys()}")

    figure_path = os.path.join(root, "image/", "feature_raio/")
    for distance_thresh in final_data:
        this_distance_path = os.path.join(figure_path, f"{distance_thresh}/")
        os.makedirs(this_distance_path, exist_ok=True)
        plot_data = {}
        for ncav in final_data[distance_thresh]:
            plot_data[ncav] = []
            for packet_size in final_data[distance_thresh][ncav]:
                total_durations = final_data[distance_thresh][ncav][packet_size]
                x_sorted_feature_size = [ele for ele in total_durations.keys()]
                x_sorted_feature_size.sort()
                y_ratios = [mean_confidence_interval(total_durations[ele]) for ele in x_sorted_feature_size]
                plot_data[ncav].append((x_sorted_feature_size, y_ratios, f"pl_size={format(packet_size, '.0e')}"))
        for ncav in plot_data:
            plt.figure()
            plt.xscale("log")
            iterator = get_next_line()
            multiline_data = plot_data[ncav]
            x_ticks = {}
            for i, (xs, ys, label) in enumerate(multiline_data):
                if len(xs) == 1:
                        continue
                marker, ls, color = next(iterator)
                for temp in xs:
                    if temp not in x_ticks:
                        x_ticks[temp] = 1
                marker, ls, color = next(iterator)
                yerr = [ele[1] for ele in ys]
                yss = [ele[0] for ele in ys]
                plt.plot(xs, yss, label=label, linestyle= ls, color=color, marker=marker)
                plt.errorbar(xs, yss, yerr=yerr, color=color, ls='none', capsize=10)
            
            plt.xlabel("Feature Size")
            plt.ylabel("Received Packet Rate")
            plt.legend()
            plt.xticks(sorted(list(x_ticks.keys())))
            plt.tight_layout()
            this_figure_path = os.path.join(this_distance_path, f"fs_{ncav}.pdf")
            plt.savefig(this_figure_path, format="pdf", dpi = 400.)
            plt.cla()
            plt.clf()
            plt.close('all')

def _parse_time_stamps(path:str, in_order = True) -> list:
    stamps = []
    for filename in os.listdir(path):
        if filename.endswith(".pcd"):
            stamps.append(filename.split(".")[0])
    if in_order:
        stamps.sort()
    return stamps

def _process_payload(payloads):
    new_payloads = {}
    for key in payloads:
        old_payload = payloads[key]
        new_payload = [[ele[1][:3]] for ele in old_payload] # remove roll pitch yaw
        new_payloads[key] = new_payload
    each_payload_size = [len(new_payloads[key]) for key in new_payloads]
    if min(each_payload_size) != max(each_payload_size):
        select = min(each_payload_size)
        new_payloads = {key:new_payloads[key][:select] for key in new_payloads}
    return new_payloads

def _read_payloads_waypoints(root):
    payloads = {}
    time_stamps = {}
    for sub_dir_name in os.listdir(root):
        sub_dir_path = os.path.join(root, sub_dir_name)
        if os.path.isdir(sub_dir_path):
            stamps = _parse_time_stamps(sub_dir_path)
            time_stamps[sub_dir_name] = stamps
            waypoints_json_path = os.path.join(sub_dir_path, sub_dir_name+".json")
            with open(waypoints_json_path, "r") as fp:
                waypoints_json = json.load(fp)
            payloads[sub_dir_name] = waypoints_json

    payloads = _process_payload(payloads)

    return payloads, stamps

def _get_avg_distance(waypoints):
    cav_nums = list(waypoints.keys())
    cav_waypoints = np.asarray([waypoints[cav_num] for cav_num in cav_nums])
    n_cav = cav_waypoints.shape[0]
    cav_waypoints = np.squeeze(cav_waypoints, axis=2)
    cav_waypoints = np.swapaxes(cav_waypoints, 0, 1)
    centers = np.average(cav_waypoints, axis=1)
    centers = np.expand_dims(centers, axis=1)

    distance = np.linalg.norm(cav_waypoints-centers, axis=-1)
    distance = np.average(distance, axis=-1)
    return distance.tolist()

def get_average_distance_scenario_dataset(root, dataset_folder):
    dataset_folder_path = os.path.join(root, dataset_folder)
    result = {}
    for scenario_folder_name in os.listdir(dataset_folder_path):
        scenario_folder_path = os.path.join(dataset_folder_path, scenario_folder_name)
        if os.path.isdir(scenario_folder_path):
            payloads, stamps = _read_payloads_waypoints(scenario_folder_path)
            distance = _get_avg_distance(payloads)
            result[scenario_folder_name] = distance
    return result

def flatten_dict(data):
    result = []
    for key in data:
        result.extend(data[key])
    return result

def get_next_line(bar_plot = False):
    markers = ["o", "v", "^", "<", ">", "1", "2", "3" , "4", "s", "P", "*"]
    patterns = [ "/" , "\\"  , "-" , "+" , "x", "o", "O", ".", "*" ]
    line_styles = ["solid", "dotted", "dashed", "dashdot"]
    colors = ["k", "b", "r"]
    if not bar_plot:
        style_iter = list(product(markers, line_styles))
        random.shuffle(style_iter)
        for i, (marker, ls) in enumerate(style_iter):
            yield marker, ls, colors[i%len(colors)]
    else:
        random.shuffle(patterns)
        for i, hatch in enumerate(patterns):
            yield hatch, colors[i%len(colors)]



if __name__ == "__main__":
    train_root = "/home/cps-tingcong/Downloads/opencood_train/"
    valid_root = "/home/cps-tingcong/Downloads/opencood_validate/"
    test_root = "/home/cps-tingcong/Downloads/opencood_test"
    # iterator = get_next_line()
    # plt.figure()
    # x = list(range(4))
    # for i, (marker, ls, color) in enumerate(iterator):
    #     plt.plot(x, [i]*len(x), linestyle= ls, color=color, marker=marker)
    # plt.show()
    # plot_set_1(train_root, dataset_folder = 'train/', cav_select='mean', distances=[50])
    # plot_set_1(valid_root, dataset_folder = 'validate/', cav_select='mean', distances=[50])
    # plot_set_1(test_root, dataset_folder = 'test/', cav_select='mean')

    # plot_set2(train_root, dataset_folder = 'train/', distances=[50])
    # plot_set2(valid_root, dataset_folder = 'validate/',  distances=[50])
    # plot_set2(test_root, dataset_folder = 'test/', )

    # plot_set3(train_root, dataset_folder = 'train/', distances=[50])
    # plot_set3(valid_root, dataset_folder = 'validate/',  distances=[50])
    # plot_set3(test_root, dataset_folder = 'test/', )
    feature_size_select = [5e05, 1e05, 5e04, 1e04, 5e03, 1e03]
    # plot_set_4(train_root, dataset_folder = 'train/', distances=[50], feature_size_select=feature_size_select)
    # plot_set_4(valid_root, dataset_folder = 'validate/',  distances=[50])
    # plot_set_4(test_root, dataset_folder = 'test/', )

    
    # plot_set_5(train_root, dataset_folder = 'train/', distances=[50], feature_size_select=feature_size_select)
    # plot_set_5(valid_root, dataset_folder = 'validate/',  distances=[50])
    # plot_set_5(test_root, dataset_folder = 'test/', )

    plot_set_6(train_root, dataset_folder = 'train/', cav_select='mean', distances=[50])
    # plot_set_6(valid_root, dataset_folder = 'validate/', cav_select='mean', distances=[50])
    # plot_set_6(test_root, dataset_folder = 'test/', cav_select='mean')
    # distances = get_average_distance_scenario_dataset(test_root, dataset_folder)
    # distances = flatten_dict(distances)
    # plt.hist(distances, bins=10)
    # plt.show()

