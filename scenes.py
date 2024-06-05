import pygame, time, threading, json
from os.path import join as joinPath


pygame.init()
pygame.font.init()

font1 = pygame.font.SysFont("comicsans", 35)
font2 = pygame.font.SysFont("comicsans", 25)
font3 = pygame.font.SysFont("comicsans", 18)
font4 = pygame.font.SysFont("comicsans", 14)

bgColor1 = (100, 200, 100)
bgColor2 = (90, 180, 90)
textColor1 = (0, 0, 0)
textColor2 = (100, 100, 100)

cardSize = (75, 112)
suitSize = (50, 50)
animDuration = 0.5
animTickSpeed = 60

with open(joinPath("resources", "options.json"), "r") as file:
    opts = json.load(file)

with open(joinPath("resources", "lang", opts["lang"]+".json"), "r") as file:
    lang = json.load(file)

images = {
    "cards": {card: pygame.transform.scale(
        pygame.image.load(
            joinPath("resources", "images", "cards", card+".png")
        ),
        cardSize
    ) for card in [
        "ah", "7h", "8h", "9h", "xh", "jh", "qh", "kh",
        "as", "7s", "8s", "9s", "xs", "js", "qs", "ks",
        "ad", "7d", "8d", "9d", "xd", "jd", "qd", "kd",
        "ac", "7c", "8c", "9c", "xc", "jc", "qc", "kc",
    ]},
    "suits": {suit: pygame.transform.scale(
        pygame.image.load(
            joinPath("resources", "images", "suits", suit+".png")
        ),
        suitSize
    ) for suit in [
        "h", "s", "d", "c"
    ]},
    "cardDeck": pygame.transform.scale(
        pygame.image.load(
            joinPath("resources", "images", "others", "deck.png")
        ),
        (cardSize[0]*1.125, cardSize[1]*1.111)
    ),
    "hiddenCard": pygame.transform.scale(
        pygame.image.load(
            joinPath("resources", "images", "others", "hidden.png")
        ),
        cardSize
    )
}

def addTuples(t1, t2):
    return tuple(t1[i] + t2[i] for i in range(min(len(t1), len(t2))))

def multTupleWithNum(t, n):
    return tuple(t[i]*n for i in range(len(t)))

def listsRemoveSame(a, b):
    a = set(a)
    b = set(b)
    
    c = list(a.difference(b))
    d = list(b.difference(a))
    
    return c, d

class Animations(threading.Thread):
    def __init__(self):
        super().__init__()
        
        self.daemon = True
        self._animList = []
        
        self.start()
    
    def run(self):
        clock = pygame.time.Clock()
        
        while True:
            for obj in self._animList:
                interpValue = (time.time() - obj["startTime"]) / obj["duration"]
                interpValue = max(0, min(interpValue, 1))
                
                diff = (
                    obj["targetPos"][0] - obj["startPos"][0],
                    obj["targetPos"][1] - obj["startPos"][1],
                    obj["targetPos"][2] - obj["startPos"][2],
                    obj["targetPos"][3] - obj["startPos"][3]
                )
                
                # obj["obj"].xPos, obj["obj"].xOffset, obj["obj"].yPos, obj["obj"].yOffset = tuple(map(lambda x: x*interpValue, diff))
                newPos = tuple(map(lambda x: x*interpValue, diff))
                obj["obj"].xPos = obj["startPos"][0] + newPos[0]
                obj["obj"].xOffset = obj["startPos"][1] + newPos[1]
                obj["obj"].yPos = obj["startPos"][2] + newPos[2]
                obj["obj"].yOffset = obj["startPos"][3] + newPos[3]
                
                if interpValue == 1:
                    self._animList.remove(obj)
            
            clock.tick(animTickSpeed)
    
    def animate(self, sceneObject, targetPos, duration):
        self._animList.append({
            "obj": sceneObject,
            "startPos": (sceneObject.xPos, sceneObject.xOffset, sceneObject.yPos, sceneObject.yOffset),
            "targetPos": targetPos,
            "duration": duration,
            "startTime": time.time()
        })

