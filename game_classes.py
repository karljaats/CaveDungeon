import pygame, random, math, itertools, copy
import in_game, main, map_gen, spells, vars

# Omadused, mida k6ik characterid peaksid omama

def block_delete(pos_y, pos_x):
    for ID in vars.item_ID.keys():
        if in_game.map_list[pos_y][pos_x] == ID:
            in_game.map_update_queue.append([pos_y, pos_x, 4])

            in_game.World_map.map_dict[(0, 0)].dropped_items.update({(pos_y, pos_x): vars.item_ID[ID]})
    in_game.map_update_queue.append([pos_y, pos_x, 0])

class Character:
    def __init__(self, pos, health=100, max_health=100):
        self.pos = pos
        self.speed_x = 0
        self.speed_y = 0
        self.health = health
        self.max_health = max_health
        self.inventory = {}
        self.buffs = []

    def collision_detect(self):
        self.dir = ""
        if self.pos[0]+self.speed_x >= 0 and self.pos[1]+self.speed_y >= 0 and self.pos[0]+self.speed_x < in_game.map_size and self.pos[1]+self.speed_y < in_game.map_size:
            if in_game.map_list[int(self.pos[1]+self.speed_y)][int(self.pos[0])] != 0 and in_game.map_list[int(self.pos[1])][int(self.pos[0]+self.speed_x)] != 0:
                return False
            elif in_game.map_list[int(self.pos[1]+self.speed_y)][int(self.pos[0]+self.speed_x)] == 0:
                return True
            elif in_game.map_list[int(self.pos[1])][int(self.pos[0]+self.speed_x)] != 0 and in_game.map_list[int(self.pos[1]+self.speed_y)][int(self.pos[0])] == 0:
                self.dir = "y"
            elif in_game.map_list[int(self.pos[1]+self.speed_y)][int(self.pos[0])] != 0 and in_game.map_list[int(self.pos[1])][int(self.pos[0]+self.speed_x)] == 0:
                self.dir = "x"
            else:
                return False
        else:
            return False

    def rand_create_character(self):
        thatWillDo = False
        while not thatWillDo:
            pos = [random.randint(10, in_game.map_size-10), random.randint(10, in_game.map_size-10)]
            if in_game.map_list[pos[1]][pos[0]] == 0:
                thatWillDo = True
        return pos

    def pick_loot(self):
        for item_pos, item in list(in_game.World_map.map_dict[(0, 0)].dropped_items.items()):
            for dx, dy in itertools.product(range(-2, 3), repeat=2):
                if item_pos[::-1] == tuple(map(sum, zip(tuple(self.pos), (dx, dy)))):
                    if item in self.inventory:
                        value = self.inventory.get(item)
                        self.inventory.update({item: value+1})
                    else:
                        self.inventory.update({in_game.World_map.map_dict[(0, 0)].dropped_items[item_pos]: 1})
                    del in_game.World_map.map_dict[(0, 0)].dropped_items[item_pos]

                    in_game.draw_map_surface(in_game.block_size)
                    in_game.update_map()
                    in_game.join_maps()
                    in_game.draw_minimap(in_game.mm_block_size, in_game.mm_surface_size)

    def add_buffs(self, buff):
        # adds a buff to character buffs list
        self.buffs.append(buff)

    def rm_buff(self, buff):
        # removes first instance of selected buff from character buff list.
        # WARNING! Might ruin stackable buffs, research index() for more info.
        self.buffs.pop(self.buffs.index(buff))

    def display_inventory(self):
        print('=======================')
        for item, count in self.inventory.items():
            print(item, "x",count)

    """def find_vertices(self):
        for i in range(len(map_list)):
            for j in map_list[i]:
                if in_game.map_list[i][j] != 0:
                    a = 0
                    vert = []
                    for dx, dy in itertools.product(range(-1, 2), repeat=2):
                        if in_game.map_list[i + dy][j + dx] != 0:
                            a += 1
                    if a >= 2:
                        vert.append(math.sqrt((i - self.pos[1])**2 + (j - self.pos[0])**2))"""

    #def field_of_vision(self):

