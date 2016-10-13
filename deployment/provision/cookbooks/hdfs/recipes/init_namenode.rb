#
# Cookbook Name:: hdfs
# Recipe:: default
#
# Copyright (c) 2016 The Authors, All Rights Reserved.




include_recipe 'hadoop_wrapper::default'
include_recipe 'hadoop::hadoop_hdfs_namenode'


ruby_block 'initaction-format-namenode' do
  block do
    resources(:execute => 'hdfs-namenode-format').run_action(:run)
  end
end



#node.set['hadoop']['core_site']['dfs.namenode.name.dir'] = "/spam/hdfs/name"
#node.set['hadoop']['core_site']['dfs.namenode.data.dir'] = "/spam/hdfs/data"
#include_recipe 'hadoop::hadoop_hdfs_namenode'

#recipe[hadoop_wrapper::hadoop_hdfs_namenode_init]




#recipe[hadoop::hadoop_hdfs_namenode] on NameNode machine
#recipe[hadoop::hadoop_hdfs_datanode] on all DataNode machines
#execute[hdfs-namenode-format] with action :run from recipe[hadoop::hadoop_hdfs_namenode] on NameNode machine
#hadoop['core_site'][service[hadoop-hdfs-namenode] with action :start from recipe[hadoop::hadoop_hdfs_namenode] on NameNode machine
#service[hadoop-hdfs-datanode] with action :start from recipe[hadoop::hadoop_hdfs_datanode] on all DataNode machines
#hadoop_wrapper::hadoop_hdfs_namenode_init
#recipe[hadoop::hadoop_hdfs_namenode]
