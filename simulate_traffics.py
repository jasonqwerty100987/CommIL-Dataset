import os
import json
import tqdm

DELTA_TIME = 0.05 # The time difference in second between two adjacent time stamp





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

def _process_payload(payloads):
    new_payloads = {}
    for key in payloads:
        old_payload = payloads[key]
        new_payload = [[ele[0], ele[1][:3]] for ele in old_payload] # remove roll pitch yaw
        new_payloads[key] = new_payload
    return new_payloads

def _create_payloads_config(total_size, packet_size, maxtime, n_nodes):
    assert total_size%packet_size == 0
    total_attempt = int(total_size/packet_size) # The number of packets needed to carry the full payloads
    rate = total_attempt/maxtime # The rate of transmission
    payload = "0"*int(packet_size) # The dummy payload
    return [payload]*n_nodes, rate, total_attempt


def main(root, total_size, packet_size, maxtime, save_dir):
    from ns import ns
    _run_exp(root, total_size, packet_size, maxtime, save_dir, ns)
    return 1

def _parse_time_stamps(path:str, in_order = True) -> list:
    stamps = []
    for filename in os.listdir(path):
        if filename.endswith(".pcd"):
            stamps.append(filename.split(".")[0])
    if in_order:
        stamps.sort()
    return stamps

def parse_results(original_result:dict, index_to_name):
    parsed_results = {}
    for key in original_result:
        mask = [0 if 'sent' in ele else 1 for ele in original_result[key]]
        name_key = index_to_name[key]
        parsed_results[name_key] = {"sent":[], "receive":{}}
        for m, ele in zip(mask, original_result[key]):
            spilted_result = ele.split(" ")
            time_stamp = spilted_result[0][1:-1]
            packet_num = int(spilted_result[2])
            if m == 0:
                # result for sent
                parsed_results[name_key]["sent"].append((time_stamp, packet_num))
            elif m == 1:
                # result for receive
                # print(spilted_result)
                # quit()
                sender_name = index_to_name[packet_num]
                received_packet_num = int(spilted_result[-1].rstrip('\x00'))
                if sender_name not in parsed_results[name_key]["receive"]:
                    parsed_results[name_key]["receive"][sender_name] = [(time_stamp, received_packet_num)]
                else:
                    parsed_results[name_key]["receive"][sender_name].append((time_stamp, received_packet_num))
    # pprint.pprint(parsed_results)
    return parsed_results

def save_results(folder, result, filename):
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, filename), 'w+') as fp:
        json.dump(result, fp)
    # print(f"Saved result to {os.path.join(folder, filename)}")

def _run_exp(root, total_size, packet_size, maxtime, folder, ns, skip = False):

    filename = "comm_sim.json"
    pbar = tqdm.tqdm(os.listdir(root))
    for sub_dir_name in pbar:
        pbar.set_description(sub_dir_name)
        sub_dir_path = os.path.join(root, sub_dir_name)
        if os.path.isdir(sub_dir_path):
            if skip and os.path.exists(os.path.join(folder, sub_dir_name, filename)):
                continue
            payloads, stamps = _read_payloads_waypoints(sub_dir_path)
            int_stamps = [int(ele) for ele in stamps]
            origin = min(int_stamps)

            nodes_names = list(payloads.keys())
            waypoints = [payloads[nodes_name] for nodes_name in nodes_names]

            nNodes = len(nodes_names)
            index_to_name = {key:value for key, value in zip(range(nNodes), nodes_names)}
            packets, rate, total_attempt = _create_payloads_config(total_size, packet_size, maxtime, nNodes)
            final_result = {}
            for stamp in int_stamps:
                start_time = (stamp - origin)*DELTA_TIME
                result = simulate(nNodes = nNodes, payloads = packets, waypoints = waypoints, rate = rate, total_attempt=total_attempt, start_time = start_time, ns=ns, experiment_title=f"{total_size}_{packet_size}_{stamp}")
                parsed_result = parse_results(result, index_to_name)
                final_result[stamp] = parsed_result

            save_results(os.path.join(folder, sub_dir_name), final_result, filename)


