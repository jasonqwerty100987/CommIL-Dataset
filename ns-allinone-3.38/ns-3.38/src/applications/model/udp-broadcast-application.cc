//
// Copyright (c) 2006 Georgia Tech Research Corporation
//
// This program is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 2 as
// published by the Free Software Foundation;
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program; if not, write to the Free Software
// Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
//
// Author: George F. Riley<riley@ece.gatech.edu>
//

// ns3 - On/Off Data Source Application class
// George F. Riley, Georgia Tech, Spring 2007
// Adapted from ApplicationOnOff in GTNetS.

#include "udp-broadcast-application.h"
#include "ns3/uinteger.h"
#include "ns3/address.h"
#include "ns3/boolean.h"
#include "ns3/data-rate.h"
#include "ns3/inet-socket-address.h"
#include "ns3/inet6-socket-address.h"
#include "ns3/log.h"
#include "ns3/node.h"
#include "ns3/nstime.h"
#include "ns3/packet-socket-address.h"
#include "ns3/packet.h"
#include "ns3/pointer.h"
#include "ns3/random-variable-stream.h"
#include "ns3/simulator.h"
#include "ns3/socket-factory.h"
#include "ns3/socket.h"
#include "ns3/string.h"
#include "ns3/trace-source-accessor.h"
#include "ns3/udp-socket-factory.h"
#include "ns3/uinteger.h"
#include "ns3/double.h"

