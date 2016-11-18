set -e 

pushd () {
    # silence pushd
    command pushd "$@" > /dev/null
}

popd () {
    # silence popd
    command popd "$@" > /dev/null
}

add_user() {
    username=$1
    home=/opt/${username}

    echo "$(date) add user ${username}"

    useradd -d ${home} ${username}
    cp -f /vagrant/configs/bashrc ${home}/.bashrc

    echo "${username}" | passwd --stdin ${username}
    mkdir ${home}/.ssh

    pushd ${home}/.ssh
    ssh-keygen -b 1024 -f id_rsa -t rsa -q -N ""
    cat id_rsa.pub > authorized_keys
    chmod 600 ${home}/.ssh/authorized_keys
    chmod 700 ${home}/.ssh
    chown -R ${username}:${username} ${home}
    popd    

    su - ${username} -c "ssh-keyscan -H localhost >> ${home}/.ssh/known_hosts 2> /dev/null"
    su - ${username} -c "ssh-keyscan -H 0.0.0.0 >> ${home}/.ssh/known_hosts 2> /dev/null"
    su - ${username} -c "ssh-keyscan -H $(hostname) >> ${home}/.ssh/known_hosts 2> /dev/null"

    # save bash history
    touch /spam/.bash_history-${username}
    ln -s /spam/.bash_history-${username} ${home}/.bash_history
    chown -R ${username}:${username} /spam/.bash_history-${username}

    usermod --append --groups supergroup ${username}
}

install_package() {
    source=$1
    destination=$2
    url=$3
    
    pushd /tmp
    echo "$(date) installing ${source}"

    curl --silent -o ${source}.tar.gz ${url}

    mkdir ${source}
    mkdir -p ${destination}

    tar zxf ${source}.tar.gz -C ${source} --strip-components 1
    
    cp -r ${source}/* ${destination}

    popd
}

# check for cairn
if [ ! -f /spam/CAIRN ]; then
    echo "cairn doesn't exist" > /dev/stderr
    exit -1
fi

# set timezone so logs are understandable
timedatectl set-timezone America/New_York

# install deps
dnf install -y dnf-plugins-core
dnf copr enable -y mstuchli/Python3.5
dnf install -y python35
dnf install -y python3-lxml.x86_64

# make supergroup
groupadd supergroup

# make users
add_user "hadoop"
add_user "spark"
add_user "zookeeper"
add_user "kafka"

## install packages

# install java - special case
echo "$(date) installing java"
pushd /tmp
curl --silent -O -j -k -L -H "Cookie: oraclelicense=accept-securebackup-cookie" http://download.oracle.com/otn-pub/java/jdk/8u102-b14/jdk-8u102-linux-x64.rpm 
rpm --upgrade jdk-8u102-linux-x64.rpm > /dev/null
popd

# install scala
install_package scala-2.11.8 /opt/scala http://downloads.lightbend.com/scala/2.11.8/scala-2.11.8.tgz

# install hadoop 
install_package hadoop-2.7.3 /opt/hadoop http://apache.javapipe.com/hadoop/common/stable/hadoop-2.7.3.tar.gz

cp -f /vagrant/configs/core-site.xml /opt/hadoop/etc/hadoop/core-site.xml
cp -f /vagrant/configs/hdfs-site.xml /opt/hadoop/etc/hadoop/hdfs-site.xml
cp -f /vagrant/configs/mapred-site.xml /opt/hadoop/etc/hadoop/mapred-site.xml
cp -f /vagrant/configs/yarn-site.xml /opt/hadoop/etc/hadoop/yarn-site.xml

echo "export JAVA_HOME=/usr/java/default" >> /opt/hadoop/etc/hadoop/hadoop-env.sh

chown -R hadoop:supergroup /opt/hadoop
chown -R hadoop:supergroup /spam/hdfs

# install spark
install_package spark-2.0.1 /opt/spark http://d3kbcqa49mib13.cloudfront.net/spark-2.0.1-bin-hadoop2.7.tgz

cp -f /vagrant/configs/spark-env.sh /opt/spark/conf/spark-env.sh

chown -R spark:supergroup /opt/spark

# install zookeeper
install_package zookeeper-3.4.9 /opt/zookeeper http://www.gtlib.gatech.edu/pub/apache/zookeeper/zookeeper-3.4.9/zookeeper-3.4.9.tar.gz

cp -f /vagrant/configs/zoo.cfg /opt/zookeeper/conf/zoo.cfg

mkdir -p /var/log/zookeeper
chown -R zookeeper:supergroup /var/log/zookeeper

chown -R zookeeper:supergroup /opt/zookeeper
chown -R zookeeper:supergroup /spam/zookeeper

# install kafka
install_package kafka-0.10.0.1 /opt/kafka http://www.gtlib.gatech.edu/pub/apache/kafka/0.10.0.1/kafka_2.11-0.10.0.1.tgz

chown -R kafka:supergroup /opt/kafka

## misc setup

# make spam user
add_user "spam"
chown -R spam:supergroup /opt/spam

# set hostnames
# TODO: this is fuckin gross, proper fix is DNS
echo "10.0.0.201 node-1" >> /etc/hosts
echo "10.0.0.202 node-2" >> /etc/hosts
echo "192.168.1.15 oldtown" >> /etc/hosts

# set permissions on /spam
chown -R root:supergroup /spam
chmod -R g+rw /spam

chown -R hadoop:supergroup /spam/hdfs

# done
date >> /spam/provision_timestamp