def CreateScenes(EmptyScene, SceneObject):
    class button(SceneObject):
        def setButtonColor(self, color):
            self.buttonColor = color
        
        def draw(self, targetSurface):
            pygamePos = self.getPygamePosOnSurface(targetSurface)
            
            rect = self.surface.get_rect().move(pygamePos)
            rect.inflate_ip(32, 8)
            
            pygame.draw.rect(targetSurface, self.buttonColor, rect)
            targetSurface.blit(self.surface, pygamePos)

    class Choice(EmptyScene):
        def load(self):
            self.bgColor = bgColor1
            
            self.sceneObjects["text"] = SceneObject(font3.render(lang["choice"], 1, textColor1), 0.5, 0, 0.4, 0)
            # self.sceneObjects["hostButton"] = SceneObject(font4.render("Vytvořit hru", 1, (0, 0, 0)), 0.5, 0, 0.6, 0, onClickCallback=self.e_onHostButtonClick)
            # self.sceneObjects["joinButton"] = SceneObject(font4.render("Připojit se do hry", 1, (0, 0, 0)), 0.5, 0, 0.6, font4.get_height()+10, onClickCallback=self.e_onJoinButtonClick)
            self.sceneObjects["hostButton"] = button(font3.render(lang["choice_host"], 1, textColor1), 0.5, 0, 0.6, 0, onClickCallback=self.e_onHostButtonClick)
            self.sceneObjects["joinButton"] = button(font3.render(lang["choice_join"], 1, textColor1), 0.5, 0, 0.6, font4.get_height()+20, onClickCallback=self.e_onJoinButtonClick)
            
            self.sceneObjects["hostButton"].setButtonColor(bgColor2)
            self.sceneObjects["joinButton"].setButtonColor(bgColor2)
        
        def e_onHostButtonClick(self, *args):
            # self.userInput("host")
            self.sceneData["hostGame"]()
        
        def e_onJoinButtonClick(self, *args):
            # self.userInput("join")
            self.setScene("ipInput", dataForScene=self.sceneData)

    class IPInput(EmptyScene):
        def load(self):
            self.bgColor = bgColor1
            
            self.sceneObjects["text"] = SceneObject(font3.render(lang["ipInput"], 1, textColor1), 0.5, 0, 0.4, 0)
            self.sceneObjects["ip"] = SceneObject(font2.render("", 1, textColor2), 0.5, 0, 0.55, 0)
            self.sceneObjects["backButton"] = button(font3.render(lang["backToChoice"], 1, textColor1), 0.5, 0, 1, -font3.get_height()*2, onClickCallback=self.e_onBackButtonClick)
            
            self.sceneObjects["backButton"].setButtonColor(bgColor2)
            
            self.sceneData["ipInput"] = ""
            
            self.addEvent(pygame.KEYDOWN, self.e_onKeydown)
        
        def e_onKeydown(self, event):
            if event.key == pygame.K_RETURN:
                self.setScene("portInput", dataForScene=self.sceneData)
            elif event.key == pygame.K_BACKSPACE:
                self.sceneData["ipInput"] = self.sceneData["ipInput"][:-1]
            elif event.unicode in "0123456789.":
                self.sceneData["ipInput"] += event.unicode
            
            self.sceneObjects["ip"].surface = font2.render(self.sceneData["ipInput"], 1, textColor2)
        
        def e_onBackButtonClick(self, *args):
            self.setScene("choice", dataForScene=self.sceneData)
    
    class PortInput(EmptyScene):
        def load(self):
            self.bgColor = bgColor1
            
            self.sceneObjects["text"] = SceneObject(font3.render(lang["portInput"], 1, textColor1), 0.5, 0, 0.4, 0)
            self.sceneObjects["port"] = SceneObject(font2.render("", 1, textColor2), 0.5, 0, 0.55, 0)
            self.sceneObjects["backButton"] = button(font3.render(lang["backToChoice"], 1, textColor1), 0.5, 0, 1, -font3.get_height()*2, onClickCallback=self.e_onBackButtonClick)
            
            self.sceneObjects["backButton"].setButtonColor(bgColor2)
            
            self.sceneData["portInput"] = ""
            
            self.addEvent(pygame.KEYDOWN, self.e_onKeydown)
        
        def e_onKeydown(self, event):
            if event.key == pygame.K_RETURN:
                self.sceneData["joinGame"]((self.sceneData["ipInput"], int(self.sceneData["portInput"])))
            elif event.key == pygame.K_BACKSPACE:
                self.sceneData["portInput"] = self.sceneData["portInput"][:-1]
            elif event.unicode in "0123456789":
                self.sceneData["portInput"] += event.unicode
            
            self.sceneObjects["port"].surface = font2.render(self.sceneData["portInput"], 1, textColor2)
        
        def e_onBackButtonClick(self, *args):
            self.setScene("choice", dataForScene=self.sceneData)
    
    class Notif(EmptyScene):
        def load(self):
            self.bgColor = bgColor1
            
            try: self.sceneObjects["text1"] = SceneObject(font1.render(self.sceneData["notif1"], 1, textColor1), 0.5, 0, 0.4, 0)
            except KeyError: pass
            
            try: self.sceneObjects["text2"] = SceneObject(font2.render(self.sceneData["notif2"], 1, textColor1), 0.5, 0, 0.4, font1.get_height()+10)
            except KeyError: pass
            
            try: self.sceneObjects["text3"] = SceneObject(font3.render(self.sceneData["notif3"], 1, textColor1), 0.5, 0, 0.4, font1.get_height()+10 + font2.get_height()+10)
            except KeyError: pass
    
    class Winner(EmptyScene):
        def load(self):
            self.bgColor = bgColor1
            
            if self.sceneData["win"]:
                self.sceneObjects["winText"] = SceneObject(font1.render(lang["win"], 1, textColor1), 0.5, 0, 0.4, 0)
                
                if self.sceneData["reason"] == "allCardsGone":
                    self.sceneObjects["reason"] = SceneObject(font3.render(lang["allCardsGone_me"], 1, textColor1), 0.5, 0, 0.4, font1.get_height()+10)
                elif self.sceneData["reason"] == "tooManyCards":
                    self.sceneObjects["reason"] = SceneObject(font3.render(lang["tooManyCards_other"], 1, textColor1), 0.5, 0, 0.4, font1.get_height()+10)
            else:
                self.sceneObjects["winText"] = SceneObject(font1.render(lang["lost"], 1, textColor1), 0.5, 0, 0.4, 0)
                
                if self.sceneData["reason"] == "allCardsGone":
                    self.sceneObjects["reason"] = SceneObject(font3.render(lang["allCardsGone_other"], 1, textColor1), 0.5, 0, 0.4, font1.get_height()+10)
                elif self.sceneData["reason"] == "tooManyCards":
                    self.sceneObjects["reason"] = SceneObject(font3.render(lang["tooManyCards_me"], 1, textColor1), 0.5, 0, 0.4, font1.get_height()+10)
            
            self.sceneObjects["playAgainButton"] = button(font3.render(lang["playAgain"], 1, textColor1), 0.5, 0, 1, -font3.get_height()*2, onClickCallback=self.e_onPlayAgainButtonClick)
            self.sceneObjects["playAgainButton"].setButtonColor(bgColor2)
        
        def e_onPlayAgainButtonClick(self, *args):
            self.userInput()
            self.sceneObjects["playAgainButton"].setHidden(True)
    
    class GameScene(EmptyScene):
        def load(self):
            self.bgColor = bgColor1
            
            self.sceneData["layout"] = {
                "cardDeck": (0.2, 0, 0.5, 0),
                "discardDeck": (0.8, 0, 0.5, 0),
                "myCards": (0, cardSize[0]/2 + 10, 1, -(cardSize[1]/2+10)),#(0, cardSize[0]/2 + 10, 1, -(cardSize[1]/2 + 10)),
                "theirCards": (0, cardSize[0]/2 + 10, 0, cardSize[1]/2+10),#(0, cardSize[0]/2 + 10, 0, cardSize[1]/2 + 10),
                "playerOnTurnText": (0.5, 0, 0.5, 0)
            }
            
            self.animations = Animations()
            
            self.sceneObjects["cardDeck"] = SceneObject(images["cardDeck"], *self.sceneData["layout"]["cardDeck"], zIndex=-2)
            self.sceneObjects["lastPlayedCard"] = SceneObject(images["hiddenCard"], *self.sceneData["layout"]["discardDeck"], zIndex=1)
            self.sceneObjects["playerOnTurnText"] = SceneObject(font3.render("", 1, textColor1), *self.sceneData["layout"]["playerOnTurnText"])
            self.sceneObjects["lastPlayedCardSuit"] = SceneObject(images["suits"]["h"], *addTuples(self.sceneData["layout"]["discardDeck"], (0, cardSize[0]/2 + suitSize[0]/2 + 20, 0, 0)))
            self.sceneObjects["lastPlayedCardSuit"].setHidden(True)
            
            self.sceneObjects["takeButton"] = button(font4.render("", 1, textColor1), *self.sceneData["layout"]["cardDeck"], zIndex=-1, onClickCallback=self.e_onTakeButtonClick)
            self.sceneObjects["takeButton"].setButtonColor(bgColor2)
            self.sceneObjects["takeButton"].setHidden(True)
        
        def sceneUpdate(self, updateData):
            me = self.sceneData["me"]
            them = [key for key in updateData["cardsOnHands"] if key != me][0]
            
            try:
                myCardsBefore = self.sceneData["cardsOnHands"][me]
                theirCardsBefore = self.sceneData["cardsOnHands"][them]
            except KeyError:
                myCardsBefore = []
                theirCardsBefore = []
            
            self.sceneData["cardsOnHands"] = updateData["cardsOnHands"]
            self.sceneObjects["lastPlayedCard"].zIndex = -1
            
            myCardsNow = updateData["cardsOnHands"][me]
            theirCardsNow = updateData["cardsOnHands"][them]
            
            myCardsNew, myCardsGone = listsRemoveSame(myCardsNow, myCardsBefore)
            theirCardsNew, theirCardsGone = listsRemoveSame(theirCardsNow, theirCardsBefore)
            
            #all gone cards
            
            for goneCard in myCardsGone+theirCardsGone:
                cardInScene = self.sceneObjects[goneCard]
                
                self.animations.animate(cardInScene, self.sceneData["layout"]["discardDeck"], animDuration)
            
            #my new cards
            
            for newCard in myCardsNew:
                self.addCardToScene(
                    newCard,
                    images["cards"][newCard],
                    # self.sceneData["layout"]["myCards"],
                    # self.sceneData["layout"]["cardDeck"],
                    # len(myCardsNow),
                    self.e_onCardClick
                )
            
            #their new cards
            
            for newCard in theirCardsNew:
                self.addCardToScene(
                    newCard,
                    images["hiddenCard"],
                    # self.sceneData["layout"]["theirCards"],
                    # self.sceneData["layout"]["cardDeck"],
                    # len(theirCardsNow),
                    None
                )
            
            #animate cards on hands
            
            for i in range(len(myCardsNow)):
                cardInScene = self.sceneObjects[myCardsNow[i]]
                
                targetPos = addTuples(
                    self.sceneData["layout"]["myCards"],
                    multTupleWithNum(
                        (0, cardSize[0] + 10, 0, 0),
                        i
                    )
                )
                
                self.animations.animate(cardInScene, targetPos, animDuration)
            
            for i in range(len(theirCardsNow)):
                cardInScene = self.sceneObjects[theirCardsNow[i]]
                
                targetPos = addTuples(
                    self.sceneData["layout"]["theirCards"],
                    multTupleWithNum(
                        (0, cardSize[0] + 10, 0, 0),
                        i
                    )
                )
                
                self.animations.animate(cardInScene, targetPos, animDuration)
            
            #remove card sceneObjects on discardDeck
            
            for objName in list(self.sceneObjects.keys()):
                obj = self.sceneObjects[objName]
                
                if objName != "lastPlayedCard" and (obj.xPos, obj.xOffset, obj.yPos, obj.yOffset) == self.sceneData["layout"]["discardDeck"]:
                    self.sceneObjects.pop(objName)
            
            #hide takeButton when not on turn
            
            if updateData["playerOnTurn"] != me:
                self.sceneObjects["takeButton"].setHidden(True)
            
            #after anims finished
            
            time.sleep(animDuration)
            
            #make sure lastPlayedCard is always on the discardDeck
            
            self.sceneObjects["lastPlayedCard"].surface = images["cards"][updateData["lastPlayedCard"][:2]]
            self.sceneObjects["lastPlayedCard"].zIndex = 1
            
            self.sceneObjects["lastPlayedCardSuit"].surface = images["suits"][updateData["lastPlayedCard"][-1]]
            
            if updateData["lastPlayedCard"][0] == "q":
                self.sceneObjects["lastPlayedCardSuit"].setHidden(False)
            else:
                self.sceneObjects["lastPlayedCardSuit"].setHidden(True)
            
            #say who is on turn
            
            if updateData["playerOnTurn"] == me:
                self.sceneObjects["playerOnTurnText"].surface = font3.render(lang["playerOnTurn_me"], 1, textColor1)
                
                if updateData["lastPlayedCard"][0] == "a" and not updateData["lastCardIsOld"]:
                    self.sceneObjects["takeButton"].surface = font4.render(lang["aceReaction"], 1, textColor1)
                else:
                    self.sceneObjects["takeButton"].surface = font4.render(lang["takeCards"], 1, textColor1)
                
                self.sceneObjects["takeButton"].setHidden(False)
            else:
                self.sceneObjects["playerOnTurnText"].surface = font3.render(lang["playerOnTurn_other"], 1, textColor1)
        
        def addCardToScene(self, card, img, onClickCallback):#(self, card, img, finalPosBase, startPos, numOfCardsNow, onClickCallback):
            # targetPos = addTuples(
                # finalPosBase,
                # multTupleWithNum(
                    # (0, cardSize[0] + 10, 0, 0),
                    # numOfCardsNow
                # )
            # )
            
            self.sceneObjects[card] = SceneObject(
                img,
                *self.sceneData["layout"]["cardDeck"],#*startPos,
                onClickCallback=onClickCallback
            )
            
            # self.animations.animate(self.sceneObjects[card], targetPos, animDuration)
            self.sceneObjects[card].cardName = card
        
        def e_onTakeButtonClick(self, *args):
            self.sceneObjects["takeButton"].setHidden(True)
            self.userInput("")
        
        def e_onCardClick(self, sceneObj):
            card = sceneObj.cardName
            self.userInput(card)
    
    class QCardChoice(EmptyScene):
        def load(self):
            self.bgColor = bgColor1
            
            self.sceneObjects["title"] = SceneObject(font2.render(lang["qCardPrompt"], 1, textColor1), 0.5, 0, 0.4, 0)
            self.sceneObjects["hButton"] = SceneObject(images["suits"]["h"], 0.5, -1.5*suitSize[0], 0.6, 0, onClickCallback=self.e_onHButtonClick)
            self.sceneObjects["sButton"] = SceneObject(images["suits"]["s"], 0.5, -0.5*suitSize[0], 0.6, 0, onClickCallback=self.e_onSButtonClick)
            self.sceneObjects["dButton"] = SceneObject(images["suits"]["d"], 0.5, 0.5*suitSize[0], 0.6, 0, onClickCallback=self.e_onDButtonClick)
            self.sceneObjects["cButton"] = SceneObject(images["suits"]["c"], 0.5, 1.5*suitSize[0], 0.6, 0, onClickCallback=self.e_onCButtonClick)
        
        def choiceMade(self, choice):
            self.sceneData["callback"](self.sceneData["originalCard"]+choice, self.sceneData["gameScene"])
        
        def e_onHButtonClick(self, *args):
            self.choiceMade("h")
        
        def e_onSButtonClick(self, *args):
            self.choiceMade("s")
        
        def e_onDButtonClick(self, *args):
            self.choiceMade("d")
        
        def e_onCButtonClick(self, *args):
            self.choiceMade("c")
    
    return {
        "choice": Choice,
        "ipInput": IPInput,
        "portInput": PortInput,
        "notif": Notif,
        "winner": Winner,
        "game": GameScene,
        "qCardChoice": QCardChoice,
    }