import json
import os
import numpy as np



def read_data(filepath):
    """
    A util function to load json file.

    Parameters
        ----------
        filepath : str
            Path to the json file.

        Returns
        -------
        data : dict
            loaded data from the file specified by the given filepath.
    """
    with open(filepath, 'r') as fp:
        data = json.load(fp)
    return data

def parse_params_from_path(folder_path):
    """
    A util function to parse the simulation config from the folder name.

    Parameters
        ----------
        folder_path : str
            Path to the config folder.

        Returns
        -------
        feature_size : float
            The size of shared feature from each CAV.
        packet_size  : float
            The size of payload in each individual packets.
        max_time     : float
            The scheduled delay between two TX of packets.
    """
    folder_name = os.path.basename(folder_path)
    feature_size, packet_size, max_time = folder_name.split('_')
    feature_size = float(feature_size)
    packet_size = float(packet_size)
    max_time = float(max_time)
    return feature_size, packet_size, max_time

def mask_from_received_packet_num(received_packet_num, feature_size, payload_size):
    """
    Given the packet numbers of received packets, feature size, and payload size, return 
    correpsonding masks.

    Parameters
        ----------
        received_packet_num : dict
            A dictionary with key equals peer CAV numbers and values of the packet numbers
            of received packets from that peer.

        Returns
        -------
        masks : dict
            A dictionary with key equals peer CAV numbers and values of the generated boolean masks.
    """
    masks = {}
    
    for peer_num in received_packet_num:
        feature_mask = np.zeros(feature_size)
        for packet_num in received_packet_num[peer_num]:
            start_index = payload_size*(packet_num)
            last_index = payload_size*(packet_num+1)
            if last_index > feature_size:
                last_index = None
            feature_mask[start_index:last_index] = 1.
        masks[peer_num] = feature_mask
    
    return masks

def generate_mask(sub_folder_path):
    """
    Given the folder path to config folders, return the generated masks.

    Parameters
        ----------
        sub_folder_path : str
            The path to config folders. (e.g., 1e+02_1e+02_1e-01).

        Returns
        -------
        mask_by_scenario : dict
            A nasted dictionary with keys of name of scenarios folders, time stamp, ego CAV number, and peer CAV number.
            The values are duration and masks. 
            e.g., 
            from generate_masks import generate_mask
            loaded_mask = generate_mask(comm_sim_folder_name)
            duration, mask = loaded_mask[scenario_folder_name][time_stamp][ego_CAV_Number][peer_CAV_Number]
    """
    filename = "comm_sim.json"
    mask_by_scenario = {}
    if os.path.isdir(sub_folder_path):
        feature_size, packet_size, max_time = parse_params_from_path(sub_folder_path)
        for scenario_folder_name in os.listdir(sub_folder_path):
            scenario_folder_path = os.path.join(sub_folder_path, scenario_folder_name)
            if os.path.isdir(scenario_folder_path):
                mask_by_scenario[scenario_folder_name] = {}
                filepath = os.path.join(scenario_folder_path, filename)
                data = read_data(filepath)
                for time_stamp in data:
                    mask_by_scenario[scenario_folder_name][time_stamp] = {}
                    
                    for cav in data[time_stamp]:
                        min_time, max_time = None, None
                        sent_times = [float(time[0]) for time in data[time_stamp][cav]['sent']]
                        receive_times = []
                        received_packet_num = {}
                        for peer_num in data[time_stamp][cav]['receive']:
                            received_packet_num[peer_num] = []
                            for time, packet_num in data[time_stamp][cav]['receive'][peer_num]:
                                receive_times.append(float(time))
                                received_packet_num[peer_num].append(int(packet_num))
                        masks = mask_from_received_packet_num(received_packet_num, int(feature_size), int(packet_size))
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
                            duration = max_time - min_time
                        else:
                            duration = None
                        mask_by_scenario[scenario_folder_name][time_stamp][cav] = (duration, masks)
    return mask_by_scenario

