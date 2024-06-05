from server import Server as newServer
from client import Client as newClient
from others.style import OnlyColorize as colorizeString
from screen import Screen

import socket, random, os, time, sys, json
from os.path import join as joinPath


with open(joinPath("resources", "options.json"), "r") as file:
    opts = json.load(file)

with open(joinPath("resources", "lang", opts["lang"]+".json"), "r") as file:
    lang = json.load(file)

class Game:
    def __init__(self):
        self.server = newServer(local=opts["localhost"], maxClients=2)
        
        self.server.events.onClientRemoved.connect(self.onPlayerDisconnected)
        self.server.events.onClientAdded.connect(self.onPlayerConnected)
    
    def onPlayerDisconnected(self, playerUUID):
        if len(self.server.getClients()) > 0:
            self.server.sendData(("otherPlayerDisconnected", None))
        else:
            self.server.stop()
    
    def onPlayerConnected(self, playerAddr, playerUUID):
        if len(self.server.getClients()) == 2:
            self.start()
        else:
            self.server.sendData(("waitingForOtherPlayer", self.server.getAddr()))
    
    def start(self):
        self.playerList = self.server.getClients()
        random.shuffle(self.playerList)
        self.playerOnTurn = self.playerList[0]
        
        self.gameData = {
            "cardDeck": [
                "ah", "7h", "8h", "9h", "xh", "jh", "qh", "kh",
                "as", "7s", "8s", "9s", "xs", "js", "qs", "ks",
                "ad", "7d", "8d", "9d", "xd", "jd", "qd", "kd",
                "ac", "7c", "8c", "9c", "xc", "jc", "qc", "kc",
            ],
            "cardsOnHands": {},
            "discardDeck": [],
            "wantToPlayAgain": {player: False for player in self.playerList}
        }
        
        random.shuffle(self.gameData["cardDeck"])
        
        # --------------- debug helper ------------------
        # if input("'yes' to give players custom cards: ") == "yes":
            # for player in self.playerList:
                # print(f"player {player}")
                
                # self.gameData["cardsOnHands"][player] = []
                
                # while True:
                    # cardInput = input("card: ")
                    
                    # if cardInput == "": break
                    
                    # try:
                        # self.gameData["cardDeck"].remove(cardInput)
                        
                        # self.gameData["cardsOnHands"][player].append(cardInput)
                    # except ValueError:
                        # print("card not in cardDeck")
        # else:
            # self.gameData["cardsOnHands"] = {client: [self.gameData["cardDeck"].pop(0) for _ in range(4)] for client in self.playerList}
        # --------------- end of debug helper ------------------
        
        self.gameData["cardsOnHands"] = {client: [self.gameData["cardDeck"].pop(0) for _ in range(4)] for client in self.playerList}
        
        self.gameData["discardDeck"].append(self.gameData["cardDeck"].pop(0))
        self.gameData["discardDeck"].append("--")
        
        self.server.events.onDataReceived.connect(self.onDataReceived)
        self.sendGameUpdate(True)
    
    def onDataReceived(self, data, player):
        if data[0] == "playCard":
            if player == self.playerOnTurn:
                self.gameUpdate(data[1])
        elif data[0] == "playAgain":
            self.gameData["wantToPlayAgain"][player] = True
            
            for value in list(self.gameData["wantToPlayAgain"].values()):
                if value == False:
                    break
            else:
                self.start()
    
    def switchPlayerOnTurn(self):
        playerListCopy = self.playerList.copy()
        playerListCopy.remove(self.playerOnTurn)
        self.playerOnTurn = playerListCopy[0]
    
    def gameUpdate(self, playedCard):
        if playedCard == "":
            discardDeckCopy = self.gameData["discardDeck"].copy()
            discardDeckCopy.reverse()
            
            if discardDeckCopy[0][0] == "a":
                self.gameData["discardDeck"].append("--")
                self.switchPlayerOnTurn()
                self.sendGameUpdate()
                return
            
            takeCards = 0
            for card in discardDeckCopy:
                if card[0] == "7":
                    takeCards += 2
                else:
                    break
            if takeCards == 0: takeCards = 1
            
            self.gameData["cardsOnHands"][self.playerOnTurn].extend([self.gameData["cardDeck"].pop(0) for _ in range(takeCards)])
            self.gameData["discardDeck"].append("--")
        else:
            self.gameData["cardsOnHands"][self.playerOnTurn].remove(playedCard[:2])
            self.gameData["discardDeck"].append(playedCard)
        
        self.refillCardDeck()
        self.switchPlayerOnTurn()
        self.sendGameUpdate()
        self.checkWinner()
    
    def refillCardDeck(self):
        discardDeckCopy = self.gameData["discardDeck"].copy()
        discardDeckCopy.reverse()
        discardDeckCopy = [card[:2] for card in discardDeckCopy if card != "--"]
        discardDeckCopy.pop(0)
        
        for card in discardDeckCopy:
            if card[0] == "7":
                discardDeckCopy.remove(card)
            else:
                break
        
        for card in self.gameData['discardDeck']:
            if card[:2] in discardDeckCopy:
                self.gameData['discardDeck'].remove(card)
        
        self.gameData["cardDeck"].extend(discardDeckCopy)
    
    def sendGameUpdate(self, isFirstUpdate=False):
        self.server.sendData(("gameUpdate", {
            "isFirstUpdate": isFirstUpdate,
            "lastPlayedCard": [card for card in self.gameData["discardDeck"] if card != "--"][-1],
            "lastCardIsOld": self.gameData["discardDeck"][-1] == "--",
            "cardsOnHands": self.gameData["cardsOnHands"],
            "playerOnTurn": self.playerOnTurn
        }))
    
    def checkWinner(self):
        for player in self.playerList:
            numCards = len(self.gameData["cardsOnHands"][player])
            
            if numCards == 0:
                self.sendWinner(player, "allCardsGone")
                return
            elif numCards > 11:
                self.sendWinner(list(set(self.playerList) - {player})[0], "tooManyCards")
                return
    
    def sendWinner(self, player, reason):
        self.server.sendData(("winner", {
            "player": player,
            "reason": reason
        }))

