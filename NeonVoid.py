import pygame
import random
import math
import sys
import os

# =============================================================================
# CONFIGURATION
# =============================================================================
WIDTH, HEIGHT = 1050, 750 
GAME_WIDTH = 850
FPS = 60

# Colors
BLACK, WHITE = (5, 5, 15), (240, 240, 255)
CYAN, MAGENTA = (0, 255, 255), (255, 0, 255)
YELLOW, RED, ORANGE = (255, 255, 0), (255, 40, 40), (255, 140, 0)
UI_BG, DARK_GRAY = (15, 15, 30), (25, 25, 40)
GREEN = (50, 255, 50)

# =============================================================================
# VISUAL EFFECTS
# =============================================================================

class DamageNumber(pygame.sprite.Sprite):
    def __init__(self, x, y, amount, color=WHITE):
        super().__init__()
        self.font = pygame.font.SysFont("Courier", 16, True)
        self.image = self.font.render(str(amount), True, color)
        self.rect = self.image.get_rect(center=(x, y))
        self.alpha = 255
        self.vy = -3.0

    def update(self):
        self.rect.y += int(self.vy)
        self.vy += 0.15 
        self.alpha -= 6
        if self.alpha <= 0: self.kill()
        else: self.image.set_alpha(self.alpha)

class ShatterPiece(pygame.sprite.Sprite):
    def __init__(self, x, y, color):
        super().__init__()
        size = random.randint(3, 6)
        self.image = pygame.Surface((size, size))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.vx, self.vy = random.uniform(-4, 4), random.uniform(-4, 4)
        self.alpha = 255

    def update(self):
        self.rect.x += self.vx; self.rect.y += self.vy
        self.alpha -= 8
        if self.alpha <= 0: self.kill()
        else: self.image.set_alpha(self.alpha)

# =============================================================================
# ENTITIES
# =============================================================================

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle, color, speed, size=5, damage=1):
        super().__init__()
        self.damage = damage
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (15, 15), size)
        self.rect = self.image.get_rect(center=(x, y))
        rad = math.radians(-angle - 90)
        self.vx, self.vy = math.cos(rad) * speed, math.sin(rad) * speed

    def update(self):
        self.rect.x += self.vx; self.rect.y += self.vy
        if not (0 <= self.rect.x <= GAME_WIDTH and 0 <= self.rect.y <= HEIGHT): self.kill()

