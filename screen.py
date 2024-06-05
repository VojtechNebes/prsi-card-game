import pygame as _pygame
from threading import Thread as _Thread
import time as _time

from others.events import Events as _Events
from scenes import CreateScenes as _CreateScenes


_pygame.init()

class _SceneObject:
    def __init__(self, surface, xPos, xOffset, yPos, yOffset, zIndex=0, posInCenter=True, onClickCallback=None):
        self.surface = surface
        self.xPos, self.xOffset, self.yPos, self.yOffset = xPos, xOffset, yPos, yOffset
        self.zIndex = zIndex
        self.posInCenter = posInCenter
        self.onClickCallback = onClickCallback
        
        self.hidden = False
    
    def getPygamePosOnSurface(self, targetSurface, originalPos=None):
        if originalPos == None:
            originalPos = (self.xPos, self.xOffset, self.yPos, self.yOffset)
        
        xPos, xOffset, yPos, yOffset = originalPos
        targetRect = targetSurface.get_rect()
        
        if self.posInCenter:
            selfRect = self.surface.get_rect()
            
            pygamePos = (
                int(targetRect.w * xPos + xOffset - selfRect.w/2),
                int(targetRect.h * yPos + yOffset - selfRect.h/2),
            )
        else:
            pygamePos = (
                int(targetRect.w * xPos + xOffset),
                int(targetRect.h * yPos + yOffset),
            )
        
        return pygamePos
    
    def setHidden(self, hide=None):
        if hide == None:
            hide = not self.hidden
        
        self.hidden = hide
    
    def draw(self, targetSurface):
        targetSurface.blit(self.surface, self.getPygamePosOnSurface(targetSurface))

class _EmptyScene:
    def __init__(self, screen, setScene, onUserInputCallback=None, dataForScene={}):
        self.screen = screen
        self.setScene = setScene
        self._onUserInputCallback = onUserInputCallback
        
        self.bgColor = (0, 0, 0)
        self.sceneObjects = {}
        self.sceneData = dataForScene
        
        self._events = {}
        
        self.load()
    
    def addEvent(self, event, reaction):
        try:
            self._events[event].append(reaction)
        except KeyError:
            self._events[event] = [reaction]
    
    def load(self):
        pass
    
    def userInput(self, userInput=None):
        if self._onUserInputCallback:
            self._onUserInputCallback(userInput)
    
    def sceneUpdate(self, updateData):
        pass
    
    def draw(self):
        self.screen.fill(self.bgColor)
        
        sceneObjects = list(self.sceneObjects.values())
        
        sceneObjects.sort(key=lambda obj: obj.zIndex)
        
        for obj in sceneObjects:
            if not obj.hidden:
                obj.draw(self.screen)

class Screen(_Thread):
    _isOpen = False
    
    def __init__(self):
        super().__init__()
        
        self.events = _Events("onPygameDied")
        
        self._clock = _pygame.time.Clock()
        
        # print("creating scenes")
        self._screen = None
        self._scenes = _CreateScenes(_EmptyScene, _SceneObject)
        
        self._onUserInputCallback = None
        
        # print("starting screen thread")
        
        self._isOpen = True
        self.start()
    
    def run(self):
        self._screen = _pygame.display.set_mode((960, 540))#((1920, 1080))#((960, 540))
        self._scene = _EmptyScene(self._screen, self.setScene)
        
        while self._isOpen == True:
            # print("------------------screen is open-----------------------")
            for event in _pygame.event.get():
                # print(event)
                
                if event.type == _pygame.QUIT:
                    self._quitPygame()
                    return
                
                if event.type == _pygame.MOUSEBUTTONUP:
                    # print(f"CLICKED on position {event.pos}")
                    for sceneObject in list(self._scene.sceneObjects.values()):
                        if sceneObject.hidden or not sceneObject.onClickCallback:
                            continue
                        
                        objRect = sceneObject.surface.get_rect()
                        objPygamePos = sceneObject.getPygamePosOnSurface(self._screen)
                        
                        if event.pos[0] >= objPygamePos[0] and event.pos[0] <= objPygamePos[0]+objRect.w and event.pos[1] >= objPygamePos[1] and event.pos[1] <= objPygamePos[1]+objRect.h:
                            # print(f"clicked on {sceneObject}")
                            sceneObject.onClickCallback(sceneObject)
                        # else: print(f"didnt click on {sceneObject}")
                
                try: reactions = self._scene._events[event.type]
                except KeyError: pass
                else:
                    for reaction in reactions:
                        # _Thread(target=reaction, args=(event))
                        reaction(event)
            
            try:
                self._scene.draw()
            except _pygame.error as e:
                self._quitPygame()
                return
            else:
                _pygame.display.update()
            
            self._clock.tick(60)
    
    def _quitPygame(self):
        self._isOpen = False
        _pygame.quit()
        self.events.onPygameDied._fire()
    
    def setCaption(self, caption):
        _pygame.display.set_caption(caption)
    
    def setScene(self, sceneName, onUserInputCallback=None, dataForScene={}):
        if not self._isOpen: return
        while self._screen == None: _time.sleep(.1)
        self._scene = self._scenes[sceneName](self._screen, self.setScene, onUserInputCallback=onUserInputCallback, dataForScene=dataForScene)
    
    def sendSceneUpdate(self, updateData):
        if not self._isOpen: return
        while self._screen == None: _time.sleep(.1)
        
        self._scene.sceneUpdate(updateData)