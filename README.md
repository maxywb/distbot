Irc bot for exploring how to build a distributed, fault-tolerant system. I chose an irc bot for this experiment because it's conceptually easy, and the operations it performs are sufficiently distinct that it can be easily broken up (e.g. something needs to speak the irc protocol, something else needs to know how to interpret commands, something needs to store data to a db, etc).

Present:
- HDFS
-- There is a collection of flat files into which I dump JSON blobs. This is my "poor-man's" database...
- Kafka
-- There are currently 2 channels: "irc-publish" for publishing all irc events the bot sees; and "irc-action" for publishing instructions to the bot.
- Zookeeper
-- The bot listents to the "/bot/config" tree and will respond to keep itself inline with the desired config. The supported config objects currently are "channels",  "name", and "ignore".

Future:
- Fail-Over 
-- I want to implement some kind of fail-over for each of the bot components.
- Spark
-- I want to enable an irc command to trigger spark queries to do searching or aggregation of the stored data.
- HBase ?
-- The flat-file business is awful, but since I'm more interested in the architecture of the bot itself (and the gross JSON datastore works well enough for now) this is lowest on the list.
