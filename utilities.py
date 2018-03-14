import pygame
from enum import Enum

class ItemTypes(Enum): # Types d'objets pouvant exister
        WEAPON=1
        HEALTH=2
        AMMO=3

class Item: # Définis un objet pouvant être utilisé par le joueur
        def __init__(self, name, type, value):
                self.name = name
                self.sprite = pygame.image.load("Resources/Items/Sprites/" + self.name + ".png")
                self.type = type # Une des options définis par le enum ItemTypes
                self.value = value # La puissance de l'arme, le nombre de points de vies rétablies...

class Map: # Définis une carte jouable
        def __init__(self, name, baseScreen, objectifCoords, items, spawnCoords = (0, 0)):
                self.name = name
                self.baseScreen = baseScreen # La fenètre principale
                self.background = pygame.image.load("Resources/Maps/Sprites/" + self.name + ".png")
                self.spawnCoords = spawnCoords # Où le joueur apparait en début de partie
                self.objectifCoords = objectifCoords # Où se trouve l'objectif à atteindre
                self.mapItems = {} # Dictionnaire de tous les items de la map. Clés: coordonnées de l'objet, Valeur: instance de le classe Item définissant l'objet en question
                with open("Resources/Maps/Data/" + self.name + ".txt") as mapItemsFile: # Récupère et assigne les items pour cette map
                        for line in mapItemsFile.readlines():
                                data = line.strip().split(',')
                                for item in items: # Retrouve l'items grâce au nom
                                        if item.name == data[0]:
                                                self.mapItems[(int(data[1]), int(data[2]))] = item # dictionary[key] = value
                self.mapObstacles = []
                with open("Resources/Maps/Obstacles/" + self.name + ".txt") as obstacleFile: 
                        for line in obstacleFile.readlines():
                                data = line.split(',')
                                self.mapObstacles.append(Obstacle(int(data[0]), int(data[1]), (int(data[2]), int(data[3]))))

                backgroundSize = self.background.get_rect().size # Récupère la taille de l'image de la map
                self.baseScreen = pygame.display.set_mode(backgroundSize) # Définis la taille de la fenètre par rapport à la map

        def load(self): # Charge la map
                self.baseScreen.blit(self.background, (0, 0)) # Affiche l'image de la map
                for k, v in self.mapItems.items(): # Itère le dictionnaire des items présents sur cette map
                         self.baseScreen.blit(v.sprite, k) # Affiche l'image de l'items aux coordonées définies
        
        def mod(self, backgroundNumber): # Met à jour l'image de la map sans avoir a créer une nouvelle instance de cette classe
                self.background = pygame.image.load("Resources/Maps/Sprites/" + self.backgroundPath + str(backgroundNumber) + ".png")
                self.baseScreen.blit(self.background, (0, 0))

class Perso:
        def __init__(self, name, fenetre, speed, map):
                self.name = name
                self.fenetre = fenetre
                self.image = pygame.image.load("Resources/Persos/" + name + ".png").convert_alpha()
                self.rect = self.image.get_rect()
                self.rect = self.rect.move(map.spawnCoords)
                self.speed = speed
                self.map = map
                
        def load(self):
                self.fenetre.blit(self.image, self.rect)

        def mouv(self,event):
                if event.key == pygame.K_UP:
                        self.rect=self.rect.move(0,-self.speed)
                        if self.rect.collidelist(self.map.mapObstacles) != -1:
                                self.rect=self.rect.move(0,self.speed)
                if event.key == pygame.K_DOWN:
                        self.rect=self.rect.move(0,self.speed)
                        if self.rect.collidelist(self.map.mapObstacles) != -1:
                                self.rect=self.rect.move(0,-self.speed)
                if event.key == pygame.K_LEFT:
                        self.rect=self.rect.move(-self.speed,0)   
                        if self.rect.collidelist(self.map.mapObstacles) != -1:     
                                self.rect=self.rect.move(self.speed, 0)        
                if event.key == pygame.K_RIGHT:
                        self.rect=self.rect.move(self.speed,0)
                        if self.rect.collidelist(self.map.mapObstacles) != -1:
                                self.rect=self.rect.move(-self.speed, 0)

class Obstacle:
        def __init__(self, length, width, coords = (0,0)) :
                self.rect = pygame.Rect(coords[0],coords[1], width, length)

        def load(self, screen):
                pygame.draw.rect(screen, pygame.Color(255, 255, 255, 100), self.rect)



        




        
        

                


        

                
        

                



                
                        

