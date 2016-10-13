set -e 

# make hadoop user
useradd -d /opt/hadoop hadoop
echo "hadoop" | passwd --stdin hadoop
mkdir /opt/hadoop/.ssh

pushd /opt/hadoop/.ssh
ssh-keygen -b 1024 -f id_dsa -t dsa -q -N ""
cat id_dsa.pub | sudo tee -a /opt/hadoop/.ssh/authorized_keys  
chmod 600 /opt/hadoop/.ssh/authorized_keys
chmod 700 /opt/hadoop/.ssh
popd
# chown later after hadoop stuff is put here

# make spark user
useradd -d /opt/spark spark
echo "spark" | passwd --stdin spark
mkdir /opt/spark/.ssh

pushd /opt/spark/.ssh
ssh-keygen -b 1024 -f id_dsa -t dsa -q -N ""
cat id_dsa.pub | sudo tee -a /opt/spark/.ssh/authorized_keys  
chmod 600 /opt/spark/.ssh/authorized_keys
chmod 700 /opt/spark/.ssh
popd
# chown later after spark stuff is put here

# make spam user
useradd spam
echo "spam" | passwd --stdin spam
mv /home/vagrant/spam/ /home/spam
mkdir /home/spam/.ssh

pushd /home/spam/.ssh
ssh-keygen -b 1024 -f id_dsa -t dsa -q -N ""
cat id_dsa.pub | sudo tee -a /home/spam/.ssh/authorized_keys  
chmod 600 /home/spam/.ssh/authorized_keys
chmod 700 /home/spam/.ssh
popd
chown -R spam:spam /home/spam

# install packages
pushd /tmp

# install java 
curl --silent -O -j -k -L -H "Cookie: oraclelicense=accept-securebackup-cookie" http://download.oracle.com/otn-pub/java/jdk/8u102-b14/jdk-8u102-linux-x64.rpm 
rpm -U jdk-8u102-linux-x64.rpm

# install scala
curl --silent -O http://downloads.lightbend.com/scala/2.11.8/scala-2.11.8.tgz -o scala-2.11.8.tgz
tar zxf scala-2.11.8.tgz
mv scala-2.11.8 /opt/scala

echo <<EOF >> /opt/hadoop/.bashrc
## add SCALA to path
export PATH=$PATH:/opt/scala/bin
EOF

echo <<EOF >> /opt/spark/.bashrc
## add SCALA to path
export PATH=$PATH:/opt/scala/bin
EOF

# setup hadoop 
curl --silent -O http://apache.javapipe.com/hadoop/common/stable/hadoop-2.7.3.tar.gz
tar zxf hadoop-2.7.3.tar.gz
cp -r hadoop-2.7.3/* /opt/hadoop

echo <<EOF >> /opt/hadoop/.bashrc
## JAVA env variables
export JAVA_HOME=/usr/java/default
export PATH=$PATH:$JAVA_HOME/bin
export CLASSPATH=.:$JAVA_HOME/jre/lib:$JAVA_HOME/lib:$JAVA_HOME/lib/tools.jar
## HADOOP env variables
export HADOOP_HOME=/opt/hadoop
export HADOOP_COMMON_HOME=$HADOOP_HOME
export HADOOP_HDFS_HOME=$HADOOP_HOME
export HADOOP_MAPRED_HOME=$HADOOP_HOME
export HADOOP_YARN_HOME=$HADOOP_HOME
export HADOOP_OPTS="-Djava.library.path=$HADOOP_HOME/lib/native"
export HADOOP_COMMON_LIB_NATIVE_DIR=$HADOOP_HOME/lib/native
export PATH=$PATH:$HADOOP_HOME/sbin:$HADOOP_HOME/bin
EOF

echo <<EOF >> /opt/spark/.bashrc
## JAVA env variables
export JAVA_HOME=/usr/java/default
export PATH=$PATH:$JAVA_HOME/bin
export CLASSPATH=.:$JAVA_HOME/jre/lib:$JAVA_HOME/lib:$JAVA_HOME/lib/tools.jar
## HADOOP env variables
export HADOOP_HOME=/opt/hadoop
export HADOOP_COMMON_HOME=$HADOOP_HOME
export HADOOP_HDFS_HOME=$HADOOP_HOME
export HADOOP_MAPRED_HOME=$HADOOP_HOME
export HADOOP_YARN_HOME=$HADOOP_HOME
export HADOOP_OPTS="-Djava.library.path=$HADOOP_HOME/lib/native"
export HADOOP_COMMON_LIB_NATIVE_DIR=$HADOOP_HOME/lib/native
export PATH=$PATH:$HADOOP_HOME/sbin:$HADOOP_HOME/bin
EOF

chown -R hadoop:hadoop /opt/hadoop

# install spark
curl --silent -O http://d3kbcqa49mib13.cloudfront.net/spark-2.0.1-bin-hadoop2.7.tgz
tar zxf spark-2.0.1-bin-hadoop2.7.tgz
cp -r spark-2.0.1-bin-hadoop2.7/* /opt/spark 

echo <<EOF >> /opt/spark/.bashrc
## add SPARK to path
export PATH=$PATH:/opt/spark/bin
EOF

chown -R spark:spark /opt/spark

# set hostnames
# TODO: this is fuckin gross, proper fix is DNS
echo "10.0.0.201 node-1" >> /etc/hosts
echo "10.0.0.202 node-2" >> /etc/hosts

# done installing packages
popd #/tmp
