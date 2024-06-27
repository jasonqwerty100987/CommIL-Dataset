# import os
# os.system('cmd /k "./ns3 shell"')



# ns.core.LogComponentEnable("UdpEchoClientApplication", ns.core.LOG_LEVEL_INFO)
# ns.core.LogComponentEnable("UdpEchoServerApplication", ns.core.LOG_LEVEL_INFO)
from ns import ns


SUPPORTED_DELAY_MODEL = {"ConstantSpeedDelay":"ns3::ConstantSpeedPropagationDelayModel", "RandomDelay":"ns3::RandomPropagationDelayModel"}

SUPPORTED_DELAY_LOSS = {"Friis":"ns3::FriisPropagationLossModel", "Cost231":"ns3::Cost231PropagationLossModel",\
                        "Fixed":"ns3::FixedRssLossModel", "ItuR1238":"ns3::ItuR1238PropagationLossModel",\
                        "ItuR1411":"ns3::ItuR1411LosPropagationLossModel","ItuR1411N":"ns3::ItuR1411NlosOverRooftopPropagationLossModel",\
                        "Jakes":"ns3::JakesPropagationLossModel", "Kun2600Mhz":"ns3::Kun2600MhzPropagationLossModel",\
                        "LogDistance":"ns3::LogDistancePropagationLossModel", "Matrix":"ns3::MatrixPropagationLossModel",\
                        "Nakagami":"ns3::NakagamiPropagationLossModel", "Okumura":"ns3::OkumuraHataPropagationLossModel",\
                        "Random":"ns3::RandomPropagationLossModel", "Range":"ns3::RangePropagationLossModel",\
                        "ThreeLogDistance":"ns3::ThreeLogDistancePropagationLossModel","TwoRayGround":"ns3::TwoRayGroundPropagationLossModel",\
                        "HybridBuildings":"ns3::HybridBuildingsPropagationLossModel","OhBuildings":"ns3::OhBuildingsPropagationLossModel"}

SUPPORTED_DATA_TYPE = {"Address":ns.core.AddressValue, "Boolean":ns.core.BooleanValue, "Box":ns.core.BoxValue, "Callback":ns.core.CallbackValue,\
                       "DataRate":ns.core.DataRateValue, "IeMeshId":ns.core.IeMeshIdValue, "Double":ns.core.DoubleValue,\
                        "Empty":ns.core.EmptyAttributeValue, "Enum":ns.core.EnumValue, "ErpInformation":ns.core.ErpInformationValue,\
                        "HtCapabilities":ns.core.HtCapabilitiesValue, "HtOperations":ns.core.HtOperationsValue, "Integer":ns.core.IntegerValue,\
                        "Ipv4Address":ns.core.Ipv4AddressValue, "Ipv4Mask":ns.core.Ipv4MaskValue, "Ipv6Address":ns.core.Ipv6AddressValue,\
                        "Ipv6Prefix":ns.core.Ipv6PrefixValue, "Mac16Address":ns.core.Mac16AddressValue, "Mac48Address":ns.core.Mac48AddressValue,\
                        "Mac64Address":ns.core.Mac64AddressValue, "ObjectFactory":ns.core.ObjectFactoryValue, "ObjectPtrContainer":ns.core.ObjectPtrContainerValue,\
                        "OrganizationIdentifier":ns.core.OrganizationIdentifierValue, "Pointer":ns.core.PointerValue, "Rectangle":ns.core.RectangleValue,\
                        "Ssid":ns.core.SsidValue, "String":ns.core.StringValue, "Time":ns.core.TimeValue, "TypeId":ns.core.TypeIdValue,\
                        "UanModesList":ns.core.UanModesListValue, "Uinteger":ns.core.UintegerValue, "Vector2D":ns.core.Vector2DValue, "Vector3D":ns.core.Vector3DValue,\
                        "VhtCapabilities":ns.core.VhtCapabilitiesValue, "Waypoint":ns.core.WaypointValue, "WifiMode":ns.core.WifiModeValue,\
                        "ValueClassTest":ns.core.ValueClassTestValue}

