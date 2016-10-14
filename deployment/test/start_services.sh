set -e

run_as_user() {
    username=$1
    command=$2

    su - ${username} -c "${command}"
}



# start hdfs
run_as_user "hadoop" "start-all.sh"

# start zookeeper
run_as_user "zookeeper" "zkServer.sh start"

# start hbase
run_as_user "hbase" "start-hbase.sh"