class Player:
    def __init__(self, serverAddr, screen):
        self.screen = screen
        
        self.screen.events.onPygameDied.connect(self.onPygameDied)
        
        self.client = newClient(serverAddr)
        
        self.client.events.onDataReceived.connect(self.onDataReceived)
        self.client.events.onDisconnected.connect(self.onDisconnected)
    
    def onPygameDied(self):
        try: self.client.stop()
        except AttributeError: pass
        
        sys.exit()
    
    def onDisconnected(self):
        self.screen.setScene("notif", dataForScene={"notif2": lang["serverConnLost"]})
    
    def onDataReceived(self, data):
        if data[0] == "otherPlayerDisconnected":
            self.screen.setScene("notif", dataForScene={"notif2": lang["otherPlayerDisconnected"]})
        elif data[0] == "waitingForOtherPlayer":
            self.screen.setScene("notif", dataForScene={
                "notif2": lang["waitingForOtherPlayer"],
                "notif3": lang["serverAddrIs"].format(data[1])
            })
        elif data[0] == "winner":
            time.sleep(1)
            self.screen.setScene("winner", dataForScene={
                "win": data[1]["player"] == self.client._uuid,
                "reason": data[1]["reason"]
            }, onUserInputCallback=self.requestPlayAgain)
        elif data[0] == "gameUpdate":
            self.onGameUpdate(data[1])
    
    def onGameUpdate(self, updateData):
        self.lastGameData = updateData
        
        if updateData["isFirstUpdate"]:
            self.screen.setScene("game", dataForScene={"me": self.client._uuid}, onUserInputCallback=self.tryToPlayCard)
        
        self.screen.sendSceneUpdate(updateData)
    
    def tryToPlayCard(self, card):
        allowedCards = self.getAllowedCards(self.lastGameData["lastPlayedCard"], self.lastGameData['lastCardIsOld'], self.lastGameData["cardsOnHands"][self.client._uuid])
        
        if self.lastGameData["playerOnTurn"] == self.client._uuid:
            if card == "":
                self.client.sendData(("playCard", card))
            elif card in allowedCards:
                if card[0] == "q":
                    self.screen.setScene("qCardChoice", dataForScene={
                        "gameScene": self.screen._scene,
                        "callback": self.qCardChoiceMade,
                        "originalCard": card
                    })
                else:
                    self.client.sendData(("playCard", card))
    
    def qCardChoiceMade(self, card, originalGameScene):
        self.screen._scene = originalGameScene
        self.client.sendData(("playCard", card))
    
    def requestPlayAgain(self, *args):
        self.client.sendData(("playAgain", None))
    
    def getAllowedCards(self, lastPlayedCard, lastCardIsOld, myCards):
        if len(lastPlayedCard) == 3:
            lastPlayedCard = "".join([lastPlayedCard[0], lastPlayedCard[2]])
        
        allowedCards = []
        
        for card in myCards:
            if card[0] == lastPlayedCard[0]:
                allowedCards.append(card)
                continue
            
            if card[1] == lastPlayedCard[1] and ((not lastPlayedCard[0] in ["a", "7"]) or lastCardIsOld):
                allowedCards.append(card)
        
        return allowedCards

if __name__ == "__main__":
    screen = Screen()
    
    # screen.setCaption(lang["screenCaption"])
    
    def hostGame():
        screen.setScene("notif", dataForScene={
            "notif1": lang["loading"],
            "notif2": lang["creatingGame"]
        })
        
        game = Game()
        player = Player(game.server.getAddr(), screen)

    def joinGame(serverAddr):
        screen.setScene("notif", dataForScene={
            "notif1": lang["loading"],
            "notif2": lang["joiningGame"]
        })
        
        try:
            player = Player(serverAddr, screen)
        except (socket.gaierror, ConnectionRefusedError, TimeoutError, OverflowError) as e:
            splitChar = "'"
            
            screen.setScene("notif", dataForScene={
                "notif1": lang["connFailed"],
                "notif2": lang["connFailed_hint"],
                "notif3": lang["error"].format(str(type(e)).split(splitChar)[1])
            })
    
    screen.setScene("choice", dataForScene={
        "hostGame": hostGame,
        "joinGame": joinGame
    })