def _parse_propagation_delay(model:str)->str:
    '''
    \param str model: the string representation of propagation delay.

    return str: the string representation of the propation delay in ns3.
    '''
    if model not in SUPPORTED_DELAY_MODEL:
        raise ValueError(f"Currently only support {', '.join(SUPPORTED_DELAY_MODEL.keys())} models, but {model} is given.")
    return SUPPORTED_DELAY_MODEL[model]

def _parse_propagation_loss(loss:str, para:dict)->str:
    '''
    \param str loss: the string representation of propagation loss.
           dict para: the parameters used to construct the parameters. The key is data type, value is a tuple. The first element is parameter name, the second element is parameter value. (name, value)

    return str: the string representation of the propation loss in ns3.
    '''
    if loss not in SUPPORTED_DELAY_LOSS:
        raise ValueError(f"Currently only support {', '.join(SUPPORTED_DELAY_LOSS.keys())} losses, but {loss} is given.")
    return SUPPORTED_DELAY_LOSS[loss], _parse_parameter(para)

def _parse_parameter(para:dict)->list:
    final_para = []

    for data_type in para:
        if data_type not in SUPPORTED_DATA_TYPE:
            raise ValueError(f"Unsupported data type, supported data types are {', '.join(SUPPORTED_DATA_TYPE.keys())}. But, {data_type} is given.")

        for para_name, para_value in para[data_type]:
            para_value = SUPPORTED_DATA_TYPE[data_type](para_value)
            final_para.extend((para_name, para_value))
    
    return final_para

