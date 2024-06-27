from ns import ns
import cppyy
# cppyy.include('/home/cps-tingcong/Desktop/ns-3-dev-master/src/core/model/callback.h')
import pickle
import math
DEBUG = True

def get_ns3_attributes() -> list:
    attributes = get_attributes(ns)
    return attributes

def get_attributes(obj) -> list:
    attributes = [attr for attr in dir(obj)]
    if DEBUG is True:
        print(f"get_attributes: attributes are {attributes}")
    return attributes

def save_data_to_file(data, filename:str) -> None:
    with open(filename, "wb+") as fp:
        pickle.dump(data, filename)
        if DEBUG is True:
            print(f"save_data_to_file: data {data} is saved to {filename}")

def save_text_to_file(string:str, filename:str, mode:str="w+") -> None:
    with open(filename, mode) as fp:
        fp.write(string)
        if DEBUG is True:
            print(f"save_text_to_file: {string} is saved to {filename}")

def list_to_str(lst:list) -> str:
    string = ""
    for ele in lst:
        string += (str(ele) + "\n")
    if DEBUG is True:
        print(f"list_to_str: list is {lst}. Converted string is {string}")
    return string

def save_ns3_attributes() -> None:
    filename = "ns3_attributes.txt"
    attributes = get_ns3_attributes()
    string = list_to_str(attributes)
    save_text_to_file(string, filename)

def save_ns3_uan_attributes() -> None:
    filename = "ns3_UanTxModeFactory_attributes.txt"
    attributes = get_attributes(ns.UanTxModeFactory)
    string = list_to_str(attributes)
    save_text_to_file(string, filename)

m_bytesTotal = 0


# cppyy.cppdef(r"""bool is_nullptr(auto arg1) { return arg1 == 0; };
# """)
# is_nullptr = cppyy.gbl.is_nullptr
             
def ReceivePacket(socket: "ns3::Ptr<ns3::Socket>") -> "void":
    global m_bytesTotal
    while True:
        packet = socket.Recv(10000, 0)
        if not packet:
            break
        size = packet.GetSize()
        m_bytesTotal+=size
        del packet

