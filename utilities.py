import pygame
import copy
import math
import random

class Item: # Définis un objet pouvant être utilisé par le joueur
        def __init__(self, name, type, value, characteristics = None):
                if name.lower == "none":
                        raise ValueError("Ne pas utiliser 'none' comme nom d'item!")
                else:
                        self.name = name
                        self.sprite = pygame.image.load("Resources/Items/Sprites/" + self.name + ".png")
                        self.type = type # Une des options définis par le enum ItemTypes
                        self.value = value # La puissance de l'arme, le nombre de points de vies rétablies...
                        self.rect = self.sprite.get_rect() # Les coordonnées et la taille de l'item. La taille est définis par la taille du sprite de l'item
                        if type == "WEAPON": # Si l'item est du type 'Weapon', charger d'autres caractéristiques
                                self.characteristics = characteristics

        def draw(self, coords, screen):
                screen.blit(self.sprite, coords)

        def __deepcopy__(self, memo): # https://stackoverflow.com/a/15774013
                cls = self.__class__
                result = cls.__new__(cls)
                memo[id(self)] = result
                for k, v in self.__dict__.items():
                        if k == "rect":
                                setattr(result, k, copy.deepcopy(v, memo))
                        else:
                                setattr(result, k, copy.copy(v))
                return result


class Weapon: # Classe auxiliaire pour définir les caractéristiques d'une arme
        def __init__(self, aim = 95, speed = 20, isExplosive = False):
                self.aim = aim # La précision de tir en pourcentage. 100% correspond à une ligne droite
                self.speed = speed # La vitesse du projectile
                self.isExplosive = isExplosive # Définis si le projectile explose sur impact (ce qui fait des dégats plus répandus)


class Hitbox:
        def __init__(self, coords, size):
                self.rect = pygame.Rect(coords, size)

        def draw(self, coords, screen):
                pygame.draw.rect(screen, pygame.Color(191, 63, 63, 127), pygame.Rect(coords[0], coords[1], self.rect.w, self.rect.h))


class Obstacle: # Définis des obstacles en perspective et qui présente une hitbox
        def __init__(self, name, hitbox):
                self.name = name
                self.lowerSprite = pygame.image.load("Resources/Obstacles/Sprites/" + name + "Lower.png").convert_alpha() # La partie basse de l'objet qui doit toujours se trouver derrière le joueur
                self.upperSprite = pygame.image.load("Resources/Obstacles/Sprites/" + name + "Upper.png").convert_alpha() # La partie haute de l'objet qui doit toujours se trouver devant le joueur
                self.rect = self.lowerSprite.get_rect()
                self.hitbox = hitbox # La hitbox associé à l'objet
                self.lowerDrawn = False # Booléen définissant quelle partie de l'objet doit être dessiné. False: partie basse, True: partie haute

        def draw(self, coords, screen): # Dessine l'objet en deux parties s'alternant. La partie basse est toujours dessiné avant la partie haute
                if self.lowerDrawn: # Dessiner la partie haute
                        screen.blit(self.upperSprite, coords)
                        self.lowerDrawn = False
                else: # Dessiner la partie basse
                        screen.blit(self.lowerSprite, coords)
                        self.lowerDrawn = True

        def __deepcopy__(self, memo): # https://stackoverflow.com/a/15774013
                cls = self.__class__
                result = cls.__new__(cls)
                memo[id(self)] = result
                for k, v in self.__dict__.items():
                        if k == "rect":
                                setattr(result, k, copy.deepcopy(v, memo))
                        else:
                                setattr(result, k, copy.copy(v))
                return result