namespace ns3
{

NS_LOG_COMPONENT_DEFINE("BroadCastApplication");

NS_OBJECT_ENSURE_REGISTERED(UdpBroadCastApplication);

TypeId
UdpBroadCastApplication::GetTypeId()
{
    static TypeId tid =
        TypeId("ns3::UdpBroadCastApplication")
            .SetParent<Application>()
            .SetGroupName("Applications")
            .AddConstructor<UdpBroadCastApplication>()
            .AddAttribute("Remote",
                          "The address of the destination",
                          AddressValue(),
                          MakeAddressAccessor(&UdpBroadCastApplication::m_peer),
                          MakeAddressChecker())
            .AddAttribute("Local",
                          "The Address on which to bind the socket. If not set, it is generated "
                          "automatically.",
                          AddressValue(),
                          MakeAddressAccessor(&UdpBroadCastApplication::m_local),
                          MakeAddressChecker())
            .AddAttribute("Buffer",
                          "The string representation of the data to be sent",
                          StringValue(""),
                          MakeStringAccessor(&UdpBroadCastApplication::m_buffer),
                          MakeStringChecker())
            .AddAttribute("Protocol",
                          "The type of protocol to use. This should be "
                          "a subclass of ns3::SocketFactory",
                          TypeIdValue(UdpSocketFactory::GetTypeId()),
                          MakeTypeIdAccessor(&UdpBroadCastApplication::m_tid),
                          // This should check for SocketFactory as a parent
                          MakeTypeIdChecker())
            .AddAttribute("EnableSeqTsSizeHeader",
                          "Enable use of SeqTsSizeHeader for sequence number and timestamp",
                          BooleanValue(false),
                          MakeBooleanAccessor(&UdpBroadCastApplication::m_enableSeqTsSizeHeader),
                          MakeBooleanChecker())
            .AddTraceSource("Tx",
                            "A new packet is created and is sent",
                            MakeTraceSourceAccessor(&UdpBroadCastApplication::m_txTrace),
                            "ns3::Packet::TracedCallback")
            .AddTraceSource("TxWithAddresses",
                            "A new packet is created and is sent",
                            MakeTraceSourceAccessor(&UdpBroadCastApplication::m_txTraceWithAddresses),
                            "ns3::Packet::TwoAddressTracedCallback")
            .AddTraceSource("TxWithSeqTsSize",
                            "A new packet is created with SeqTsSizeHeader",
                            MakeTraceSourceAccessor(&UdpBroadCastApplication::m_txTraceWithSeqTsSize),
                            "ns3::PacketSink::SeqTsSizeCallback")
            .AddAttribute("OffTime",
                          "A RandomVariableStream used to pick the duration of the 'Off' state.",
                          StringValue("ns3::UniformRandomVariable[Min=0.0|Max=0.1]"),
                          MakePointerAccessor(&UdpBroadCastApplication::m_startTime),
                          MakePointerChecker<RandomVariableStream>())
            .AddAttribute("TotalAttempt",
                         "The total number of attempts of sending packets.",
                         UintegerValue(1),
                         MakeUintegerAccessor(&UdpBroadCastApplication::m_total_send),
                         MakeUintegerChecker<uint64_t>(1))
            .AddAttribute("SendRate",
                         "The rate of sending packets.",
                         DoubleValue(1.0),
                         MakeDoubleAccessor(&UdpBroadCastApplication::m_send_rate),
                         MakeDoubleChecker<double>(0.0))
            .AddAttribute("Port",
                          "The port used for remote and local address",
                          UintegerValue(100),
                          MakeUintegerAccessor(&UdpBroadCastApplication::m_port),
                          MakeUintegerChecker<uint16_t>());
    return tid;
}

UdpBroadCastApplication::UdpBroadCastApplication()
    : m_socket(nullptr),
      m_connected(false),
      m_totBytes(0),
      m_current_attempts(0)
{
    NS_LOG_FUNCTION(this);
    // DoubleValue Min;
    // DoubleValue Max;
    // m_startTime->GetAttribute("Min", Min);
    // m_startTime->GetAttribute("Max", Max);
    // std::cout<<"The min is "<<Min.Get()<<", and the max is "<<Max.Get()<<"."<<std::endl;
    m_buffer = "";
}

UdpBroadCastApplication::~UdpBroadCastApplication()
{
    NS_LOG_FUNCTION(this);
}


Ptr<Socket>
UdpBroadCastApplication::GetSocket() const
{
    NS_LOG_FUNCTION(this);
    return m_socket;
}


void
UdpBroadCastApplication::DoDispose()
{
    NS_LOG_FUNCTION(this);

    StopApplication();
    m_socket = nullptr;
    // chain up
    Application::DoDispose();
}

void UdpBroadCastApplication::SetData(std::string buffer){
    // std::cout<<buffer<<std::endl;
    m_buffer = buffer;
}

// Application Methods
void
UdpBroadCastApplication::StartApplication() // Called at time specified by Start
{
    NS_LOG_FUNCTION(this);

    // Create the socket if not already
    if (!m_socket)
    {
        m_socket = Socket::CreateSocket(GetNode(), m_tid);
        int ret = -1;
        if (!m_local.IsInvalid())
        {
            NS_ABORT_MSG_IF((Inet6SocketAddress::IsMatchingType(m_peer) &&
                             InetSocketAddress::IsMatchingType(m_local)) ||
                                (InetSocketAddress::IsMatchingType(m_peer) &&
                                 Inet6SocketAddress::IsMatchingType(m_local)),
                            "Incompatible peer and local address IP version");
            // std::cout<<"Connecting socket with m_local address"<<std::endl;
            ret = m_socket->Bind(m_local);
        }
        else
        {
            // std::cout<<"Connecting socket with autogenerated address"<<std::endl;
            if (Inet6SocketAddress::IsMatchingType(m_peer))
            {
                // std::cout<<"IPV6"<<std::endl;
                ret = m_socket->Bind(Inet6SocketAddress(Ipv6Address::GetAny (), m_port).ConvertTo());
            }
            else if (InetSocketAddress::IsMatchingType(m_peer) ||
                     PacketSocketAddress::IsMatchingType(m_peer))
            {
                // std::cout<<"IPV4"<<std::endl;
                ret = m_socket->Bind(InetSocketAddress(Ipv4Address::GetAny (), m_port).ConvertTo());
            }
        }

        if (ret == -1)
        {
            NS_FATAL_ERROR("Failed to bind socket");
        }

        m_socket->SetConnectCallback(MakeCallback(&UdpBroadCastApplication::ConnectionSucceeded, this),
                                     MakeCallback(&UdpBroadCastApplication::ConnectionFailed, this));
        m_socket->SetAllowBroadcast(true);
        int connect_result = m_socket->Connect(m_peer);
        // std::cout<<"Node "<<this->GetNode()->GetId()<<" connection status is "<<connect_result<<std::endl;
        if (m_socket){
            m_socket->SetRecvCallback(MakeCallback(&UdpBroadCastApplication::DefaultOnReceived, this));
            // std::cout<<"udp-broadcast-application.cc::StartApplication:: m_socket receive callback is set."<<std::endl;
        }
    }

    // Ensure no pending event
    CancelEvents();

    // If we are not yet connected, there is nothing to do here,
    // the ConnectionComplete upcall will start timers at that time.
    // If we are already connected, CancelEvents did remove the events,
    // so we have to start them again.
    if (m_connected)
    {
        ScheduleNextTx();
    }
}

void UdpBroadCastApplication::SetRecvCallback(void (*fnptr)(Ptr<Socket> socket)){
    NS_LOG_FUNCTION(this);
    if (m_socket){
        m_socket->SetRecvCallback(MakeCallback(fnptr));
    }
    else{
        NS_LOG_WARN("UdpBraodCastApplication found null socket to set RecvCallback in SetRecvCallback");
    }
}

void
UdpBroadCastApplication::StopApplication() // Called at time specified by Stop
{
    NS_LOG_FUNCTION(this);

    CancelEvents();
    if (m_socket)
    {
        m_socket->Close();
        m_socket->SetRecvCallback(MakeNullCallback<void, Ptr<Socket>>());
        m_socket->SetConnectCallback(MakeNullCallback<void, Ptr<Socket>>(),
                                     MakeNullCallback<void, Ptr<Socket>>());
        m_socket = nullptr;
    }
    else
    {
        NS_LOG_WARN("UdpBraodCastApplication found null socket to close in StopApplication");
    }
}

void
UdpBroadCastApplication::CancelEvents()
{
    NS_LOG_FUNCTION(this);

    Simulator::Cancel(m_sendEvent);
    Simulator::Cancel(m_startStopEvent);
    // Canceling events may cause discontinuity in sequence number if the
    // SeqTsSizeHeader is header, and m_unsentPacket is true
    // if (m_unsentPacket)
    // {
    //     NS_LOG_DEBUG("Discarding cached packet upon CancelEvents ()");
    // }
    // m_unsentPacket = nullptr;
}


// Private helpers
void
UdpBroadCastApplication::ScheduleNextTx()
{
    NS_LOG_FUNCTION(this);

    
    m_sendEvent = Simulator::Schedule(Seconds(1/m_send_rate+m_startTime->GetValue()), &UdpBroadCastApplication::SendPacket, this);
    

    // if (m_maxBytes == 0 || m_totBytes < m_maxBytes)
    // {
    //     NS_ABORT_MSG_IF(m_residualBits > m_pktSize * 8,
    //                     "Calculation to compute next send time will overflow");
    //     uint32_t bits = m_pktSize * 8 - m_residualBits;
    //     NS_LOG_LOGIC("bits = " << bits);
    //     Time nextTime(
    //         Seconds(bits / static_cast<double>(m_cbrRate.GetBitRate()))); // Time till next packet
    //     NS_LOG_LOGIC("nextTime = " << nextTime.As(Time::S));
    //     m_sendEvent = Simulator::Schedule(nextTime, &UdpBroadCastApplication::SendPacket, this);
    // }
    // else
    // { // All done, cancel any pending events
    //     StopApplication();
    // }
}

uint8_t* 
UdpBroadCastApplication::StringToPtr(std::string data){
    return (uint8_t *)data.c_str();
}

void
UdpBroadCastApplication::SendPacket()
{
    NS_LOG_FUNCTION(this);

    NS_ASSERT(m_sendEvent.IsExpired());
    if(!m_buffer.empty()){
        Ptr<Packet> packet;
        if (m_enableSeqTsSizeHeader)
        {
            Address from;
            Address to;
            m_socket->GetSockName(from);
            m_socket->GetPeerName(to);
            SeqTsSizeHeader header;
            header.SetSeq(m_seq++);
            header.SetSize(m_buffer.size()+1);
            NS_ABORT_IF(m_buffer.size()+1 < header.GetSerializedSize());
            packet = Create<Packet>(StringToPtr(m_buffer), m_buffer.size()+1);
            // Trace before adding header, for consistency with PacketSink
            m_txTraceWithSeqTsSize(packet, from, to, header);
            packet->AddHeader(header);
        }
        else
        {
            std::string data_with_packet_num = m_buffer;
            std::string packet_num = std::to_string(m_current_attempts);
            int end_index = data_with_packet_num.size() - packet_num.size() - 1;
            data_with_packet_num = data_with_packet_num.substr(0, end_index) + " " + packet_num;
            packet = Create<Packet>(StringToPtr(data_with_packet_num), m_buffer.size()+1);
        }
        

        int actual = m_socket->Send(packet);
        // std::cout<<"Node "<<this->GetNode()->GetId()<<" is sending packet."<<std::endl;
        // std::cout<<"actual is "<<actual<< "; to be sent size is "<<m_buffer.size()+1<<std::endl;
        if ((uint32_t)actual == m_buffer.size()+1)
        {
            
            std::stringstream ss;
            ss << Simulator::Now().As(Time::S);
            std::string time_stamp = ss.str();
            std::string data_string = time_stamp + " packet " + std::to_string(m_current_attempts) + " sent.";
            UpdateResult(GetNode()->GetId(), data_string);
            m_current_attempts += 1;
            m_txTrace(packet);
            m_totBytes += m_buffer.size()+1;
            // m_unsentPacket = nullptr;
            Address localAddress;
            m_socket->GetSockName(localAddress);
            if (InetSocketAddress::IsMatchingType(m_peer))
            {
                NS_LOG_INFO("At time " << Simulator::Now().As(Time::S) << " udp-broadcast application sent "
                                        << packet->GetSize() << " bytes to "
                                        << InetSocketAddress::ConvertFrom(m_peer).GetIpv4() << " port "
                                        << InetSocketAddress::ConvertFrom(m_peer).GetPort()
                                        << " total Tx " << m_totBytes << " bytes");
                m_txTraceWithAddresses(packet, localAddress, InetSocketAddress::ConvertFrom(m_peer));
            }
            else if (Inet6SocketAddress::IsMatchingType(m_peer))
            {
                NS_LOG_INFO("At time " << Simulator::Now().As(Time::S) << " udp-broadcast application sent "
                                        << packet->GetSize() << " bytes to "
                                        << Inet6SocketAddress::ConvertFrom(m_peer).GetIpv6() << " port "
                                        << Inet6SocketAddress::ConvertFrom(m_peer).GetPort()
                                        << " total Tx " << m_totBytes << " bytes");
                m_txTraceWithAddresses(packet, localAddress, Inet6SocketAddress::ConvertFrom(m_peer));
            }
            if (m_current_attempts < m_total_send)
            {
                ScheduleNextTx();
            }
        }
        else
        {
            NS_LOG_DEBUG("Unable to send packet; actual " << actual << " size " << m_buffer.size()+1
                                                            << "; caching for later attempt");
            // std::cout<<"actual is "<<actual<< "; to be sent size is "<<m_buffer.size()+1<<std::endl;
            ScheduleNextTx();
        }
       
    }
    
}

void
UdpBroadCastApplication::ConnectionSucceeded(Ptr<Socket> socket)
{
    NS_LOG_FUNCTION(this << socket);
    // std::cout<<"Node IP "<<m_local<<" is conncted to "<<m_peer<<std::endl;
    ScheduleNextTx();
    m_connected = true;
}

void
UdpBroadCastApplication::ConnectionFailed(Ptr<Socket> socket)
{
    NS_LOG_FUNCTION(this << socket);
    NS_FATAL_ERROR("Can't connect");
}

void UdpBroadCastApplication::DefaultOnReceived(Ptr<Socket> receivedData){
        // uint32_t size = 0;
        Ptr<Packet> packet;
        while((packet = receivedData->Recv())){
            
            if(packet->GetSize () == 0){
                break;
            }
            uint32_t packet_size = packet->GetSize();
            uint8_t* byte_buffer = (uint8_t *)calloc(packet_size, sizeof(uint8_t));
            uint32_t copied_size = packet->CopyData(byte_buffer, packet_size);
            std::string data_string(byte_buffer, byte_buffer+copied_size);
            std::stringstream ss;
            ss << Simulator::Now().As(Time::S);
            std::string time_stamp = ss.str();
            UpdateResult(GetNode()->GetId(), time_stamp + " received " + data_string);
            // std::cout << "UdpBroadCastApplication::DefaultOnReceived:: Node "<<GetNode()->GetId()<<": "<< data_string<< std::endl; 
        }   
}
void
UdpBroadCastApplication::UpdateResult(int id, std::string data){
  std::map<int, std::vector<std::string>>::iterator it = m_result.find(id);
  if(it != m_result.end()) {
    std::vector<std::string>::iterator it_vecotor = std::find(it->second.begin(), it->second.end(), data);
    if (!(it_vecotor != it->second.end())){
      
      it->second.push_back(data);
    }
  }else{
    std::vector<std::string> string_container = {data};
    m_result[id] = string_container;
  }
}

std::map<int, std::vector<std::string>> 
UdpBroadCastApplication::GetResult(void)
{
//   for(const auto& elem : m_result)
//     {
//         std::string s;
//         for (const auto &piece : elem.second) s += ", " + piece;
//    std::cout << elem.first << " " << s << "\n";
//     }
  return std::map<int, std::vector<std::string>>(m_result);
}

} // Namespace ns3
