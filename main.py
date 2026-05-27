import pygame
import heapq
import math
import random
import os

# --- Configuration ---
TILE_SIZE = 50
COLS, ROWS = 16, 12
WIDTH, HEIGHT = COLS * TILE_SIZE, ROWS * TILE_SIZE + 100
FPS = 60

# --- Theme Colors ---
CLR_BG = (252, 248, 242)
CLR_UI = (235, 225, 210)
CLR_CAT = (65, 60, 70)
CLR_TABLE = (139, 90, 43)
CLR_CHAIR = (110, 70, 30)
CLR_CUST = (230, 160, 160)
CLR_ACCENT = (110, 160, 130) 
CLR_BTN = (180, 170, 160)
CLR_DIRT = (200, 190, 170)
CLR_LEAF = (80, 120, 90)
CLR_GOLD = (212, 175, 55)

class Dijkstra:
    @staticmethod
    def find_path(start, goal, obstacles):
        directions = [
            (0, 1, 1.0), (0, -1, 1.0), (1, 0, 1.0), (-1, 0, 1.0),
            (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)
        ]
        
        pq = [(0, start)]
        came_from = {start: None}
        cost_so_far = {start: 0}
        
        while pq:
            current_cost, current = heapq.heappop(pq)
            
            if current == goal:
                break
                
            for dx, dy, step_cost in directions:
                next_node = (current[0] + dx, current[1] + dy)
                
                if 0 <= next_node[0] < COLS and 0 <= next_node[1] < ROWS:
                    if abs(dx) == 1 and abs(dy) == 1:
                        if (current[0] + dx, current[1]) in obstacles or (current[0], current[1] + dy) in obstacles:
                            continue

                    if next_node not in obstacles or next_node == goal:
                        new_cost = cost_so_far[current] + step_cost
                        if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                            cost_so_far[next_node] = new_cost
                            heapq.heappush(pq, (new_cost, next_node))
                            came_from[next_node] = current
                            
        path = []
        curr = goal
        while curr is not None:
            path.append(curr)
            curr = came_from.get(curr)
        return path[::-1] if len(path) > 1 else []

class FloatingText:
    def __init__(self, text, x, y, color):
        self.text = text
        self.x, self.y = x, y
        self.color = color
        self.alpha = 255
        self.life = 60

    def update(self):
        self.y -= 1
        self.life -= 1
        self.alpha = max(0, self.alpha - 4)

class Petal:
    def __init__(self, width, height):
        self.x = random.randint(0, width)
        self.y = random.randint(-100, -10)
        self.speed = random.uniform(1.0, 2.5)
        self.size = random.randint(2, 4)
        self.swing = random.uniform(0, 10) 

    def update(self, width, height):
        self.y += self.speed
        self.x += math.sin(self.swing) * 0.5
        self.swing += 0.05
        
        if self.y > height or self.x < 0 or self.x > width:
            self.x = random.randint(0, width)
            self.y = random.randint(-50, -10)
            self.speed = random.uniform(1.0, 2.5)