class Boss(pygame.sprite.Sprite):
    def __init__(self, level):
        super().__init__()
        self.level = level
        self.max_health = 2000 + (level * 1500)
        self.health = self.max_health
        self.image = pygame.Surface((240, 240), pygame.SRCALPHA)
        
        self.exact_x, self.exact_y = GAME_WIDTH // 2, -300.0
        self.rect = self.image.get_rect(center=(int(self.exact_x), int(self.exact_y)))
        
        self.move_dir, self.last_attack, self.hover_timer = 1, 0, 0
        self.spawn_timer = 0
        self.phase = 1
        self.rot_angle = 0
        
        # NEW: Flags to fix the health bar jitter
        self.is_spawned = False
        self.is_active = False

    def update(self, player_pos, bullet_group, enemy_group):
        if not self.is_spawned:
            self.exact_y += 1.5 
            self.rect.centery = int(self.exact_y)
            if self.exact_y >= 180:
                self.is_spawned = True
                self.is_active = True
        else:
            self.is_active = True
            hp_pct = max(0, self.health / self.max_health)
            
            if hp_pct > 0.6: self.phase, col = 1, RED
            elif hp_pct > 0.3: self.phase, col = 2, ORANGE
            else: self.phase, col = 3, MAGENTA

            self.image.fill((0,0,0,0))
            self.rot_angle += (2 * self.phase)
            
            core_pts = []
            for i in range(6):
                a = math.radians(self.rot_angle/2 + (i * 60))
                core_pts.append((120 + math.cos(a)*60, 120 + math.sin(a)*60))
            pygame.draw.polygon(self.image, DARK_GRAY, core_pts)
            pygame.draw.polygon(self.image, col, core_pts, 5)
            
            for i in range(self.phase * 2 + 2):
                a = math.radians(-self.rot_angle*1.5 + (i * (360/(self.phase*2+2))))
                r = 90 + math.sin(self.hover_timer*2)*15
                px, py = 120 + math.cos(a)*r, 120 + math.sin(a)*r
                pts = [(px, py-15), (px+15, py), (px, py+15), (px-15, py)]
                pygame.draw.polygon(self.image, WHITE, pts, 2)

            self.hover_timer += 0.05
            now = pygame.time.get_ticks()

            if self.phase == 1:
                self.exact_x += (3 + self.level*0.5) * self.move_dir
                if self.rect.right > GAME_WIDTH - 20 or self.rect.left < 20: self.move_dir *= -1
                
                self.exact_y = 180 + (math.sin(self.hover_timer) * 15)
                self.rect.centerx = int(self.exact_x)
                self.rect.centery = int(self.exact_y)
                
                cooldown = max(300, 1000 - (self.level*60))
                if now - self.last_attack > cooldown:
                    dx, dy = player_pos[0] - self.rect.centerx, player_pos[1] - self.rect.centery
                    base_ang = -math.degrees(math.atan2(dy, dx)) - 90
                    
                    spread_count = 1 + (self.level // 2)
                    spread_gap = max(5, 20 - self.level)
                    start_ang = base_ang - (spread_gap * (spread_count // 2))
                    
                    for i in range(spread_count):
                        bullet_group.add(Bullet(self.rect.centerx, self.rect.centery, start_ang + (i*spread_gap), col, 6+self.level*0.5, 8))
                    self.last_attack = now
                    
            elif self.phase == 2:
                self.exact_x += (4 + self.level*0.5) * self.move_dir
                if self.rect.right > GAME_WIDTH - 20 or self.rect.left < 20: self.move_dir *= -1
                self.rect.centerx = int(self.exact_x)
                
                if now - self.spawn_timer > max(1500, 4000 - (self.level*200)):
                    e_type = "SWARMER" if self.level >= 4 else "STALKER"
                    enemy_group.add(Enemy(self.level, forced_type=e_type, x=self.rect.centerx, y=self.rect.centery))
                    self.spawn_timer = now
                    
                cooldown = max(200, 800 - (self.level*50))
                if now - self.last_attack > cooldown:
                    b_count = min(6, 2 + (self.level//3))
                    for i in range(b_count):
                        ang = 180 + random.randint(-40, 40)
                        bullet_group.add(Bullet(self.rect.centerx, self.rect.centery, ang, col, 8, 10))
                    self.last_attack = now

            elif self.phase == 3:
                tx, ty = GAME_WIDTH // 2, 250
                self.exact_x += (tx - self.exact_x) * 0.05
                self.exact_y += (ty - self.exact_y) * 0.05
                self.rect.center = (int(self.exact_x), int(self.exact_y))
                
                cooldown = max(50, 250 - (self.level*15))
                spiral_arms = min(8, 3 + (self.level // 2))
                
                if now - self.last_attack > cooldown:
                    for i in range(spiral_arms):
                        a = self.rot_angle * (2 + self.level*0.2) + (i * (360/spiral_arms))
                        bullet_group.add(Bullet(self.rect.centerx, self.rect.centery, a, col, 5+self.level*0.3, 6))
                    self.last_attack = now

class Player(pygame.sprite.Sprite):
    def __init__(self, ship_type="BALANCED"):
        super().__init__()
        self.ship_type = ship_type
        self.max_health = 100
        self.fire_rate = 260
        self.move_speed = 6
        self.bullet_damage = 1
        
        self.orig_image = pygame.Surface((60, 60), pygame.SRCALPHA)
        
        if ship_type == "BALANCED":
            pygame.draw.polygon(self.orig_image, CYAN, [(30, 0), (60, 60), (30, 42), (0, 60)], 3)
        elif ship_type == "TANK":
            self.max_health = 150
            self.fire_rate = 320
            self.move_speed = 4
            pygame.draw.polygon(self.orig_image, ORANGE, [(30, 0), (50, 20), (50, 60), (10, 60), (10, 20)], 3)
        elif ship_type == "SPEEDSTER":
            self.max_health = 60
            self.fire_rate = 180
            self.move_speed = 8
            pygame.draw.polygon(self.orig_image, YELLOW, [(30, 0), (45, 60), (30, 45), (15, 60)], 3)

        self.image = self.orig_image
        self.rect = self.image.get_rect(center=(GAME_WIDTH//2, HEIGHT - 100))
        self.health = self.max_health
        self.lives = 3
        self.side_cannons, self.side_cannon_level = False, 1
        self.scrap, self.last_shot, self.damage_timer = 0, 0, 0
        self.triple_timer, self.shield_count = 0, 0

    def update(self, mx, my):
        if self.damage_timer > 0: self.damage_timer -= 1
        keys = pygame.key.get_pressed()
        
        if (keys[pygame.K_w] or keys[pygame.K_UP]) and self.rect.top > 0: self.rect.y -= self.move_speed
        if (keys[pygame.K_s] or keys[pygame.K_DOWN]) and self.rect.bottom < HEIGHT: self.rect.y += self.move_speed
        if (keys[pygame.K_a] or keys[pygame.K_LEFT]) and self.rect.left > 0: self.rect.x -= self.move_speed
        if (keys[pygame.K_d] or keys[pygame.K_RIGHT]) and self.rect.right < GAME_WIDTH: self.rect.x += self.move_speed
        
        if self.triple_timer > 0: self.triple_timer -= 1
        angle = -math.degrees(math.atan2(my - self.rect.centery, mx - self.rect.centerx)) - 90
        self.image = pygame.transform.rotate(self.orig_image, angle)
        self.rect = self.image.get_rect(center=self.rect.center)
        
        if self.damage_timer > 0 and (self.damage_timer // 5) % 2 == 0:
            self.image.set_alpha(100)
        else:
            self.image.set_alpha(255)
            
        return angle

# =============================================================================
# ENGINE
# =============================================================================

class NeonEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.canvas = pygame.Surface((WIDTH, HEIGHT)) 
        self.clock = pygame.time.Clock()
        self.is_fullscreen = False
        self.fonts = {"L": pygame.font.SysFont("Courier", 80, True), "M": pygame.font.SysFont("Courier", 26, True), "S": pygame.font.SysFont("Courier", 18, True)}
        self.start_btn_rect = pygame.Rect(GAME_WIDTH//2 - 100, 580, 200, 60)
        self.selected_ship_idx = 0
        
        # Load High Score
        self.high_score = 0
        self.highscore_file = "neon_void_highscore.txt"
        if os.path.exists(self.highscore_file):
            try:
                with open(self.highscore_file, "r") as f:
                    self.high_score = int(f.read().strip())
            except: pass

        # Pause UI elements
        self.resume_btn = pygame.Rect(GAME_WIDTH//2 - 150, 400, 300, 50)
        self.quit_btn = pygame.Rect(GAME_WIDTH//2 - 150, 480, 300, 50)
        
        self.reset_game(full_reset=True)

    def check_high_score(self):
        if self.score > self.high_score:
            self.high_score = self.score
            try:
                with open(self.highscore_file, "w") as f:
                    f.write(str(self.high_score))
            except: pass

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))

    def reset_game(self, full_reset=False, ship_type="BALANCED"):
        if full_reset: 
            self.player = Player(ship_type)
            self.level, self.score = 1, 0
            self.dmg_numbers = pygame.sprite.Group() 
        else:
            self.player.health = self.player.max_health
            self.player.rect.center = (GAME_WIDTH//2, HEIGHT - 100)
            self.player.damage_timer = 120
            
        self.p_bullets = pygame.sprite.Group()
        self.b_bullets = pygame.sprite.Group()
        
        if full_reset:
            self.enemies = pygame.sprite.Group()
            self.powerups = pygame.sprite.Group()
            self.orbs = pygame.sprite.Group()
            self.shatters = pygame.sprite.Group()
            self.boss_grp = pygame.sprite.GroupSingle()
            self.kills_in_level = 0
            self.kill_goal = 10 + (self.level * 5)
            self.victory_timer = 0
            
        self.stars = [Star() for _ in range(100)]
        self.state, self.shake = "MENU" if full_reset else "PLAYING", 0

    def draw_text(self, surf, text, font, color, x, y, center=True):
        img = font.render(str(text), True, color)
        rect = img.get_rect(center=(x, y)) if center else img.get_rect(topleft=(x, y))
        surf.blit(img, rect)

    def draw_legend(self, surf):
        pygame.draw.rect(surf, UI_BG, (GAME_WIDTH, 0, WIDTH-GAME_WIDTH, HEIGHT))
        pygame.draw.line(surf, CYAN, (GAME_WIDTH, 0), (GAME_WIDTH, HEIGHT), 4)
        px = GAME_WIDTH + 20
        
        self.draw_text(surf, "DATABASE", self.fonts["M"], CYAN, px, 40, False)
        goal = f"GOAL: {max(0, self.kill_goal - self.kills_in_level)}" if not self.boss_grp.sprite else "BOSS ENGAGED"
        stats = [f"LEVEL: {self.level}/10", f"SCRAP: {self.player.scrap}", f"SCORE: {self.score}", goal]
        
        for i, s in enumerate(stats): self.draw_text(surf, s, self.fonts["S"], WHITE, px, 90 + (i*25), False)
        
        self.draw_text(surf, "IDENTIFIER", self.fonts["M"], MAGENTA, px, 220, False)
        icons = [(YELLOW, "TRIPLE SHOT"), (CYAN, "SHIELD"), (GREEN, "REPAIR")]
        for i, (col, desc) in enumerate(icons):
            iy = 265 + (i * 35)
            pygame.draw.rect(surf, col, (px, iy-10, 20, 20), 2)
            self.draw_text(surf, desc, self.fonts["S"], WHITE, px + 35, iy - 8, False)

        self.draw_text(surf, "SHIP STATS", self.fonts["M"], CYAN, px, 400, False)
        shots_per_sec = 1000 / self.player.fire_rate
        stats2 = [
            f"MAX HP: {self.player.max_health}",
            f"SPEED: {self.player.move_speed}",
            f"DMG: {self.player.bullet_damage}",
            f"FIRE: {shots_per_sec:.1f}/s",
            f"SHIELDS: {self.player.shield_count}",
            f"CANNONS: Lvl {self.player.side_cannon_level if self.player.side_cannons else 0}"
        ]
        for i, s in enumerate(stats2): self.draw_text(surf, s, self.fonts["S"], WHITE, px, 440 + (i*25), False)

        for i in range(self.player.lives):
            lx, ly = WIDTH - 50 - (i * 45), HEIGHT - 50
            pts = [(lx, ly-15), (lx+15, ly+15), (lx, ly+6), (lx-15, ly+15)]
            pygame.draw.polygon(surf, CYAN, pts, 2)
            
        self.draw_text(surf, "CONTROLS:", self.fonts["S"], DARK_GRAY, px, HEIGHT - 140, False)
        self.draw_text(surf, "WASD/ARROWS: MOVE", self.fonts["S"], DARK_GRAY, px, HEIGHT - 115, False)
        self.draw_text(surf, "SPACE/P: PAUSE", self.fonts["S"], DARK_GRAY, px, HEIGHT - 90, False)

    def get_shop_rects(self):
        rects = []
        for i in range(5):
            rects.append(pygame.Rect(GAME_WIDTH//2 - 230, 220 + (i*60), 460, 40))
        rects.append(pygame.Rect(GAME_WIDTH//2 - 230, 580, 460, 40)) 
        return rects

    def run(self):
        while True:
            sw, sh = self.screen.get_size()
            offset_x = (sw - WIDTH) // 2
            offset_y = (sh - HEIGHT) // 2
            raw_mx, raw_my = pygame.mouse.get_pos()
            mx, my = raw_mx - offset_x, raw_my - offset_y

            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_f: self.toggle_fullscreen()
                    
                    # Pause Logic
                    if event.key in [pygame.K_SPACE, pygame.K_p]:
                        if self.state == "PLAYING":
                            self.state = "PAUSED"
                        elif self.state == "PAUSED":
                            self.state = "PLAYING"
                    
                    if self.state == "SHOP": self.handle_shop(key=event.key)
                    
                    if self.state == "SHIP_SELECT":
                        if event.key in [pygame.K_LEFT, pygame.K_a]: self.selected_ship_idx = (self.selected_ship_idx - 1) % 3
                        elif event.key in [pygame.K_RIGHT, pygame.K_d]: self.selected_ship_idx = (self.selected_ship_idx + 1) % 3
                        elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                            ships = ["BALANCED", "TANK", "SPEEDSTER"]
                            self.reset_game(full_reset=True, ship_type=ships[self.selected_ship_idx])
                            self.state = "PLAYING"

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.state == "MENU" and self.start_btn_rect.collidepoint(mx, my):
                        self.state = "SHIP_SELECT"
                    
                    elif self.state == "PAUSED":
                        if self.resume_btn.collidepoint(mx, my):
                            self.state = "PLAYING"
                        elif self.quit_btn.collidepoint(mx, my):
                            self.check_high_score()
                            self.state = "MENU"

                    elif self.state == "SHIP_SELECT":
                        for i in range(3):
                            x = GAME_WIDTH//2 + (i - 1) * 260
                            y = 400
                            ship_rect = pygame.Rect(x-115, y-105, 230, 260)
                            if ship_rect.collidepoint(mx, my):
                                self.selected_ship_idx = i
                                
                        launch_rect = pygame.Rect(GAME_WIDTH//2 - 230, 670, 460, 50)
                        if launch_rect.collidepoint(mx, my):
                            ships = ["BALANCED", "TANK", "SPEEDSTER"]
                            self.reset_game(full_reset=True, ship_type=ships[self.selected_ship_idx])
                            self.state = "PLAYING"
                            
                    elif self.state == "SHOP":
                        self.handle_shop(mouse_pos=(mx, my))
                    elif self.state in ["GAMEOVER", "VICTORY"]: self.state = "MENU"

            if self.state == "PLAYING":
                p_ang = self.player.update(mx, my)
                self.shatters.update()
                self.dmg_numbers.update() 
                for s in self.stars: s.update()
                
                if pygame.mouse.get_pressed()[0] and pygame.time.get_ticks() - self.player.last_shot > self.player.fire_rate:
                    self.p_bullets.add(Bullet(self.player.rect.centerx, self.player.rect.centery, p_ang, CYAN, 16, 6, self.player.bullet_damage))
                    if self.player.triple_timer > 0:
                        for a in [-15, 15]: self.p_bullets.add(Bullet(self.player.rect.centerx, self.player.rect.centery, p_ang+a, YELLOW, 16, 6, self.player.bullet_damage))
                    if self.player.side_cannons:
                        s_dmg = max(1, (self.player.bullet_damage // 2) + self.player.side_cannon_level)
                        self.p_bullets.add(Bullet(self.player.rect.left, self.player.rect.centery, p_ang, MAGENTA, 14, 4, s_dmg))
                        self.p_bullets.add(Bullet(self.player.rect.right, self.player.rect.centery, p_ang, MAGENTA, 14, 4, s_dmg))
                    self.player.last_shot = pygame.time.get_ticks()

                boss = self.boss_grp.sprite
                if not boss:
                    if self.kills_in_level < self.kill_goal:
                        if len(self.enemies) < 6 and random.randint(1, 40) == 1: 
                            self.enemies.add(Enemy(self.level))
                    elif len(self.enemies) == 0 and self.victory_timer == 0: 
                        self.boss_grp.add(Boss(self.level))
                else: 
                    boss.update(self.player.rect.center, self.b_bullets, self.enemies)

                self.enemies.update(self.player.rect.centerx, self.player.rect.centery, self.b_bullets)
                self.p_bullets.update(); self.b_bullets.update(); self.powerups.update()

                for b in self.p_bullets:
                    for e in pygame.sprite.spritecollide(b, self.enemies, False):
                        e.health -= b.damage
                        b.kill()
                        
                        self.dmg_numbers.add(DamageNumber(e.rect.centerx, e.rect.top, b.damage, WHITE))
                        
                        if e.health <= 0:
                            self.kills_in_level += 1; self.score += 50
                            for _ in range(5): self.shatters.add(ShatterPiece(e.rect.centerx, e.rect.centery, e.color))
                            self.orbs.add(ScrapOrb(e.rect.centerx, e.rect.centery))
                            if random.random() < 0.1: self.powerups.add(PowerUp(e.rect.centerx, e.rect.centery))
                            e.kill()
                    
                    if boss and boss.is_active and b.rect.colliderect(boss.rect):
                        dmg_dealt = 50 * b.damage
                        boss.health -= dmg_dealt
                        b.kill()
                        self.shake = 5
                        
                        self.dmg_numbers.add(DamageNumber(b.rect.centerx + random.randint(-20, 20), b.rect.top + random.randint(0, 40), dmg_dealt, RED))
                        
                        if boss.health <= 0: 
                            for _ in range(50): self.shatters.add(ShatterPiece(boss.rect.centerx, boss.rect.centery, RED))
                            for _ in range(15 + (self.level * 2)):
                                ox = boss.rect.centerx + random.randint(-80, 80)
                                oy = boss.rect.centery + random.randint(-80, 80)
                                self.orbs.add(ScrapOrb(ox, oy))
                            boss.kill()
                            self.victory_timer = pygame.time.get_ticks()

                if self.victory_timer != 0 and pygame.time.get_ticks() - self.victory_timer > 3000:
                    if self.level >= 10: 
                        self.check_high_score()
                        self.state = "VICTORY"
                    else: 
                        self.state = "SHOP"
                        self.victory_timer = 0

                if self.player.damage_timer == 0:
                    hit_by_enemy = pygame.sprite.spritecollide(self.player, self.enemies, True)
                    hit_by_bullet = pygame.sprite.spritecollide(self.player, self.b_bullets, True)
                    hit_by_boss = boss and boss.is_active and self.player.rect.colliderect(boss.rect)
                    
                    if hit_by_enemy or hit_by_bullet or hit_by_boss:
                        if self.player.shield_count > 0: 
                            self.player.shield_count -= 1
                            self.player.damage_timer = 60 
                        else:
                            dmg = 10 + (self.level * 2) if not hit_by_boss else 30 + (self.level * 5)
                            self.player.health -= dmg
                            self.player.damage_timer = 40 
                            
                            self.dmg_numbers.add(DamageNumber(self.player.rect.centerx, self.player.rect.top, dmg, RED))
                            
                            if self.player.health <= 0:
                                for _ in range(15): self.shatters.add(ShatterPiece(self.player.rect.centerx, self.player.rect.centery, WHITE))
                                self.player.lives -= 1
                                if self.player.lives > 0: self.reset_game(full_reset=False)
                                else: 
                                    self.check_high_score()
                                    self.state = "GAMEOVER"

                for p in pygame.sprite.spritecollide(self.player, self.powerups, True):
                    if p.type == "TRIPLE": self.player.triple_timer = 500
                    elif p.type == "SHIELD": self.player.shield_count += 1
                    elif p.type == "HEAL": 
                        heal_amt = min(40, self.player.max_health - self.player.health)
                        self.player.health += heal_amt
                        if heal_amt > 0: self.dmg_numbers.add(DamageNumber(self.player.rect.centerx, self.player.rect.top, f"+{heal_amt}", GREEN))
                
                attract_dist = 400 if self.victory_timer != 0 else 200
                for o in self.orbs: o.update(self.player.rect.centerx, self.player.rect.centery, attract_dist)
                
                collected_orbs = pygame.sprite.spritecollide(self.player, self.orbs, True)
                for _ in collected_orbs: self.player.scrap += 25

            # RENDERING
            self.canvas.fill(BLACK)
            for s in self.stars: s.draw(self.canvas)
            off = (random.randint(-self.shake, self.shake), random.randint(-self.shake, self.shake)) if self.shake > 0 else (0,0)
            if self.shake > 0: self.shake -= 1

            if self.state in ["PLAYING", "PAUSED", "SHOP"]:
                self.shatters.draw(self.canvas)
                for g in [self.orbs, self.powerups, self.enemies, self.p_bullets, self.b_bullets, self.player, self.boss_grp, self.dmg_numbers]:
                    if hasattr(g, 'image'): self.canvas.blit(g.image, g.rect.move(off))
                    else: 
                        for spr in g: self.canvas.blit(spr.image, spr.rect.move(off))

                for i in range(self.player.shield_count):
                    pygame.draw.circle(self.canvas, CYAN, (self.player.rect.centerx + off[0], self.player.rect.centery + off[1]), 35 + (i * 6), 2)

                pygame.draw.rect(self.canvas, DARK_GRAY, (20, 20, 250, 20))
                pygame.draw.rect(self.canvas, RED, (20, 20, (max(0, self.player.health)/self.player.max_health)*250, 20))
                self.draw_text(self.canvas, f"HP: {self.player.health}/{self.player.max_health}", self.fonts["S"], WHITE, 145, 30)
                
                if self.kills_in_level >= self.kill_goal:
                    bx, by = 250, 60
                    pygame.draw.rect(self.canvas, DARK_GRAY, (bx, by, 400, 25))
                    hp_val = boss.health if boss else (2000 + (self.level * 1500))
                    max_hp = boss.max_health if boss else (2000 + (self.level * 1500))
                    
                    if hp_val > 0 or self.victory_timer != 0:
                        pygame.draw.rect(self.canvas, RED, (bx, by, (max(0, hp_val)/max_hp)*400, 25))
                        
                        if boss and boss.is_active:
                            msg = f"{int(hp_val)} / {int(max_hp)}"
                        else:
                            msg = "BOSS DETECTED" if hp_val > 0 else "SECTOR CLEAR"
                            
                        self.draw_text(self.canvas, msg, self.fonts["S"], WHITE, bx + 200, by + 12)

            if self.state == "PAUSED": self.draw_pause(self.canvas, mx, my)
            elif self.state == "SHOP": self.draw_shop(self.canvas, mx, my)
            elif self.state == "SHIP_SELECT": self.draw_ship_select(self.canvas, mx, my)
            elif self.state == "MENU": self.draw_menu(self.canvas)
            elif self.state == "GAMEOVER": 
                self.draw_text(self.canvas, "SYSTEM OFFLINE", self.fonts["L"], RED, GAME_WIDTH//2, HEIGHT//2)
                self.draw_text(self.canvas, "CLICK ANYWHERE TO REBOOT", self.fonts["S"], WHITE, GAME_WIDTH//2, HEIGHT//2 + 80)
            elif self.state == "VICTORY":
                self.draw_text(self.canvas, "VICTORY ACHIEVED", self.fonts["L"], CYAN, GAME_WIDTH//2, HEIGHT//2)
                self.draw_text(self.canvas, f"FINAL SCORE: {self.score}", self.fonts["M"], WHITE, GAME_WIDTH//2, HEIGHT//2 + 80)
            
            self.draw_legend(self.canvas)
            
            self.screen.fill((0, 0, 0))
            self.screen.blit(self.canvas, (offset_x, offset_y))
            pygame.display.flip(); self.clock.tick(FPS)

    def draw_menu(self, surf):
        self.draw_text(surf, "NEON VOID", self.fonts["L"], CYAN, GAME_WIDTH//2, 180)
        self.draw_text(surf, f"HIGH SCORE: {self.high_score}", self.fonts["M"], YELLOW, GAME_WIDTH//2, 260)
        
        pygame.draw.rect(surf, CYAN, self.start_btn_rect, 2)
        self.draw_text(surf, "DEPLOY VESSEL", self.fonts["M"], CYAN, self.start_btn_rect.centerx, self.start_btn_rect.centery)

    def draw_pause(self, surf, mx, my):
        overlay = pygame.Surface((GAME_WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,180))
        surf.blit(overlay, (0,0))
        
        self.draw_text(surf, "SYSTEM PAUSED", self.fonts["L"], CYAN, GAME_WIDTH//2, 200)
        self.draw_text(surf, f"CURRENT SECTOR: LEVEL {self.level}", self.fonts["M"], WHITE, GAME_WIDTH//2, 300)
        
        # Resume Button
        if self.resume_btn.collidepoint(mx, my): pygame.draw.rect(surf, (10, 50, 50), self.resume_btn)
        pygame.draw.rect(surf, CYAN, self.resume_btn, 2)
        self.draw_text(surf, "RESUME", self.fonts["M"], CYAN, self.resume_btn.centerx, self.resume_btn.centery)

        # Quit Button
        if self.quit_btn.collidepoint(mx, my): pygame.draw.rect(surf, (50, 10, 10), self.quit_btn)
        pygame.draw.rect(surf, RED, self.quit_btn, 2)
        self.draw_text(surf, "QUIT TO MENU", self.fonts["M"], RED, self.quit_btn.centerx, self.quit_btn.centery)

    def draw_ship_select(self, surf, mx, my):
        self.draw_text(surf, "SELECT CHASSIS", self.fonts["L"], CYAN, GAME_WIDTH//2, 150)
        
        ships = [
            ("BALANCED", CYAN, "Standard Issue", ["HP: 100", "SPD: 6", "FIRE: Normal"]),
            ("TANK", ORANGE, "Heavy Plating", ["HP: 150", "SPD: 4", "FIRE: Slow"]),
            ("SPEEDSTER", YELLOW, "High Velocity", ["HP: 60", "SPD: 8", "FIRE: Fast"])
        ]
        
        for i, (name, col, desc, stats) in enumerate(ships):
            x = GAME_WIDTH//2 + (i - 1) * 260
            y = 400
            rect = pygame.Rect(x-115, y-105, 230, 260)
            
            if rect.collidepoint(mx, my) and i != self.selected_ship_idx:
                pygame.draw.rect(surf, (20, 20, 30), rect)
            
            if i == self.selected_ship_idx:
                pygame.draw.rect(surf, col, rect, 3)
                pygame.draw.rect(surf, (col[0]//4, col[1]//4, col[2]//4), (x-112, y-102, 224, 254))
            else:
                pygame.draw.rect(surf, DARK_GRAY, rect, 2)
                
            self.draw_text(surf, name, self.fonts["M"], col, x, y - 60)
            self.draw_text(surf, desc, self.fonts["S"], WHITE, x, y + 40)
            
            for j, stat_line in enumerate(stats):
                self.draw_text(surf, stat_line, self.fonts["S"], WHITE, x, y + 75 + (j * 25))
            
            icon_y = y - 10
            if name == "BALANCED": pygame.draw.polygon(surf, col, [(x, icon_y-30), (x+15, icon_y+10), (x, icon_y), (x-15, icon_y+10)], 3)
            elif name == "TANK": pygame.draw.polygon(surf, col, [(x, icon_y-20), (x+15, icon_y-5), (x+15, icon_y+20), (x-15, icon_y+20), (x-15, icon_y-5)], 3)
            elif name == "SPEEDSTER": pygame.draw.polygon(surf, col, [(x, icon_y-30), (x+12, icon_y+15), (x, icon_y+5), (x-12, icon_y+15)], 3)

        self.draw_text(surf, "< A / D > OR < ARROWS > TO BROWSE", self.fonts["S"], WHITE, GAME_WIDTH//2, 640)
        
        launch_rect = pygame.Rect(GAME_WIDTH//2 - 230, 670, 460, 50)
        if launch_rect.collidepoint(mx, my):
            pygame.draw.rect(surf, (10, 50, 50), launch_rect)
        pygame.draw.rect(surf, CYAN, launch_rect, 2)
        self.draw_text(surf, "[SPACE] OR CLICK TO LAUNCH", self.fonts["M"], CYAN, launch_rect.centerx, launch_rect.centery)

    def draw_shop(self, surf, mx, my):
        overlay = pygame.Surface((GAME_WIDTH, HEIGHT), pygame.SRCALPHA); overlay.fill((0,0,0,220)); surf.blit(overlay, (0,0))
        self.draw_text(surf, "ARMORY", self.fonts["L"], CYAN, GAME_WIDTH//2, 100)
        
        s_text = "SIDE CANNONS" if not self.player.side_cannons else f"UPGRADE CANNONS"
        s_cost = 500 if not self.player.side_cannons else 300
        opts = [(1, "HULL (+25 HP)", 150), (2, "FIRE RATE", 250), (3, "THRUSTERS", 200), (4, "AP ROUNDS", 300), (5, s_text, s_cost)]
        
        rects = self.get_shop_rects()
        
        for i, (k, n, c) in enumerate(opts):
            r = rects[i]
            can_afford = self.player.scrap >= c
            base_col = YELLOW if can_afford else DARK_GRAY
            
            if r.collidepoint(mx, my) and can_afford:
                pygame.draw.rect(surf, (base_col[0]//3, base_col[1]//3, base_col[2]//3), r)
            
            pygame.draw.rect(surf, base_col, r, 2)
            self.draw_text(surf, f"[{k}] {n} - {c} Scrap", self.fonts["M"], base_col, r.centerx, r.centery)
            
        btn_rect = rects[5]
        if btn_rect.collidepoint(mx, my): pygame.draw.rect(surf, (10, 50, 50), btn_rect)
        pygame.draw.rect(surf, CYAN, btn_rect, 2)
        self.draw_text(surf, "[SPACE] DEPLOY TO NEXT ZONE", self.fonts["M"], WHITE, btn_rect.centerx, btn_rect.centery)

    def handle_shop(self, key=None, mouse_pos=None):
        p = self.player
        action = None
        
        if key is not None:
            if key == pygame.K_1: action = 1
            elif key == pygame.K_2: action = 2
            elif key == pygame.K_3: action = 3
            elif key == pygame.K_4: action = 4
            elif key == pygame.K_5: action = 5
            elif key in [pygame.K_SPACE, pygame.K_RETURN]: action = 6
        elif mouse_pos is not None:
            rects = self.get_shop_rects()
            for i, r in enumerate(rects):
                if r.collidepoint(mouse_pos):
                    action = i + 1
                    break
                    
        if action == 1 and p.scrap >= 150: p.scrap -= 150; p.max_health += 25; p.health = p.max_health
        elif action == 2 and p.scrap >= 250: p.scrap -= 250; p.fire_rate = max(80, p.fire_rate - 30)
        elif action == 3 and p.scrap >= 200: p.scrap -= 200; p.move_speed += 1
        elif action == 4 and p.scrap >= 300: p.scrap -= 300; p.bullet_damage += 1
        elif action == 5:
            if not p.side_cannons and p.scrap >= 500: p.scrap -= 500; p.side_cannons = True
            elif p.side_cannons and p.scrap >= 300: p.scrap -= 300; p.side_cannon_level += 1
        elif action == 6: 
            self.level += 1
            self.reset_game(full_reset=False)
            self.kills_in_level = 0
            self.kill_goal = 10 + (self.level * 5)
            self.state = "PLAYING"

class Enemy(pygame.sprite.Sprite):
    def __init__(self, level, forced_type=None, x=None, y=None):
        super().__init__()
        
        spawn_pool = ["STALKER", "SNIPER"]
        if level >= 4:
            spawn_pool.append("SWARMER")
            
        self.type = forced_type if forced_type else random.choice(spawn_pool)
        self.color = CYAN if self.type == "STALKER" else MAGENTA if self.type == "SNIPER" else YELLOW
        size = 12 if self.type != "SWARMER" else 8
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color, (15, 15), size, 2)
        
        sx = x if x is not None else random.randint(50, GAME_WIDTH-50)
        sy = y if y is not None else -50
        self.rect = self.image.get_rect(center=(sx, sy))
        
        self.health = int(3 + (level * 1.5))
        self.last_shot = pygame.time.get_ticks()
        self.move_timer = 0
        
        self.speed = 3 + (level * 0.2)
        if self.type == "SWARMER": self.speed += 1

    def update(self, px, py, bullet_group):
        dx, dy = px - self.rect.centerx, py - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist == 0: dist = 1
        
        if self.type == "STALKER":
            self.rect.x += (dx/dist) * self.speed; self.rect.y += (dy/dist) * self.speed
        
        elif self.type == "SNIPER":
            if dist > 350:
                self.rect.x += (dx/dist) * self.speed; self.rect.y += (dy/dist) * self.speed
            elif dist < 250:
                self.rect.x -= (dx/dist) * self.speed; self.rect.y -= (dy/dist) * self.speed
            
            now = pygame.time.get_ticks()
            if now - self.last_shot > 2000:
                ang = -math.degrees(math.atan2(dy, dx)) - 90
                bullet_group.add(Bullet(self.rect.centerx, self.rect.centery, ang, self.color, 5))
                self.last_shot = now
                
        elif self.type == "SWARMER":
            self.move_timer += 0.1
            self.rect.x += (dx/dist) * self.speed + math.sin(self.move_timer) * 5
            self.rect.y += (dy/dist) * self.speed + math.cos(self.move_timer) * 5

class ScrapOrb(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((10,10), pygame.SRCALPHA)
        pygame.draw.circle(self.image, GREEN, (5,5), 5)
        self.rect = self.image.get_rect(center=(x,y))
        
        self.exact_x = float(x)
        self.exact_y = float(y)
        
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(3.0, 6.0)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        
    def update(self, px, py, attract_dist=200):
        dx, dy = px - self.rect.centerx, py - self.rect.centery
        dist = math.hypot(dx, dy)
        
        if dist < attract_dist and dist > 0: 
            self.exact_x += (dx/dist) * 12
            self.exact_y += (dy/dist) * 12
        else: 
            self.vx *= 0.92 
            self.vy *= 0.92 
            self.exact_x += self.vx
            self.exact_y += self.vy + 0.5
            
        self.rect.centerx = int(self.exact_x)
        self.rect.centery = int(self.exact_y)

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.type = random.choices(["TRIPLE", "SHIELD", "HEAL"], weights=[1, 2, 1], k=1)[0]
        col = YELLOW if self.type == "TRIPLE" else CYAN if self.type == "SHIELD" else GREEN
        self.image = pygame.Surface((24,24), pygame.SRCALPHA)
        pygame.draw.rect(self.image, col, (0,0,24,24), 2)
        self.rect = self.image.get_rect(center=(x,y))
        
    def update(self): 
        self.rect.y += 2

class Star:
    def __init__(self): self.x, self.y, self.s = random.randint(0, GAME_WIDTH), random.randint(0, HEIGHT), random.randint(1, 3)
    def update(self):
        self.y += self.s
        if self.y > HEIGHT: self.y = 0
    def draw(self, surf): pygame.draw.circle(surf, (100,100,150), (self.x, self.y), self.s)

if __name__ == "__main__": NeonEngine().run()
