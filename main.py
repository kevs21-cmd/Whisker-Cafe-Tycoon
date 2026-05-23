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

    def update_move(self):
        for i in range(2):
            if abs(self.pixel_pos[i] - self.target_pixel[i]) > self.speed:
                if self.pixel_pos[i] < self.target_pixel[i]: self.pixel_pos[i] += self.speed
                else: self.pixel_pos[i] -= self.speed
            else: self.pixel_pos[i] = self.target_pixel[i]

class Game:
    def __init__(self):
        pygame.init()

        pygame.mixer.init() #music

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Neko Cafe Tycoon - Sprite Sheet Integrated")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Quicksand, Arial", 20, bold=True)
        self.ui_font = pygame.font.SysFont("Quicksand, Arial", 26, bold=True)

        # --- Load Lo-Fi Background Music ---
        try:
            # Make sure the path matches where your file is saved!
            # If it's inside an assets folder, use: 'assets/audio/lofi_bgm.mp3'
            pygame.mixer.music.load('assets/audio/lofi_bgm.mp3')
            pygame.mixer.music.set_volume(0.4)
            pygame.mixer.music.play(-1)  # -1 means loop indefinitely
            print("🎵 Lo-Fi Music loaded and playing!")
        except pygame.error as e:
            print(f"⚠️ Music Asset 'lofi_bgm.mp3' not found or failed to load. Game is muted. Error: {e}")
        
        # --- Asset Loading ---
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
        # General Game Object Paths
        paths = {
            "cat": "assets/images/cat.png",
            "cat_tray": "assets/images/cat_tray.png",
            "table": "assets/images/table.png",
            "chair": "assets/images/chair.png",
            "spill": "assets/images/spill.png",
            "plant": "assets/images/plant.png",
            "bg_tile": "assets/images/bg.png"
        }
        for key, path in paths.items():
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                if key != "bg":
                    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                self.assets[key] = img
            else:
                self.assets[key] = None

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

        # UI Sprite Sheet Loading
        if os.path.exists("ui_spritesheet.png"):
            sheet = pygame.image.load("ui_spritesheet.png").convert_alpha()
            # Slicing the UI components based on the image provided
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
        
        for i in range(self.upgrades["Tables"]["lv"]):
            t_pos = self.all_tables[i]
            self.obstacles.add(t_pos)
            self.chair_positions[i] = []
            for c_idx in range(self.upgrades["Furniture Size"]["lv"]):
                off_x, off_y = chair_offsets[c_idx]
                chair_pos = (t_pos[0] + off_x, t_pos[1] + off_y)
                if 0 <= chair_pos[0] < COLS and 0 <= chair_pos[1] < ROWS:
                    self.chair_positions[i].append(chair_pos)
                    self.obstacles.add(chair_pos)

    def get_dynamic_obstacles(self, exclude_cust=None):
        obs = self.obstacles.copy()
        for c in self.customers:
            if c != exclude_cust and c.state == "SITTING":
                obs.add(c.grid_pos)
        return obs

    def get_best_delivery_spot(self, table_pos, table_idx):
        potential = [(0,1), (0,-1), (1,0), (-1,0)]
        chairs = self.chair_positions[table_idx]
        valid_spots = []
        for dx, dy in potential:
            check = (table_pos[0] + dx, table_pos[1] + dy)
            if 0 <= check[0] < COLS and 0 <= check[1] < ROWS:
                if check not in self.obstacles or (check in chairs and check != self.customers[0].grid_pos):
                    valid_spots.append(check)
        if not valid_spots: return (table_pos[0], table_pos[1] + 1)
        return min(valid_spots, key=lambda s: abs(s[0]-self.cat_grid[0]) + abs(s[1]-self.cat_grid[1]))

    def handle_input(self):
        mx, my = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.MOUSEBUTTONDOWN:
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
            occupied_indices = [c.table_idx for c in self.customers]
            available = [i for i in range(self.upgrades["Tables"]["lv"]) if i not in occupied_indices]
            if available:
                idx = random.choice(available)
                target_chair = self.chair_positions[idx][0]

                num_variants = len(self.assets["cust_variants"])
                new_cust = Customer(self.door_pos, idx, target_chair, num_variants)

                new_cust.path = Dijkstra.find_path(self.door_pos, target_chair, self.obstacles)
                self.customers.append(new_cust)
            self.spawn_timer = 0

        for c in self.customers[:]:
            c.update_move()
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
                    t_pos = self.all_tables[self.active_cust_ref.table_idx]
                    delivery_spot = self.get_best_delivery_spot(t_pos, self.active_cust_ref.table_idx)
                    self.cat_path = Dijkstra.find_path(self.cat_grid, delivery_spot, self.get_dynamic_obstacles())
                elif self.cat_state == "DELIVERING":
                    val = 15 + (self.upgrades["Premium Beans"]["lv"] * 5) + (self.upgrades["Furniture Size"]["lv"] * 10)
                    self.add_money(val, self.cat_pos[0], self.cat_pos[1])
                    self.active_cust_ref.state = "WALKING_OUT"
                    self.active_cust_ref.path = Dijkstra.find_path(self.active_cust_ref.grid_pos, self.door_pos, self.obstacles)
                    self.cat_state = "IDLE"

        for t in self.floating_texts[:]:
            t.update()
            if t.life <= 0: self.floating_texts.remove(t)

    def draw_cat(self, x, y, has_tray):
        time_ms = pygame.time.get_ticks()
        
        # Kunin ang kasalukuyang speed multiplier mula sa upgrades mo (karaniwang nasa 3 hanggang 7)
        current_speed = 2 + self.upgrades["Cat Speed"]["lv"]
        
        if self.cat_pos != self.cat_target:
            # WALKING STATE: Inihambing natin ang bilis sa aktwal na paglakad (current_speed)
            # Ginawa nating 0.0035 para swabe at hindi mukhang jelly
            anim_timer = time_ms * (0.0025 * current_speed)
            
            bounce_y = abs(math.sin(anim_timer)) * -5  # Binabaan natin sa -5 pixels lang ang taas ng talbog
            squash_w = int(TILE_SIZE + math.sin(anim_timer) * 1.5) # Binawasan ang squash para hindi masyadong malambot
            squash_h = int(TILE_SIZE - math.sin(anim_timer) * 1.5)
        else:
            # IDLE STATE (Nakatambay): Banayad na paghinga, hindi apektado ng lakad
            bounce_y = math.sin(time_ms * 0.003) * -1.5
            squash_w = int(TILE_SIZE + math.sin(time_ms * 0.003) * 0.8)
            squash_h = int(TILE_SIZE - math.sin(time_ms * 0.003) * 0.8)

        # --- DITO ANG BAGONG LOGIC ---
        if self.assets["cat"]:
            # 1. Palaging i-draw ang base na pusa
            animated_cat = pygame.transform.scale(self.assets["cat"], (squash_w, squash_h))
            render_x = x - (squash_w // 2)
            render_y = y - (squash_h // 2) + bounce_y
            self.screen.blit(animated_cat, (render_x, render_y))
            
            # 2. Kung may dalang tray, i-scale at i-patong ito sa ibabaw ng pusa
            if has_tray and self.assets["cat_tray"]:
                animated_tray = pygame.transform.scale(self.assets["cat_tray"], (squash_w, squash_h))
                # I-blit sa eksaktong pwesto para sumabay sa talbog ng pusa!
                self.screen.blit(animated_tray, (render_x, render_y))
        else:
            # Panatilihin ang iyong lumang primitve shape draw logic bilang fallback
            y += bounce_y
            pygame.draw.ellipse(self.screen, CLR_CAT, (x-18, y-12, 36, 24))
            pygame.draw.arc(self.screen, CLR_CAT, (x-25, y-5, 20, 20), 0, 3, 4)
            pygame.draw.circle(self.screen, CLR_CAT, (int(x+10), int(y-5)), 12)
            pygame.draw.polygon(self.screen, CLR_CAT, [(x+5, y-12), (x+10, y-22), (x+15, y-12)])
            pygame.draw.polygon(self.screen, CLR_CAT, [(x+12, y-12), (x+18, y-20), (x+20, y-10)])
            pygame.draw.circle(self.screen, (255,255,100), (int(x+14), int(y-7)), 2)
            if has_tray:
                pygame.draw.rect(self.screen, (255,255,255), (x+5, y-2, 12, 8), border_radius=2)

    def draw_chair(self, grid_x, grid_y, is_gold):
        if self.assets["chair"]:
            self.screen.blit(self.assets["chair"], (grid_x * TILE_SIZE, grid_y * TILE_SIZE))
            if is_gold:
                pygame.draw.rect(self.screen, CLR_GOLD, (grid_x*TILE_SIZE, grid_y*TILE_SIZE, 50, 50), 3, border_radius=4)
        else:
            cx, cy = grid_x * TILE_SIZE + 25, grid_y * TILE_SIZE + 25
            size = 15
            pygame.draw.rect(self.screen, CLR_CHAIR, (cx-size, cy-size, size*2, size*2), border_radius=4)
            pygame.draw.rect(self.screen, (90, 50, 20), (cx-size, cy-size-3, size*2, 8), border_radius=2)
            if is_gold:
                pygame.draw.rect(self.screen, CLR_GOLD, (cx-size, cy-size, size*2, size*2), 2, border_radius=4)

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

    def draw(self):
        # --- BACKGROUND TILING LOGIC ---
        if self.assets["bg_tile"]:
            # Uulitin natin ang bg.png sa bawat Rows at Columns ng screen mo
            for r in range(ROWS):
                for c in range(COLS):
                    self.screen.blit(self.assets["bg_tile"], (c * TILE_SIZE, r * TILE_SIZE))
        else:
            # Fallback kapag hindi nahanap ang bg.png file
            self.screen.fill(CLR_BG)
            for x in range(0, WIDTH, 50): pygame.draw.line(self.screen, (242,238,230), (x,0), (x, HEIGHT-100))
        
        self.draw_decor()
        pygame.draw.rect(self.screen, CLR_ACCENT, (WIDTH-10, HEIGHT//2-50, 10, 100))
        
        for s in self.spills: 
            if self.assets["spill"]:
                self.screen.blit(self.assets["spill"], (s[0]*50, s[1]*50))
            else:
                pygame.draw.circle(self.screen, CLR_DIRT, (s[0]*50+25, s[1]*50+25), 18)

        # Counter
        pygame.draw.rect(self.screen, (100, 70, 40), (0, 45, 155, 60), border_radius=5)
        pygame.draw.rect(self.screen, CLR_TABLE, (0, 50, 150, 50), border_radius=5)
        self.screen.blit(self.font.render("Counter", True, (255,255,255)), (40, 65))

        for i, pos in enumerate(self.all_tables):
            locked = i >= self.upgrades["Tables"]["lv"]
            px, py = pos[0]*50+25, pos[1]*50+25
            if locked:
                pygame.draw.circle(self.screen, (220,220,220), (px, py), 20, 2)
            else:
                for c_pos in self.chair_positions[i]:
                    self.draw_chair(c_pos[0], c_pos[1], self.upgrades["Furniture Size"]["lv"] == 4)
                
                if self.assets["table"]:
                    self.screen.blit(self.assets["table"], (pos[0]*50, pos[1]*50))
                else:
                    t_size = 22
                    pygame.draw.circle(self.screen, (50,50,50,40), (px, py+2), int(t_size))
                    pygame.draw.rect(self.screen, CLR_TABLE, (px-t_size, py-t_size, t_size*2, t_size*2), border_radius=4)

        time_ms = pygame.time.get_ticks()
        for c in self.customers:
            c_time = time_ms + c.anim_offset
            
            if c.state == "SITTING":
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
                # Isama ang c_bounce_y para sumabay din ang white bubbles sa pag-talbog ng pusa
                pygame.draw.circle(self.screen, (255,255,255), (c.pixel_pos[0]+15, c.pixel_pos[1]-18 + c_bounce_y), 10)
                pygame.draw.circle(self.screen, (255,255,255), (c.pixel_pos[0]+8, c.pixel_pos[1]-10 + c_bounce_y), 4)

        self.draw_cat(self.cat_pos[0], self.cat_pos[1], self.cat_state == "DELIVERING")
        
        # UI Bottom Bar
        if self.assets["ui_bar"]:
            self.screen.blit(self.assets["ui_bar"], (0, HEIGHT-100))
        else:
            pygame.draw.rect(self.screen, CLR_UI, (0, HEIGHT-100, WIDTH, 100))
            
        self.screen.blit(self.ui_font.render(f"Yen: ¥{self.money}", True, CLR_CAT), (30, HEIGHT-65))
        
        # Upgrade Button
        btn_rect = pygame.Rect(WIDTH-160, HEIGHT-80, 140, 60)
        if self.assets["ui_btn_long"]:
            self.screen.blit(self.assets["ui_btn_long"], (WIDTH-160, HEIGHT-80))
        else:
            pygame.draw.rect(self.screen, CLR_BTN, btn_rect, border_radius=10)
        self.screen.blit(self.font.render("UPGRADES", True, (255,255,255)), (WIDTH-135, HEIGHT-60))

        for t in self.floating_texts:
            img = self.font.render(t.text, True, t.color)
            img.set_alpha(t.alpha)
            self.screen.blit(img, (t.x, t.y))

        if self.show_upgrades:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            self.screen.blit(overlay, (0,0))
            
            # Shop Panel
            win = pygame.Rect(WIDTH//2-200, HEIGHT//2-200, 400, 400)
            if self.assets["ui_panel_big"]:
                self.screen.blit(self.assets["ui_panel_big"], (WIDTH//2-200, HEIGHT//2-200))
            else:
                pygame.draw.rect(self.screen, CLR_BG, win, border_radius=15)
                
            # Close Button
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
                display_name = "Add Chairs" if name == "Furniture Size" else name
                self.screen.blit(self.font.render(f"{display_name} ({data['lv']})", True, (50,50,50)), (WIDTH//2-130, y_off))
                
                # Buy Buttons
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