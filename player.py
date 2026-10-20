"""
Player-controlled vehicle and Live A* GPS Navigator for GridLock AI: Driver Edition.
Handles precision lane-constrained steering, Q-key instant GPS recalculation,
signal obedience, and night-drive lighting effects (headlight cones, taillights,
and ambient traffic light reflections).
"""

import math
import random
import pygame
from config import (
    PLAYER_COLOR, PLAYER_ACCENT, PLAYER_MAX_SPEED, PLAYER_ACCELERATION,
    PLAYER_BRAKE, PLAYER_REVERSE_SPEED, PLAYER_TURN_SPEED,
    PLAYER_COLLISION_COOLDOWN, VEHICLE_LENGTH, VEHICLE_WIDTH,
    ROAD_WIDTH, GRID_AREA_WIDTH, WINDOW_HEIGHT, WINDOW_WIDTH,
    PATH_OVERLAY, RED_LIGHT_PENALTY, MAX_COLLISION_PENALTY,
    RED_LIGHT, GREEN_LIGHT, YELLOW_LIGHT, STEERING_MAX_ANGLE
)

class PlayerCar:
    """Player-driven cyber vehicle with precision controls & Live A* GPS Co-Pilot."""
    def __init__(self, start_x, start_y, grid, sound_manager=None):
        self.x = float(start_x)
        self.y = float(start_y)
        self.angle = 0.0          # 0 deg = East (+X), 90 deg = South (+Y)
        self.speed = 0.0
        self.grid = grid
        self.sound_manager = sound_manager
        
        # Dimensions (Vehicle Masters Sport Coupe)
        self.length = VEHICLE_LENGTH + 4
        self.width = VEHICLE_WIDTH + 3
        self.wheelbase = float(self.length) * 0.70
        
        # Vehicle Masters Cockpit & Transmission State
        self.gear = "D"                  # 'P', 'R', 'N', 'D'
        self.steer_angle = 0.0           # Physical front wheel pivot degrees (-STEERING_MAX_ANGLE to +STEERING_MAX_ANGLE)
        self.steering_wheel_angle = 0.0  # On-screen steering wheel rotation degrees (-120 to +120)
        self.gas_pressed = False
        self.brake_pressed = False
        self.is_dragging_wheel = False
        self.is_keyboard_gas = False
        self.is_keyboard_brake = False
        
        # Turn Indicators & Hazards
        self.turn_signal = None          # 'LEFT', 'RIGHT', 'HAZARD', or None
        self.blink_timer = 0.0
        self.blink_on = False
        
        # Driver Performance & Violations
        self.score = 1000
        self.violations_count = 0
        self.collisions_count = 0
        self.collision_cooldown = 0.0
        self.violated_intersections = set()
        self.last_violation_msg = ""
        self.violation_msg_timer = 0.0

        # GPS Co-Pilot
        self.destination_node = None
        self.destination_name = "CITY HOSPITAL"
        self.gps_path = []
        self.gps_reroute_timer = 0.0
        self.last_gps_path_ids = []
        self.gps_reroute_notif = ""
        self.gps_notif_timer = 0.0
        
        # Ambient light reflection on chassis
        self.chassis_ambient_color = None
        
        # Trail particles
        self.trail_timer = 0.0
        self.trail_particles = []

    def set_gear(self, new_gear):
        """Switch transmission state: P, R, N, or D."""
        if new_gear in ("P", "R", "N", "D") and new_gear != self.gear:
            self.gear = new_gear
            if self.sound_manager:
                self.sound_manager.play('gear_shift')
            if self.gear == "P":
                self.speed = 0.0

    def toggle_turn_signal(self, signal_type):
        """Toggle LEFT, RIGHT, or HAZARD indicators."""
        if self.turn_signal == signal_type:
            self.turn_signal = None
        else:
            self.turn_signal = signal_type
        if self.sound_manager:
            self.sound_manager.play('turn_signal')

    def honk_horn(self):
        """Honk Vehicle Masters car horn."""
        if self.sound_manager:
            self.sound_manager.play('horn')



    def set_steering_input(self, normalized_val):
        """Normalized steer input from -1.0 (full left) to +1.0 (full right)."""
        clamped = max(-1.0, min(1.0, normalized_val))
        self.steer_angle = clamped * STEERING_MAX_ANGLE
        self.steering_wheel_angle = clamped * 120.0

    def set_destination(self, node, name="CITY HOSPITAL"):
        """Assign destination for the live A* GPS Co-Pilot."""
        self.destination_node = node
        self.destination_name = name
        self.recalculate_gps_path(force=True)

    def get_closest_node(self):
        """Find the nearest graph intersection or perimeter node."""
        closest = None
        min_dist = float('inf')
        for node in self.grid.nodes.values():
            d = math.hypot(node.x - self.x, node.y - self.y)
            if d < min_dist:
                min_dist = d
                closest = node
        return closest

    def recalculate_gps_path(self, force=False, user_triggered=False):
        """
        AI Dynamic A* Navigator:
        Calculates the fastest route from current location to destination,
        factoring in live AI traffic density and bottleneck weights.
        """
        if not self.destination_node:
            return
            
        current_node = self.get_closest_node()
        if not current_node:
            return
            
        new_path = self.grid.a_star(current_node, self.destination_node, is_emergency=True)
        if new_path:
            new_ids = [n.id for n in new_path]
            
            if user_triggered:
                self.gps_reroute_notif = "⚡ GPS REFRESHED: Optimal route updated!"
                self.gps_notif_timer = 2.5
                if self.sound_manager:
                    self.sound_manager.play('gps_refresh')
            elif not force and self.last_gps_path_ids and new_ids != self.last_gps_path_ids:
                self.gps_reroute_notif = "GPS REROUTE: Bottleneck bypassed (+speed)"
                self.gps_notif_timer = 3.0
                if self.sound_manager:
                    self.sound_manager.play('light_change')
                    
            self.gps_path = new_path
            self.last_gps_path_ids = new_ids

    def trigger_manual_reroute(self):
        """Called when player presses 'Q' to force live A* GPS re-query."""
        self.recalculate_gps_path(force=True, user_triggered=True)

    def handle_input(self, keys, dt):
        """
        Process keyboard inputs (WASD or Arrow keys) with precision steering,
        immediate forward/reverse transitions, firm braking, and zero deadzone lag.
        """
        key_up = keys[pygame.K_UP] or keys[pygame.K_w]
        key_down = keys[pygame.K_DOWN] or keys[pygame.K_s]
        key_left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        key_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]

        # ----------------------------------------------------
        # 1. STEERING INPUT (LEFT / RIGHT or Cockpit Wheel)
        # ----------------------------------------------------
        if not self.is_dragging_wheel:
            steer_target = 0.0
            if key_left:
                steer_target -= 1.0
            if key_right:
                steer_target += 1.0

            if steer_target != 0.0:
                # Fast, snappy steering response (reaches full lock in ~0.15s)
                self.steer_angle += steer_target * 340.0 * dt
                self.steer_angle = max(-STEERING_MAX_ANGLE, min(STEERING_MAX_ANGLE, self.steer_angle))
                self.steering_wheel_angle = (self.steer_angle / STEERING_MAX_ANGLE) * 120.0
            else:
                # Smooth, decisive return-to-center spring
                self.steer_angle -= self.steer_angle * min(1.0, 16.0 * dt)
                if abs(self.steer_angle) < 0.2:
                    self.steer_angle = 0.0
                self.steering_wheel_angle = (self.steer_angle / STEERING_MAX_ANGLE) * 120.0

        # ----------------------------------------------------
        # 2. ACCELERATOR & BRAKE / FORWARD & REVERSE DYNAMICS
        # ----------------------------------------------------
        is_pressing_gas = False
        is_pressing_brake = False

        # Mouse pedal input integration
        mouse_gas = self.gas_pressed
        mouse_brake = self.brake_pressed

        if (key_up and key_down) or (mouse_gas and mouse_brake):
            # Both pressed simultaneously: safety stop to halt
            if self.speed > 0:
                self.speed = max(0.0, self.speed - PLAYER_BRAKE * dt)
            elif self.speed < 0:
                self.speed = min(0.0, self.speed + PLAYER_BRAKE * dt)
            is_pressing_brake = True

        elif mouse_brake and not key_up and not key_down:
            # Pure on-screen brake pedal held
            if self.speed > 0:
                self.speed = max(0.0, self.speed - PLAYER_BRAKE * dt)
            elif self.speed < 0:
                self.speed = min(0.0, self.speed + PLAYER_BRAKE * dt)
            is_pressing_brake = True

        elif key_up or (mouse_gas and self.gear != "R"):
            # UP ARROW / W: ALWAYS MOVE FORWARD
            if self.gear == "P":
                self.set_gear("D")

            if self.speed < -1.0:
                # If currently moving backward in reverse, UP acts as a brake to cancel reverse momentum
                self.speed = min(0.0, self.speed + PLAYER_BRAKE * dt)
                is_pressing_brake = True
            else:
                # Once stopped or moving forward, engage Drive and accelerate smoothly
                if self.gear != "D":
                    self.set_gear("D")
                self.speed = min(PLAYER_MAX_SPEED, self.speed + PLAYER_ACCELERATION * dt)
                is_pressing_gas = True

        elif key_down or (mouse_gas and self.gear == "R"):
            # DOWN ARROW / S: BRAKE WHEN MOVING FORWARD, REVERSE WHEN STOPPED
            if self.speed > 1.5:
                # Moving forward: firm, decisive braking
                self.speed = max(0.0, self.speed - PLAYER_BRAKE * dt)
                is_pressing_brake = True
            else:
                # Stopped or already in reverse: shift to Reverse gear and back up cleanly
                if self.gear != "R":
                    self.set_gear("R")
                self.speed = max(-PLAYER_REVERSE_SPEED, self.speed - PLAYER_ACCELERATION * dt)
                is_pressing_gas = True

        else:
            # Neither UP nor DOWN pressed: natural rolling friction deceleration to a clean stop
            if self.speed > 0:
                self.speed = max(0.0, self.speed - 120.0 * dt)
            elif self.speed < 0:
                self.speed = min(0.0, self.speed + 120.0 * dt)
            if abs(self.speed) < 1.0:
                self.speed = 0.0

        # Synchronize cockpit HUD visual pedal animations
        self.is_keyboard_gas = is_pressing_gas
        self.is_keyboard_brake = is_pressing_brake

        # ----------------------------------------------------
        # 3. CHASSIS TURNING PHYSICS
        # ----------------------------------------------------
        if abs(self.speed) > 0.1:
            speed_ratio = min(1.0, abs(self.speed) / PLAYER_MAX_SPEED)
            # Agility factor: 0.88 at slow speeds -> 1.0 at cruise speed.
            # Guarantees sharp, responsive cornering at intersections without sluggish understeer
            agility = 0.88 + 0.12 * speed_ratio
            turn_direction = 1.0 if self.speed >= 0 else -1.0
            turn_rate = (self.steer_angle / STEERING_MAX_ANGLE) * PLAYER_TURN_SPEED * turn_direction * agility
            self.angle = (self.angle + turn_rate * dt) % 360.0

    def update(self, dt, controllers, ai_vehicles):
        """Update physics, collisions, signal obedience, and GPS navigation."""
        # 1. Update Position
        rad = math.radians(self.angle)
        self.x += math.cos(rad) * self.speed * dt
        self.y += math.sin(rad) * self.speed * dt

        # 2. Road Bounds Soft Cushioning (Keep inside simulation grid)
        min_bound = 30
        max_bound_x = self.grid.intersections.get((0, 3)).x + 130 if hasattr(self.grid, 'intersections') else 900
        max_bound_y = self.grid.intersections.get((3, 0)).y + 130 if hasattr(self.grid, 'intersections') else 900
        self.x = max(min_bound, min(max_bound_x, self.x))
        self.y = max(min_bound, min(max_bound_y, self.y))

        # 3. Collision Cooldown
        if self.collision_cooldown > 0:
            self.collision_cooldown -= dt

        # 4. Check Collisions with AI Vehicles
        self._check_ai_collisions(ai_vehicles)

        # 5. Check Traffic Light Obedience & Ambient Reflections
        self._check_traffic_lights(controllers)

        # 6. Periodic Live A* GPS Recalculation
        self.gps_reroute_timer += dt
        if self.gps_reroute_timer >= 1.2:
            self.gps_reroute_timer = 0.0
            self.recalculate_gps_path()

        # Update notification timers
        if self.violation_msg_timer > 0:
            self.violation_msg_timer -= dt
        if self.gps_notif_timer > 0:
            self.gps_notif_timer -= dt



        # Turn indicator blinker timer
        self.blink_timer += dt
        if self.blink_timer >= 0.35:
            self.blink_timer = 0.0
            self.blink_on = not self.blink_on

        # Spawn exhaust trail particles when moving
        if abs(self.speed) > 15.0:
            self.trail_timer += dt
            if self.trail_timer >= 0.05:
                self.trail_timer = 0.0
                rear_x = self.x - math.cos(rad) * (self.length / 2)
                rear_y = self.y - math.sin(rad) * (self.length / 2)
                self.trail_particles.append([rear_x, rear_y, 0.4])

        # Decay trail particles
        for p in self.trail_particles[:]:
            p[2] -= dt
            if p[2] <= 0:
                self.trail_particles.remove(p)

    def _check_ai_collisions(self, ai_vehicles):
        if self.collision_cooldown > 0:
            return

        for ai in ai_vehicles:
            dist = math.hypot(self.x - ai.x, self.y - ai.y)
            if dist < 20.0:
                self.collisions_count += 1
                self.collision_cooldown = PLAYER_COLLISION_COOLDOWN
                self.score = max(0, self.score - MAX_COLLISION_PENALTY)
                self.speed = -self.speed * 0.4
                
                # Collision penalty
                self.last_violation_msg = f"COLLISION! -{MAX_COLLISION_PENALTY} PTS"
                self.violation_msg_timer = 2.0
                if self.sound_manager:
                    self.sound_manager.play('crash')
                break

    def _check_traffic_lights(self, controllers):
        in_junction = False
        self.chassis_ambient_color = None
        
        for (r, c), node in self.grid.intersections.items():
            dist = math.hypot(node.x - self.x, node.y - self.y)
            if dist < ROAD_WIDTH // 2 + 35:
                ctrl = controllers.get(node.id)
                if ctrl:
                    rad = math.radians(self.angle % 360)
                    dx = math.cos(rad)
                    dy = math.sin(rad)
                    direction = 'EW' if abs(dx) > abs(dy) else 'NS'
                    
                    # Ambient light reflection on car roof
                    if ctrl.is_red(direction):
                        self.chassis_ambient_color = RED_LIGHT
                    elif ctrl.is_green(direction):
                        self.chassis_ambient_color = GREEN_LIGHT
                    elif ctrl.is_yellow(direction):
                        self.chassis_ambient_color = YELLOW_LIGHT

            if dist < ROAD_WIDTH // 2 + 6:
                in_junction = True
                if node.id not in self.violated_intersections:
                    ctrl = controllers.get(node.id)
                    if ctrl:
                        rad = math.radians(self.angle % 360)
                        dx = math.cos(rad)
                        dy = math.sin(rad)
                        direction = 'EW' if abs(dx) > abs(dy) else 'NS'
                        
                        if ctrl.is_red(direction):
                            self.violations_count += 1
                            self.score = max(0, self.score - RED_LIGHT_PENALTY)
                            self.violated_intersections.add(node.id)
                            self.last_violation_msg = f"RED LIGHT VIOLATION! -{RED_LIGHT_PENALTY} PTS"
                            self.violation_msg_timer = 2.0
                            if self.sound_manager:
                                self.sound_manager.play('violation')
                        elif ctrl.is_green(direction) and abs(self.speed) > 10.0:
                            # Clean Green Passage Reward!
                            self.score += 25
                            self.last_violation_msg = "CLEAN SIGNAL PASSAGE! +25 PTS"
                            self.violation_msg_timer = 1.0
            else:
                if node.id in self.violated_intersections:
                    self.violated_intersections.remove(node.id)

    def draw(self, surface, camera_offset=(0, 0)):
        """Draw Vehicle Masters stylized player car with dynamic steerable wheels and lighting."""
        ox, oy = camera_offset
        draw_x = self.x - ox
        draw_y = self.y - oy

        # 1. Trail particles
        for p in self.trail_particles:
            alpha = int(180 * (p[2] / 0.4))
            p_surf = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(p_surf, (250, 204, 21, alpha), (3, 3), 2)
            surface.blit(p_surf, (p[0] - ox - 3, p[1] - oy - 3))

        rad = math.radians(self.angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        
        hw = self.width / 2.0
        hl = self.length / 2.0

        # 2. Dynamic Drop Shadow
        shadow_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        s_corners = [(-hl - 2, -hw - 2), (hl + 2, -hw - 2), (hl + 2, hw + 2), (-hl - 2, hw + 2)]
        s_poly = []
        for cx, cy in s_corners:
            rx = draw_x + (cx * cos_a - cy * sin_a) + 3
            ry = draw_y + (cx * sin_a + cy * cos_a) + 4
            s_poly.append((rx, ry))
        pygame.draw.polygon(shadow_surf, (20, 35, 15, 90), s_poly)
        surface.blit(shadow_surf, (0, 0))

        # 3. Soft Photorealistic Headlight Beams forward
        cone_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        f_center_x = draw_x + math.cos(rad) * hl
        f_center_y = draw_y + math.sin(rad) * hl
        cone_dist = 60.0
        cone_spread = 22.0
        left_beam = (
            f_center_x + math.cos(rad) * cone_dist - math.sin(rad) * cone_spread,
            f_center_y + math.sin(rad) * cone_dist + math.cos(rad) * cone_spread
        )
        right_beam = (
            f_center_x + math.cos(rad) * cone_dist + math.sin(rad) * cone_spread,
            f_center_y + math.sin(rad) * cone_dist - math.cos(rad) * cone_spread
        )
        # Outer soft cone
        pygame.draw.polygon(cone_surf, (254, 240, 138, 35), [(f_center_x, f_center_y), left_beam, right_beam])
        # Inner focused beam
        inner_dist = 36.0
        inner_spread = 11.0
        i_left = (
            f_center_x + math.cos(rad) * inner_dist - math.sin(rad) * inner_spread,
            f_center_y + math.sin(rad) * inner_dist + math.cos(rad) * inner_spread
        )
        i_right = (
            f_center_x + math.cos(rad) * inner_dist + math.sin(rad) * inner_spread,
            f_center_y + math.sin(rad) * inner_dist - math.cos(rad) * inner_spread
        )
        pygame.draw.polygon(cone_surf, (254, 240, 138, 65), [(f_center_x, f_center_y), i_left, i_right])
        surface.blit(cone_surf, (0, 0))

        # 4. Realistic Turning Wheels (Vehicle Masters Front Steering)
        wheel_l = 6.0
        wheel_w = 3.0
        wheel_positions = [
            # Front Left (Steerable)
            (hl * 0.65, -hw * 0.95, True),
            # Front Right (Steerable)
            (hl * 0.65, hw * 0.95, True),
            # Rear Left (Fixed)
            (-hl * 0.65, -hw * 0.95, False),
            # Rear Right (Fixed)
            (-hl * 0.65, hw * 0.95, False),
        ]

        for w_rel_x, w_rel_y, is_front in wheel_positions:
            w_world_x = draw_x + (w_rel_x * cos_a - w_rel_y * sin_a)
            w_world_y = draw_y + (w_rel_x * sin_a + w_rel_y * cos_a)
            
            # Pivot front wheels by steer_angle!
            w_angle_rad = rad + (math.radians(self.steer_angle) if is_front else 0.0)
            w_cos = math.cos(w_angle_rad)
            w_sin = math.sin(w_angle_rad)
            
            w_pts = [
                (w_world_x + (-wheel_l * w_cos - (-wheel_w) * w_sin), w_world_y + (-wheel_l * w_sin + (-wheel_w) * w_cos)),
                (w_world_x + (wheel_l * w_cos - (-wheel_w) * w_sin), w_world_y + (wheel_l * w_sin + (-wheel_w) * w_cos)),
                (w_world_x + (wheel_l * w_cos - wheel_w * w_sin), w_world_y + (wheel_l * w_sin + wheel_w * w_cos)),
                (w_world_x + (-wheel_l * w_cos - wheel_w * w_sin), w_world_y + (-wheel_l * w_sin + wheel_w * w_cos)),
            ]
            # Dark rubber tire
            pygame.draw.polygon(surface, (20, 24, 33), w_pts)
            # Metallic wheel rim
            rim_x = w_world_x
            rim_y = w_world_y
            pygame.draw.circle(surface, (148, 163, 184), (int(rim_x), int(rim_y)), 1)

        # 5. Chassis Body (Stylized aerodynamic curves)
        corners = [
            (-hl, -hw * 0.85),
            (-hl * 0.8, -hw),
            (hl * 0.7, -hw),
            (hl, -hw * 0.7),
            (hl, hw * 0.7),
            (hl * 0.7, hw),
            (-hl * 0.8, hw),
            (-hl, hw * 0.85)
        ]
        
        poly_points = []
        for cx, cy in corners:
            rx = draw_x + (cx * cos_a - cy * sin_a)
            ry = draw_y + (cx * sin_a + cy * cos_a)
            poly_points.append((rx, ry))

        # Main Chassis Color
        pygame.draw.polygon(surface, PLAYER_COLOR, poly_points)
        pygame.draw.polygon(surface, (255, 255, 255), poly_points, 1)

        # 6. Wing Mirrors
        mirror_offsets = [(hl * 0.25, -hw - 2.5), (hl * 0.25, hw + 2.5)]
        for mx_off, my_off in mirror_offsets:
            m_rx = draw_x + (mx_off * cos_a - my_off * sin_a)
            m_ry = draw_y + (mx_off * sin_a + my_off * cos_a)
            pygame.draw.circle(surface, PLAYER_COLOR, (int(m_rx), int(m_ry)), 2)
            pygame.draw.circle(surface, (255, 255, 255), (int(m_rx), int(m_ry)), 1)

        # 7. Interior Cabin & Seated Driver Avatar (Visible through clear glass)
        # Cabin floor
        roof_corners = [
            (-hl * 0.45, -hw * 0.75),
            (hl * 0.25, -hw * 0.75),
            (hl * 0.45, -hw * 0.6),
            (hl * 0.45, hw * 0.6),
            (hl * 0.25, hw * 0.75),
            (-hl * 0.45, hw * 0.75)
        ]
        roof_points = []
        for cx, cy in roof_corners:
            rx = draw_x + (cx * cos_a - cy * sin_a)
            ry = draw_y + (cx * sin_a + cy * cos_a)
            roof_points.append((rx, ry))
        
        # Dark leather cabin floor
        pygame.draw.polygon(surface, (18, 22, 33), roof_points)

        # Driver Seat (Left side) & Passenger Seat (Right side)
        seat_cos = math.cos(rad)
        seat_sin = math.sin(rad)
        # Left Seat (Driver)
        ds_x = draw_x + (-hl * 0.1 * seat_cos - (-hw * 0.38) * seat_sin)
        ds_y = draw_y + (-hl * 0.1 * seat_sin + (-hw * 0.38) * seat_cos)
        pygame.draw.circle(surface, (35, 42, 58), (int(ds_x), int(ds_y)), 4)
        
        # Driver Avatar: Torso in Driver Seat
        pygame.draw.circle(surface, (30, 58, 138), (int(ds_x), int(ds_y)), 3)
        # Driver Head & Red Racing Helmet/Cap
        dh_x = draw_x + (hl * 0.05 * seat_cos - (-hw * 0.38) * seat_sin)
        dh_y = draw_y + (hl * 0.05 * seat_sin + (-hw * 0.38) * seat_cos)
        pygame.draw.circle(surface, (239, 68, 68), (int(dh_x), int(dh_y)), 3)
        pygame.draw.circle(surface, (254, 240, 138), (int(dh_x + seat_cos * 1.5), int(dh_y + seat_sin * 1.5)), 1)
        
        # Driver Hands & Mini Steering Wheel inside cabin
        sw_cx = draw_x + (hl * 0.25 * seat_cos - (-hw * 0.38) * seat_sin)
        sw_cy = draw_y + (hl * 0.25 * seat_sin + (-hw * 0.38) * seat_cos)
        sw_rad = rad + math.radians(self.steer_angle * 0.7)
        pygame.draw.circle(surface, (15, 23, 42), (int(sw_cx), int(sw_cy)), 3, 1)
        # Driver hands on steering wheel
        h1_x = sw_cx - math.sin(sw_rad) * 2.5
        h1_y = sw_cy + math.cos(sw_rad) * 2.5
        h2_x = sw_cx + math.sin(sw_rad) * 2.5
        h2_y = sw_cy - math.cos(sw_rad) * 2.5
        pygame.draw.circle(surface, (251, 191, 36), (int(h1_x), int(h1_y)), 1)
        pygame.draw.circle(surface, (251, 191, 36), (int(h2_x), int(h2_y)), 1)

        # Passenger Seat (Right side)
        ps_x = draw_x + (-hl * 0.1 * seat_cos - (hw * 0.38) * seat_sin)
        ps_y = draw_y + (-hl * 0.1 * seat_sin + (hw * 0.38) * seat_cos)
        pygame.draw.circle(surface, (35, 42, 58), (int(ps_x), int(ps_y)), 4)

        # Clear Tinted Windshield Glass over cabin with reflection
        glass_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(glass_surf, (56, 189, 248, 55), roof_points)
        surface.blit(glass_surf, (0, 0))
        pygame.draw.polygon(surface, (148, 163, 184), roof_points, 1)
        
        # Windshield specular glare stripe
        glare_corners = [
            (hl * 0.1, -hw * 0.65),
            (hl * 0.38, -hw * 0.5),
            (hl * 0.38, -hw * 0.2),
            (hl * 0.1, -hw * 0.35)
        ]
        gl_pts = []
        for cx, cy in glare_corners:
            rx = draw_x + (cx * cos_a - cy * sin_a)
            ry = draw_y + (cx * sin_a + cy * cos_a)
            gl_pts.append((rx, ry))
        glare_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(glare_surf, (255, 255, 255, 95), gl_pts)
        surface.blit(glare_surf, (0, 0))

        # 8. Ambient Traffic Light Reflection on Roof
        if self.chassis_ambient_color:
            refl_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            pygame.draw.polygon(refl_surf, (*self.chassis_ambient_color, 95), roof_points)
            surface.blit(refl_surf, (0, 0))

        # 9. Headlight Bulbs (Front corners)
        f_left = poly_points[3]
        f_right = poly_points[4]
        pygame.draw.circle(surface, (254, 240, 138), (int(f_left[0]), int(f_left[1])), 2)
        pygame.draw.circle(surface, (254, 240, 138), (int(f_right[0]), int(f_right[1])), 2)

        # 10. Taillights & Intense Brake Flares
        r_left = poly_points[0]
        r_right = poly_points[7]
        is_braking = self.brake_pressed or self.speed < 2.0 or self.gear == "P"
        brake_col = (255, 45, 45) if is_braking else (195, 25, 25)
        pygame.draw.circle(surface, brake_col, (int(r_left[0]), int(r_left[1])), 2)
        pygame.draw.circle(surface, brake_col, (int(r_right[0]), int(r_right[1])), 2)
        
        if is_braking:
            flare_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            pygame.draw.circle(flare_surf, (239, 68, 68, 100), (int(r_left[0]), int(r_left[1])), 6)
            pygame.draw.circle(flare_surf, (239, 68, 68, 100), (int(r_right[0]), int(r_right[1])), 6)
            surface.blit(flare_surf, (0, 0))

        # 11. Flashing Amber Turn Indicator Blinkers
        show_left = (self.turn_signal in ("LEFT", "HAZARD") or self.steer_angle < -22.0) and self.blink_on
        show_right = (self.turn_signal in ("RIGHT", "HAZARD") or self.steer_angle > 22.0) and self.blink_on
        
        amber_col = (245, 158, 11)
        if show_left:
            # Front left & rear left
            pygame.draw.circle(surface, amber_col, (int(poly_points[2][0]), int(poly_points[2][1])), 2)
            pygame.draw.circle(surface, amber_col, (int(r_left[0]), int(r_left[1])), 2)
        if show_right:
            # Front right & rear right
            pygame.draw.circle(surface, amber_col, (int(poly_points[5][0]), int(poly_points[5][1])), 2)
            pygame.draw.circle(surface, amber_col, (int(r_right[0]), int(r_right[1])), 2)

    def draw_gps_overlay(self, surface, camera_offset=(0, 0)):
        """Render Live Dynamic A* GPS path with glowing gold/cyan navigation route."""
        if not self.gps_path:
            return

        ox, oy = camera_offset
        points = [(self.x - ox, self.y - oy)]
        for node in self.gps_path:
            points.append((node.x - ox, node.y - oy))

        if len(points) >= 2:
            gps_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            # Outer cyan glow
            pygame.draw.lines(gps_surf, (6, 182, 212, 130), False, points, 6)
            # Inner bright gold core
            pygame.draw.lines(gps_surf, (250, 204, 21, 240), False, points, 2)

            # Pulsing waypoints along GPS route
            t = pygame.time.get_ticks() / 280.0
            for i, (wx, wy) in enumerate(points[1:]):
                radius = 4 + int(2 * math.sin(t + i))
                pygame.draw.circle(gps_surf, (250, 204, 21, 240), (int(wx), int(wy)), radius)
                pygame.draw.circle(gps_surf, (6, 182, 212, 170), (int(wx), int(wy)), radius + 3, 1)

            surface.blit(gps_surf, (0, 0))

    def draw_hud_notifications(self, surface, font, camera_offset=(0, 0), is_cockpit=False):
        """Draw heads-up display notifications for violations & reroutes."""
        ox, oy = camera_offset
        if self.violation_msg_timer > 0:
            is_good = "PERFECT" in self.last_violation_msg or "BONUS" in self.last_violation_msg or "+" in self.last_violation_msg
            col = (34, 197, 94) if is_good else (239, 68, 68)
            alert_surf = font.render(self.last_violation_msg, True, col)
            if is_cockpit:
                screen_x = WINDOW_WIDTH // 2
                screen_y = 130
            else:
                screen_x = self.x - ox
                screen_y = self.y - oy - 36
            alert_rect = alert_surf.get_rect(center=(screen_x, screen_y))
            bg_rect = alert_rect.inflate(18, 10)
            
            box_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(box_surf, (15, 23, 42, 230), box_surf.get_rect(), border_radius=8)
            pygame.draw.rect(box_surf, (*col, 220), box_surf.get_rect(), width=2, border_radius=8)
            surface.blit(box_surf, bg_rect.topleft)
            surface.blit(alert_surf, alert_rect)

        if self.gps_notif_timer > 0:
            notif_surf = font.render(self.gps_reroute_notif, True, (6, 182, 212))
            center_y = 85 if is_cockpit else 75
            notif_rect = notif_surf.get_rect(center=(WINDOW_WIDTH // 2, center_y))
            bg_rect = notif_rect.inflate(24, 12)
            
            box_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(box_surf, (15, 23, 42, 240), box_surf.get_rect(), border_radius=8)
            pygame.draw.rect(box_surf, (6, 182, 212, 200), box_surf.get_rect(), width=1, border_radius=8)
            surface.blit(box_surf, bg_rect.topleft)
            surface.blit(notif_surf, notif_rect)