class Experiment:
    def __init__(self) -> None:
        pass
    
    @staticmethod
    def CreateMode(m_totalRate:int, m_numRates:int, kass:int, fc:int, upperblock:bool, name:str):
        buf = name + " " + str(kass)
        rate = int(m_totalRate / (m_numRates + 1) * (kass))
        bw = int(kass * m_totalRate / (m_numRates + 1))
        if (upperblock):
            fcmode = int((m_totalRate - bw) / 2 + fc)
        else:
            fcmode = int(((-(float(m_totalRate)) + float(bw)) / 2.0 + float(fc)))
        
        phyrate = m_totalRate
        mode = ns.uan.UanTxModeFactory.CreateMode(ns.uan.UanTxMode.FSK, rate, phyrate, fcmode, bw, 2, buf)
        return mode

    
    
    
    def Run(self, m_numRates:int, fc:int, m_doNode:bool, param:int, m_numNodes:int, m_sifs:ns.core.Time, m_simTime:ns.core.Time, m_maxRange:int, m_pktSize:int, m_totalRate:int):
        m_dataModes = ns.uan.UanModesList()
        m_controlModes = ns.uan.UanModesList()
        if m_doNode:
            a = 0
            nNodes = param
        else:
            nNodes = m_numNodes
            a = param

        for i in range(1, m_numRates+1):
            m_controlModes.AppendMode(Experiment.CreateMode(m_totalRate, m_numRates, i, fc, False, "control "))
        for i in range(m_numRates, 0, -1):
            m_dataModes.AppendMode(Experiment.CreateMode(m_totalRate, m_numRates, i, fc, True, "data "))
        pDelay = ns.core.Seconds(float(m_maxRange) / 1500.0)
        uan = ns.uan.UanHelper()
        sinrFhfsk = ns.core.CreateObject("UanPhyCalcSinrFhFsk")
        perUmodem = ns.core.CreateObject("UanPhyPerUmodem"),
        uan.SetPhy("ns3::UanPhyDual",
                "SupportedModesPhy1",
                ns.uan.UanModesListValue(m_dataModes),
                "SupportedModesPhy2",
                ns.uan.UanModesListValue(m_controlModes),
                "PerModelPhy1",
                ns.core.PointerValue(perUmodem),
                "PerModelPhy2",
                ns.core.PointerValue(perUmodem),
                "SinrModelPhy1",
                ns.core.PointerValue(sinrFhfsk),
                "SinrModelPhy2",
                ns.core.PointerValue(sinrFhfsk)
                )
        
        uan.SetMac("ns3::UanMacRcGw",
                "NumberOfRates",
                ns.core.UintegerValue(m_numRates),
                "NumberOfNodes",
                ns.core.UintegerValue(nNodes),
                "MaxReservations",
                ns.core.UintegerValue(a),
                "SIFS",
                ns.core.TimeValue(m_sifs),
                "MaxPropDelay",
                ns.core.TimeValue(pDelay),
                "FrameSize",
                ns.core.UintegerValue(m_pktSize))

        chan = ns.core.CreateObject("UanChannel")
        chan.SetPropagationModel(ns.core.CreateObject("UanPropModelThorp"))
        sink = ns.network.NodeContainer()
        sink.Create(1)
        sinkDev = uan.Install(sink, chan)

        uan.SetMac("ns3::UanMacRc",
                "NumberOfRates",
                ns.core.UintegerValue(m_numRates),
                "MaxPropDelay",
                ns.core.TimeValue(pDelay))
        
        nodes = ns.network.NodeContainer()
        nodes.Create(nNodes)

        devices = uan.Install(nodes, chan)
        mobility = ns.mobility.MobilityHelper()
        depth = 70

        pos = ns.core.CreateObject("ListPositionAllocator")
        urv = ns.core.CreateObject("UniformRandomVariable")
        utheta = ns.core.CreateObject("UniformRandomVariable")
        pos.Add(ns.core.Vector(m_maxRange, m_maxRange, depth))

        M_PI = 3.14159265358979323846264338327950288

        for i in range(0, nNodes):
            theta = utheta.GetValue(0, 2.0 * M_PI)
            r = urv.GetValue(0, m_maxRange)

            x = m_maxRange + r * math.cos(theta)
            y = m_maxRange + r * math.sin(theta)

            pos.Add(ns.core.Vector(x, y, depth))
        
        mobility.SetPositionAllocator(pos)
        mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel")
        mobility.Install(sink)
        mobility.Install(nodes)

        pktskth = ns.network.PacketSocketHelper()
        pktskth.Install(nodes)
        pktskth.Install(sink)

        socket = ns.network.PacketSocketAddress()
        socket.SetSingleDevice(sinkDev.Get(0).GetIfIndex())
        socket.SetPhysicalAddress(sinkDev.Get(0).GetAddress())
        socket.SetProtocol(0)
        # print(socket)

        app = ns.applications.OnOffHelper("ns3::PacketSocketFactory", socket.ConvertTo())
        app.SetAttribute("OnTime", ns.core.StringValue("ns3::ConstantRandomVariable[Constant=1]"))
        app.SetAttribute("OffTime", ns.core.StringValue("ns3::ConstantRandomVariable[Constant=0]"))
        app.SetAttribute("DataRate", ns.core.DataRateValue(m_totalRate))
        app.SetAttribute("PacketSize", ns.core.UintegerValue(m_pktSize))

        apps = app.Install(nodes)

        apps.Start(ns.core.Seconds(0.5))
        apps.Stop(m_simTime + ns.core.Seconds(0.5))

        sinkNode = sink.Get(0)
        psfid = ns.core.TypeId.LookupByName("ns3::PacketSocketFactory")
        
    
        sinkSocket = ns.network.Socket.CreateSocket(sinkNode, psfid)
        # print(sinkSocket)
        sinkSocket.Bind(socket.ConvertTo())
        # print(makecallbackcustom)
        sinkSocket.SetRecvCallback(ReceivePacket)
        
        cppyy.set_debug(True)
        sink_mob = sinkNode.GetObject["ns3::ConstantPositionMobilityModel"]()
        sink_pos = sink_mob.GetPosition()
        x, y, z = sink_pos.x, sink_pos.y, sink_pos.z
        print(f"sink_mob location is {x, y, z}")
        for i in range(nNodes):
            node = nodes.Get(i)
            node_mob = node.GetObject["ns3::ConstantPositionMobilityModel"]()
            node_pos = node_mob.GetPosition()
            x, y, z = node_pos.x, node_pos.y, node_pos.z
            print(f"node {i}'s location is {x, y, z}")

        ns.core.Simulator.Stop(m_simTime + ns.core.Seconds(0.6))
        ns.core.Simulator.Run()
        ns.core.Simulator.Destroy()

def main(m_simMin:int, m_simMax:int, m_simStep:int) -> None:
    global m_bytesTotal
    exp = Experiment()
    for param in range(m_simMin, m_simMax+1, m_simStep):
        m_bytesTotal = 0
        exp.Run(m_numRates=1023, fc=12000, m_doNode=True, param=param, m_numNodes=15, m_sifs=ns.core.Seconds(0.05), m_simTime=ns.core.Seconds(5000), m_maxRange=3000, m_pktSize=1000, m_totalRate=4096)
        print(param, m_bytesTotal)

if __name__ == "__main__":
    # import cppyy
    # cppyy.include('/home/cps-tingcong/Desktop/ns-3-dev-master/src/core/model/callback.h')
    # template = cppyy.gbl.ns3
    # print("MakeCallbackCustom" in dir(template))
    # makecallbackcustom = template.MakeCallbackCustom[None, "ns3::Socket"]
    # print(makecallbackcustom)
    # print(dir(ns3))
    main(m_simMin = 1, m_simMax=15, m_simStep=1)