#! /bin/sh
# Created By Tata for Tunstall Board <Thirumalesha N>
# emmc_partition.sh v1.0
# Licensed under terms of GPLv2
# Creates following size partitions
# Boot 			  : 8MB
# Primary(rootfs) : 256MB
# Backup1(rootfs) : 256MB
# Backup2(rootfs) : 256MB
# Temparary area  : 256MB
# user data		  : Remaining flash size
#
DRIVE=$1

#Find the Accessing Device is valid or not
#DEV=`echo $DRIVE | grep "mmc" | cut -c6-12`
#MMC_DEV=`cat /proc/partitions | grep -i $DEV`
#if [ "$MMC_DEV" == "" ]; then
#        echo -e "$DRIVE is not exist\n"
#        echo -e "Usage: ./emmc_partition.sh <emmc device path>\n"
#        exit 1
#fi

#un mount the mounted partitions before create partitions
umount ${DRIVE}*

#erase the partitions of $DRIVE 
dd if=/dev/zero of=$DRIVE bs=1024 count=1024

#Read the total size of the flash
SIZE=`fdisk -l $DRIVE | grep Disk | awk '{print $5}'`

#Display the size of flash
echo DISK SIZE - $SIZE bytes

#Calculate the number of cylinders from flash size
CYLINDERS=`echo $SIZE/255/63/512 | bc`

#Create the partitions
sfdisk -D -H 255 -S 63 -C $CYLINDERS $DRIVE << EOF
,1,0x0C,*
,32
,32
,,E
,32
,32
;
EOF

#Formate the partitions with EXT4 type
umount ${DRIVE}p1
mkfs.vfat -n "boot" ${DRIVE}p1
umount ${DRIVE}p2
mke2fs -L "primary" ${DRIVE}p2
umount ${DRIVE}p3
mke2fs -L "backup1" ${DRIVE}p3
umount ${DRIVE}p5
mke2fs -L "backup2" ${DRIVE}p5
umount ${DRIVE}p6
mke2fs -L "tmp" ${DRIVE}p6
umount ${DRIVE}p7
mke2fs -L "user data" ${DRIVE}p7
