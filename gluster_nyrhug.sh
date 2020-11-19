#!/bin/bash

#############
# add storage
#############
./gluster_attach_disk.sh rhgs35-1 brickvol 10G vdb
./gluster_attach_disk.sh rhgs35-2 brickvol 10G vdb
./gluster_attach_disk.sh rhgs35-3 brickvol 10G vdb

export bricknum=######TERMINAL NUMBER####

###############
# Open firewall
###############
#all hosts
firewall-cmd --add-service=glusterfs 
firewall-cmd --add-service=glusterfs --permanent 

############
# peer hosts
############
# first host
gluster peer probe rhgs35-2
gluster peer probe rhgs35-3

################
# format & mount
################
vgcreate glustervg1 /dev/vdb
lvcreate --type thin-pool -L 9G glustervg1/vg1tp
lvcreate -V 1G glustervg1/vg1tp --name brick${bricknum}
mkfs.xfs -f -i size=512 -n size=8192 /dev/mapper/glustervg1-brick${bricknum}

#add to /etc/fstab
echo /dev/mapper/glustervg1-brick${bricknum} /bricks/brick${bricknum}  xfs     rw,inode64,noatime,nouuid,nofail 1 2 >> /etc/fstab
mkdir -p /bricks/brick${bricknum}/brick
mount -a

semanage fcontext -a -t glusterd_brick_t /bricks/brick${bricknum}
restorecon -Rv /bricks/brick${bricknum}

###############
# Create volume
###############
gluster volume create volume1 replica 3 rhgs35-1:/bricks/brick1/brick rhgs35-2:/bricks/brick2/brick rhgs35-3:/bricks/brick3/brick
gluster volume start volume1

gluster volume info volume1


################
# gluster client
################
#subscription-manager repos --enable=rh-gluster-3-client-for-rhel-7-server-rpms
yum install glusterfs glusterfs-fuse
mkdir -p /mnt/volume1
mount -t glusterfs -o backup-volfile-servers=rhgs35-2:rhgs35-3 rhgs35-1:/volume1 /mnt/volume1


################
# do stuff
################
dd if=/dev/urandom of=./bar count=102400
getfattr -d -m. foo