class Enemy: # Définis un ennemis qui va tenter d'attaquer les joueurs s'ils se trovent suffisament proche
        def __init__(self, name, screen, map, speed, health, viewingRadius, reactionTime, weapons):
                self.name = name # Le nom de l'ennemis
                self.sprite = pygame.image.load("Resources/Enemies/Sprites/" + name + ".png").convert_alpha() # l'image de l'ennemis
                self.rect = self.sprite.get_rect() # Le rectangle définissant la hitbox de l'ennemis
                self.screen = screen # La surface sur laquelle l'ennemis doit être affiché
                self.speed = speed # La vitesse de l'ennemis
                self.map = map # La map sur laquelle se trouve l'ennemis
                self.health = health # Les points de vie de l'ennemis
                self.viewingRadius = viewingRadius # Le radius auxquel l'ennemis "voit" un joueurs
                self.reactionTime = reactionTime # Le "temps de réaction" de l'ennemis. Correspond à la distance minimale parcouru par le joueur le plus proche pour que l'ennemis change sa trajectoire
                self.weapons = weapons # Arme que l'ennemis pourrait porter
                self.pathFinder = PathFinder(self.map.hitboxes, max(self.rect.width, self.rect.height), self.viewingRadius) # Le chercheur de chemin de l'ennemis, pour trouver le chemin le plus rapide vers les joueurs en tenant en compte les obstacles
                self.lastPlayerPos = None # La dernière position du joueur se trouvant le plus proche de l'ennemis
                self.idleTime = 0 # Temps d'immobilité de l'ennemis entre chaque mouvement aléatoire (tant qu'aucun joueur est proche)

        def draw(self, coords, screen): # Dessine l'ennemis aux bonnes coordonnées écran
                screen.blit(self.sprite, coords)

        def distanceBetween(self, pointA, pointB): # Retourne la distance entre un point A et un point B
                return math.sqrt(math.pow(pointA[0] - pointB[0], 2) + math.pow(pointA[1] - pointB[1], 2))

        def atan2Normalized(self, y, x): # Retourne l'angle d'un point par rapport à l'origine du repère (https://stackoverflow.com/a/10343477)
                result = math.atan2(y, x)
                if result < 0: # Ajoute 2π à l'angle s'il est négatif 
                        result += 2 * math.pi
                return result

        def randomPath(self): # Trouve un chemin aléatoire si aucun joueur se trouve à proximité de l'ennemis
                dest = None
                while not dest or any([x for x in self.map.hitboxes if x.rect.collidepoint(dest)]): # Tant que la destination ne se trouve pas dans une hitbox
                        randomAngle = random.randint(0, 360) # Angle aléatoire
                        randomDistance = random.randint(self.speed, self.viewingRadius / 2) # Distance aléatoire entre la vitesse de l'ennemi et le radius de visibilité divisé par 2
                        dest = (round(self.rect.centerx + randomDistance * math.cos(randomAngle * math.pi / 180)), round(self.rect.centery + randomDistance * math.sin(randomAngle * math.pi / 180))) # Trouve la destination à l'aide de trigonométrie
                self.pathFinder.findBest(self.rect.center, dest) # Trouve le meilleur chemin pour atteindre la destination

        def moveTowards(self, coords): # Bouge les coordonnées de l'ennemis vers les coordonnées indiqué
                angle = self.atan2Normalized((self.rect.centery - coords[1]), (coords[0] - self.rect.centerx)) # Angle de la destination par rapport au personnage dans la plan du repère
                coords = (self.speed * round(math.cos(angle), 5), -self.speed * round(math.sin(angle), 5)) # Trouve les coefficients avec lesquels incrémenté les coordonnées de l'ennemi pour atteindre la destination à l'aide de trigonométrie
                self.rect.move_ip(coords[0], coords[1]) # Incrémente les coordonnées de l'ennemis par le coefficient calculé auparavant

        def move(self): # Trouve une destination et incrémente les coordonnées du perso vers celle-ci
                radiusPlayers = [x for x in self.map.players if self.distanceBetween(self.rect.center, x.rect.center) <= self.viewingRadius] # Liste des joueurs se trouvant dans le radius de visibilité de l'ennemis
                radiusPlayers.sort(key = lambda x: self.distanceBetween(self.rect.center, x.rect.center)) # Classe les joueurs du plus proche au plus éloigné
                if any(radiusPlayers): # Si au moins un joueur se trouve dans la zone de visibilité de l'ennemis
                        if self.lastPlayerPos: # Si ce joueur a déjà été visé auparavant
                                if (self.distanceBetween(self.lastPlayerPos, radiusPlayers[0].rect.center) >= self.reactionTime or self.rect.center == self.lastPlayerPos) and not self.rect.center == radiusPlayers[0]: # Si le joueur a bougé plus que le temps de réaction, que l'ennemis se trouve sur la dernière position du joueur mais pas sur le joueur 
                                        self.pathFinder.findBest(self.rect.center, radiusPlayers[0].rect.center) # Cherche le chemin le plus rapide vers le joueur
                                        self.lastPlayerPos = radiusPlayers[0].rect.center # Met à jour la dernière position du joueur
                        else:
                                self.pathFinder.findBest(self.rect.center, radiusPlayers[0].rect.center) # Cherche le chemin le plus rapide vers le joueur
                                self.lastPlayerPos = radiusPlayers[0].rect.center # Met à jour la dernière position du joueur
                elif (not self.pathFinder.path and self.rect.center == self.pathFinder.finish) or not self.pathFinder.finish: # Si l'ennemis n'a pas déjà une destination et un chemin
                        if self.idleTime > 0: # Si l'ennemis doit encore attendre 
                                self.idleTime -= 1
                        else:
                                self.randomPath() # Trouver un chemin aléatoire
                                self.idleTime = random.randint(self.reactionTime, self.speed * 50) # Définis un temps d'attente aléatoire à partir de la vitesse de l'ennemis


                if self.pathFinder.path: # Si l'ennemis a un chemin 
                        if self.distanceBetween(self.rect.center, self.pathFinder.path[0].rect.center) <= self.speed: # Si la distance entre l'ennemis et le prochain node du chemin est plus petite que la vitesse de l'ennemis
                                self.pathFinder.path.pop(0) # Enlève ce node du chemin
                        else:
                                self.moveTowards(self.pathFinder.path[0].rect.center) # Marche en direction du prochain node du chemin
                else: # Si l'ennemis n'a plus de chemin mais n'a pas encore atteint sa destination
                        if self.distanceBetween(self.rect.center, self.pathFinder.finish) <= self.speed: # Si la distance entre l'ennemis et la fin est plus petite que la vitesse de marche de l'ennemis
                                self.rect.center = self.pathFinder.finish # Place l'ennemis directement sur la fin
                        else:
                                self.moveTowards(self.pathFinder.finish) # Marche vers la fin


