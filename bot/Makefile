all:
	mvn -s ~/.m2/settings-home.xml clean install -T 1C -e

run-producer: 
	java -cp target/bot-1.0-SNAPSHOT-jar-with-dependencies.jar com.beckett.IrcConnector

run-simple-writer: 

	sudo su - hadoop -c "java -cp /home/meatwad/prog/src/hdfs-playground/bot/target/bot-1.0-SNAPSHOT-jar-with-dependencies.jar com.beckett.SimpleWriter"	
