#include “ns3/vector.h”
#include “ns3/string.h”
#include “ns3/socket.h”
#include “ns3/double.h”
#include “ns3/config.h”
#include “ns3/log.h”
#include “ns3/command-line.h”
#include “ns3/mobility-model.h”
#include “ns3/yans-wifi-helper.h”
#include “ns3/position-allocator.h”
#include “ns3/mobility-helper.h”
#include “ns3/internet-stack-helper.h”
#include “ns3/ipv4-address-helper.h”
#include “ns3/ipv4-interface-container.h”
#include
#include “ns3/ocb-wifi-mac.h”
#include “ns3/wifi-80211p-helper.h”
#include “ns3/wave-mac-helper.h”

using namespace ns3;
NS_LOG_COMPONENT_DEFINE (“WifiSimpleOcb”);
void ReceivePacket (Ptr socket)
{
while (socket->Recv ())
{
NS_LOG_UNCOND (“Received one packet!”);
}
}
static void GenerateTraffic (Ptr socket, uint32_t pktSize,
uint32_t pktCount, Time pktInterval )
{
if (pktCount > 0)
{
socket->Send (Create (pktSize));
Simulator::Schedule (pktInterval, &GenerateTraffic,
socket, pktSize,pktCount – 1, pktInterval);
}
else
{
socket->Close ();
}
}
int main (int argc, char *argv[])
{
std::string phyMode (“OfdmRate6MbpsBW10MHz”);
uint32_t packetSize = 1000; // bytes
uint32_t numPackets = 1;
double interval = 1.0; // seconds
bool verbose = false;
CommandLine cmd;
cmd.AddValue (“phyMode”, “Wifi Phy mode”, phyMode);
cmd.AddValue (“packetSize”, “size of application packet sent”, packetSize);
cmd.AddValue (“numPackets”, “number of packets generated”, numPackets);
cmd.AddValue (“interval”, “interval (seconds) between packets”, interval);
cmd.AddValue (“verbose”, “turn on all WifiNetDevice log components”, verbose);
cmd.Parse (argc, argv);
Time interPacketInterval = Seconds (interval);
NodeContainer c;
c.Create (2);
YansWifiPhyHelper wifiPhy = YansWifiPhyHelper::Default ();
YansWifiChannelHelper wifiChannel = YansWifiChannelHelper::Default ();
Ptr channel = wifiChannel.Create ();
wifiPhy.SetChannel (channel);
wifiPhy.SetPcapDataLinkType (YansWifiPhyHelper::DLT_IEEE802_11);
NqosWaveMacHelper wifi80211pMac = NqosWaveMacHelper::Default ();
Wifi80211pHelper wifi80211p = Wifi80211pHelper::Default ();
if (verbose)
{
wifi80211p.EnableLogComponents (); // Turn on all Wifi 802.11p logging
}
wifi80211p.SetRemoteStationManager (“ns3::ConstantRateWifiManager”,
“DataMode”,StringValue (phyMode),
“ControlMode”,StringValue (phyMode));
NetDeviceContainer devices = wifi80211p.Install (wifiPhy, wifi80211pMac, c);
wifiPhy.EnablePcap (“wave-simple-80211p”, devices);
MobilityHelper mobility;
Ptr positionAlloc = CreateObject ();
positionAlloc->Add (Vector (0.0, 0.0, 0.0));
positionAlloc->Add (Vector (5.0, 0.0, 0.0));
mobility.SetPositionAllocator (positionAlloc);
mobility.SetMobilityModel (“ns3::ConstantPositionMobilityModel”);
mobility.Install (c);
InternetStackHelper internet;
internet.Install (c);
Ipv4AddressHelper ipv4;
NS_LOG_INFO (“Assign IP Addresses.”);
ipv4.SetBase (“10.1.1.0”, “255.255.255.0”);
Ipv4InterfaceContainer i = ipv4.Assign (devices);
TypeId tid = TypeId::LookupByName (“ns3::UdpSocketFactory”);
Ptr recvSink = Socket::CreateSocket (c.Get (0), tid);
InetSocketAddress local = InetSocketAddress (Ipv4Address::GetAny (), 80);
recvSink->Bind (local);
recvSink->SetRecvCallback (MakeCallback (&ReceivePacket));
Ptr source = Socket::CreateSocket (c.Get (1), tid);
InetSocketAddress remote = InetSocketAddress (Ipv4Address (“255.255.255.255”), 80);
source->SetAllowBroadcast (true);
source->Connect (remote);
Simulator::ScheduleWithContext (source->GetNode ()->GetId (),
Seconds (1.0), &GenerateTraffic,
source, packetSize, numPackets, interPacketInterval);
Simulator::Run ();
Simulator::Destroy ();
return 0;
}