class Customer:
    def __init__(self, start_pos, target_table_idx, target_pos, total_variants):
        self.grid_pos = start_pos
        self.pixel_pos = [start_pos[0]*TILE_SIZE + 25, start_pos[1]*TILE_SIZE + 25]
        self.target_pixel = list(self.pixel_pos)
        self.table_idx = target_table_idx
        self.target_grid = target_pos
        self.path = []
        self.state = "WALKING_IN" 
        self.speed = 2
        self.anim_offset = random.uniform(0, 100)
        self.variant = random.randint(0, total_variants - 1)
        self.max_patience = 800  
        self.patience = self.max_patience
        self.eating_timer = 300  # 15 seconds at 60 FPS

    def update_move(self):
        for i in range(2):
            if abs(self.pixel_pos[i] - self.target_pixel[i]) > self.speed:
                if self.pixel_pos[i] < self.target_pixel[i]: self.pixel_pos[i] += self.speed
                else: self.pixel_pos[i] -= self.speed
            else: self.pixel_pos[i] = self.target_pixel[i]

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init() 

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Whiskers Cafe Tycoon")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Quicksand, Arial", 20, bold=True)
        self.ui_font = pygame.font.SysFont("Quicksand, Arial", 26, bold=True)
        self.title_font = pygame.font.SysFont("Quicksand, Arial", 50, bold=True)

        self.game_state = "START" 
        self.loading_timer = 0  
        
        self.petals = [Petal(WIDTH, HEIGHT) for _ in range(25)]
        
        self.map_nodes = {
            "restaurant": {
                "rect": pygame.Rect(40, 240, 150, 120),      
                "locked": True, 
                "name": "Miso's Seafood Restaurant"
            },
            "bakery": {
                "rect": pygame.Rect(210, 140, 150, 120),     
                "locked": True, 
                "name": "Pawsome Bakery"
            },
            "hotel": {
                "rect": pygame.Rect(440, 140, 150, 120),     
                "locked": True, 
                "name": "Kitty Hotel"
            },
            "lounge": {
                "rect": pygame.Rect(610, 240, 150, 120),     
                "locked": True, 
                "name": "Cat Lounge"
            },
            "cafe": {
                "rect": pygame.Rect(325, 340, 150, 120),     
                "locked": False,                            
                "name": "Whiskers Cafe"
            }
        }

        try:
            pygame.mixer.music.load('assets/audio/lofi_bgm.mp3')
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play(-1)
            print("🎵 Lo-Fi Music loaded and playing!")
        except pygame.error as e:
            print(f"⚠️ Music Asset 'lofi_bgm.mp3' not found or failed to load. Game is muted. Error: {e}")
        
        self.assets = {}
        self.load_assets()

        self.money = 100
        self.show_upgrades = False
        self.door_pos = (15, 6)
        self.counter_pos = (1, 1)
        
        self.upgrades = {
            "Cat Speed": {"lv": 1, "cost": 30, "max": 5},
            "Tables": {"lv": 2, "cost": 50, "max": 5},
            "Auto-Brewer": {"lv": 0, "cost": 100, "max": 10},
            "Premium Beans": {"lv": 1, "cost": 60, "max": 5},
            "Furniture Size": {"lv": 1, "cost": 150, "max": 4} 
        }
        
        self.all_tables = [(4,3), (10,3), (4,8), (10,8), (14,9)]
        self.rugs = [(4,3), (10,3), (4,8), (10,8), (14,9)]
        self.decorations = [(1, 10), (14, 1), (7, 5)] 
        self.obstacles = set()
        self.chair_positions = {} 
        self.customers = []
        self.floating_texts = []
        self.spills = []
        self.update_obstacles()
        
        self.cat_pos = [1*TILE_SIZE+25, 2*TILE_SIZE+25]
        self.cat_target = list(self.cat_pos)
        self.cat_grid = (1, 2)
        self.cat_path = []
        self.cat_state = "IDLE"
        self.active_cust_ref = None

        self.spawn_timer = 0
        self.spill_timer = 0
        self.auto_brew_timer = 0

    def get_sprite(self, sheet, x, y, w, h):
        sprite = pygame.Surface((w, h), pygame.SRCALPHA)
        sprite.blit(sheet, (0, 0), (x, y, w, h))
        return sprite

    def load_assets(self):
        paths = {
            "cat": "assets/images/cat.png",
            "cat_tray": "assets/images/cat_tray.png",
            "table": "assets/images/table.png",
            "chair": "assets/images/chair.png",
            "spill": "assets/images/spill.png",
            "plant": "assets/images/plant.png",
            "bg_tile": "assets/images/bg.png",
            "kitchen": "assets/images/kitchen.png",
            "door": "assets/images/door.png",
            "bottom_bar": "assets/images/bottom_ui.png",
            "chef": "assets/images/cat_chef.png",
            "auto_brewer": "assets/images/auto_brewer.png",  
            "premium_beans": "assets/images/premium_beans.png",
            "start_bg": "assets/images/menu.png",
            "map_bg": "assets/images/map.png",
            "lock_icon": "assets/images/lock.png"
        }
        for key, path in paths.items():
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                if key == "kitchen":
                    img = pygame.transform.scale(img, (TILE_SIZE * 3, TILE_SIZE * 2))
                elif key == "bottom_bar":
                    img = pygame.transform.scale(img, (WIDTH, 100))
                elif key == "door":
                    img = pygame.transform.scale(img, (50, 80))
                elif key == "chef":
                    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                elif key in ["premium_beans", "auto_brewer"]:
                    img = pygame.transform.scale(img, (40, 40))
                elif key == "start_bg":
                    img = pygame.transform.scale(img, (WIDTH, HEIGHT))
                elif key == "map_bg":
                    img = pygame.transform.smoothscale(img, (WIDTH, HEIGHT))
                elif key != "bg": 
                    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                self.assets[key] = img
            else:
                self.assets[key] = None

        self.assets["cat"] = pygame.transform.scale(self.assets["cat"], (40, 40)) if self.assets["cat"] else None
        self.assets["table"] = pygame.transform.scale(self.assets["table"], (40, 40)) if self.assets["table"] else None
        self.assets["chair"] = pygame.transform.scale(self.assets["chair"], (40, 40)) if self.assets["chair"] else None

        variant_files = [
            "assets/images/cat_bnw.png",
            "assets/images/cat_dark.png",
            "assets/images/cat_mix.png",
            "assets/images/cat_siamese.png"
        ]

        self.assets["cust_variants"] = []
        for path in variant_files:
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                self.assets["cust_variants"].append(img)
        if not self.assets["cust_variants"]:
            self.assets["cust_variants"].append(None)

        if os.path.exists("ui_spritesheet.png"):
            sheet = pygame.image.load("ui_spritesheet.png").convert_alpha()
            self.assets["ui_panel_big"] = pygame.transform.scale(self.get_sprite(sheet, 396, 750, 190, 95), (400, 400))
            self.assets["ui_btn_long"] = pygame.transform.scale(self.get_sprite(sheet, 181, 749, 100, 35), (140, 60))
            self.assets["ui_btn_sq"] = pygame.transform.scale(self.get_sprite(sheet, 791, 19, 26, 26), (100, 30))
            self.assets["ui_btn_sq_off"] = pygame.transform.scale(self.get_sprite(sheet, 791, 145, 26, 26), (100, 30))
            self.assets["ui_close"] = pygame.transform.scale(self.get_sprite(sheet, 937, 24, 26, 26), (30, 30))
            self.assets["ui_bar"] = pygame.transform.scale(self.get_sprite(sheet, 181, 749, 100, 35), (WIDTH, 100))
        else:
            self.assets["ui_panel_big"] = None
            self.assets["ui_btn_long"] = None
            self.assets["ui_btn_sq"] = None
            self.assets["ui_btn_sq_off"] = None
            self.assets["ui_close"] = None
            self.assets["ui_bar"] = None

    def update_obstacles(self):
        self.obstacles = set()
        for x in range(3): self.obstacles.add((x, 1))
        for d in self.decorations: self.obstacles.add(d)
        
        self.chair_positions = {}
        chair_offsets = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        
        for i in range(len(self.all_tables)):
            t_pos = self.all_tables[i]
            if i < self.upgrades["Tables"]["lv"]:
                self.obstacles.add(t_pos)
            
            self.chair_positions[i] = []
            for c_idx in range(self.upgrades["Furniture Size"]["lv"]):
                off_x, off_y = chair_offsets[c_idx]
                chair_pos = (t_pos[0] + off_x, t_pos[1] + off_y)
                if 0 <= chair_pos[0] < COLS and 0 <= chair_pos[1] < ROWS:
                    self.chair_positions[i].append(chair_pos)
                    if i < self.upgrades["Tables"]["lv"]:
                        self.obstacles.add(chair_pos)

    def get_dynamic_obstacles(self, exclude_cust=None):
        obs = self.obstacles.copy()
        for c in self.customers:
            if c != exclude_cust and c.state in ["SITTING", "EATING"]:
                obs.add(c.grid_pos)
        return obs

    def get_best_delivery_spot(self, cust_ref):
        cust_pos = cust_ref.grid_pos
        table_pos = self.all_tables[cust_ref.table_idx]
        potential = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        valid_spots = []
        
        for dx, dy in potential:
            check = (cust_pos[0] + dx, cust_pos[1] + dy)
            if 0 <= check[0] < COLS and 0 <= check[1] < ROWS:
                if check != table_pos and check != cust_pos:
                    if check not in self.obstacles:
                        valid_spots.append(check)
        
        if not valid_spots:
            for dx, dy in potential:
                check = (cust_pos[0] + dx, cust_pos[1] + dy)
                if 0 <= check[0] < COLS and 0 <= check[1] < ROWS:
                    if check != table_pos and check != cust_pos:
                        valid_spots.append(check)
                        
        if not valid_spots: return (cust_pos[0], cust_pos[1])
        return min(valid_spots, key=lambda s: abs(s[0]-self.cat_grid[0]) + abs(s[1]-self.cat_grid[1]))

    def handle_input(self):
        mx, my = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.game_state == "START":
                    self.game_state = "MAP"
                    return True

                if self.game_state == "MAP":
                    for key, node in self.map_nodes.items():
                        if node["rect"].collidepoint(mx, my):
                            if not node["locked"]:
                                self.game_state = "LOADING"
                                self.loading_timer = pygame.time.get_ticks()
                            else:
                                self.floating_texts.append(FloatingText("LOCKED AREA", mx, my, (220, 60, 60)))
                    return True

                if self.show_upgrades:
                    if pygame.Rect(WIDTH//2+130, HEIGHT//2-160, 30, 30).collidepoint(mx, my):
                        self.show_upgrades = False
                    self.buy_upgrade(mx, my)
                else:
                    if pygame.Rect(WIDTH-160, HEIGHT-80, 140, 60).collidepoint(mx, my):
                        self.show_upgrades = True
                    for s in self.spills[:]:
                        if math.dist((mx, my), (s[0]*50+25, s[1]*50+25)) < 25:
                            self.spills.remove(s)
                            self.add_money(10, mx, my)
                    
                    gx, gy = mx // TILE_SIZE, my // TILE_SIZE
                    for c in self.customers:
                        if (c.grid_pos == (gx, gy)) and c.state == "SITTING" and self.cat_state == "IDLE":
                            self.active_cust_ref = c
                            self.cat_state = "FETCHING"
                            self.cat_path = Dijkstra.find_path(self.cat_grid, (1, 2), self.get_dynamic_obstacles())
        return True

    def buy_upgrade(self, mx, my):
        y_start = HEIGHT//2 - 80
        for name, data in self.upgrades.items():
            if name == "Furniture Size" and self.upgrades["Tables"]["lv"] < self.upgrades["Tables"]["max"]:
                continue
            btn_rect = pygame.Rect(WIDTH//2+40, y_start-5, 100, 30)
            if btn_rect.collidepoint(mx, my) and self.money >= data["cost"] and data["lv"] < data["max"]:
                self.money -= data["cost"]
                data["lv"] += 1
                data["cost"] = int(data["cost"] * 1.8)
                self.update_obstacles()
            y_start += 45

    def add_money(self, amt, x, y):
        self.money += amt
        color = CLR_ACCENT if amt > 0 else (200, 50, 50)
        self.floating_texts.append(FloatingText(f"{'+' if amt > 0 else ''}¥{amt}", x, y, color))

    def update(self):
        if self.game_state in ["START", "MAP"]:
            return

        if self.game_state == "LOADING":
            if pygame.time.get_ticks() - self.loading_timer > 2000:
                self.game_state = "PLAYING"
            return

        if self.upgrades["Auto-Brewer"]["lv"] > 0:
            self.auto_brew_timer += 1
            if self.auto_brew_timer > 300:
                self.add_money(self.upgrades["Auto-Brewer"]["lv"] * 2, 80, HEIGHT-120)
                self.auto_brew_timer = 0

        self.spill_timer += 1
        if self.spill_timer > 400:
            rx, ry = random.randint(3, 12), random.randint(2, 10)
            if (rx, ry) not in self.obstacles: self.spills.append((rx, ry))
            self.spill_timer = 0

        self.spawn_timer += 1
        if self.spawn_timer > 220:
            occupied_chair_positions = [c.target_grid for c in self.customers]
            available_chairs = []
            
            for t_idx in range(self.upgrades["Tables"]["lv"]):
                for chair_pos in self.chair_positions[t_idx]:
                    if chair_pos not in occupied_chair_positions:
                        available_chairs.append((t_idx, chair_pos))
            
            if available_chairs:
                target_table_idx, target_chair_pos = random.choice(available_chairs)
                num_variants = len(self.assets["cust_variants"])
                new_cust = Customer(self.door_pos, target_table_idx, target_chair_pos, num_variants)
                new_cust.path = Dijkstra.find_path(self.door_pos, target_chair_pos, self.obstacles)
                self.customers.append(new_cust)
            self.spawn_timer = 0

        for c in self.customers[:]:
            c.update_move()
            if c.state == "SITTING":
                c.patience -= 0.5
                if c.patience <= 0:
                    self.add_money(-15, c.pixel_pos[0], c.pixel_pos[1])
                    c.state = "WALKING_OUT"
                    c.path = Dijkstra.find_path(c.grid_pos, self.door_pos, self.obstacles)
                    if self.active_cust_ref == c:
                        self.active_cust_ref = None
                        self.cat_state = "IDLE"
                        self.cat_path = []
            elif c.state == "EATING":
                c.eating_timer -= 1
                if c.eating_timer <= 0:
                    c.state = "WALKING_OUT"
                    c.path = Dijkstra.find_path(c.grid_pos, self.door_pos, self.obstacles)

            if c.pixel_pos == c.target_pixel:
                if c.path:
                    next_node = c.path.pop(0)
                    c.grid_pos = next_node
                    c.target_pixel = [next_node[0]*50+25, next_node[1]*50+25]
                elif c.state == "WALKING_IN": 
                    c.state = "SITTING"
                elif c.state == "WALKING_OUT": 
                    self.customers.remove(c)

        cat_speed = 2 + self.upgrades["Cat Speed"]["lv"]
        for i in range(2):
            if abs(self.cat_pos[i] - self.cat_target[i]) > cat_speed:
                self.cat_pos[i] += cat_speed if self.cat_pos[i] < self.cat_target[i] else -cat_speed
            else: self.cat_pos[i] = self.cat_target[i]

        if self.cat_pos == self.cat_target:
            if self.cat_path:
                next_node = self.cat_path.pop(0)
                self.cat_grid = next_node
                self.cat_target = [next_node[0]*50+25, next_node[1]*50+25]
            else:
                if self.cat_state == "FETCHING":
                    self.cat_state = "DELIVERING"
                    delivery_spot = self.get_best_delivery_spot(self.active_cust_ref)
                    self.cat_path = Dijkstra.find_path(self.cat_grid, delivery_spot, self.get_dynamic_obstacles())
                elif self.cat_state == "DELIVERING":
                    val = 15 + (self.upgrades["Premium Beans"]["lv"] * 5) + (self.upgrades["Furniture Size"]["lv"] * 10)
                    self.money += val 
                    text_color = CLR_ACCENT if self.upgrades["Premium Beans"]["lv"] == 1 else CLR_GOLD
                    self.floating_texts.append(FloatingText(f"+¥{val}", self.cat_pos[0], self.cat_pos[1], text_color))
                    self.active_cust_ref.state = "EATING"
                    self.active_cust_ref = None 
                    self.cat_state = "IDLE"

        for t in self.floating_texts[:]:
            t.update()
            if t.life <= 0: self.floating_texts.remove(t)

    def draw_cat(self, x, y, has_tray):
        time_ms = pygame.time.get_ticks()
        current_speed = 2 + self.upgrades["Cat Speed"]["lv"]
        if self.cat_pos != self.cat_target:
            anim_timer = time_ms * (0.0025 * current_speed)
            bounce_y = abs(math.sin(anim_timer)) * -5  
            squash_w = int(TILE_SIZE + math.sin(anim_timer) * 1.5) 
            squash_h = int(TILE_SIZE - math.sin(anim_timer) * 1.5)
        else:
            bounce_y = math.sin(time_ms * 0.003) * -1.5
            squash_w = int(TILE_SIZE + math.sin(time_ms * 0.003) * 0.8)
            squash_h = int(TILE_SIZE - math.sin(time_ms * 0.003) * 0.8)

        if self.assets["cat"]:
            animated_cat = pygame.transform.scale(self.assets["cat"], (squash_w, squash_h))
            render_x = x - (squash_w // 2)
            render_y = y - (squash_h // 2) + bounce_y
            self.screen.blit(animated_cat, (render_x, render_y))
            if has_tray and self.assets["cat_tray"]:
                animated_tray = pygame.transform.scale(self.assets["cat_tray"], (squash_w, squash_h))
                self.screen.blit(animated_tray, (render_x, render_y))
        else:
            y += bounce_y
            pygame.draw.ellipse(self.screen, CLR_CAT, (x-18, y-12, 36, 24))
            pygame.draw.arc(self.screen, CLR_CAT, (x-25, y-5, 20, 20), 0, 3, 4)
            pygame.draw.circle(self.screen, CLR_CAT, (int(x+10), int(y-5)), 12)
            pygame.draw.polygon(self.screen, CLR_CAT, [(x+5, y-12), (x+10, y-22), (x+15, y-12)])
            pygame.draw.polygon(self.screen, CLR_CAT, [(x+12, y-12), (x+18, y-20), (x+20, y-10)])
            pygame.draw.circle(self.screen, (255,255,100), (int(x+14), int(y-7)), 2)
            if has_tray:
                pygame.draw.rect(self.screen, (255,255,255), (x+5, y-2, 12, 8), border_radius=2)

    def draw_chair(self, grid_x, grid_y):
        if self.assets["chair"]:
            self.screen.blit(self.assets["chair"], (grid_x * TILE_SIZE, grid_y * TILE_SIZE))
        else:
            cx, cy = grid_x * TILE_SIZE + 25, grid_y * TILE_SIZE + 25
            size = 15
            pygame.draw.rect(self.screen, CLR_CHAIR, (cx-size, cy-size, size*2, size*2), border_radius=4)
            pygame.draw.rect(self.screen, (90, 50, 20), (cx-size, cy-size-3, size*2, 8), border_radius=2)

    def draw_decor(self):
        for r in self.rugs[:self.upgrades["Tables"]["lv"]]:
            pygame.draw.rect(self.screen, (235, 225, 210), (r[0]*50-10, r[1]*50-10, 70, 70), border_radius=10)
        for p in self.decorations:
            if self.assets["plant"]:
                self.screen.blit(self.assets["plant"], (p[0]*50, p[1]*50))
            else:
                px, py = p[0]*50+25, p[1]*50+25
                pygame.draw.circle(self.screen, (101, 67, 33), (px, py+10), 12)
                pygame.draw.circle(self.screen, CLR_LEAF, (px, py-5), 15)
                pygame.draw.circle(self.screen, CLR_LEAF, (px-8, py), 10)
                pygame.draw.circle(self.screen, CLR_LEAF, (px+8, py), 10)

    def draw_start_screen(self):
        if self.assets.get("start_bg"):
            self.screen.blit(self.assets["start_bg"], (0, 0))
        else:
            self.screen.fill(CLR_BG)
            
        import math
        alpha = int((math.sin(pygame.time.get_ticks() * 0.005) + 1) * 127.5)
        
        text_color = (245, 235, 215) 
        start_text = self.title_font.render("CLICK ANYWHERE TO START", True, text_color)
        start_text.set_alpha(alpha)
        
        text_rect = start_text.get_rect()
        text_rect.center = (WIDTH // 2, HEIGHT - 60) 
        
        self.screen.blit(start_text, text_rect)

    def draw_map_screen(self):
        if self.assets.get("map_bg"):
            self.screen.blit(self.assets["map_bg"], (0, 0))
        else:
            self.screen.fill((240, 220, 200))
            
        for key, node in self.map_nodes.items():
            rect = node["rect"]
            
            if node["locked"]:
                lock_overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                lock_overlay.fill((30, 30, 40, 110)) 
                self.screen.blit(lock_overlay, (rect.x, rect.y))
                
                pygame.draw.rect(self.screen, (220, 80, 80), rect, 2, border_radius=10)
                
                if self.assets.get("lock_icon"):
                    scaled_lock = pygame.transform.smoothscale(self.assets["lock_icon"], (40, 40))
                    self.screen.blit(scaled_lock, (rect.centerx - 20, rect.centery - 20))
                else:
                    lock_lbl = self.font.render("LOCKED", True, (255, 120, 120))
                    self.screen.blit(lock_lbl, (rect.centerx - lock_lbl.get_width()//2, rect.centery - 10))
            
            else:
                pygame.draw.rect(self.screen, (100, 180, 120), rect, 3, border_radius=10)
                
                pulse = int((math.sin(pygame.time.get_ticks() * 0.01) + 1) * 127.5)
                play_lbl = self.font.render("▶ ENTER", True, (80, 160, 100))
                play_lbl.set_alpha(pulse)
                self.screen.blit(play_lbl, (rect.centerx - play_lbl.get_width()//2, rect.y + 20))

        for petal in self.petals:
            petal.update(WIDTH, HEIGHT)
            pygame.draw.circle(self.screen, (255, 192, 203), (int(petal.x), int(petal.y)), petal.size)

        for t in self.floating_texts:
            img = self.font.render(t.text, True, t.color)
            img.set_alpha(t.alpha)
            self.screen.blit(img, (t.x, t.y))

    def draw_loading_screen(self):
        self.screen.fill((40, 35, 45)) 
        
        pulse = int((math.sin(pygame.time.get_ticks() * 0.01) + 1) * 127.5)
        load_text = self.ui_font.render("LOADING WHISKERS CAFE...", True, (245, 235, 215))
        load_text.set_alpha(pulse)
        
        text_rect = load_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.screen.blit(load_text, text_rect)
        
    def draw(self):
        if self.game_state == "START":
            self.draw_start_screen()
            pygame.display.flip()
            return
        elif self.game_state == "MAP":
            self.draw_map_screen()
            pygame.display.flip()
            return
        elif self.game_state == "LOADING":
            self.draw_loading_screen()
            pygame.display.flip()
            return

        if self.assets["bg_tile"]:
            for r in range(ROWS):
                for c in range(COLS):
                    self.screen.blit(self.assets["bg_tile"], (c * TILE_SIZE, r * TILE_SIZE))
        else:
            self.screen.fill(CLR_BG)
            for x in range(0, WIDTH, 50): pygame.draw.line(self.screen, (242,238,230), (x,0), (x, HEIGHT-100))
        
        self.draw_decor()
        if self.assets["door"]:
            self.screen.blit(self.assets["door"], (WIDTH - 45, HEIGHT // 2 - 50))
        else:
            pygame.draw.rect(self.screen, CLR_ACCENT, (WIDTH-15, HEIGHT//2-50, 10, 100))
        
        for s in self.spills: 
            if self.assets["spill"]:
                self.screen.blit(self.assets["spill"], (s[0]*50, s[1]*50))
            else:
                pygame.draw.circle(self.screen, CLR_DIRT, (s[0]*50+25, s[1]*50+25), 18)

        if self.assets["kitchen"]:
            self.screen.blit(self.assets["kitchen"], (-5, 45))
            if self.assets["chef"]:
                chef_bounce = math.sin(pygame.time.get_ticks() * 0.004) * -3
                self.screen.blit(self.assets["chef"], (35, 60 + chef_bounce))
            if self.upgrades["Auto-Brewer"]["lv"] > 0 and self.assets["auto_brewer"]:
                brewer_img = pygame.transform.scale(self.assets["auto_brewer"], (45, 45))
                self.screen.blit(brewer_img, (95, 65))
        else:
            pygame.draw.rect(self.screen, CLR_TABLE, (0, 45, 150, 100), border_radius=5)
            self.screen.blit(self.font.render("Counter", True, (255,255,255)), (40, 80))

        for i, pos in enumerate(self.all_tables):
            locked = i >= self.upgrades["Tables"]["lv"]
            px, py = pos[0]*50+25, pos[1]*50+25
            if locked:
                pygame.draw.circle(self.screen, (220,220,220), (px, py), 20, 2)
            else:
                for c_pos in self.chair_positions[i]:
                    self.draw_chair(c_pos[0], c_pos[1])
                if self.assets["table"]:
                    self.screen.blit(self.assets["table"], (pos[0]*50, pos[1]*50))
                else:
                    t_size = 22
                    pygame.draw.circle(self.screen, (50,50,50,40), (px, py+2), int(t_size))
                    pygame.draw.rect(self.screen, CLR_TABLE, (px-t_size, py-t_size, t_size*2, t_size*2), border_radius=4)

        time_ms = pygame.time.get_ticks()
        for c in self.customers:
            c_time = time_ms + c.anim_offset
            if c.state in ["SITTING", "EATING"]:
                c_bounce_y = math.sin(c_time * 0.002) * -1.5 
                c_w = int(TILE_SIZE + math.sin(c_time * 0.002) * 0.5)
                c_h = int(TILE_SIZE - math.sin(c_time * 0.002) * 0.5)
            else:
                anim_timer = c_time * 0.006 
                c_bounce_y = abs(math.sin(anim_timer)) * -4
                c_w = int(TILE_SIZE + math.sin(anim_timer) * 1.2)
                c_h = int(TILE_SIZE - math.sin(anim_timer) * 1.2)

            cust_asset = self.assets["cust_variants"][c.variant]
            if cust_asset:
                animated_cust = pygame.transform.scale(cust_asset, (c_w, c_h))
                cx = c.pixel_pos[0] - (c_w // 2)
                cy = c.pixel_pos[1] - (c_h // 2) + c_bounce_y
                self.screen.blit(animated_cust, (cx, cy))
            else:
                pygame.draw.circle(self.screen, CLR_CUST, (int(c.pixel_pos[0]), int(c.pixel_pos[1] + c_bounce_y)), 16)
            
            if c.state == "SITTING":
                bar_w, bar_h = 40, 6
                bx = c.pixel_pos[0] - bar_w//2
                by = c.pixel_pos[1] - 45 + c_bounce_y
                pygame.draw.rect(self.screen, (100, 100, 100), (bx, by, bar_w, bar_h))
                p_ratio = max(0, c.patience / c.max_patience)
                p_color = (int(255 * (1 - p_ratio)), int(255 * p_ratio), 0)
                pygame.draw.rect(self.screen, p_color, (bx, by, int(bar_w * p_ratio), bar_h))
                
                pygame.draw.circle(self.screen, (255,255,255), (c.pixel_pos[0]+15, c.pixel_pos[1]-18 + c_bounce_y), 10)
                pygame.draw.circle(self.screen, (255,255,255), (c.pixel_pos[0]+8, c.pixel_pos[1]-10 + c_bounce_y), 4)

                if c == self.active_cust_ref:
                    tri_y = c.pixel_pos[1] - 65 + math.sin(time_ms * 0.01) * 5
                    pygame.draw.polygon(self.screen, CLR_GOLD, [(c.pixel_pos[0]-10, tri_y), (c.pixel_pos[0]+10, tri_y), (c.pixel_pos[0], tri_y+15)])
                    pygame.draw.polygon(self.screen, (255, 255, 255), [(c.pixel_pos[0]-10, tri_y), (c.pixel_pos[0]+10, tri_y), (c.pixel_pos[0], tri_y+15)], 2)

        self.draw_cat(self.cat_pos[0], self.cat_pos[1], self.cat_state == "DELIVERING")
        
        if self.assets["bottom_bar"]:
            self.screen.blit(self.assets["bottom_bar"], (0, HEIGHT-100))
        else:
            pygame.draw.rect(self.screen, CLR_UI, (0, HEIGHT-100, WIDTH, 100))
        self.screen.blit(self.ui_font.render(f"Yen: ¥{self.money}", True, (255, 255, 255)), (40, HEIGHT-65))
        
        if self.assets["ui_btn_long"]:
            self.screen.blit(self.assets["ui_btn_long"], (WIDTH-160, HEIGHT-80))
        else:
            pygame.draw.rect(self.screen, (210, 105, 30), pygame.Rect(WIDTH-160, HEIGHT-80, 140, 60), border_radius=13)
        self.screen.blit(self.font.render("UPGRADES", True, (255,255,255)), (WIDTH-135, HEIGHT-60))

        for t in self.floating_texts:
            img = self.font.render(t.text, True, t.color)
            img.set_alpha(t.alpha)
            self.screen.blit(img, (t.x, t.y))

        if self.show_upgrades:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            self.screen.blit(overlay, (0,0))
            if self.assets["ui_panel_big"]:
                self.screen.blit(self.assets["ui_panel_big"], (WIDTH//2-200, HEIGHT//2-200))
            else:
                pygame.draw.rect(self.screen, CLR_BG, (WIDTH//2-200, HEIGHT//2-200, 400, 400), border_radius=15)
            if self.assets["ui_close"]:
                self.screen.blit(self.assets["ui_close"], (WIDTH//2+130, HEIGHT//2-160))
            else:
                pygame.draw.rect(self.screen, (200, 50, 50), (WIDTH//2+130, HEIGHT//2-160, 30, 30), border_radius=5)
                self.screen.blit(self.font.render("X", True, (255, 255, 255)), (WIDTH//2+138, HEIGHT//2-158))
            self.screen.blit(self.ui_font.render("Shop Upgrades", True, CLR_CAT), (WIDTH//2-80, HEIGHT//2-160))
            y_off = HEIGHT//2 - 80
            for name, data in self.upgrades.items():
                if name == "Furniture Size" and self.upgrades["Tables"]["lv"] < self.upgrades["Tables"]["max"]:
                    continue
                icon_to_draw = None
                if name == "Cat Speed": icon_to_draw = self.assets["cat"]
                elif name == "Tables": icon_to_draw = self.assets["table"]
                elif name == "Auto-Brewer": icon_to_draw = self.assets["auto_brewer"]
                elif name == "Premium Beans": icon_to_draw = self.assets["premium_beans"]
                elif name == "Furniture Size": icon_to_draw = self.assets["chair"]
                text_x_offset = WIDTH // 2 - 175
                if icon_to_draw:
                    self.screen.blit(icon_to_draw, (WIDTH // 2 - 175, y_off - 10))
                    text_x_offset += 50
                display_name = "Add Chairs" if name == "Furniture Size" else name
                self.screen.blit(self.font.render(f"{display_name} ({data['lv']})", True, (50,50,50)), (text_x_offset, y_off))
                btn = pygame.Rect(WIDTH//2+40, y_off-5, 100, 30)
                afford = self.money >= data["cost"] and data["lv"] < data["max"]
                if afford and self.assets["ui_btn_sq"]:
                    self.screen.blit(self.assets["ui_btn_sq"], (WIDTH//2+40, y_off-5))
                elif not afford and self.assets["ui_btn_sq_off"]:
                    self.screen.blit(self.assets["ui_btn_sq_off"], (WIDTH//2+40, y_off-5))
                else:
                    pygame.draw.rect(self.screen, CLR_ACCENT if afford else (200,200,200), btn, border_radius=5)
                lbl = f"¥{data['cost']}" if data["lv"] < data["max"] else "MAX"
                self.screen.blit(self.font.render(lbl, True, (255,255,255)), (WIDTH//2+50, y_off))
                y_off += 45
        pygame.display.flip()

    def run(self):
        while True:
            if not self.handle_input(): break
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()

if __name__ == "__main__":
    Game().run()