# AeroLoop


## Licenses
* The modification of the NS-3 tap-bridge.cc is under the terms of the [GNU General Public License version 2](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html).
*	Aeroloop-specific software (scripts) is under the terms of the [GNU General Public License version 3](https://www.gnu.org/licenses/gpl-3.0.en.html).

## Installation & configuration instructions
The following section describes the installation instructions of the AeroLoop simulator environment for a typical configuration that consists of:
*	One quadcopter in SITL configuration
*	One rover in SITL configuration
*	The Gazebo simulation environment
*	The WiFi simulation engine (also see [patched-ns3 repo](https://github.com/mlsysops-eu/patched-ns3.git))
  
The following guide has been tested on Ubuntu 22.04 LTS (KVM hosts) and Ubuntu 20.04 LTS (VMs). Please note that this guide excludes the steps related to the standard Linux installation and focuses merely on the configuration necessary for the AeroLoop simulator environment.

### AeroLoop host - basic configuration
All simulation entities of the AeroLoop simulator, except the Gazebo-related stuff, run on top of a KVM hypervisor, so a working KVM host is mandatory to follow this guide. Below are the basic instructions for configuring the KVM host. If more detailed installation instructions are necessary for your premises use the [official site](https://linux-kvm.org/page/Main_Page).
```bash
$ sudo apt install -y qemu-kvm virt-manager libvirt-daemon-system virtinst libvirt-clients bridge-utils
$ sudo systemctl enable --now libvirtd
$ sudo systemctl start libvirtd
```
Run the virt-manager to test the basic installation
```bash
$ virt-manager
```
Through the virt-manager GUI you should be able to inspect the system resources of the KVM host and configure the VMs for the vUAV and vRover.

### vUAV and vRover - basic configuration
Through the virt-manager interface, connect to the localhost (QEMU), create a new virtual machine for the vUAV and one for the vRover and proceed to the following configurations for the network:
1. Virtual Network Interface A (wireless interface): 
  * Network Source: Bridge device
  *	Device Name : ns-rover1 or ns-uav1 for vUAV and vRover respectively 
  *	Device model: rtl8139
2. Virtual Network Interface B (eth0): 
  *	Network Source: “Virtual Network default NAT”
  *	Device model: virtio
3. Virtual Network Interface (mgmt): 
  *	Network Source: “Virtual Network default NAT”
  *	Device model: virtio

Proceed with the standard Linux installation and once it is completed make sure that you can ping the vUAV and vRover VMs from the host.
Install the following software packages. 
```bash
$ apt-get update && apt-get install python3 python3-dev python3-pip build-essential libxml2 libxml2-dev tzdata git 
$ python3 -m pip install --upgrade pip
$ pip3 install wheel pymavlink mavproxy –user dronekit dataclasses dacite requests dataclass-struct pyzmq pyproj
```
Edit the `/etc/netplan/00-installer-config.yaml` to change the name of the network interface for the wireless adapter from `enp7s0` to `wlan0`. Add the following lines and change the MAC addresses to reflect your VM status
```yaml
enp7s0:
  match:
    macaddress: 52:54:00:c9:d1:5b
  set-name: wlan0
```
Install docker using the following steps
```bash
$ sudo apt update
$ sudo apt install apt-transport-https ca-certificates curl software-properties-common
$ curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add –
$ sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"
sudo apt install docker-ce
```
### NS - basic configuration
Through the virt-manager interface connect to the localhost (QEMU), create a new virtual machine for the NS VM and proceed to the following configurations for the network:
1. Virtual Network Interface A (vUAV wireless interface): 
  *	Network Source: Bridge device
  *	Device Name: ns-uav1
  *	Device model: rtl8139
2. Virtual Network Interface B (vRover wireless interface): 
  *	Network Source: Bridge device
  *	Device Name: ns-rover1
  *	Device model: rtl8139
3. Virtual Network Interface C (mgmt): 
  *	Network Source: “Virtual Network default NAT”
  *	Device model: virtio

Proceed with the standard Linux installation and once it is completed make sure that you can ping the NS VM from the host.
Edit the `/etc/netplan/00-installer-config.yaml` to change the names of the wireless interfaces. Add the following lines and change the MAC addresses to reflect your VM status.
```yaml
enp7s0:
  dhcp4: true
  dhcp-identifier: mac
  match:
    macaddress: 52:54:00:6e:20:a8
  set-name: wu1L 
enp8s0:
  dhcp4: true
  dhcp-identifier: mac
  match:
    macaddress: 52:54:00:0c:d7:63
  set-name: we1L 
```
### Gazebo PC - basic configuration
On a standard Ubuntu 22.04 follow the basic instructions below for configuring the Gazebo simulator. If more detailed installation instructions are necessary for your premises use the [official site](https://gazebosim.org/docs/harmonic/install_ubuntu/).
```bash
$ sudo apt-get update
$ sudo apt-get install curl lsb-release gnupg
$ sudo curl https://packages.osrfoundation.org/gazebo.gpg --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
$ echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null
$ sudo apt-get update
$ sudo apt-get install gz-harmonic
$ sudo apt update
$ sudo apt install libgz-sim8-dev rapidjson-dev
$ sudo apt install libopencv-dev libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev gstreamer1.0-plugins-bad gstreamer1.0-libav gstreamer1.0-gl
```
### AeroLoop host – simulation configuration
Through the virt-manager start the vUAV, vRover, and NS VMs.  Once the VMs are up and running perform the following steps on the host.
```bash
$ git clone https://github.com/mlsysops-eu/AeroLoop.git
$ cd AeroLoop/aeroloop/config
$ sudo ./host_net_conf.sh
```
### vUAV and vRover - simulation configuration
Clone the Ardupilot software stack and build the docker image with the name ardupilot.
```bash
$ git clone --recurse-submodules https://github.com/ArduPilot/ardupilot.git
$ cd ardupilot
$ docker build . -t ardupilot --build-arg USER_UID=$(id -u) --build-arg USER_GID=$(id -g)
```
Clone the AeroLoop software stack and configure the network interface.
```bash
$ git clone https://github.com/mlsysops-eu/AeroLoop.git
$ cd AeroLoop/aeroloop/config
$ sudo ./uav_net_conf.sh (for the vUAV)
$ sudo ./rover_net_conf.sh (for the vRover)
$ cd aeroloop/apm_params
$ cp *  ~/ ardupilot
```
NS - simulation configuration
Clone the AeroLoop software stack and configure the network interfaces.
```bash
$ git clone https://github.com/mlsysops-eu/AeroLoop.git
$ cd AeroLoop/aeroloop/config
$ sudo ./ns_vm_net_conf.sh
```
Clone the patched version of ns3.31 from the repository below and build it
```bash
$ git clone https://github.com/mlsysops-eu/patched-ns3.git
$ cd patched-ns3/ns-allinone-3.31/ns-3.31
$ ./waf build
```

### Gazebo - simulation configuration
Clone the Ardupilot’s gazebo plugin and build
```bash
$ git clone https://github.com/ArduPilot/ardupilot_gazebo
$ cd ardupilot_gazebo
$ mkdir build && cd build
$ cmake .. -DCMAKE_BUILD_TYPE=RelWithDebInfo
$ make -j4
```
Assuming that you have cloned the repository to `$HOME/ardupilot_gazebo`
```bash
$ echo 'export GZ_SIM_SYSTEM_PLUGIN_PATH=$HOME/ardupilot_gazebo/build:${GZ_SIM_SYSTEM_PLUGIN_PATH}' >> ~/.bashrc
$ echo 'export GZ_SIM_RESOURCE_PATH=$HOME/ardupilot_gazebo/models:$HOME/ardupilot_gazebo/worlds:${GZ_SIM_RESOURCE_PATH}' >> ~/.bashrc
$ source ~/.bashrc
```
Clone the AeroLoop software stack and configure the models.
```bash
$ git clone https://github.com/mlsysops-eu/AeroLoop.git
$ cp -r AeroLoop/aeroloop/gazebo_models/iris_static_cam ardupilot_gazebo/models/
$ cp -r AeroLoop/aeroloop/gazebo_models/r1_rover ardupilot_gazebo/models/
$ cp -r AeroLoop/aeroloop/gazebo_world/test.sdf ardupilot_gazebo/worlds
```
### Realistic simulation of mobile communication
The following section describes the steps to perform bandwidth capping and increase the communication latency for a given network interface so that it can have performance similar to 4/5G links. We use the Linux traffic control subsystem’s [tc utility](https://man7.org/linux/man-pages/man8/tc.8.html). One can modify the desired parameters as needed based on the following example:
To configure the “eth0” interface of a given node to have 4 Mbps BW and 50 ms latency (egress)
```bash
$ tc qdisc add dev eth0 handle 1: root htb default 11
$ tc class add dev eth0 parent 1: classid 1:1 htb rate 1000Mbps
$ tc class add dev eth0 parent 1:1 classid 1:11 htb rate 4Mbit
$ tc qdisc add dev eth0 parent 1:11 handle 10: netem delay 50ms
```
## Usage example 
The following section describes the steps to instantiate the AeroLoop environment for a simulation that includes a vUAV and a vRover. The vehicles communicate via a simulated WiFi network and stream their cameras over RSTP.
* Step 1 (configuration of Gazebo)
```bash
$ gz sim -v4 -r test.sdf
$ gz topic -t world/iris_runway/model/iris_with_gimbal/model/gimbal/link/tilt_link/sensor/camera/image/enable_streaming -m gz.msgs.Boolean -p "data: 1"
$ gz topic -t world/iris_runway/model/r1_rover/link/base_link/sensor/camera/image/enable_streaming -m gz.msgs.Boolean -p "data: 1"
$ cd ~/aeroloop/gazebo_streamers
$ python3 rover_rstp.py &
$ python3 uav_rstp.py &
```
* Step 2 (configuration of NS VM)
```bash
$ cd ~/ ns-allinone-3.31/ns-3.31
$ ./waf shell
$ cd ~/aeroloop/net_sim
$ python3 net_sim_pos_update.py
```
* Step 3 (configuration of vUAV VM)
```bash
$ cd ~/adupilot
$ docker run --network host --rm -it -v `pwd`:/ardupilot ardupilot bash
$ cd ArduCopter
$ sim_vehicle.py --model JSON:<GAZEBO_IP> --add-param-file=/ardupilot/gazebo-iris-gimbal.parm  -I 0 --out <vUAV IP>:14556 –out <MissionPlanner IP>:14557
```
On another terminal 
```bash
$ cd ~/aeroloop 
python3 uav_pos_update.py
```
* Step 4 (configuration of vRover VM)
```bash
$ cd ~/adupilot
$ docker run --network host --rm -it -v `pwd`:/ardupilot ardupilot bash
$ cd Rover
$ sim_vehicle.py --model JSON:<GAZEBO_IP> --add-param-file=/ardupilot/ r1_rover.param  -I 1 --out <vUAV IP>:14556 –out <MissionPlanner IP>:14558
```
On another terminal 
```bash
$ cd ~/aeroloop 
$ python3 rover_pos_update.py
```
After completing step 4 you should be able to control the vehicles from any GCS software like the MissionPlanner to perform a mission. You can find typical usage of [MissionPlanner](https://ardupilot.org/planner/) with example missions on the official MissionPlanner site. 
The RSTP links for the (virtual) camera streams of the two vehicles are shown below: 
* vUAV RSTP: `rstp://<GAZEBO_IP>:8556`
* vRover RSTP: `rstp://<GAZEBO_IP>:8557`
You can connect and receive to these streams using any standard media player like [VLC](https://www.videolan.org/).
