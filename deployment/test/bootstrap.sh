set -e 

add_user() {
    username=$1
    home=/opt/${username}

    useradd -d ${home} ${username}
    cp -f /vagrant/configs/bashrc ${home}/.bashrc

    echo "${username}" | passwd --stdin ${username}
    mkdir ${home}/.ssh

    pushd ${home}/.ssh
    ssh-keygen -b 1024 -f id_dsa -t dsa -q -N ""
    cat id_dsa.pub > authorized_keys
    chmod 600 ${home}/.ssh/authorized_keys
    chmod 700 ${home}/.ssh
    chown -R ${username}:${username} ${home}
    
    su - ${username} -c "ssh-keyscan -H localhost >> ${home}/.ssh/known_hosts"
    su - ${username} -c "ssh-keyscan -H $(hostname) >> ${home}/.ssh/known_hosts"

    popd
}

install_package() {
    source=$1
    destination=$2
    url=$3

    echo "curl  -o ${source}.tar.gz ${url}"
    curl  --silent -o ${source}.tar.gz ${url}

    echo "tar zxf ${source}.tar.gz"
    tar zxf ${source}.tar.gz

    echo "mkdir -p ${destination}"
    mkdir -p ${destination}
    
    echo "cp -r ${source}/* ${destination}"
    cp -r ${source}/* ${destination}
}

# make users
add_user "hadoop"
add_user "hbase"
add_user "spam"
add_user "spark"
add_user "zookeeper"

# install packages
pushd /tmp

# install java 
curl --silent -O -j -k -L -H "Cookie: oraclelicense=accept-securebackup-cookie" http://download.oracle.com/otn-pub/java/jdk/8u102-b14/jdk-8u102-linux-x64.rpm 
rpm -U jdk-8u102-linux-x64.rpm

# install scala
install_package scala-2.11.8 /opt/scala http://downloads.lightbend.com/scala/2.11.8/scala-2.11.8.tgz

# install hadoop 
install_package hadoop-2.7.3 /opt/hadoop http://apache.javapipe.com/hadoop/common/stable/hadoop-2.7.3.tar.gz

cp -f /vagrant/configs/core-site.xml /opt/hadoop/etc/hadoop/core-site.xml
cp -f /vagrant/configs/hdfs-site.xml /opt/hadoop/etc/hadoop/hdfs-site.xml
cp -f /vagrant/configs/mapred-site.xml /opt/hadoop/etc/hadoop/mapred-site.xml
cp -f /vagrant/configs/yarn-site.xml /opt/hadoop/etc/hadoop/yarn-site.xml

echo "export JAVA_HOME=/usr/java/default" >> /opt/hadoop/etc/hadoop/hadoop-env.sh

chown -R hadoop:hadoop /opt/hadoop

# install spark
install_package spark-2.0.1-bin-hadoop2.7 /opt/spark http://d3kbcqa49mib13.cloudfront.net/spark-2.0.1-bin-hadoop2.7.tgz

chown -R spark:spark /opt/spark

# install hbase
install_package hbase-1.2.3 /opt/hbase http://mirror.symnds.com/software/Apache/hbase/1.2.3/hbase-1.2.3-bin.tar.gz

cp -f /vagrant/configs/hbase-site.xml /opt/hbase/conf/hbase-site.xml

echo "export JAVA_HOME=/usr/java/default" >> /opt/hbase/conf/hbase-env.sh

chown -R hbase:hbase /opt/hbase

# install zookeeper
install_package zookeeper-3.4.9 /opt/zookeeper  http://www.gtlib.gatech.edu/pub/apache/zookeeper/zookeeper-3.4.9/zookeeper-3.4.9.tar.gz

chown -R zookeeper:zookeeper /opt/zookeeper

# done installing packages
popd #/tmp

# set hostnames
# TODO: this is fuckin gross, proper fix is DNS
echo "10.0.0.201 node-1" >> /etc/hosts
echo "10.0.0.202 node-2" >> /etc/hosts


date >> /spam/provision_timestamp