def simulate(nNodes = 5,
    simStop = 100.,
    payloads = ["Data 1","Data 2","Data 3","Data 4","Data 5"],
    phymode = "OfdmRate6MbpsBW10MHz", verbose = False, waypoints=[], rate = 1, total_attempt = 10, start_time = 0., parsing_fn = None, ns=None, experiment_title="Experiement"):
    '''
    This is the method that construct scenarios based on given arguments, and return the information of interest.
    \param int nNodes: nNodes decides how many node will be created in the simulation.
           float simStop: simStop decides the max time that the simulator will simulate the experiment. Unit in seconds.
           list payloads: paylodas is a list of strings. The strings will be sent to other node. The length of payloads should be the same as the nNodes.
           list waypoints:  locations is a list of 3 floating point tuple (x,y,z). The x, y, and z defines the locations of the created nodes,
                            the assignment of the (x,y,z) tuples will be in the same order of their appearance in the location list.
    return dict: A dictionary with node ids as keys and their recieved message as values.
    '''
    assert len(payloads) == nNodes

    SUPPORTED_DATA_TYPE = {"Address":ns.core.AddressValue, "Boolean":ns.core.BooleanValue, "Box":ns.core.BoxValue, "Callback":ns.core.CallbackValue,\
                        "DataRate":ns.core.DataRateValue, "Double":ns.core.DoubleValue,\
                            "Empty":ns.core.EmptyAttributeValue, "Enum":ns.core.EnumValue, \
                            "Integer":ns.core.IntegerValue,\
                            "Ipv4Address":ns.core.Ipv4AddressValue, "Ipv4Mask":ns.core.Ipv4MaskValue, "Ipv6Address":ns.core.Ipv6AddressValue,\
                            "Ipv6Prefix":ns.core.Ipv6PrefixValue, "Mac16Address":ns.core.Mac16AddressValue, "Mac48Address":ns.core.Mac48AddressValue,\
                            "Mac64Address":ns.core.Mac64AddressValue, "ObjectFactory":ns.core.ObjectFactoryValue, "ObjectPtrContainer":ns.core.ObjectPtrContainerValue,\
                            "OrganizationIdentifier":ns.core.OrganizationIdentifierValue, "Pointer":ns.core.PointerValue, "Rectangle":ns.core.RectangleValue,\
                            "Ssid":ns.core.SsidValue, "String":ns.core.StringValue, "Time":ns.core.TimeValue, "TypeId":ns.core.TypeIdValue,\
                            "UanModesList":ns.core.UanModesListValue, "Uinteger":ns.core.UintegerValue, "Vector2DValue":ns.core.Vector2DValue, "Vector3DValue":ns.core.Vector3DValue,\
                            "WaypointValue":ns.core.WaypointValue, "WifiMode":ns.core.WifiModeValue, "Vector3D":ns.core.Vector3D, "Vector2D":ns.core.Vector2D,
                            "Waypoint":ns.mobility.Waypoint, "Seconds":ns.core.Seconds}

    def _install_waypoint_mob(node, waypoints_list:list):
        mobility = ns.mobility.MobilityHelper()
        mobility.SetMobilityModel("ns3::WaypointMobilityModel")
        mobility.Install(node)
        node_mob = node.GetObject["MobilityModel"]()

        for time_stamp, waypoints in waypoints_list:
            waypoint_vector = SUPPORTED_DATA_TYPE['Vector3D'](*waypoints)
            time_stamp = SUPPORTED_DATA_TYPE['Seconds'](time_stamp)
            # print(time_stamp, waypoint_vector)
            waypoint_value = SUPPORTED_DATA_TYPE['Waypoint'](time_stamp, waypoint_vector)
            node_mob.AddWaypoint(waypoint_value)

    # Create nodes
    nodes = ns.network.NodeContainer()
    nodes.Create(nNodes)



    # Create V2V topology
    wifiPhy = ns.wifi.YansWifiPhyHelper()
    wifiChannel = ns.wifi.YansWifiChannelHelper.Default()
    channel = wifiChannel.Create()
    wifiPhy.SetChannel(channel)
    wifiPhy.SetPcapDataLinkType (ns.wifi.YansWifiPhyHelper.DLT_IEEE802_11)
    wifi80211pMac = ns.wave.NqosWaveMacHelper.Default()
    wifi80211p = ns.wave.Wifi80211pHelper.Default()
    if (verbose):
        wifi80211p.EnableLogComponents() # Turn on all Wifi 802.11p logging

    wifi80211p.SetRemoteStationManager("ns3::ConstantRateWifiManager","DataMode", ns.core.StringValue(phymode), "ControlMode", ns.core.StringValue(phymode))
    devices = wifi80211p.Install(wifiPhy, wifi80211pMac, nodes)
    wifiPhy.EnablePcap ("wave-simple-80211p", devices)

    for node_id in range(nNodes):
        _install_waypoint_mob(nodes.Get(node_id), waypoints[node_id])

    internet = ns.internet.InternetStackHelper()
    internet.Install (nodes)

    ipAddrs = ns.internet.Ipv4AddressHelper()
    ipAddrs.SetBase("192.168.0.0", "255.255.255.0")
    cInterfaces=ipAddrs.Assign(devices)

    m_peerPort = 100
    remote_address = ns.network.InetSocketAddress(ns.network.Ipv4Address.GetBroadcast(), m_peerPort)
    app = ns.applications.UdpBroadcastHelper(remote_address.ConvertTo())
    for i, payload in enumerate(payloads):
        string_i = str(i)
        if len(string_i) > len(payload):
            raise ValueError("Payload size is too small.")
        buffer = string_i + " " + payload[len(string_i)+1:]
        assert len(buffer) == len(payload)
        app.SetData(buffer)

    app.SetAttribute("TotalAttempt", ns.core.UintegerValue(total_attempt))
    app.SetAttribute("SendRate", ns.core.DoubleValue(rate))
    app.SetAttribute("Port", ns.core.UintegerValue(m_peerPort))
    apps = app.Install(nodes)
    apps.Start(ns.core.Seconds(start_time))
    apps.Stop(ns.core.Seconds(simStop))

    wifiPhy.EnablePcapAll(experiment_title)

    ns.core.Simulator.Stop(ns.core.Seconds(simStop))
    ns.core.Simulator.Run()
    result = {}
    for i in range(nNodes):
        app = apps.Get(i)
        result.update(dict(app.GetResult()))
    ns.core.Simulator.Destroy()
    parsed_result = {}
    for key in result:
        temp_list = list(result[key])
        temp_list = [ele.decode(encoding="ascii") for ele in temp_list]
        parsed_result[key] = temp_list
    if parsing_fn is not None:
        parsed_result = parsing_fn(parsed_result)
    return parsed_result

