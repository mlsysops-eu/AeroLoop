#!/bin/bash
echo "Add bridges..."
ip link add name wu1br type bridge
ip link add name we1br type bridge
echo "Done."


ip tuntap add wu1U mode tap
ip tuntap add we1U mode tap


ifconfig wu1U 0.0.0.0 promisc up
ifconfig we1U 0.0.0.0 promisc up

echo "Attach taps to bridges..."
ip link set wu1U master wu1br
ip link set wu1L master wu1br
ip link set wu1br up
ip link set we1U master we1br
ip link set we1L master we1br
ip link set we1br up
echo "Done."


# disallow bridge traffic to go through ip tables chain
# See: https://unix.stackexchange.com/questions/499756/how-does-iptable-work-with-linux-bridge
# and: https://wiki.libvirt.org/page/Net.bridge.bridge-nf-call_and_sysctl.conf
pushd /proc/sys/net/bridge
for f in bridge-nf-*; do echo 0 > $f; done
popd
