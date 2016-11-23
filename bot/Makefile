all:
	mvn -s ~/.m2/settings-home.xml clean install -T 1C -e

run-producer: 
	java -Xmx512m -Dlog4j.configuration="file:/home/meatwad/prog/src/distbot/bot/log4j.properties" -cp target/bot-1.0-SNAPSHOT-jar-with-dependencies.jar com.beckett.IrcConnector 

run-producer-test: 
	java -Xmx512m -Dlog4j.configuration="file:/home/meatwad/prog/src/distbot/bot/log4j.properties" -cp target/bot-1.0-SNAPSHOT-jar-with-dependencies.jar com.beckett.IrcConnector boatz-test boatz

run-something: 
	java -cp target/bot-1.0-SNAPSHOT-jar-with-dependencies.jar $(ARGS)

run-simple-writer: 

	sudo su - hadoop -c "java -Xmx512m -cp /home/meatwad/prog/src/distbot/bot/target/bot-1.0-SNAPSHOT-jar-with-dependencies.jar com.beckett.SimpleWriter"	
