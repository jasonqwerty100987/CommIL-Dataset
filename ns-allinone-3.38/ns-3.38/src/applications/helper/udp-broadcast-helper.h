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
 * Author: Tingcong Jiang (tingcong.jiang@rutgers.edu)
 */ 
#ifndef UDP_BROADCAST_HELPER_H
#define UDP_BROADCAST_HELPER_H

#include "ns3/application-container.h"
#include "ns3/ipv4-address.h"
#include "ns3/node-container.h"
#include "ns3/object-factory.h"

namespace ns3
{

class UdpBroadcastHelper
{
  public:
    /**
     * Create a UdpBroadcastHelper to make it easier to work with UdpBoradcastApplications
     *
     * \param local the address of the local socket to listening incoming trafic
     * \param remote the address where the generated trafic send to
     *
     */
    UdpBroadcastHelper(Address remote);
    /**
     * Create a UdpBroadcastHelper to make it easier to work with UdpBoradcastApplications
     *
     * \param local the address of the local socket to listening incoming trafic
     * \param remote the address where the generated trafic send to
     *
     */
    UdpBroadcastHelper(Address local, Address remote);

    /**
     * Set the data to be transmitted for all applications
     *
     * \param data the address of the local socket to listening incoming trafic
     *
     */
    void SetData(std::string buffer);

    /**
     * Helper function used to set the underlying application attributes.
     *
     * \param name the name of the application attribute to set
     * \param value the value of the application attribute to set
     */
    void SetAttribute(std::string name, const AttributeValue& value);

    /**
     * Install an ns3::PacketSinkApplication on each node of the input container
     * configured with all the attributes set with SetAttribute.
     *
     * \param c NodeContainer of the set of nodes on which a PacketSinkApplication
     * will be installed.
     * \returns Container of Ptr to the applications installed.
     */
    ApplicationContainer Install(NodeContainer c) const;

    /**
     * Install an ns3::PacketSinkApplication on each node of the input container
     * configured with all the attributes set with SetAttribute.
     *
     * \param node The node on which a PacketSinkApplication will be installed.
     * \returns Container of Ptr to the applications installed.
     */
    ApplicationContainer Install(Ptr<Node> node) const;

    /**
     * Install an ns3::PacketSinkApplication on each node of the input container
     * configured with all the attributes set with SetAttribute.
     *
     * \param nodeName The name of the node on which a PacketSinkApplication will be installed.
     * \returns Container of Ptr to the applications installed.
     */
    ApplicationContainer Install(std::string nodeName) const;

  private:
    ObjectFactory m_factory; //!< Object factory.
    std::vector<std::string> buffers; //!<Vector of buffers for each application
};

} // namespace ns3

#endif /* PACKET_SINK_HELPER_H */
