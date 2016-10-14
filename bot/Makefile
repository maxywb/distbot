all:
	mvn clean install -T 1C

run-producer: 
	java -cp target/bot-1.0-SNAPSHOT-jar-with-dependencies.jar com.beckett.IrcConnector

run-consumer: 
	java -cp target/bot-1.0-SNAPSHOT-jar-with-dependencies.jar com.beckett.IrcListener