class Map: # Définis une carte jouable
        def __init__(self, name, screen, objectifCoords, items, obstacles, spawnCoords):
                self.name = name
                self.screen = screen # La fenètre principale
                self.background = pygame.image.load("Resources/Maps/Sprites/" + self.name + ".png").convert() # Charge l'image de fond d'écran
                self.size = self.background.get_size() # Définis la taille de la map à partir de l'image de fond d'écran
                self.objectifCoords = objectifCoords # Où se trouve l'objectif à atteindre
                self.items = [] # Dictionnaire de tous les items de la map. Clés: coordonnées de l'objet, Valeur: instance de le classe Item définissant l'objet en question
                with open("Resources/Maps/Items/" + self.name + ".txt") as itemsFile: # Récupère et assigne les items pour cette map
                        for line in itemsFile.readlines():
                                data = line.strip().split(',')
                                for item in items: # Retrouve l'items grâce au nom
                                        if item.name == data[0]:
                                                temp = copy.deepcopy(item) # Recrée l'item dans une nouvelle variable afin de pouvoir le modifier sans modifier l'original
                                                temp.rect.move_ip(int(data[1]), int(data[2])) # Change les coordonnées de la copie de l'item aux coordonnées définies
                                                self.items.append(temp)
                                                break
                self.hitboxes = [] # Récupère les hitbox de cette map
                with open("Resources/Maps/Hitboxes/" + self.name + ".txt") as hitboxFile:
                        for line in hitboxFile.readlines():
                                data = line.split(',')
                                self.hitboxes.append(Hitbox((int(data[0]), int(data[1])), (int(data[2]), int(data[3]))))
                self.hitboxes.append(Hitbox((0, -1000), (self.size[0], 1000)))
                self.hitboxes.append(Hitbox((0, self.size[1]), (self.size[0], 1000)))
                self.hitboxes.append(Hitbox((-1000, -1000), (1000, self.size[1] + 2000)))
                self.hitboxes.append(Hitbox((self.size[0], -1000), (1000, self.size[1] + 2000)))

                self.obstacles = [] # Récupère les obstacles de cette map
                with open("Resources/Maps/Obstacles/" + self.name + ".txt") as obstaclesFile: # Récupère les obstacles pour cette map
                        for line in obstaclesFile.readlines():
                                data = line.strip().split(',')
                                for obstacle in obstacles: # Retrouve l'obstacle grâce au nom
                                        if obstacle.name == data[0]:
                                                temp = copy.deepcopy(obstacle) # Recrée l'obstacle dans une nouvelle variable afin de pouvoir le modifier sans modifier l'original
                                                temp.rect.move_ip(int(data[1]), int(data[2])) # Change les coordonnées de la copie de l'obstacle aux coordonnées définies
                                                self.obstacles.append(temp)
                                                self.hitboxes.append(Hitbox((temp.hitbox.rect.left + temp.rect.left, temp.hitbox.rect.top + temp.rect.top), temp.hitbox.rect.size)) # Ajoute aux hitbox de la map celle correspondant à cette obstacle. Les coordonnées sont définie par la hitbox au sein de l'obstacle et par l'emplacement de l'obstacle
                                                break
                self.enemies = [] # Liste des ennemis de cette map
                self.players = [] # Liste des joueurs de la map

        def appendEnemies(self, enemies):
                with open("Resources/Maps/Enemies/" + self.name + ".txt") as enemiesFile:
                        for line in enemiesFile.readlines():
                                data = line.strip().split(',')
                                for enemy in enemies: # Retrouve l'ennemis grâce au nom
                                        if enemy.name == data[0]:
                                                temp = copy.copy(enemy) # Recrée l'ennemis dans une nouvelle variable afin de pouvoir le modifier sans modifier l'original
                                                temp.rect.move_ip(int(data[1]), int(data[2])) # Change les coordonnées de la copie de l'ennemis aux coordonnées définies
                                                temp.fCoords = temp.rect.center
                                                self.enemies.append(temp)
                                                break

        def draw(self, screenRect, widthSmaller, heightSmaller): # Charge la map
                chosenX = 0 # Le côté gauche de la map
                chosenY = 0 # Le côté haut de la map
                chosenXs = screenRect.x # Le côté gauche de l'écran
                chosenYs = screenRect.y # Le côté haut de l'écran
                if widthSmaller: # Si la largeur de la map est inférieure à celle de l'écran
                        chosenX = screenRect.width / 2 - self.size[0] / 2 # Centre la map sur l'écran
                        chosenXs = 0
                if heightSmaller: # Si l'hauteur de la map est inférieure à celle de l'écran
                        chosenY = screenRect.height / 2 - self.size[1] / 2 # Centre la map sur l'écran
                        chosenYs = 0
                self.screen.blit(self.background, (chosenX, chosenY), pygame.Rect((chosenXs, chosenYs), screenRect.size)) # Affiche l'image de la map

        def mod(self, backgroundNumber): # Met à jour l'image de la map sans avoir a créer une nouvelle instance de cette classe
                self.background = pygame.image.load("Resources/Maps/Sprites/" + self.backgroundPath + str(backgroundNumber) + ".png")
                self.screen.blit(self.background, (0, 0))

        def drawObjects(self, objects, screenRect, isTransparent = False, alphaSurface = None): # Calcul les coordonnés écran d'une liste d'objets devant suivre une syntaxe stricte
                if objects: # Vérifie que la liste donnée n'est pas vide
                        for obj in objects:
                                if screenRect.colliderect(obj.rect): # Sélectionne tout les objets en collision avec le rectangle de l'écran, c'est à dire ceux qui devont être affiché
                                        if isTransparent:
                                                obj.draw((obj.rect.x - screenRect.x, obj.rect.y - screenRect.y), alphaSurface) # Place les objets à déssiner sur leurs emplacements écran
                                        else:
                                                obj.draw((obj.rect.x - screenRect.x, obj.rect.y - screenRect.y), self.screen) # Place les objets à déssiner sur leurs emplacements écran

        def moveEnemies(self):
                for enemy in self.enemies:
                        enemy.move()