def exp_method(nNodes = 5,
    simStop = 100.,
    payloads = ["Data 1","Data 2","Data 3","Data 4","Data 5"],
    locations = [],
    debug = False,
    propagation_delay = "ConstantSpeedDelay"):
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

    # Create drone nodes
    nodes = ns.network.NodeContainer()
    nodes.Create(nNodes)

    wifi = ns.wifi.WifiHelper()
    wifi.SetStandard(ns.wifi.WifiStandard.WIFI_STANDARD_80211b)
    
    mac = ns.wifi.WifiMacHelper()
    mac.SetType("ns3::AdhocWifiMac")

    wifi.SetRemoteStationManager("ns3::ConstantRateWifiManager",
                                "DataMode", ns.core.StringValue("OfdmRate54Mbps"))
    
    wifiPhy = ns.wifi.YansWifiPhyHelper()
    wifiChannel = ns.wifi.YansWifiChannelHelper()
    wifiChannel.SetPropagationDelay (_parse_propagation_delay(propagation_delay))
    wifiChannel.AddPropagationLoss ("ns3::FriisPropagationLossModel", "Frequency", ns.core.DoubleValue(2412000000.0))
    wifiPhy.SetChannel(wifiChannel.Create())
    cDevices = wifi.Install(wifiPhy, mac, nodes)

    # Reading Tx Parameters
    if debug:
        for i in range(nNodes):
            device = cDevices.Get(i)
            tempPHY = device.GetPhy()
            tempChannel = device.GetChannel()
            tempLoss = tempChannel.GetPropagationLoss()
            lossFrequency = tempLoss.GetFrequency()
            TxPWR = tempPHY.GetTxGain()
            minTxPWR = tempPHY.GetTxPowerStart()
            maxTxPWR = tempPHY.GetTxPowerEnd()
            phyFrequency = tempPHY.GetFrequency()
            print(f"For node {i}, the transmission power gain is {TxPWR}. Min power is {minTxPWR}, max power is {maxTxPWR}, Loss Frequency is {lossFrequency}, Phy Frequency is {phyFrequency}.")


    aodv = ns.aodv.AodvHelper()
    internet = ns.internet.InternetStackHelper()
    internet.SetRoutingHelper(aodv)
    internet.Install (nodes)

    ipAddrs = ns.internet.Ipv4AddressHelper()
    ipAddrs.SetBase("192.168.0.0", "255.255.255.0")
    cInterfaces=ipAddrs.Assign(cDevices)

    # mobility = ns.mobility.MobilityHelper()
    # mobility.SetMobilityModel("ns3::GaussMarkovMobilityModel",
    #     "Bounds", ns.core.BoxValue(ns.mobility.Box(0, 100, 0, 100, 0, 100)),
    #     "TimeStep", ns.core.TimeValue(ns.core.Seconds(0.5)),
    #     "Alpha", ns.core.DoubleValue(0.85),
    #     "MeanVelocity", ns.core.StringValue("ns3::UniformRandomVariable[Min=10|Max=20]"),
    #     "MeanDirection", ns.core.StringValue("ns3::UniformRandomVariable[Min=0|Max=6.283185307]"),
    #     "MeanPitch", ns.core.StringValue("ns3::UniformRandomVariable[Min=0.05|Max=0.05]"),
    #     "NormalVelocity", ns.core.StringValue("ns3::NormalRandomVariable[Mean=0.0|Variance=0.0|Bound=0.0]"),
    #     "NormalDirection", ns.core.StringValue("ns3::NormalRandomVariable[Mean=0.0|Variance=0.2|Bound=0.4]"),
    #     "NormalPitch", ns.core.StringValue("ns3::NormalRandomVariable[Mean=0.0|Variance=0.02|Bound=0.04]"))
    # mobility.SetPositionAllocator("ns3::RandomBoxPositionAllocator",
    #     "X", ns.core.StringValue("ns3::UniformRandomVariable[Min=0|Max=100]"),
    #     "Y", ns.core.StringValue("ns3::UniformRandomVariable[Min=0|Max=100]"),
    #     "Z", ns.core.StringValue("ns3::UniformRandomVariable[Min=0|Max=100]"))
    # mobility.Install (nodes)

    # echoServer = ns.applications.UdpEchoServerHelper(9)
    # serverApps = echoServer.Install(nodes.Get(0))
    # serverApps.Start(ns.core.Seconds(1.0))
    # serverApps.Stop(ns.core.Seconds(10.0))

    # echoClient = ns.applications.UdpEchoClientHelper(cInterfaces.GetAddress(0).ConvertTo(), 9)
    # echoClient.SetAttribute ("MaxPackets", ns.core.UintegerValue(1))
    # echoClient.SetAttribute ("Interval", ns.core.TimeValue(ns.core.Seconds(1.0)))
    # echoClient.SetAttribute ("PacketSize", ns.core.UintegerValue(1024))

    # clientApps = echoClient.Install(nodes.Get(1))
    # clientApps.Start(ns.core.Seconds(2.0))
    # clientApps.Stop(ns.core.Seconds(10.0))
    # socketHelper = ns.network.PacketSocketHelper()
    # socketHelper.Install(nodes)

    # channel = ns.aqua_sim_ng.AquaSimChannelHelper.Default()
    # channel.SetPropagation("ns3::AquaSimRangePropagation")
    # # channel.SetNoiseGenerator("ns3::AquaSimNoiseGen")
    # asHelper = ns.aqua_sim_ng.AquaSimHelper.Default()
    # asHelper.SetChannel(channel.Create())
    # asHelper.SetMac("ns3::AquaSimBroadcastMac")
    # asHelper.SetRouting("ns3::AquaSimRoutingDummy")

    # # print("Creating containers")
    # devices = ns.network.NetDeviceContainer()
    position = ns.core.CreateObject("ListPositionAllocator")
    mobility = ns.mobility.MobilityHelper()
    # # boundries = []
    # # for (x,y,z) in locations:
    # #     # print(x,y,z)
    # #     boundries.append(ns.core.Vector(x,y,z))
    boundry = ns.core.Vector(0,0,0)


    # # # print("Generating random locations")
    for i, (x,y,z) in zip(range(nNodes), locations):
        boundry.x=x
        boundry.y=y
        boundry.z=z
        # print(boundry)
        # node = nodes.Get(i)
        # # print(f"Node {i} has m_id = {node.GetId()}")
        # newDevice = ns.aqua_sim_ng.AquaSimNetDevice.CreateAquaSimNetDevice()
        position.Add(boundry)
        # devices.Add(asHelper.Create(node, newDevice))
        
    
    # # for i, boundry in zip(range(nNodes), boundries):
    # #     # print(boundry)
    # #     node = nodes.Get(i)
    # #     # print(f"Node {i} has m_id = {node.GetId()}")
    # #     newDevice = ns.aqua_sim_ng.AquaSimNetDevice.CreateAquaSimNetDevice()
    # #     position.Add(boundry)
    # #     devices.Add(asHelper.Create(node, newDevice))
    # #     # boundry.x+=100
    # #     # boundry.y+=25
    # #     # boundry.z+=10

    mobility.SetPositionAllocator(position)
    mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel")
    mobility.Install(nodes)

    # socket = ns.network.PacketSocketAddress()
    # socket.SetAllDevices()
    # socket.SetPhysicalAddress(ns.network.Ipv4Address.GetBroadcast().ConvertTo())
    # socket.SetProtocol(0)
    m_peerPort = 100
    remote_address = ns.network.InetSocketAddress(ns.network.Ipv4Address.GetBroadcast(), m_peerPort)
    app = ns.applications.UdpBroadcastHelper(remote_address.ConvertTo())
    for i, payload in enumerate(payloads):
        buffer = f"This is message from node {i}; " + payload
        # payload_size = str(len(buffer))
        # if len(payload_size) > 10:
        #     print("Payload too large")
        #     quit()
        # while len(payload_size) < 10:
        #     payload_size = "0" + payload_size
        
        # assert len(payload_size) == 10 
        # buffer += payload_size
        app.SetData(buffer)
    # # psfid = ns.core.TypeId.LookupByName ("ns3::PacketSocketFactory")
    # # app.SetAttribute("Protocol", ns.core.TypeIdValue(psfid))

    # # print("Installing up apps")
    app.SetAttribute("TotalAttempt", ns.core.UintegerValue(2))
    app.SetAttribute("SendRate", ns.core.DoubleValue(2.0))
    app.SetAttribute("Port", ns.core.UintegerValue(m_peerPort))
    apps = app.Install(nodes)
    apps.Start(ns.core.Seconds(0.5))
    apps.Stop(ns.core.Seconds(simStop-1))

    # # sinkNodeInstance = sinkNode.Get(0)



    # # CallBackMethod(Ptr<Socket> receivedData){
    # #         size = 0
    # #         Ptr<Packet> packet = receivedData.Recv();
    # #         while(packet){
    # #                 size += packet->GetSize();
    # #         }
    # #         std::cout << "Received " << size << " bytes of data." << std::endl; 
    # # }
    for i in range(nNodes):
        # print(boundry)
        node = nodes.Get(i)
        mob = node.GetObject["MobilityModel"]()
        pos_vector=mob.GetPosition()
        print(pos_vector.x, pos_vector.y, pos_vector.z)
    # # sinkSocket = ns.network.Socket.CreateSocket(sinkNodeInstance, psfid)
    # # sinkSocket.Bind(socket.ConvertTo())
    # # sinkSocket.SetRecvCallback(ns.core.MakeCallback(CallBackMethod));

    wifiPhy.EnablePcapAll("Fanet3D")
    anim = ns.netanim.AnimationInterface("Fanet3D.xml")
    traceHelper = ns.network.AsciiTraceHelper()
    wifiPhy.EnableAsciiAll(traceHelper.CreateFileStream("Fanet3D.tr"))
    ns.core.Simulator.Stop(ns.core.Seconds(simStop))
    # print("Start to run exp")
    ns.core.Simulator.Run()
    # ns.core.Simulator.Destroy()
    result = {}
    for i in range(nNodes):
        app = apps.Get(i)
        result.update(dict(app.GetResult()))
    ns.core.Simulator.Destroy()
    parsed_result = {}
    for key in result:
        temp_list = list(result[key])
        print(temp_list)
        temp_list = [ele.decode(encoding="ascii") for ele in temp_list]
        parsed_result[key] = temp_list
    # return parsed_result
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
    locations = [(0,10,0),(0,0,0), (0,30,0), (0,60,0), (0,100,0)]
    print(main(nNodes=size, payloads=payloads, locations=locations, simStop=10))
