#!/bin/bash

virsh vol-create-as Slow_Storage ${1}-${2}.qcow2 ${3} --format qcow2
virsh attach-disk --current --domain ${1} --source /data/libvirt_Slow_Storage/${1}-${2}.qcow2 --target ${4} --targetbus virtio --subdriver qcow2
virsh attach-disk --config  --domain ${1} --source /data/libvirt_Slow_Storage/${1}-${2}.qcow2 --target ${4} --targetbus virtio --subdriver qcow2
