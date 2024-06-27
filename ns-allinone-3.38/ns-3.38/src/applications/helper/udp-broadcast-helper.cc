/*
 * Copyright (c) 2008 INRIA
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation;
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 * Author: Tingcong Jiang <tingcong.jiang@rutgers.edu>
 */
#include "udp-broadcast-helper.h"

#include "ns3/string.h"
#include "ns3/udp-broadcast-application.h"
#include "ns3/inet-socket-address.h"
#include "ns3/names.h"

namespace ns3
{

UdpBroadcastHelper::UdpBroadcastHelper(Address remote)
{
    m_factory.SetTypeId("ns3::UdpBroadCastApplication");
    SetAttribute("Remote", AddressValue(remote));
}

UdpBroadcastHelper::UdpBroadcastHelper(Address local, Address remote)
{
    m_factory.SetTypeId("ns3::UdpBroadCastApplication");
    SetAttribute("Remote", AddressValue(remote));
    SetAttribute("Local", AddressValue(local));
}

void 
UdpBroadcastHelper::SetData(std::string buffer){
    buffers.push_back(buffer);
}

void
UdpBroadcastHelper::SetAttribute(std::string name, const AttributeValue& value)
{
    m_factory.Set(name, value);
}

// ApplicationContainer
// UdpBroadcastHelper::InstallWithInstance(NodeContainer c)
// {
//     int index_count = 0;
//     std::string name = "Buffer";
//     ApplicationContainer apps;
//     for (NodeContainer::Iterator i = c.Begin(); i != c.End(); ++i)
//     {
//         std::string data = "dummy data!";
//         if(!buffers.empty()){
//             data = buffers[index_count];
//             index_count = (index_count + 1) % buffers.size();
//         }
//         Ptr<Node> node = *i;
//         SetAttribute("Local", AddressValue(local));
//         Ptr<Application> m_server = m_factory.Create<Application>();
//         node->AddApplication(m_server);
//         apps.Add(m_server);
//     }
//     return apps;
// }

ApplicationContainer
UdpBroadcastHelper::Install(NodeContainer c) const
{
    int index_count = 0;
    // std::string name = "Buffer";
    ApplicationContainer apps;
    for (NodeContainer::Iterator i = c.Begin(); i != c.End(); ++i)
    {
        std::string data = "dummy data!";
        if(!buffers.empty()){
            data = buffers[index_count];
            index_count = (index_count + 1) % buffers.size();
        }
        Ptr<Node> node = *i;
        Ptr<Application> m_server = m_factory.Create<Application>();
        m_server->SetAttribute("Buffer", StringValue(data));
        node->AddApplication(m_server);
        apps.Add(m_server);
    }
    return apps;
}

ApplicationContainer UdpBroadcastHelper::Install(Ptr<Node> node) const
{
    ApplicationContainer apps;
    Ptr<Application> m_server = m_factory.Create<Application>();
    node->AddApplication(m_server);
    apps.Add(m_server);
    return apps;
}

ApplicationContainer UdpBroadcastHelper::Install(std::string nodeName) const
{
    ApplicationContainer apps;
    Ptr<Application>  m_server = m_factory.Create<Application>();
    Ptr<Node> node = Names::Find<Node>(nodeName);
    node->AddApplication(m_server);
    apps.Add(m_server);
    return apps;
}






} // namespace ns3
