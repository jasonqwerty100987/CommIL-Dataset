# import os
# os.system('cmd /k "./ns3 shell"')



# ns.core.LogComponentEnable("UdpEchoClientApplication", ns.core.LOG_LEVEL_INFO)
# ns.core.LogComponentEnable("UdpEchoServerApplication", ns.core.LOG_LEVEL_INFO)
from ns import ns

def exp_method(nNodes = 5,
    simStop = 100.,
    payloads = ["Data 1","Data 2","Data 3","Data 4","Data 5"],
    locations = []):
    '''
    This is the method that construct scenarios based on given arguments, and return the information of interest.
    \param int nNodes: nNodes decides how many node will be created in the simulation. 
           float simStop: simStop decides the max time that the simulator will simulate the experiment. Unit in seconds.
           list payloads: paylodas is a list of strings. The strings will be sent to other node. The length of payloads should be the same as the nNodes.
           list locations:  locations is a list of 3 floating point tuple (x,y,z). The x, y, and z defines the locations of the created nodes, 
                            the assignment of the (x,y,z) tuples will be in the same order of their appearance in the location list.
    return dict: A dictionary with node ids as keys and their recieved message as values.
    '''
    assert len(payloads) == nNodes and len(payloads) == len(locations)

    # ns.cppyy.set_debug(True)

    # print("Creating Channel and Topology Helpers")
    nodes = ns.network.NodeContainer()
    nodes.Create(nNodes)

    socketHelper = ns.network.PacketSocketHelper()
    socketHelper.Install(nodes)

    channel = ns.aqua_sim_ng.AquaSimChannelHelper.Default()
    channel.SetPropagation("ns3::AquaSimRangePropagation")
    # channel.SetNoiseGenerator("ns3::AquaSimNoiseGen")
    asHelper = ns.aqua_sim_ng.AquaSimHelper.Default()
    asHelper.SetChannel(channel.Create())
    asHelper.SetMac("ns3::AquaSimBroadcastMac")
    asHelper.SetRouting("ns3::AquaSimRoutingDummy")

    # print("Creating containers")
    devices = ns.network.NetDeviceContainer()
    position = ns.core.CreateObject("ListPositionAllocator")
    mobility = ns.mobility.MobilityHelper()
    # boundries = []
    # for (x,y,z) in locations:
    #     # print(x,y,z)
    #     boundries.append(ns.core.Vector(x,y,z))
    boundry = ns.core.Vector(0,0,0)


    # # print("Generating random locations")
    for i, (x,y,z) in zip(range(nNodes), locations):
        boundry.x+=x
        boundry.y+=y
        boundry.z+=z
        # print(boundry)
        node = nodes.Get(i)
        # print(f"Node {i} has m_id = {node.GetId()}")
        newDevice = ns.aqua_sim_ng.AquaSimNetDevice.CreateAquaSimNetDevice()
        position.Add(boundry)
        devices.Add(asHelper.Create(node, newDevice))
        
    
    # for i, boundry in zip(range(nNodes), boundries):
    #     # print(boundry)
    #     node = nodes.Get(i)
    #     # print(f"Node {i} has m_id = {node.GetId()}")
    #     newDevice = ns.aqua_sim_ng.AquaSimNetDevice.CreateAquaSimNetDevice()
    #     position.Add(boundry)
    #     devices.Add(asHelper.Create(node, newDevice))
    #     # boundry.x+=100
    #     # boundry.y+=25
    #     # boundry.z+=10

    mobility.SetPositionAllocator(position)
    mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel")
    mobility.Install(nodes)

    socket = ns.network.PacketSocketAddress()
    socket.SetAllDevices()
    socket.SetPhysicalAddress(ns.aqua_sim_ng.AquaSimAddress.GetBroadcast().ToAddress())
    socket.SetProtocol(0)

    app = ns.applications.UdpBroadcastHelper(socket.ConvertTo())
    for i, payload in enumerate(payloads):
        buffer = f"This is message from node {i}; " + payload
        payload_size = str(len(buffer))
        if len(payload_size) > 10:
            print("Payload too large")
            quit()
        while len(payload_size) < 10:
            payload_size = "0" + payload_size
        
        assert len(payload_size) == 10 
        buffer += payload_size
        app.SetData(buffer)
    psfid = ns.core.TypeId.LookupByName ("ns3::PacketSocketFactory")
    app.SetAttribute("Protocol", ns.core.TypeIdValue(psfid))

    # print("Installing up apps")
    apps = app.Install(nodes)
    apps.Start(ns.core.Seconds(0.5))
    apps.Stop(ns.core.Seconds(simStop-1))

    # sinkNodeInstance = sinkNode.Get(0)



    # CallBackMethod(Ptr<Socket> receivedData){
    #         size = 0
    #         Ptr<Packet> packet = receivedData.Recv();
    #         while(packet){
    #                 size += packet->GetSize();
    #         }
    #         std::cout << "Received " << size << " bytes of data." << std::endl; 
    # }
    for i in range(nNodes):
        # print(boundry)
        node = nodes.Get(i)
        mob = node.GetObject["MobilityModel"]()
        pos_vector=mob.GetPosition()
        # print(pos_vector.x, pos_vector.y, pos_vector.z)
    # sinkSocket = ns.network.Socket.CreateSocket(sinkNodeInstance, psfid)
    # sinkSocket.Bind(socket.ConvertTo())
    # sinkSocket.SetRecvCallback(ns.core.MakeCallback(CallBackMethod));

    ns.core.Simulator.Stop(ns.core.Seconds(simStop))
    # print("Start to run exp")
    ns.core.Simulator.Run()
    result = {}
    for i in range(nNodes):
        device = devices.Get(i)
        result.update(dict(device.GetResult()))
    ns.core.Simulator.Destroy()
    parsed_result = {}
    for key in result:
        temp_list = list(result[key])
        temp_list = [ele.decode(encoding="ascii") for ele in temp_list]
        parsed_result[key] = temp_list
    return parsed_result

def main(**kwargs):
    while True:
        option = input("C to continue, Q to exit").upper()
        if option=="C":
            print(exp_method(**kwargs))
        elif option == "Q":
            break

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
    # for key in keys:
    #     result[key] = []
    #     for row in rows:
    #         for i in select_index:
    #             result[key].append(row[i])
    if toString:
        result = [json.dumps(ele) for ele in result]
    return result

if __name__ == "__main__":
    import pprint
    payloads = reading_dummy_data('/home/cps-tingcong/Downloads/concentration.csv')
    size = len(payloads)
    # print(size)
    locations = [(5,5,0),(100,10,10), (100,25,10), (100,25,10), (100,25,10)]
    print(main(nNodes=size, payloads=payloads, locations=locations, simStop=2000))
