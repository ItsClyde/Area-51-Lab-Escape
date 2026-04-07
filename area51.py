import pygame
import sys
import os
import math
import random

# --- INITIALIZATION ---
os.chdir(os.path.dirname(os.path.abspath(__file__)))
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.init()

# --- SCREEN SETUP ---
info = pygame.display.Info()
screen_w, screen_h = info.current_w, info.current_h
game_width, game_height = screen_w, screen_h - 70
screen = pygame.display.set_mode((game_width, game_height))
pygame.display.set_caption("AREA 51: Lab Escape")

# --- COLORS ---
WHITE, BLACK, RED, GREEN = (255, 255, 255), (0, 0, 0), (200, 0, 0), (0, 200, 0)
DARK_GRAY, WALL_COLOR, DOOR_COLOR = (30, 30, 30), (40, 40, 50), (0, 50, 0)
FLOOR_COLOR_1, FLOOR_COLOR_2, GRID_COLOR = (30, 30, 35), (25, 25, 30), (15, 15, 20)
CYAN, DGREEN = (0, 255, 255), (0, 100, 0)
TILE_SIZE = 60

room_memory = {}
current_coords = [0, 0]
available_passcode_images = [
    "passcode-images/passcode1.png", "passcode-images/passcode2.png",
    "passcode-images/passcode3.png", "passcode-images/passcode4.png",
    "passcode-images/passcode5.png", "passcode-images/passcode6.png",
    "passcode-images/passcode7.png", "passcode-images/passcode8.png"
]

# --- FONTS ---
try:
    title_font    = pygame.font.Font('fonts/Nosifier.ttf', 70)
    menu_font     = pygame.font.Font('fonts/Creepster.ttf', 50)
    hud_font      = pygame.font.Font('fonts/Creepster.ttf', 35)
    terminal_font = pygame.font.SysFont('Courier New', 25, bold=True)
    digit_font    = pygame.font.SysFont('Courier New', 120, bold=True)
except:
    title_font    = pygame.font.SysFont('Arial', 70, bold=True)
    menu_font     = pygame.font.SysFont('Arial', 50)
    hud_font      = pygame.font.SysFont('Arial', 35)
    terminal_font = pygame.font.SysFont('Consolas', 25, bold=True)
    digit_font    = pygame.font.SysFont('Consolas', 120, bold=True)

# --- CLASSES ---

class PasscodeTerminal(pygame.sprite.Sprite):
    def __init__(self, x, y, image_path):
        super().__init__()
        self.passable = True
        try:
            self.image = pygame.image.load(image_path).convert_alpha()
            self.image = pygame.transform.scale(self.image, (70, 70))
        except:
            self.image = pygame.Surface((50, 50)); self.image.fill(RED)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.interact_time = 0
        self.required_time = 90
        self.is_collected  = False

        # Pulse glow effect
        self.pulse_timer = 0

    def update(self, player_rect):
        self.pulse_timer += 0.07

        dist = math.hypot(player_rect.centerx - self.rect.centerx,
                          player_rect.centery - self.rect.centery)
        keys = pygame.key.get_pressed()
        if dist < 100 and keys[pygame.K_e] and not self.is_collected:
            self.interact_time += 1
            if self.interact_time >= self.required_time:
                self.is_collected = True
                return True
        else:
            self.interact_time = 0
        return False

    def draw_pulse(self, surface):
        """Draw a pulsing glow ring around the terminal so it's easy to spot."""
        if self.is_collected:
            return
        alpha = int(100 + 80 * math.sin(self.pulse_timer))
        radius = int(38 + 6 * math.sin(self.pulse_timer))
        glow_surf = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (0, 255, 180, alpha), (radius + 2, radius + 2), radius, 3)
        surface.blit(glow_surf, (self.rect.centerx - radius - 2, self.rect.centery - radius - 2))


class RoomObject(pygame.sprite.Sprite):
    def __init__(self, x, y, image_path, scale=(100, 100)):
        super().__init__()
        passable_items = ["Blood.png", "bloody-scientist.png"]
        self.passable = any(name in image_path for name in passable_items)
        try:
            self.image = pygame.image.load(image_path).convert_alpha()
            self.image = pygame.transform.scale(self.image, scale)
        except:
            self.image = pygame.Surface(scale); self.image.fill((100, 100, 120))
        self.rect = pygame.Rect(x, y, 40, 40)


class SpecialDoor(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, side):
        super().__init__()
        self.image = pygame.Surface((w, h)); self.image.fill((255, 215, 0))
        pygame.draw.rect(self.image, WHITE, (0, 0, w, h), 3)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.side = side


class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h)); self.image.fill(WALL_COLOR)
        pygame.draw.rect(self.image, (70, 70, 90), (0, 0, w, h), 4)
        self.rect = self.image.get_rect(topleft=(x, y))