def reading_dummy_data(filename, n_row = 5, select_index = [1,2,3,10], toString=True):
    import csv
    import json
    with open(filename, "r") as fp:
        reader = csv.reader(fp)
        header = next(reader)
        rows = []
        for i, row in enumerate(reader):
            if i == n_row:
                break
            rows.append(row)
    result = []
    keys = [header[i].strip() for i in select_index]
    for row in rows:
        result.append({})
        for key, index in zip(keys, select_index):
            result[-1][key] = row[index]
    if toString:
        result = [json.dumps(ele) for ele in result]
    return result

import time
import multiprocessing

class ProcessQueue():
    def __init__(self, max_alive = 8, sleep_time = 10) -> None:
        self.processes = []
        self.jobs = []
        self.max_num_process = max_alive
        self.sleep_time = sleep_time
        self.alive = -1

    def append_job(self, method, args):
        self.jobs.append((method, args))

    def _start_job(self):
        if self.jobs:
            target, args = self.jobs.pop()
            process_instance = multiprocessing.Process(target=target, args=args)
            process_instance.start()
            self.processes.append(process_instance)



    def _monitor(self):
        new_process_list = []
        for process_instance in self.processes:
            if process_instance.is_alive():
                new_process_list.append(process_instance)

        new_process_pids = [ele.pid for ele in new_process_list]
        for process_instance in self.processes:
            process_pid = process_instance.pid
            if process_pid not in new_process_pids:
                process_instance.join()
                process_instance.close()

        self.processes = new_process_list

        while self.jobs and len(new_process_list) < self.max_num_process:
            self._start_job()

        self.alive = len(self.processes)
        print(f"Currently {self.alive} process alive, {len(self.jobs)} jobs remaining", end='\r')
        time.sleep(self.sleep_time)

    def start(self):
        print("started")
        while self.alive != 0:
            self._monitor()





if __name__ == "__main__":
    # Change the following directories to the OPV2V dataset directories
    train_root = "/home/cps-tingcong/Downloads/opencood_train/train"
    test_root = "/home/cps-tingcong/Downloads/opencood_test/test"
    valid_root = "/home/cps-tingcong/Downloads/opencood_validate/validate"

    maxtime = 0.1 # max retry time
    roots = [train_root, test_root, valid_root]

    process_queue = ProcessQueue(max_alive=6, sleep_time=0.1)

    # total_size unit in bytes
    # packet_size unit in bytes
    total_sizes = [6e6, 4e6, 2e6, 1e6, 5e5, 1e5, 5e4, 1e4, 5e3, 1e3, 5e2, 1e2]
    packet_sizes = [1e6, 5e5, 1e5, 5e4, 1e4, 5e3, 1e3, 5e2, 1e2]
    total_sizes = [5e3, 1e3]
    packet_sizes = [1e3]

    for total_size in total_sizes:
        for packet_size in packet_sizes:
            if total_size >= packet_size and total_size%packet_size == 0:
                # Change the following dir to your local save directories
                save_dir_train = f"/home/cps-tingcong/Downloads/opencood_train/comm_sim/{format(total_size, '.0e')}_{format(packet_size, '.0e')}_{format(maxtime, '.0e')}"
                save_dir_test = f"/home/cps-tingcong/Downloads/opencood_test/comm_sim/{format(total_size, '.0e')}_{format(packet_size, '.0e')}_{format(maxtime, '.0e')}"
                save_dir_valid = f"/home/cps-tingcong/Downloads/opencood_validate/comm_sim/{format(total_size, '.0e')}_{format(packet_size, '.0e')}_{format(maxtime, '.0e')}"
                save_roots = [save_dir_train, save_dir_test, save_dir_valid]
                for root, save_dir in zip(roots, save_roots):
                    process_queue.append_job(main, (root, total_size, packet_size, maxtime, save_dir))

    process_queue.start()