class Enemy(Character, pygame.sprite.Sprite):
    # Omadused, mis on iseloomulikud vastastele
    def __init__(self, pos=None):
        pygame.sprite.Sprite.__init__(self)
        # if no position is given generate randomly, else generate with the position given
        if pos is None:
            Character.__init__(self, Character.rand_create_character(self))
        else:
            Character.__init__(self, self.pos)

        self.image = pygame.Surface([in_game.block_size, 2*in_game.block_size])
        #self.image.fill((0,255,255))
        self.rect = self.image.get_rect()

        self.rect.x = self.pos[0] * in_game.block_size - in_game.camera_pos[0]
        self.rect.y = self.pos[1] * in_game.block_size - in_game.camera_pos[1]

    def update(self, screen):
        self.rect.x = self.pos[0] * in_game.block_size + in_game.camera_pos[0]
        self.rect.y = self.pos[1] * in_game.block_size + in_game.camera_pos[1]

class player(Character):
    # Omadused, mis on iseloomulikud playerile
    def __init__(self, pos):
        # players position is the position of the block that the player legs are on
        Character.__init__(self, self.rand_create_character())
        self.size = [in_game.block_size, 2*in_game.block_size] # the player is 1x2 blocks
        self.pos_onscreen = [main.screen_width//2 - self.size[0]/2, main.screen_height//2 - self.size[1]/2]
        self.color = [255, 10, 10]

        self.flamethrower = False
        self.block_mine_range = 20

        #Päris maksimaalne kiirus millega mängja liigub, ühik - ruutu/millisekundis
        self.real_speed = 0.04

        #ümardamata asukoht
        self.real_pos = self.pos

    def update(self, screen, mouse_pos, ms):
        # esimene: kolmnurga alus; teine: vasak haar; kolmas: parem haar
        pygame.draw.line(screen, self.color, (self.pos_onscreen[0], self.pos_onscreen[1]+self.size[1]), (self.pos_onscreen[0]+self.size[0], self.pos_onscreen[1]+self.size[1]), 3)
        pygame.draw.line(screen, self.color, (self.pos_onscreen[0], self.pos_onscreen[1]+self.size[1]), (self.pos_onscreen[0]+self.size[0]/2, self.pos_onscreen[1]), 2)
        pygame.draw.line(screen, self.color, (self.pos_onscreen[0]+self.size[0], self.pos_onscreen[1]+self.size[1]), (self.pos_onscreen[0]+self.size[0]/2, self.pos_onscreen[1]), 2)
        self.ft(mouse_pos)

        if self.collision_detect():
            self.real_pos = [self.real_pos[0]+self.speed_x*self.real_speed*ms, self.real_pos[1]+self.speed_y*self.real_speed*ms]
        elif self.dir == "y":
            self.real_pos = [self.real_pos[0], self.real_pos[1]+self.speed_y*self.real_speed*ms]
        elif self.dir == "x":
            self.real_pos = [self.real_pos[0]+self.speed_x*self.real_speed*ms, self.real_pos[1]]

        self.pos[0] = round(self.real_pos[0])
        self.pos[1] = round(self.real_pos[1])
        self.pick_loot()

    def mine_block(self, mouse_click_pos):
        try:
            if (((mouse_click_pos[0] - self.pos[0])**2 + (mouse_click_pos[1] - self.pos[1])**2)**(0.5)) <= self.block_mine_range:
                for dy, dx in itertools.product(range(-3, 4), repeat=2):
                    # kustutab kivi map_list'ist, uuendab kaarti ja minimapi
                    block_delete(mouse_click_pos[1] + int(dy), mouse_click_pos[0] + int(dx))
        except: pass

        in_game.draw_map_surface(in_game.block_size)
        in_game.draw_minimap(in_game.mm_block_size, in_game.mm_surface_size)

    def shoot(self, mouse_click_pos, lifetime=30000, explode_size=3, color=(255, 255, 255)):
        #global bulletGroup
        bullet = spells.Fireparticle(self.pos, mouse_click_pos, lifetime, explode_size, color=color)
        in_game.bulletGroup.add(bullet)


    def ft(self, mouse_pos):
        if self.flamethrower:
            angle = math.atan2(mouse_pos[1] - self.pos[1], mouse_pos[0] - self.pos[0])
            rand = random.uniform(-math.pi/8, math.pi/8)
            # multiplied with 100 for numerical stability. Doesn't do anything else.
            self.shoot([math.cos(angle+rand)*100000, math.sin(angle+rand)*100000], lifetime=600+random.randint(-50, 50), explode_size=3)
