#
# Cookbook Name:: hdfs
# Recipe:: default
#
# Copyright (c) 2016 The Authors, All Rights Reserved.



#recipe[hadoop::hadoop_hdfs_namenode] on NameNode machine
#recipe[hadoop::hadoop_hdfs_datanode] on all DataNode machines
#execute[hdfs-namenode-format] with action :run from recipe[hadoop::hadoop_hdfs_namenode] on NameNode machine
#service[hadoop-hdfs-namenode] with action :start from recipe[hadoop::hadoop_hdfs_namenode] on NameNode machine
#service[hadoop-hdfs-datanode] with action :start from recipe[hadoop::hadoop_hdfs_datanode] on all DataNode machines
