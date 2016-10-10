
mkdir /spam
mount /dev/vdb1 /spam
mkdir -p /spam/hdfs/data
mkdir -p /spam/hdfs/name
useradd spam
echo "spam" | passwd --stdin spam
mv /home/vagrant/spam/ /home/spam
mkdir /home/spam/.ssh
pushd /home/spam/.ssh
ssh-keygen -b 1024 -f spam -t dsa -q -N ""
cat spam.pub | sudo tee -a /home/spam/.ssh/authorized_keys  
chmod 600 /home/spam/.ssh/authorized_keys
chmod 700 /home/spam/.ssh

popd

chown -R spam:spam /home/spam
chown -R spam:spam /spam
