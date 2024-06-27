from ns import ns
# cppyy.include('/home/cps-tingcong/Desktop/ns-allinone-3.38/ns-3.38/src/aqua-sim-ng/examples/broadcastMAC_example.cc')
'''
params
'''
# print(vars(ns).keys())
nNodes = 5
m_dataRate = 128
m_packetSize = 40
simStop = 100.
# ns.cppyy.set_debug(True)

print("Creating Channel and Topology Helpers")
nodes = ns.network.NodeContainer()
nodes.Create(nNodes)
sinkNode = ns.network.NodeContainer()
# sinkNode.Create(1)

socketHelper = ns.network.PacketSocketHelper()
socketHelper.Install(nodes)
# socketHelper.Install(sinkNode)

channel = ns.aqua_sim_ng.AquaSimChannelHelper.Default()
channel.SetPropagation("ns3::AquaSimRangePropagation")
# channel.SetNoiseGenerator("ns3::AquaSimNoiseGen")
asHelper = ns.aqua_sim_ng.AquaSimHelper.Default()
asHelper.SetChannel(channel.Create())
asHelper.SetMac("ns3::AquaSimBroadcastMac")
asHelper.SetRouting("ns3::AquaSimRoutingDummy")

print("Creating containers")
devices = ns.network.NetDeviceContainer()
position = ns.core.CreateObject("ListPositionAllocator")
mobility = ns.mobility.MobilityHelper()
boundry = ns.core.Vector(0,0,0)


print("Generating random locations")
for i in range(nNodes):
    node = nodes.Get(i)
    print(f"Node {i} has m_id = {node.GetId()}")
    newDevice = ns.aqua_sim_ng.AquaSimNetDevice.CreateAquaSimNetDevice()
    position.Add(boundry)
    devices.Add(asHelper.Create(node, newDevice))
    boundry.x+=100
    boundry.y+=25
    boundry.z+=10

# newDevice = ns.aqua_sim_ng.AquaSimNetDevice.CreateAquaSimNetDevice()
# position.Add(boundry)
# devices.Add(asHelper.Create(sinkNode.Get(0), newDevice))

print("Installing locations")
mobility.SetPositionAllocator(position)
mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel")
mobility.Install(nodes)
# mobility.Install(sinkNode)


# print("Creating Socket Address")
socket = ns.network.PacketSocketAddress()
socket.SetAllDevices()
socket.SetPhysicalAddress(ns.aqua_sim_ng.AquaSimAddress.GetBroadcast().ToAddress())
socket.SetProtocol(0)

print("Setting up apps")
app = ns.applications.UdpBroadcastHelper(socket.ConvertTo())
for i in range(nNodes):
    buffer = f"This is message from node {i}, and testing."
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

print("Installing up apps")
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


# sinkSocket = ns.network.Socket.CreateSocket(sinkNodeInstance, psfid)
# sinkSocket.Bind(socket.ConvertTo())
# sinkSocket.SetRecvCallback(ns.core.MakeCallback(CallBackMethod));

ns.core.Simulator.Stop(ns.core.Seconds(simStop))
print("Start to run exp")
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
print(parsed_result)

# def parseResult(pre_result):
#     map_dict = {}
#     for key in pre_result:
#         map_dict[key] = {}
#         std_map = 

# cppyy.gbl.main()