class Perso:
        def __init__(self, name, fenetre, speed, maxItems, maxHealth, map):
                self.name = name
                self.fenetre = fenetre
                self.sprite = pygame.image.load("Resources/Persos/Sprites/" + name + ".png").convert_alpha()
                self.rect = self.sprite.get_rect() # Définis l'image du personnage comme un rectangle
                self.speed = speed # Vitesse de déplacement du personnage selon le choix du joueur
                self.maxItems = maxItems # Taille de l'inventaire
                self.map = map # Map dans laquelle on se trouve
                self.items = []
                self.health = maxHealth # Met le nombre de points de vie de départ au maximum
                self.maxhealth = maxHealth # Points de vie maximum que le perso peut avoir
                self.ammo = 25 # Le perso a 25 munitions au départ de la partie

        def draw(self, screenRect):
                chosenX = screenRect.w / 2 # Coordonnée X du joueur au centre de l'écran
                chosenY = screenRect.h / 2 # Coordonnée Y du joueur au centre de l'écran

                if screenRect.x <= 0 or screenRect.right == self.map.size[0]: # L'écran se trouve collé contre le bord droit ou gauche
                        chosenX = self.rect.x - screenRect.x # Coordonnée X écran du joueur
                if screenRect.y <= 0 or screenRect.bottom == self.map.size[1]: # L'écran se trouve collé contre le bord haut ou bas
                        chosenY = self.rect.y - screenRect.y # Coordonnée Y écran du joueur
                self.fenetre.blit(self.sprite, (chosenX, chosenY)) # Affiche l'image du personnage aux coordonnées écran

        def mouv(self, action):
            if action == "haut":
                self.rect.move_ip(0, -self.speed) # déplace le perso vers le haut
                if self.rect.collidelist(self.map.hitboxes) != -1: # si le perso se trouve sur un hitbox
                    self.rect.move_ip(0, self.speed) # Ramène le perso à la position précédente
            if action == "bas":
                self.rect.move_ip(0, self.speed) # déplace le perso vers le bas
                if self.rect.collidelist(self.map.hitboxes) != -1:
                    self.rect.move_ip(0, -self.speed)
            if action == "gauche":
                self.rect.move_ip(-self.speed, 0) # déplace le perso vers la gauche
                if self.rect.collidelist(self.map.hitboxes) != -1:
                    self.rect.move_ip(self.speed, 0)
            if action == "droite":
                self.rect.move_ip(self.speed, 0) # déplace le perso vers la droite
                if self.rect.collidelist(self.map.hitboxes) != -1:
                    self.rect.move_ip(-self.speed, 0)
            if action=="ramasser":
                if len(self.items) <= self.maxItems: # Vérifie que le perso a encore de la place dans son inventaire
                                for item in self.map.items: # Cherche dans la liste d'items de cette map
                                        if self.rect.colliderect(item.rect): # Vérifie si le perso se trouve sur un item
                                                if item.type == "HEALTH": #verifie que l'item est du type santé
                                                        if self.health < self.maxhealth : #vérifie que le perso n'est pas au max de sa vie
                                                                self.health = self.health + item.value #ajoute la valeur de l'item santé à la santé du perso
                                                                if self.health >= self.maxhealth :  # verifie si le niveau de santé ajouté dépasse la valeur maximale de santé
                                                                        self.health = self.maxhealth    #ramène le niveau de santé au maximum
                                                elif item.type == "AMMO":
                                                        self.ammo = self.ammo + item.value
                                                elif item.type == "WEAPON":
                                                    self.items.append(item) # Ajoute l'item à l'inventaire du perso

                                                self.map.items.remove(item) # Enlève l'item de la map
                                                break # Sort de la boucle


