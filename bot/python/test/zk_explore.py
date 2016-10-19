#!/usr/bin/env python3

import logging

import kazoo.client as kzc

logging.basicConfig()

def my_listener(state):
    if state == kzc.KazooState.LOST:
        print("zk connection lost")
    elif state == kzc.KazooState.SUSPENDED:
        print("zk connection suspended")
    else:
        print("zk connection connected")



zk = kzc.KazooClient(hosts="192.168.1.201:2181")
zk.add_listener(my_listener)
zk.start()


zk.ensure_path("/bot/config/ignore")
ignored = ["SICPBot",
	   "Nimdok",
	   "sed",
	   "grep",
	   "deedeegee",
	   "yossarian-bot",
	   "yosbot",
	   "weedle",
	   "glenda",
	   "Byzantium",
	   "Combot",
	   "Techbot",
	   "ni",
	   "LimitServ",
	   "Trivia",
	   "Quotes",
	   "Internets",
	   "eRepublik",
	   "e-Sim",
	   "KG-Bot",
	   "YouTube",
	   "MafGuard",
	   "foobar",
	   "ChanStat",
	   "AntiBullyBot",
	   "Barkeep",
	   "fivequestionmarks",
	   "RuneScript",
	   "GambleBot",
	   "uguubot",
	   "PurplePanda-",
	   "Xeur",
	   "Trivia-Bot",
	   "yeah",
	   "Tradebot",
	   "TradeBot",
	   "BotOfLegends",
	   "CoffeeStat",
	   "Wharrgarbl",
	   "YT-info",
	   "Ambrogio",
	   "PokeBot",
	   "rms",
	   "lich_bot",
	   "cuck",
	   "PlutoBot",
	   "YouTube",
	   "MacBot",
	   "BagelBot",
	   "boatz",
	   "Pharazon",
	   "lykbot",
	   "KawaiiBot"
	  ]

for bot in set(ignored):
    path = "/bot/config/ignore/%s" % bot
    value = bytes(bot, "utf-8")
    if zk.exists(path) is None:
        zk.create(path, value=value)
