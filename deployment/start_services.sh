set -e

run_as_user() {
    username=$1
    command=$2

    echo "$(date) starting ${username}"

    su - ${username} -c "${command}"
}

# start hdfs
run_as_user "hadoop" "start-dfs.sh"

# start zookeeper
run_as_user "zookeeper" "zkServer.sh start"

# start kafka
run_as_user "kafka" "kafka-server-start.sh -daemon /opt/kafka/config/server.properties"

# start spark
run_as_user "spark" "start-all.sh"