class PathFinder: # Classe permettant de trouver le chemin le plus rapide entre deux points en tenant compte des obstacles
        def __init__(self, hitboxes, precision, maxRadius):
                self.start = None # Le point de départ
                self.finish = None # Le point d'arrivé
                self.hitboxes = hitboxes # Les hitboxes a prendre en compte 
                self.precision = precision # La précision de la recherche 
                self.maxRadius = maxRadius # Radius maximale a ne pas dépasser pour la recherche 
                self.nodes = [] # La liste des "nodes"
                self.path = [] # Liste de "nodes" correspondant au chemin le plus rapide. Seulement aggrémenter avec findBest()

        def __nodeInHitbox(self, rect): # Vérifie si le rectangle d'un node se trouve sur des hitboxes
                if rect.collidelistall(self.hitboxes):
                                return True
                return False

        def __addNeighbourNodes(self, node): # Ajoute 8 nodes à la liste de nodes autour du node précisé si ils n'existent pas déjà et ne se trouvent pas sur des hitboxes
                # Vérifie que le node à la droite n'existe pas déja
                nextNodeCoords = (node.rect.x + node.rect.width, node.rect.y) # Position du prochain node 
                if (not [x for x in self.nodes if nextNodeCoords == x.rect.topleft] and not self.__nodeInHitbox(pygame.Rect(nextNodeCoords, (node.rect.width, node.rect.height)))) or pygame.Rect(nextNodeCoords, (node.rect.width, node.rect.height)).collidepoint(self.finish): # Si le node ne se trouve pas déjà sur l'emplacement d'un autre node et qu'il ne collisionne pas avec des hitboxes ou si un joueur se trouve dedans
                        # Ajoute le node de droite si elle n'existe pas déja
                        self.nodes.append(self.Node(nextNodeCoords, node.rect.width, node, 1, self.start, self.finish))
                        
                # Vérifie que le node à la gauche n'existe pas déja
                nextNodeCoords = (node.rect.x - node.rect.width, node.rect.y) # Position du prochain node 
                if (not [x for x in self.nodes if nextNodeCoords == x.rect.topleft] and not self.__nodeInHitbox(pygame.Rect(nextNodeCoords, (node.rect.width, node.rect.height)))) or pygame.Rect(nextNodeCoords, (node.rect.width, node.rect.height)).collidepoint(self.finish): # Si le node ne se trouve pas déjà sur l'emplacement d'un autre node et qu'il ne collisionne pas avec des hitboxes ou si un joueur se trouve dedans
                        # Ajoute le node de gauche si elle n'existe pas déja
                        self.nodes.append(self.Node(nextNodeCoords, node.rect.width, node, 1, self.start, self.finish))

                # Vérifie que le node au dessus n'existe pas déja
                nextNodeCoords = (node.rect.x, node.rect.y - node.rect.width) # Position du prochain node 
                if (not [x for x in self.nodes if nextNodeCoords == x.rect.topleft] and not self.__nodeInHitbox(pygame.Rect(nextNodeCoords, (node.rect.width, node.rect.height)))) or pygame.Rect(nextNodeCoords, (node.rect.width, node.rect.height)).collidepoint(self.finish): # Si le node ne se trouve pas déjà sur l'emplacement d'un autre node et qu'il ne collisionne pas avec des hitboxes ou si un joueur se trouve dedans
                        # Ajoute le node au dessus si elle n'existe pas déja
                        self.nodes.append(self.Node(nextNodeCoords, node.rect.width, node, 1, self.start, self.finish))

                # Vérifie que le node en dessous n'existe pas déja
                nextNodeCoords = (node.rect.x, node.rect.y + node.rect.width) # Position du prochain node 
                if (not [x for x in self.nodes if nextNodeCoords == x.rect.topleft] and not self.__nodeInHitbox(pygame.Rect(nextNodeCoords, (node.rect.width, node.rect.height)))) or pygame.Rect(nextNodeCoords, (node.rect.width, node.rect.height)).collidepoint(self.finish): # Si le node ne se trouve pas déjà sur l'emplacement d'un autre node et qu'il ne collisionne pas avec des hitboxes ou si un joueur se trouve dedans
                        # Ajoute le node en dessous si elle n'existe pas déja
                        self.nodes.append(self.Node(nextNodeCoords, node.rect.width, node, 1, self.start, self.finish))

                # Vérifie que le node à la droite en haut n'existe pas déja
                nextNodeCoords = (node.rect.x + node.rect.width, node.rect.y - node.rect.width) # Position du prochain node 
                if (not [x for x in self.nodes if nextNodeCoords == x.rect.topleft] and not self.__nodeInHitbox(pygame.Rect(nextNodeCoords, (node.rect.width, node.rect.height)))) or pygame.Rect(nextNodeCoords, (node.rect.width, node.rect.height)).collidepoint(self.finish): # Si le node ne se trouve pas déjà sur l'emplacement d'un autre node et qu'il ne collisionne pas avec des hitboxes ou si un joueur se trouve dedans
                        # Ajoute le node à la droite en haut si elle n'existe pas déja
                        self.nodes.append(self.Node(nextNodeCoords, node.rect.width, node, 1, self.start, self.finish))

                # Vérifie que le node à la droite en bas n'existe pas déja
                nextNodeCoords = (node.rect.x + node.rect.width, node.rect.y + node.rect.width) # Position du prochain node 
                if (not [x for x in self.nodes if nextNodeCoords == x.rect.topleft] and not self.__nodeInHitbox(pygame.Rect(nextNodeCoords, (node.rect.width, node.rect.height)))) or pygame.Rect(nextNodeCoords, (node.rect.width, node.rect.height)).collidepoint(self.finish): # Si le node ne se trouve pas déjà sur l'emplacement d'un autre node et qu'il ne collisionne pas avec des hitboxes ou si un joueur se trouve dedans
                        # Ajoute le node à la droite en bas si elle n'existe pas déja
                        self.nodes.append(self.Node(nextNodeCoords, node.rect.width, node, 1, self.start, self.finish))

                # Vérifie que le node à la gauche en haut n'existe pas déja
                nextNodeCoords = (node.rect.x - node.rect.width, node.rect.y - node.rect.width) # Position du prochain node 
                if (not [x for x in self.nodes if nextNodeCoords == x.rect.topleft] and not self.__nodeInHitbox(pygame.Rect(nextNodeCoords, (node.rect.width, node.rect.height)))) or pygame.Rect(nextNodeCoords, (node.rect.width, node.rect.height)).collidepoint(self.finish): # Si le node ne se trouve pas déjà sur l'emplacement d'un autre node et qu'il ne collisionne pas avec des hitboxes ou si un joueur se trouve dedans
                        # Ajoute le node à la gauche en haut si elle n'existe pas déja
                        self.nodes.append(self.Node(nextNodeCoords, node.rect.width, node, 1, self.start, self.finish))

                # Vérifie que le node à la gauche en bas n'existe pas déja
                nextNodeCoords = (node.rect.x - node.rect.width, node.rect.y + node.rect.width) # Position du prochain node 
                if (not [x for x in self.nodes if nextNodeCoords == x.rect.topleft] and not self.__nodeInHitbox(pygame.Rect(nextNodeCoords, (node.rect.width, node.rect.height)))) or pygame.Rect(nextNodeCoords, (node.rect.width, node.rect.height)).collidepoint(self.finish): # Si le node ne se trouve pas déjà sur l'emplacement d'un autre node et qu'il ne collisionne pas avec des hitboxes ou si un joueur se trouve dedans
                        # Ajoute le node à la gauche en bas si elle n'existe pas déja
                        self.nodes.append(self.Node(nextNodeCoords, node.rect.width, node, 1, self.start, self.finish))

                node.state = 2 # Change l'état du node pour qu'il ne soit pas pris en compte une deuxième fois par closestNode()

        def __closestNode(self, includeChecked): # Indique le node le plus proche du point de fin dans la liste de nodes
                smallestTLList = [] # "Smallest Total Lengths List" - liste des nodes dont la longueur totale (longueur au début + longueur à la fin) est la plus courte
                for node in (list(filter(lambda x: x.state == 1, self.nodes)) if not includeChecked else self.nodes): # Itère les nodes qui n'ont pas encore été les plus proche
                        if smallestTLList: # Si un node se trouve déjà dans la liste
                                if node.totalLength < smallestTLList[0].totalLength:
                                        smallestTLList = [node] # Si un node est plus petits que les autres nodes de la liste, il les remplace
                                elif node.totalLength == smallestTLList[0].totalLength:
                                        smallestTLList.append(node) # Si un node a la même longueur totale que les autres nodes il est seulement ajouté
                        else:
                                smallestTLList.append(node) # On ajoute le premier node du "for" pour avoir quelque chose à comparer
                if len(smallestTLList) > 1: # Si plusieurs nodes ont la même longueur totale 
                        smallestELList = [] # "Smallest End Lenghts List" - liste des nodes, qui ont la même longueur totale, dont la longueur à la fin est la plus courte
                        for node in smallestTLList:
                                if smallestELList:
                                        if node.endLength < smallestELList[0].endLength:
                                                smallestELList = [node] # Si un node est plus petits que les autres nodes de la liste, il les remplace
                                        elif node.endLength == smallestELList[0].endLength:
                                                smallestELList.append(node) # Si un node a la même longueur à la fin que les autres nodes il est seulement ajouté
                                else:
                                        smallestELList.append(node) # On ajoute le premier node du "for" pour avoir quelque chose à comparer
                        return smallestELList[0] # On retourne le premier node de la liste de nodes ayant la même longueur totale et à la fin
                else:
                        return smallestTLList[0] # Retourne l'unique node le plus proche

        def findBest(self, start, finish): # Trouve le chemin le plus rapide du point début au point fin en tenant compte des obstacles
                self.start = start
                self.finish = finish
                self.path = [] # Initialise la liste contenant le meilleur chemin a prendre
                self.nodes = [self.Node((self.start[0] - self.precision / 2, self.start[1] - self.precision / 2), self.precision, None, 1, self.start, finish)] # Initialise la liste de tout les nodes avec un node centré sur le point de départ

                while not [x for x in self.nodes if x.rect.colliderect(pygame.Rect(self.finish[0] - self.precision / 2, self.finish[1] - self.precision / 2, self.precision, self.precision))] and not any([x for x in self.nodes if x.startLength > self.maxRadius]): # Tant qu'un node n'est pas en collision avec le rectangle centré sur le point de fin et qu'aucun node n'excède le radius maximale précisé, on continue à chercher
                        closest = self.__closestNode(False) # On cherche le node le plus proche
                        self.__addNeighbourNodes(closest) # On ajoute les nodes voisin au node le plus proche
                if any([x for x in self.nodes if x.startLength > self.maxRadius]): # Si un node se trouve en dehors du radius maximale
                        current_node = self.__closestNode(True) # On retrace le chemin le plus court à l'envers (en incluant les nodes déjà vérifié) en partant du node le plus proche du point de fin 
                else:
                        current_node = self.__closestNode(False) # On retrace le chemin le plus court à l'envers en partant du node le plus proche du point de fin 
                while current_node != self.nodes[0]: # Tant que l'on a pas atteint le node de départ
                        self.path.append(current_node) # On ajoute le node parent au dernier
                        current_node = current_node.parent
                return self.path.reverse() # On retoune la liste du chemin le plus court après l'avoir inversé

        def drawPath(self, screen, screenCoords): # Déssine le chemin le plus court à l'aide d'un tracé rouge
                if self.path:
                        lastNode = None
                        for node in self.path:
                                pygame.draw.circle(screen, pygame.Color("red"), (node.rect.center[0] - screenCoords[0], node.rect.center[1] - screenCoords[1]), 10) # On indique un node du chemin par un cercle rouge à son centre
                                if lastNode:
                                        pygame.draw.line(screen, pygame.Color("red"), (node.rect.center[0] - screenCoords[0], node.rect.center[1] - screenCoords[1]), (lastNode.rect.center[0] - screenCoords[0], lastNode.rect.center[1] - screenCoords[1]), 5) # On indique le chemin à prendre à l'aide d'une ligne rouge
                                lastNode = node
                        pygame.draw.line(screen, pygame.Color("red"), (lastNode.rect.center[0] - screenCoords[0], lastNode.rect.center[1] - screenCoords[1]), (self.finish[0] - screenCoords[0], self.finish[1] - screenCoords[1]), 5) # On déssine une dernière ligne reliant le dernier node au point de fin
                        pygame.draw.circle(screen, pygame.Color("yellow"), (self.finish[0] - screenCoords[0], self.finish[1] - screenCoords[1]), 5) # On indique le point de fin à l'aide d'un point jaune

        class Node: # Classe définissant un node
                def __init__(self, coords, precision, parent, state, startPoint, endPoint):
                        self.rect = pygame.Rect(coords, (precision, precision)) # Rectangle définissant le node
                        self.parent = parent # Node parent
                        self.state = state # Etat du node. 1: à analyser        2: déjà analysé
                        self.startLength = math.sqrt(pow(startPoint[0] - self.rect.centerx, 2) + pow(startPoint[1] - self.rect.centery, 2)) # Distance du node au point de départ
                        self.endLength = math.sqrt(pow(endPoint[0] - self.rect.centerx, 2) + pow(endPoint[1] - self.rect.centery, 2)) # Distance du node au point d'arrivée
                        self.totalLength = self.startLength + self.endLength # Distance totale du node (distance au départ + distance à l'arrivée)

                def draw(self, coords, screen): # Dessine le node aux coordonnées écran indiqués
                        if self.state == 2: # Si le node a déjà été analysé
                                chosenColor = pygame.Color(107, 244, 66, 127)
                        elif self.state == 1: # Si le node n'a pas ncore été analysé
                                chosenColor = pygame.Color(65, 244, 241, 127)

                        pygame.draw.rect(screen, chosenColor, pygame.Rect(coords, (self.rect.width, self.rect.height)))