class Door(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, side):
        super().__init__()
        self.image = pygame.Surface((w, h)); self.image.fill(DOOR_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.side = side


class Alien(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.rect = pygame.Rect(0, 0, 60, 70)
        self.rect.center = (x, y)

        # FIX: Reduced chase speed so the player has a fighting chance.
        # The wind-up system means it doesn't hit full speed instantly either.
        self.speed_patrol  = 1.5
        self.speed_chase   = 2.2   # was 3.2

        self.state         = "patrol"

        # FIX: Reduced detect radius so entering a room doesn't instantly
        # trigger a chase. Reduced lose radius so sprinting to a corner works.
        self.detect_radius = 140   # was 200
        self.lose_radius   = 380   # was 500

        pad = 150
        self.waypoints = [
            (pad, pad),
            (game_width - pad, pad),
            (game_width - pad, game_height - pad),
            (pad, game_height - pad),
        ]
        self.wp_index        = random.randint(0, 3)
        self.return_target   = self.waypoints[self.wp_index]
        self.linger_timer    = 0
        self.linger_duration = random.randint(60, 120)

        # FIX: Chase wind-up — alien ramps to full speed over ~2 seconds
        # instead of snapping to max speed immediately.
        self.chase_buildup = 0.0

        # NEW: Footstep sound indicator — screen edge warning when alien is close
        self.warning_alpha = 0

        self._build_image(chasing=False)

    def _build_image(self, chasing):
        self.image = pygame.Surface((60, 70), pygame.SRCALPHA)
        body_col = (160, 0, 220) if chasing else (100, 0, 160)
        head_col = (180, 0, 255) if chasing else (130, 0, 200)
        eye_col  = (255, 50, 50) if chasing else (200, 200, 200)
        pygame.draw.ellipse(self.image, body_col, (5, 20, 50, 45))
        pygame.draw.ellipse(self.image, head_col, (10, 0, 40, 35))
        pygame.draw.ellipse(self.image, eye_col,  (14, 8, 10, 8))
        pygame.draw.ellipse(self.image, eye_col,  (36, 8, 10, 8))

    def update(self, player_rect):
        px, py = player_rect.centerx, player_rect.centery
        ax, ay = self.rect.centerx, self.rect.centery
        dist   = math.hypot(px - ax, py - ay)

        if self.state == "patrol":
            self._build_image(False)
            if dist < self.detect_radius:
                self.state = "chase"
                self.linger_timer = 0
            else:
                tx, ty  = self.waypoints[self.wp_index]
                wp_dist = math.hypot(tx - ax, ty - ay)
                if wp_dist < 12:
                    self.linger_timer += 1
                    if self.linger_timer >= self.linger_duration:
                        self.wp_index        = (self.wp_index + 1) % len(self.waypoints)
                        self.linger_timer    = 0
                        self.linger_duration = random.randint(60, 120)
                else:
                    self._move_toward(tx, ty, self.speed_patrol)

        elif self.state == "chase":
            self._build_image(True)
            if dist > self.lose_radius:
                self.return_target = self.waypoints[self.wp_index]
                self.state = "return"
                self.chase_buildup = 0.0   # FIX: reset wind-up on disengage
            else:
                # FIX: Gradual wind-up instead of instant max speed
                self.chase_buildup = min(self.chase_buildup + 0.05, 1.0)
                self._move_toward(px, py, self.speed_chase * self.chase_buildup)

        elif self.state == "return":
            self._build_image(False)
            self.chase_buildup = 0.0       # FIX: also reset here for safety
            tx, ty  = self.return_target
            wp_dist = math.hypot(tx - ax, ty - ay)
            if wp_dist < 12:
                self.state = "patrol"
            else:
                self._move_toward(tx, ty, self.speed_patrol)

        # NEW: proximity warning — red vignette intensity based on distance
        # Only visible when alien is within ~350px
        proximity_threshold = 350
        if dist < proximity_threshold:
            self.warning_alpha = int(120 * (1 - dist / proximity_threshold))
        else:
            self.warning_alpha = max(0, self.warning_alpha - 3)

        return self.rect.inflate(10, 10).colliderect(player_rect)

    def _move_toward(self, tx, ty, speed):
        dx   = tx - self.rect.centerx
        dy   = ty - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.rect.x += int(speed * dx / dist)
            self.rect.y += int(speed * dy / dist)

    def draw_proximity_warning(self, surface):
        """Red vignette that pulses brighter as the alien closes in."""
        if self.warning_alpha <= 0:
            return
        vignette = pygame.Surface((game_width, game_height), pygame.SRCALPHA)
        # Draw a thick red border inward
        for i in range(5):
            alpha = max(0, self.warning_alpha - i * 18)
            thick = 30 + i * 20
            pygame.draw.rect(vignette, (180, 0, 0, alpha),
                             (i * 8, i * 8,
                              game_width - i * 16, game_height - i * 16), thick)
        surface.blit(vignette, (0, 0))


class Scientist(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.animations = {
            "idle_up":    ["idle-images/Idle-up.png"],
            "idle_down":  ["idle-images/Idle-down.png"],
            "idle_left":  ["idle-images/Idle-left.png"],
            "idle_right": ["idle-images/Idle-right.png"],
            "walk_up":    ["walking-frames/up-direction/walking-up1.png",
                           "walking-frames/up-direction/walking-up2.png"],
            "walk_down":  ["walking-frames/down-direction/walking-down1.png",
                           "walking-frames/down-direction/walking-down2.png"],
            "walk_left":  ["walking-frames/left-direction/walking-left1.png",
                           "walking-frames/left-direction/walking-left2.png",
                           "walking-frames/left-direction/walking-left3.png"],
            "walk_right": ["walking-frames/right-direction/walking-right1.png",
                           "walking-frames/right-direction/walking-right2.png"],
        }
        for state in self.animations:
            img_list = []
            for path in self.animations[state]:
                try:
                    img = pygame.image.load(path).convert_alpha()
                    img = pygame.transform.scale(img, (110, 160))
                    img_list.append(img)
                except:
                    err = pygame.Surface((110, 160)); err.fill((255, 0, 255))
                    img_list.append(err)
            self.animations[state] = img_list

        self.facing, self.state, self.frame_index = "down", "idle", 0
        self.image = self.animations[f"{self.state}_{self.facing}"][self.frame_index]
        self.rect  = pygame.Rect(0, 0, 50, 50)
        self.rect.center = (game_width // 2, game_height // 2)
        self.speed, self.anim_speed = 4, 0.13

        # NEW: Sprint mechanic — hold Shift to move faster, drains stamina
        self.stamina         = 100.0
        self.stamina_max     = 100.0
        self.stamina_drain   = 0.6
        self.stamina_regen   = 0.25
        self.is_sprinting    = False
        self.sprint_speed    = 6.5

        try:
            self.walk_snd     = pygame.mixer.Sound("sound-effects/walking-floor.wav")
            self.walk_channel = pygame.mixer.Channel(5)
        except:
            self.walk_snd = None

    def update(self, walls, objects):
        keys    = pygame.key.get_pressed()
        moving  = False
        old_pos = self.rect.copy()

        # NEW: Sprint logic
        shift_held = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        if shift_held and self.stamina > 0 and moving:
            self.is_sprinting = True
        else:
            self.is_sprinting = False

        # Determine current speed
        current_speed = self.speed

        if keys[pygame.K_a] or keys[pygame.K_d] or keys[pygame.K_w] or keys[pygame.K_s]:
            moving = True
            if shift_held and self.stamina > 0:
                self.is_sprinting = True
                current_speed = self.sprint_speed
                self.stamina = max(0, self.stamina - self.stamina_drain)
            else:
                self.is_sprinting = False
                self.stamina = min(self.stamina_max, self.stamina + self.stamina_regen)
        else:
            self.is_sprinting = False
            self.stamina = min(self.stamina_max, self.stamina + self.stamina_regen)

        if keys[pygame.K_a]:
            self.rect.x -= current_speed; self.facing = "left"
        elif keys[pygame.K_d]:
            self.rect.x += current_speed; self.facing = "right"
        if pygame.sprite.spritecollideany(self, walls): self.rect.x = old_pos.x
        hit_obj = pygame.sprite.spritecollideany(self, objects)
        if hit_obj and not hit_obj.passable:
            if not (isinstance(hit_obj, PasscodeTerminal) and hit_obj.is_collected):
                self.rect.x = old_pos.x

        old_y = self.rect.y
        if keys[pygame.K_w]:
            self.rect.y -= current_speed; self.facing = "up"
        elif keys[pygame.K_s]:
            self.rect.y += current_speed; self.facing = "down"
        if pygame.sprite.spritecollideany(self, walls): self.rect.y = old_y
        hit_obj = pygame.sprite.spritecollideany(self, objects)
        if hit_obj and not hit_obj.passable:
            if not (isinstance(hit_obj, PasscodeTerminal) and hit_obj.is_collected):
                self.rect.y = old_y

        if moving:
            if self.walk_snd and not self.walk_channel.get_busy():
                self.walk_channel.play(self.walk_snd, loops=-1)
        else:
            if self.walk_snd: self.walk_channel.stop()

        if moving:
            self.state        = "walk"
            self.frame_index += self.anim_speed
            if self.frame_index >= len(self.animations[f"walk_{self.facing}"]):
                self.frame_index = 0
        else:
            self.state = "idle"; self.frame_index = 0

        self.image = self.animations[f"{self.state}_{self.facing}"][int(self.frame_index)]
        self.rect.clamp_ip(pygame.Rect(0, 0, game_width, game_height))

    def draw_stamina_bar(self, surface):
        """Small stamina bar near bottom of screen, only shown while sprinting or low."""
        if self.stamina >= self.stamina_max and not self.is_sprinting:
            return
        bar_w = 180
        bar_h = 14
        bx    = game_width // 2 - bar_w // 2
        by    = game_height - 50
        fill  = int((self.stamina / self.stamina_max) * bar_w)
        col   = (0, 220, 80) if self.stamina > 40 else (220, 120, 0) if self.stamina > 15 else (220, 30, 30)
        pygame.draw.rect(surface, (30, 30, 30),  (bx - 2, by - 2, bar_w + 4, bar_h + 4))
        pygame.draw.rect(surface, col,            (bx, by, fill, bar_h))
        pygame.draw.rect(surface, WHITE,          (bx - 2, by - 2, bar_w + 4, bar_h + 4), 1)
        label = terminal_font.render("SPRINT", True, col)
        surface.blit(label, (bx + bar_w + 8, by - 2))


# --- WORLD LOGIC ---
def get_room(coords):
    coord_key = tuple(coords)
    if coord_key in room_memory: return room_memory[coord_key]

    max_total_rooms, thickness, door_size = 12, 50, 200
    is_safe_zone  = (coords == [0, 0])
    room_number   = len(room_memory)
    walls         = pygame.sprite.Group()
    doors         = pygame.sprite.Group()
    room_objects  = pygame.sprite.Group()
    special_doors = pygame.sprite.Group()

    forced_doors = {}
    neighbors = [
        ((coords[0], coords[1] + 1), 'top',    'bottom'),
        ((coords[0], coords[1] - 1), 'bottom', 'top'),
        ((coords[0] - 1, coords[1]), 'left',   'right'),
        ((coords[0] + 1, coords[1]), 'right',  'left'),
    ]

    for n_coord, my_side, n_side in neighbors:
        if n_coord in room_memory:
            _, n_doors, _, _, _ = room_memory[n_coord]
            for d in n_doors:
                if d.side == n_side:
                    if my_side in ['top', 'bottom']: forced_doors[my_side] = d.rect.x
                    else:                             forced_doors[my_side] = d.rect.y

    sides        = ['top', 'bottom', 'left', 'right']
    active_sides = list(forced_doors.keys())

    if len(room_memory) < max_total_rooms - 1:
        for s in sides:
            if s not in active_sides and random.random() < 0.2:
                active_sides.append(s)

        found_new_path = False
        for s in active_sides:
            target = None
            if   s == 'top':    target = (coords[0], coords[1] + 1)
            elif s == 'bottom': target = (coords[0], coords[1] - 1)
            elif s == 'left':   target = (coords[0] - 1, coords[1])
            elif s == 'right':  target = (coords[0] + 1, coords[1])
            if target not in room_memory:
                found_new_path = True; break

        if not found_new_path:
            unvisited = [n for n in neighbors if n[0] not in room_memory]
            if unvisited:
                new_n = random.choice(unvisited)
                if new_n[1] not in active_sides: active_sides.append(new_n[1])

    special_side = None
    if len(room_memory) == max_total_rooms - 1:
        potential_walls = [s for s in sides if s not in active_sides]
        if potential_walls:
            special_side = potential_walls[0]
            pos_fixed    = (game_width // 2 - 100) if special_side in ['top', 'bottom'] else (game_height // 2 - 100)
            special_doors.add(SpecialDoor(
                pos_fixed if special_side in ['top', 'bottom'] else (0 if special_side == 'left' else game_width  - thickness),
                pos_fixed if special_side in ['left', 'right'] else (0 if special_side == 'top'  else game_height - thickness),
                200       if special_side in ['top', 'bottom'] else thickness,
                thickness if special_side in ['top', 'bottom'] else 200,
                special_side
            ))

    for side in sides:
        if side in active_sides:
            pos = forced_doors.get(side, random.randint(
                thickness,
                (game_width if side in ['top', 'bottom'] else game_height) - thickness - door_size
            ))
            doors.add(Door(
                pos       if side in ['top', 'bottom'] else (0 if side == 'left' else game_width  - thickness),
                pos       if side in ['left', 'right'] else (0 if side == 'top'  else game_height - thickness),
                door_size if side in ['top', 'bottom'] else thickness,
                thickness if side in ['top', 'bottom'] else door_size,
                side
            ))

    if not is_safe_zone:
        avoid_rects = ([d.rect.inflate(150, 150) for d in doors] +
                       [sd.rect.inflate(150, 150) for sd in special_doors])
        global available_passcode_images
        if available_passcode_images and len(room_memory) < max_total_rooms - 1:
            p_img    = available_passcode_images.pop(0)
            placed_p = False
            attempts = 0
            while not placed_p and attempts < 100:
                px, py = random.randint(150, game_width - 150), random.randint(150, game_height - 150)
                p_rect = pygame.Rect(px, py, 70, 70)
                if not any(p_rect.colliderect(a) for a in avoid_rects):
                    room_objects.add(PasscodeTerminal(px, py, p_img))
                    avoid_rects.append(p_rect.inflate(100, 100))
                    placed_p = True
                attempts += 1

        master_items = [
            ("decorations-images/Chemical.png",          (160, 180)),
            ("decorations-images/Broken-radio.png",       (100, 100)),
            ("decorations-images/Broken-Chem-Glass.png",  (110,  70)),
            ("decorations-images/Blood.png",              (110,  80)),
            ("decorations-images/bloody-scientist.png",   (130, 100)),
            ("decorations-images/Smoke.png",              (150,  80)),
            ("decorations-images/Papers.png",             ( 80,  80)),
            ("decorations-images/table.png",              (100,  80)),
            ("decorations-images/chair.png",              (130, 110)),
            ("decorations-images/stones.png",             (110,  80)),
            ("decorations-images/broken-wire.png",        (140, 160)),
            ("decorations-images/destroyed-computer.png", (180, 200)),
        ]

        for _ in range(random.randint(8, 12)):
            path, size = random.choice(master_items)
            rx, ry     = random.randint(100, game_width - 200), random.randint(100, game_height - 200)
            temp_rect  = pygame.Rect(rx, ry, size[0], size[1])
            if not any(temp_rect.colliderect(a) for a in avoid_rects):
                room_objects.add(RoomObject(rx, ry, path, size))
                avoid_rects.append(temp_rect.inflate(40, 40))

    for side in sides:
        is_reg_door  = any(d.side == side for d in doors)
        is_spec_door = (side == special_side)
        if side == 'top':
            if is_reg_door or is_spec_door:
                d_rect = next(d.rect for d in list(doors) + list(special_doors) if d.side == 'top')
                walls.add(Wall(0, 0, d_rect.x, thickness),
                          Wall(d_rect.right, 0, game_width - d_rect.right, thickness))
            else: walls.add(Wall(0, 0, game_width, thickness))
        elif side == 'bottom':
            if is_reg_door or is_spec_door:
                d_rect = next(d.rect for d in list(doors) + list(special_doors) if d.side == 'bottom')
                walls.add(Wall(0, game_height - thickness, d_rect.x, thickness),
                          Wall(d_rect.right, game_height - thickness, game_width - d_rect.right, thickness))
            else: walls.add(Wall(0, game_height - thickness, game_width, thickness))
        elif side == 'left':
            if is_reg_door or is_spec_door:
                d_rect = next(d.rect for d in list(doors) + list(special_doors) if d.side == 'left')
                walls.add(Wall(0, 0, thickness, d_rect.y),
                          Wall(0, d_rect.bottom, thickness, game_height - d_rect.bottom))
            else: walls.add(Wall(0, 0, thickness, game_height))
        elif side == 'right':
            if is_reg_door or is_spec_door:
                d_rect = next(d.rect for d in list(doors) + list(special_doors) if d.side == 'right')
                walls.add(Wall(game_width - thickness, 0, thickness, d_rect.y),
                          Wall(game_width - thickness, d_rect.bottom, thickness, game_height - d_rect.bottom))
            else: walls.add(Wall(game_width - thickness, 0, thickness, game_height))

    room_memory[coord_key] = (walls, doors, room_objects, special_doors, room_number)
    return walls, doors, room_objects, special_doors, room_number


# --- DRAW HELPERS ---
def draw_text(text, font, color, x, y):
    img = font.render(text, True, color); screen.blit(img, (x, y))


def draw_floor(surface):
    for x in range(0, game_width, TILE_SIZE):
        for y in range(0, game_height, TILE_SIZE):
            color = FLOOR_COLOR_1 if (x // TILE_SIZE + y // TILE_SIZE) % 2 == 0 else FLOOR_COLOR_2
            pygame.draw.rect(surface, color, (x, y, TILE_SIZE, TILE_SIZE))
            pygame.draw.rect(surface, GRID_COLOR, (x, y, TILE_SIZE, TILE_SIZE), 1)


def draw_lighting(player_rect, mouse_pos, is_backup_mode):
    darkness = pygame.Surface((game_width, game_height), pygame.SRCALPHA)

    if not is_backup_mode:
        # FIX: Denser base darkness — was 210, now 230
        darkness.fill((0, 0, 0, 230))

        # FIX: Tighter ambient glow — was 130, now 80
        glow_radius = 80
        for r in range(glow_radius, 0, -6):
            alpha = int(200 * (r / glow_radius))
            pygame.draw.circle(darkness, (0, 0, 0, alpha), player_rect.center, r)

        # FIX: Narrower cone with more alpha so unlit areas stay dark
        rel_x = mouse_pos[0] - player_rect.centerx
        rel_y = mouse_pos[1] - player_rect.centery
        angle = math.atan2(rel_y, rel_x)
        p1    = player_rect.center

        cone_layers = [
            (0.40, 100),  # wide outer edge — was (0.55, 55)
            (0.25, 60),   # mid             — was (0.38, 30)
            (0.12, 20),   # bright core     — was (0.20, 10)
        ]
        for spread, alpha in cone_layers:
            p2 = (p1[0] + math.cos(angle - spread) * 1800,
                  p1[1] + math.sin(angle - spread) * 1800)
            p3 = (p1[0] + math.cos(angle + spread) * 1800,
                  p1[1] + math.sin(angle + spread) * 1800)
            pygame.draw.polygon(darkness, (0, 0, 0, alpha), [p1, p2, p3])

    else:
        # Backup / flicker mode — tight blue-tinted circle only
        darkness.fill((0, 0, 15, 235))
        backup_radius = 115
        for r in range(backup_radius, 0, -5):
            alpha = int(210 * (r / backup_radius))
            pygame.draw.circle(darkness, (0, 0, 10, alpha), player_rect.center, r)

    screen.blit(darkness, (0, 0))


def draw_minimap(surface, current_coords, room_memory, player_rect):
    """
    NEW: Simple minimap in the top-right corner showing visited rooms
    and the player's current position. Helps navigation without
    breaking immersion since it's small and dark-themed.
    """
    cell   = 14
    pad    = 4
    origin = (game_width - 160, 55)

    # Background panel
    panel_w, panel_h = 145, 145
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 160))
    pygame.draw.rect(panel, (0, 180, 180, 120), (0, 0, panel_w, panel_h), 1)
    surface.blit(panel, origin)

    label = terminal_font.render("MAP", True, (0, 180, 180))
    surface.blit(label, (origin[0] + panel_w // 2 - label.get_width() // 2, origin[1] + 2))

    # Center the map on current coords
    cx, cy = current_coords
    for coord_key in room_memory:
        rx, ry     = coord_key
        rel_x      = rx - cx
        rel_y      = -(ry - cy)   # flip Y so up = up
        draw_x     = origin[0] + panel_w // 2 + rel_x * (cell + pad) - cell // 2
        draw_y     = origin[1] + panel_h // 2 + rel_y * (cell + pad) - cell // 2
        _, _, _, special_doors, room_num = room_memory[coord_key]
        is_exit    = len(list(special_doors)) > 0
        color      = (255, 215, 0) if is_exit else (0, 140, 140)
        pygame.draw.rect(surface, color, (draw_x, draw_y, cell, cell))
        if coord_key == (cx, cy):
            # Current room — bright highlight + player dot
            pygame.draw.rect(surface, (0, 255, 200), (draw_x, draw_y, cell, cell), 2)
            pygame.draw.circle(surface, WHITE, (draw_x + cell // 2, draw_y + cell // 2), 3)

    # Legend
    lx, ly = origin[0] + 4, origin[1] + panel_h - 18
    pygame.draw.rect(surface, (255, 215, 0), (lx, ly, 8, 8))
    surface.blit(terminal_font.render("EXIT", True, (255, 215, 0)), (lx + 12, ly - 3))


def draw_digital_pad(digit):
    pad_w, pad_h = 400, 500
    pad_x = (game_width  - pad_w) // 2
    pad_y = (game_height - pad_h) // 2
    pygame.draw.rect(screen, (0, 150, 150), (pad_x - 5, pad_y - 5, pad_w + 10, pad_h + 10), 2)
    pygame.draw.rect(screen, (10, 20, 20),  (pad_x, pad_y, pad_w, pad_h))
    pygame.draw.rect(screen, (0, 80, 80),   (pad_x, pad_y, pad_w, 40))
    head_txt = terminal_font.render("TERMINAL ACCESS: GRANTED", True, CYAN)
    screen.blit(head_txt, (pad_x + 20, pad_y + 8))
    digit_main = digit_font.render(digit, True, CYAN)
    screen.blit(digit_main, (pad_x + 130, pad_y + 150))
    draw_text("STORING TO HUD...",       terminal_font, CYAN,  pad_x + 40, pad_y + 400)
    draw_text("CLICK MOUSE TO CONTINUE", terminal_font, WHITE, pad_x + 35, pad_y + 440)


def draw_win_screen(time_str, mouse_pos):
    pad_w, pad_h = 650, 450
    pad_x = (game_width  - pad_w) // 2
    pad_y = (game_height - pad_h) // 2
    again_rect = pygame.Rect(pad_x + 50,  pad_y + 320, 250, 60)
    quit_rect  = pygame.Rect(pad_x + 350, pad_y + 320, 250, 60)
    pygame.draw.rect(screen, (0, 255, 0), (pad_x - 5, pad_y - 5, pad_w + 10, pad_h + 10), 2)
    pygame.draw.rect(screen, (5, 15, 5),  (pad_x, pad_y, pad_w, pad_h))
    draw_text("Congratulations! You survived!", menu_font,     GREEN, pad_x + 30,  pad_y + 50)
    draw_text(f"Survival Time: {time_str}",     terminal_font, WHITE, pad_x + 185, pad_y + 160)
    pygame.draw.rect(screen, GREEN if again_rect.collidepoint(mouse_pos) else DGREEN,      again_rect)
    pygame.draw.rect(screen, RED   if quit_rect.collidepoint(mouse_pos)  else (100, 0, 0), quit_rect)
    draw_text("PLAY AGAIN", terminal_font,
              BLACK if again_rect.collidepoint(mouse_pos) else WHITE, again_rect.x + 55, again_rect.y + 15)
    draw_text("QUIT GAME",  terminal_font,
              BLACK if quit_rect.collidepoint(mouse_pos)  else WHITE, quit_rect.x  + 60, quit_rect.y  + 15)
    return again_rect, quit_rect


def draw_gameover_screen(mouse_pos):
    respawn_rect = pygame.Rect(game_width // 2 - 160, game_height // 2 + 60, 140, 55)
    quit_rect    = pygame.Rect(game_width // 2 + 20,  game_height // 2 + 60, 140, 55)
    dim = pygame.Surface((game_width, game_height), pygame.SRCALPHA)
    dim.fill((0, 0, 0, 210)); screen.blit(dim, (0, 0))
    draw_text("YOU HAVE BEEN KILLED!",       hud_font,      RED,   game_width // 2 - 220, game_height // 2 - 80)
    draw_text("The alien has caught you...", terminal_font, WHITE, game_width // 2 - 185, game_height // 2 - 20)
    pygame.draw.rect(screen, GREEN if respawn_rect.collidepoint(mouse_pos) else DGREEN,      respawn_rect)
    pygame.draw.rect(screen, RED   if quit_rect.collidepoint(mouse_pos)    else (100, 0, 0), quit_rect)
    draw_text("Respawn",   terminal_font,
              BLACK if respawn_rect.collidepoint(mouse_pos) else WHITE, respawn_rect.x + 18, respawn_rect.y + 15)
    draw_text("Quit Game", terminal_font,
              BLACK if quit_rect.collidepoint(mouse_pos)    else WHITE, quit_rect.x    + 12, quit_rect.y    + 15)
    return respawn_rect, quit_rect


def draw_crosshair(mouse_pos):
    cx, cy = mouse_pos
    pygame.draw.circle(screen, (255, 255, 180), (cx, cy), 5)
    pygame.draw.circle(screen, (220, 220, 100), (cx, cy), 9, 1)
    pygame.draw.line(screen, (220, 220, 100), (cx - 14, cy), (cx - 7,  cy), 1)
    pygame.draw.line(screen, (220, 220, 100), (cx + 7,  cy), (cx + 14, cy), 1)
    pygame.draw.line(screen, (220, 220, 100), (cx, cy - 14), (cx, cy - 7),  1)
    pygame.draw.line(screen, (220, 220, 100), (cx, cy + 7),  (cx, cy + 14), 1)


# --- PAUSE MENU ---
def draw_pause_screen(mouse_pos):
    """NEW: In-game pause menu with resume and quit options."""
    dim = pygame.Surface((game_width, game_height), pygame.SRCALPHA)
    dim.fill((0, 0, 0, 200))
    screen.blit(dim, (0, 0))

    pad_w, pad_h = 500, 380
    pad_x = (game_width  - pad_w) // 2
    pad_y = (game_height - pad_h) // 2

    pygame.draw.rect(screen, (0, 150, 150), (pad_x - 3, pad_y - 3, pad_w + 6, pad_h + 6), 2)
    pygame.draw.rect(screen, (8, 18, 18),   (pad_x, pad_y, pad_w, pad_h))

    draw_text("— PAUSED —", hud_font, CYAN, pad_x + pad_w // 2 - 100, pad_y + 40)
    draw_text("WASD  — Move",         terminal_font, WHITE, pad_x + 60, pad_y + 110)
    draw_text("E     — Decrypt terminal", terminal_font, WHITE, pad_x + 60, pad_y + 140)
    draw_text("F     — Use exit door / Cancel input", terminal_font, WHITE, pad_x + 60, pad_y + 170)
    draw_text("SHIFT — Sprint (drains stamina)", terminal_font, WHITE, pad_x + 60, pad_y + 200)
    draw_text("ESC   — Pause / Unpause", terminal_font, WHITE, pad_x + 60, pad_y + 230)

    resume_rect = pygame.Rect(pad_x + 60,  pad_y + 290, 170, 50)
    quit_rect   = pygame.Rect(pad_x + 270, pad_y + 290, 170, 50)

    pygame.draw.rect(screen, GREEN if resume_rect.collidepoint(mouse_pos) else DGREEN, resume_rect)
    pygame.draw.rect(screen, RED   if quit_rect.collidepoint(mouse_pos)   else (100, 0, 0), quit_rect)
    draw_text("RESUME",    terminal_font,
              BLACK if resume_rect.collidepoint(mouse_pos) else WHITE, resume_rect.x + 30, resume_rect.y + 12)
    draw_text("QUIT GAME", terminal_font,
              BLACK if quit_rect.collidepoint(mouse_pos)   else WHITE, quit_rect.x   + 12, quit_rect.y   + 12)
    return resume_rect, quit_rect


# --- MAIN GAME LOOP ---
def play_game():
    global current_coords, available_passcode_images
    pygame.mouse.set_visible(False)

    pygame.mixer.music.load("music/background-music.mp3")
    pygame.mixer.music.set_volume(0.3)
    pygame.mixer.music.play(-1)

    decrypt_snd = pygame.mixer.Sound("sound-effects/decrypting.wav")
    decrypt_snd.set_volume(0.5)

    current_coords = [0, 0]
    room_memory.clear()
    available_passcode_images = [
        "passcode-images/passcode1.png", "passcode-images/passcode2.png",
        "passcode-images/passcode3.png", "passcode-images/passcode4.png",
        "passcode-images/passcode5.png", "passcode-images/passcode6.png",
        "passcode-images/passcode7.png", "passcode-images/passcode8.png"
    ]
    random.shuffle(available_passcode_images)

    walls, doors, room_objects, special_doors, current_room_id = get_room(current_coords)
    player = Scientist()
    clock  = pygame.time.Clock()

    # Alien — FIX: spawn in the corner furthest from the player
    alien        = Alien(game_width // 4, game_height // 4)
    alien_active = False
    alien_room   = None

    passcodes_collected = 0

    # Flashlight flicker state
    is_flickering, flicker_timer             = False, 0
    is_strobing,   strobe_timer, strobe_count = False, 0, 0
    backup_blend = 0.0

    start_ticks      = pygame.time.get_ticks()
    collected_digits = ["?"] * 8
    current_popup_digit, popup_active = "", False
    input_active, user_input_text, input_feedback, feedback_timer = False, "", "", 0
    game_won  = False
    game_over = False
    paused    = False   # NEW: pause state
    final_time_str              = ""
    win_again_btn, win_quit_btn = None, None
    go_respawn_btn, go_quit_btn = None, None
    pause_resume_btn, pause_quit_btn = None, None
    intense_music_started       = False

    # NEW: Room transition fade
    fade_alpha   = 255
    fading_in    = True

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        keys      = pygame.key.get_pressed()

        if not game_won and not game_over and not paused:
            current_seconds = (pygame.time.get_ticks() - start_ticks) // 1000
            display_time    = f"Time: {current_seconds // 60}m {current_seconds % 60}s"

        if tuple(current_coords) != (0, 0):
            alien_active = True

        if passcodes_collected >= 8 and not intense_music_started and not game_won:
            intense_music_started = True
            try:
                pygame.mixer.music.load("music/intense-bg.mp3")
                pygame.mixer.music.set_volume(0.8)
                pygame.mixer.music.play(-1)
            except:
                pass

        # --- EVENTS ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if game_won:
                    if win_again_btn and win_again_btn.collidepoint(mouse_pos):
                        pygame.mouse.set_visible(True); play_game(); return
                    if win_quit_btn  and win_quit_btn.collidepoint(mouse_pos):
                        pygame.quit(); sys.exit()
                if game_over:
                    if go_respawn_btn and go_respawn_btn.collidepoint(mouse_pos):
                        pygame.mouse.set_visible(True); play_game(); return
                    if go_quit_btn   and go_quit_btn.collidepoint(mouse_pos):
                        pygame.quit(); sys.exit()
                if paused:
                    if pause_resume_btn and pause_resume_btn.collidepoint(mouse_pos):
                        paused = False
                        pygame.mouse.set_visible(False)
                    if pause_quit_btn and pause_quit_btn.collidepoint(mouse_pos):
                        pygame.quit(); sys.exit()
                if popup_active:
                    popup_active = False

            if event.type == pygame.KEYDOWN:
                # NEW: ESC now toggles pause instead of quitting directly
                if event.key == pygame.K_ESCAPE:
                    if game_won or game_over:
                        pygame.mouse.set_visible(True); running = False
                    elif input_active:
                        input_active = False
                    else:
                        paused = not paused
                        pygame.mouse.set_visible(paused)

                if input_active and not game_won and not game_over and not paused:
                    if event.key == pygame.K_RETURN:
                        correct_code = "".join(collected_digits)
                        if user_input_text == correct_code and "?" not in correct_code:
                            seconds        = (pygame.time.get_ticks() - start_ticks) // 1000
                            final_time_str = f"{seconds // 60}m {seconds % 60}s"
                            game_won       = True
                            input_active   = False
                            pygame.mouse.set_visible(True)
                            try:
                                pygame.mixer.music.load("music/victory-sound.wav")
                                pygame.mixer.music.set_volume(1.0)
                                pygame.mixer.music.play(-1)
                            except:
                                pass
                        else:
                            input_feedback  = "ACCESS DENIED"
                            user_input_text = ""
                            feedback_timer  = 60
                    elif event.key == pygame.K_BACKSPACE:
                        user_input_text = user_input_text[:-1]
                    elif event.key == pygame.K_f:
                        input_active = False
                    else:
                        if event.unicode.isdigit() and len(user_input_text) < 8:
                            user_input_text += event.unicode

        # --- UPDATES (skip while paused) ---
        if not popup_active and not input_active and not game_won and not game_over and not paused:
            player.update(walls, room_objects)

        if alien_active and not game_won and not game_over and not popup_active and not input_active and not paused:
            coord_key = tuple(current_coords)
            if coord_key != (0, 0) and coord_key != alien_room:
                alien_room = coord_key
                # FIX: Spawn alien in the quadrant furthest from the player
                ax = game_width  - 200 if player.rect.centerx < game_width  // 2 else 200
                ay = game_height - 200 if player.rect.centery < game_height // 2 else 200
                alien.rect.center = (ax, ay)
                alien.state       = "patrol"
                alien.chase_buildup = 0.0

            if alien.update(player.rect):
                game_over = True
                try: pygame.mixer.music.stop()
                except: pass

        if not game_won and not game_over and not paused:
            for s_door in special_doors:
                if math.hypot(player.rect.centerx - s_door.rect.centerx,
                              player.rect.centery - s_door.rect.centery) < 120:
                    if keys[pygame.K_f] and not input_active and not popup_active:
                        input_active    = True
                        user_input_text = ""
                        input_feedback  = ""

            is_decrypting = False
            for obj in room_objects:
                if isinstance(obj, PasscodeTerminal) and not obj.is_collected:
                    if math.hypot(player.rect.centerx - obj.rect.centerx,
                                  player.rect.centery - obj.rect.centery) < 100:
                        if keys[pygame.K_e]:
                            is_decrypting = True
                            if not pygame.mixer.Channel(2).get_busy():
                                pygame.mixer.Channel(2).play(decrypt_snd, loops=-1)
                            if obj.update(player.rect):
                                pygame.mixer.Channel(2).stop()
                                new_digit = str(random.randint(0, 9))
                                for i in range(len(collected_digits)):
                                    if collected_digits[i] == "?":
                                        collected_digits[i] = new_digit; break
                                passcodes_collected += 1
                                current_popup_digit  = new_digit
                                popup_active         = True
            if not is_decrypting:
                pygame.mixer.Channel(2).stop()

        # Door traversal
        if not game_won and not game_over and not input_active and not popup_active and not paused:
            door_hit = pygame.sprite.spritecollideany(player, doors)
            if door_hit:
                if   door_hit.side == 'top':    current_coords[1] += 1
                elif door_hit.side == 'bottom': current_coords[1] -= 1
                elif door_hit.side == 'left':   current_coords[0] -= 1
                elif door_hit.side == 'right':  current_coords[0] += 1
                walls, doors, room_objects, special_doors, current_room_id = get_room(current_coords)
                rev    = {'top': 'bottom', 'bottom': 'top', 'left': 'right', 'right': 'left'}[door_hit.side]
                target = next((d for d in doors if d.side == rev), None)
                if target:
                    if   rev == 'bottom': player.rect.centerx = target.rect.centerx; player.rect.bottom = target.rect.top    - 10
                    elif rev == 'top':    player.rect.centerx = target.rect.centerx; player.rect.top    = target.rect.bottom  + 10
                    elif rev == 'right':  player.rect.centery = target.rect.centery; player.rect.right  = target.rect.left   - 10
                    elif rev == 'left':   player.rect.centery = target.rect.centery; player.rect.left   = target.rect.right  + 10

                # NEW: Trigger room fade-in on transition
                fading_in  = True
                fade_alpha = 200

        # Flicker / strobe (paused when game is paused)
        if not paused:
            if not is_flickering and not is_strobing:
                if random.random() < 0.002:
                    is_strobing, strobe_timer, strobe_count = True, 0, 0
            if is_strobing:
                strobe_timer += 1
                if strobe_timer > random.randint(2, 5):
                    strobe_timer = 0; strobe_count += 1
                if strobe_count > 10:
                    is_strobing, is_flickering, flicker_timer = False, True, 0
            if is_flickering:
                flicker_timer += 1
                if flicker_timer > 300: is_flickering = False

        target_blend  = 1.0 if is_flickering else 0.0
        backup_blend += (target_blend - backup_blend) * 0.12

        # --- DRAW ---
        draw_floor(screen)

        # Draw terminal pulse glow under other objects
        for obj in room_objects:
            if isinstance(obj, PasscodeTerminal) and not obj.is_collected:
                obj.draw_pulse(screen)

        for obj in room_objects:
            if isinstance(obj, PasscodeTerminal) and obj.is_collected: continue
            screen.blit(obj.image, obj.image.get_rect(center=obj.rect.center))

        walls.draw(screen); doors.draw(screen); special_doors.draw(screen)
        screen.blit(player.image, player.image.get_rect(center=player.rect.center))

        if alien_active and tuple(current_coords) != (0, 0) and not game_over:
            screen.blit(alien.image, alien.rect)

        # --- LIGHTING ---
        if is_strobing and strobe_count % 2 == 0:
            screen.blit(pygame.Surface((game_width, game_height)), (0, 0))
        elif backup_blend > 0.95:
            draw_lighting(player.rect, mouse_pos, is_backup_mode=True)
        elif backup_blend > 0.05:
            draw_lighting(player.rect, mouse_pos, is_backup_mode=False)
            overlay = pygame.Surface((game_width, game_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 15, int(backup_blend * 235)))
            br = 115
            for r in range(br, 0, -5):
                a = int(backup_blend * 210 * (r / br))
                pygame.draw.circle(overlay, (0, 0, 10, a), player.rect.center, r)
            screen.blit(overlay, (0, 0))
        else:
            draw_lighting(player.rect, mouse_pos, is_backup_mode=False)

        # NEW: Proximity warning vignette drawn AFTER lighting
        if alien_active and tuple(current_coords) != (0, 0) and not game_over and not game_won:
            alien.draw_proximity_warning(screen)

        # --- HUD ---
        room_label = "SAFE ZONE" if current_room_id == 0 else f"ROOM: {current_room_id}"
        draw_text(room_label, hud_font, WHITE, 20, 20)
        if not game_won and not game_over:
            draw_text(display_time, hud_font, WHITE, game_width // 2 - 100, 20)
        draw_text(f"COLLECTED: {passcodes_collected}/8", hud_font, GREEN, game_width - 220, 20)
        draw_text("PASSCODES: " + " ".join(collected_digits), terminal_font, CYAN, 20, 60)

        # NEW: Minimap
        draw_minimap(screen, current_coords, room_memory, player.rect)

        # NEW: Stamina bar
        player.draw_stamina_bar(screen)

        if alien_active and tuple(current_coords) != (0, 0) and not game_over and not game_won:
            if alien.state == "chase" and (pygame.time.get_ticks() // 300) % 2 == 0:
                draw_text("!! ALIEN DETECTED !!", hud_font, RED, game_width // 2 - 180, game_height - 120)

        if passcodes_collected >= 8 and not game_won and not game_over:
            if (pygame.time.get_ticks() // 500) % 2 == 0:
                draw_text("ALL PASSCODES SECURED: FIND THE EXIT!", hud_font, RED, game_width // 2 - 250, 80)

        # Interaction prompts + progress bar
        if not input_active and not popup_active and not game_won and not game_over and not paused:
            for s_door in special_doors:
                if math.hypot(player.rect.centerx - s_door.rect.centerx,
                              player.rect.centery - s_door.rect.centery) < 120:
                    draw_text("PRESS [F] TO ENTER CODE", hud_font, CYAN,
                              game_width // 2 - 180, game_height - 150)
            for obj in room_objects:
                if isinstance(obj, PasscodeTerminal) and not obj.is_collected:
                    if math.hypot(player.rect.centerx - obj.rect.centerx,
                                  player.rect.centery - obj.rect.centery) < 100:
                        draw_text("HOLD [E] TO DECRYPT", hud_font, WHITE,
                                  game_width // 2 - 150, game_height - 150)
                        pygame.draw.rect(screen, GREEN, (
                            game_width // 2 - 200, game_height - 90,
                            (obj.interact_time / obj.required_time) * 400, 20
                        ))

        # NEW: Room transition fade overlay
        if fading_in and fade_alpha > 0:
            fade_surf = pygame.Surface((game_width, game_height))
            fade_surf.fill(BLACK)
            fade_surf.set_alpha(fade_alpha)
            screen.blit(fade_surf, (0, 0))
            fade_alpha = max(0, fade_alpha - 8)
            if fade_alpha == 0:
                fading_in = False

        # Custom crosshair
        if not game_over and not game_won and not popup_active and not input_active and not paused:
            draw_crosshair(mouse_pos)

        # --- OVERLAYS ---
        if popup_active:
            dim = pygame.Surface((game_width, game_height), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 180)); screen.blit(dim, (0, 0))
            draw_digital_pad(current_popup_digit)

        if input_active:
            dim = pygame.Surface((game_width, game_height), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 220)); screen.blit(dim, (0, 0))
            box_rect = pygame.Rect(game_width // 2 - 300, game_height // 2 - 100, 600, 220)
            pygame.draw.rect(screen, (10, 20, 20), box_rect)
            pygame.draw.rect(screen, CYAN, box_rect, 3)
            draw_text("SECURITY INTERFACE - 8 DIGITS REQUIRED", terminal_font, CYAN,
                      box_rect.x + 40, box_rect.y + 20)
            input_surf  = digit_font.render(user_input_text + "_", True, CYAN)
            screen.blit(input_surf, input_surf.get_rect(center=(game_width // 2, game_height // 2)))
            if feedback_timer > 0:
                draw_text(input_feedback, terminal_font, RED,   box_rect.x + 220, box_rect.y + 180)
                feedback_timer -= 1
            else:
                draw_text("[ENTER] TO CONFIRM | [F] TO CANCEL", terminal_font, WHITE,
                          box_rect.x + 60, box_rect.y + 180)

        if paused:
            pygame.mouse.set_visible(True)
            pause_resume_btn, pause_quit_btn = draw_pause_screen(mouse_pos)

        if game_won:
            dim = pygame.Surface((game_width, game_height), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 240)); screen.blit(dim, (0, 0))
            win_again_btn, win_quit_btn = draw_win_screen(final_time_str, mouse_pos)

        if game_over:
            go_respawn_btn, go_quit_btn = draw_gameover_screen(mouse_pos)

        pygame.display.update()
        clock.tick(60)


# --- MAIN MENU ---
def main_menu():
    start_rect = pygame.Rect(100, 300, 350, 60)
    quit_rect  = pygame.Rect(100, 400, 350, 60)

    try:
        menu_bg = pygame.image.load("background-image/game-background.jpeg").convert()
        menu_bg = pygame.transform.scale(menu_bg, (game_width, game_height))
    except:
        menu_bg = None

    pygame.mixer.music.load("music/menu-music.mp3")
    pygame.mixer.music.play(-1)

    while True:
        mouse_pos = pygame.mouse.get_pos()
        if menu_bg: screen.blit(menu_bg, (0, 0))
        else:       screen.fill(BLACK)

        draw_text("AREA 51: Lab Escape", title_font, RED,   105, 105)
        draw_text("AREA 51: Lab Escape", title_font, WHITE, 100, 100)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_rect.collidepoint(mouse_pos):
                    play_game()
                    pygame.mixer.music.load("music/menu-music.mp3")
                    pygame.mixer.music.play(-1)
                if quit_rect.collidepoint(mouse_pos):
                    pygame.quit(); sys.exit()

        draw_text("START GAME", menu_font, RED if start_rect.collidepoint(mouse_pos) else WHITE,
                  start_rect.x, start_rect.y)
        draw_text("QUIT GAME",  menu_font, RED if quit_rect.collidepoint(mouse_pos)  else WHITE,
                  quit_rect.x,  quit_rect.y)
        pygame.display.update()


if __name__ == "__main__":
    main_menu()