class Bullet :
        def __init__(self, map, perso, screen, screenRect, weaponCharacteristics):
                screenMouseCoords = pygame.mouse.get_pos() #on obtient les coordonées de la souris
                self.weaponCharacteristics = weaponCharacteristics
                realMouseCoords = screenMouseCoords + screenRect.topleft #on obtient les coordonnées réelles du curseur (pas dans le repère de la map)
                bulletSpeed = weaponCharacteristics.speed  #on défini un coefficient de vitesse pour la balle
                self.direction = ((realMouseCoords.x - perso.rect.center.x, realMouseCoords.y)*bulletSpeed - (perso.rect.center.y)*bulletSpeed) #on défini des composantes de direction pour la balle
                self.rect = rect(perso.center,(1, 1))   #on défini le rectangle lié à la balle

        def move (self):
                pygame.self.rect.move_ip(direction[0], direction[1])  #on donne la trajectoire à la balle
                if self.rect.collidelist([hitbox.rect for hitbox in map.hitboxes]):    #on vérifie que la balle ne collisionne pas d'hitboxes
                        print("supprimer l'objet")

                collision = [x for x in map.enemies if self.rect.colliderect(x.rect)]
                if any(collision):
                        for enemy in collision:
                                enemy.health -= self.weaponCharacteristics.speed


class Bouton:
        def __init__(self,coords,text,size,screen):
                self.rect=pygame.Rect(coords,size)
                self.coords=coords
                self.size=size
                self.screen=screen
                self.text=text

        def draw(self):
                pygame.draw.rect(self.screen,pygame.Color(255,0,0), pygame.Rect(self.coords[0], self.coords[1], self.rect.size[0],self.rect.size[1]))
                font=pygame.font.SysFont("Times New Roman",50,bold=False,italic=False)
                texte=font.render(self.text,1,(0,0,0))
                self.screen.blit(texte,(self.coords[0]+30,self.coords[1]+30))




