"""
Vehicle Agent and Dynamic A* Rerouting Engine for GridLock AI.
Simulates car-following physics, intersection stop lines, wait-time tracking,
dynamic path rerouting, and emergency vehicles.
"""

import math
import random
import pygame
from config import (
    CAR_COLOR, CAR_ACCENT, EMERGENCY_COLOR, EMERGENCY_ACCENT,
    BASE_SPEED_LIMIT, EMERGENCY_SPEED_LIMIT,
    VEHICLE_LENGTH, VEHICLE_WIDTH, SAFE_DISTANCE,
    ROAD_WIDTH, PATH_OVERLAY
)

class Vehicle:
    """Base vehicle agent operating on the grid road network."""
    def __init__(self, vehicle_id, path, grid, sound_manager=None, is_emergency=False):
        self.id = vehicle_id
        self.path = list(path)
        self.grid = grid
        self.sound_manager = sound_manager
        self.is_emergency = is_emergency
        
        self.max_speed = EMERGENCY_SPEED_LIMIT if is_emergency else BASE_SPEED_LIMIT
        self.speed = self.max_speed * 0.6
        self.acceleration = 130.0
        self.deceleration = 220.0
        
        # Vehicle Masters Stylized Color Palette
        if not is_emergency:
            colors = [
                ((239, 68, 68), (254, 202, 202)),   # Vibrant Red
                ((59, 130, 246), (191, 219, 254)),  # Electric Blue
                ((16, 185, 129), (167, 243, 208)),  # Mint Green
                ((245, 158, 11), (254, 240, 138)),  # Amber Gold
                ((168, 85, 247), (233, 213, 255)),  # Violet
                ((241, 245, 249), (148, 163, 184)), # White
            ]
            self.body_color, self.accent_color = random.choice(colors)
        else:
            self.body_color = EMERGENCY_COLOR
            self.accent_color = EMERGENCY_ACCENT


        self.path_idx = 0
        self.current_edge = None
        self.dist_along_edge = 0.0
        
        self.x = self.path[0].x
        self.y = self.path[0].y
        self.angle = 0.0
        
        # Performance & Stats
        self.wait_time = 0.0          # Seconds spent stopped (< 1.5 px/s)
        self.travel_time = 0.0        # Total journey time
        self.completed = False
        self.reroute_cooldown = random.uniform(1.5, 3.5)
        self.reroute_count = 0
        
        # Setup on first edge
        self._init_first_edge()

    def _init_first_edge(self):
        if len(self.path) >= 2:
            self.current_edge = self.grid.get_edge(self.path[0], self.path[1])
            if self.current_edge:
                self.current_edge.vehicles.append(self)
                self.x, self.y = self.current_edge.start_pos
                self.angle = self.current_edge.angle_deg
                self.dist_along_edge = 0.0
            else:
                self.completed = True
        else:
            self.completed = True

    @property
    def next_node(self):
        if self.current_edge:
            return self.current_edge.to_node
        return None

    def get_lead_vehicle(self):
        """Find the vehicle directly ahead of this one on the current edge."""
        if not self.current_edge:
            return None, 9999.0
            
        lead = None
        min_dist = 9999.0
        
        for v in self.current_edge.vehicles:
            if v == self:
                continue
            dist_diff = v.dist_along_edge - self.dist_along_edge
            if 0 < dist_diff < min_dist:
                min_dist = dist_diff
                lead = v
                
        return lead, min_dist

    def should_stop_for_traffic_light(self, controllers):
        """Check if traffic light at the end of this edge requires stopping."""
        if not self.current_edge:
            return False, 9999.0
            
        target_node = self.current_edge.to_node
        if target_node.is_perimeter or target_node.grid_pos is None:
            return False, 9999.0  # Perimeter exits don't have traffic lights
            
        ctrl = controllers.get(target_node.id)
        if not ctrl:
            return False, 9999.0
            
        # Determine approach direction (EW or NS)
        dx = self.current_edge.to_node.x - self.current_edge.from_node.x
        dy = self.current_edge.to_node.y - self.current_edge.from_node.y
        direction = 'EW' if abs(dx) > abs(dy) else 'NS'
        
        # Stop line is located slightly before intersection junction box
        dist_to_stop_line = self.current_edge.length - (ROAD_WIDTH // 2 + 10) - self.dist_along_edge
        
        # If signal is red, or yellow and too far to cross safely
        is_red = ctrl.is_red(direction)
        is_yellow = ctrl.is_yellow(direction)
        
        if is_red or (is_yellow and dist_to_stop_line > 25):
            return True, max(0.0, dist_to_stop_line)
            
        return False, dist_to_stop_line

    def try_dynamic_reroute(self, k_penalty):
        """
        AI Dynamic A* Path Recalculation:
        If stuck in traffic or approaching a congested corridor,
        reevaluate optimal path from next node to destination.
        """
        if self.completed or not self.current_edge:
            return
            
        # Must have at least 2 nodes remaining to destination
        rem_nodes = len(self.path) - (self.path_idx + 1)
        if rem_nodes < 2:
            return
            
        next_n = self.path[self.path_idx + 1]
        dest_n = self.path[-1]
        
        # Calculate new dynamic A* path from next node to destination
        new_subpath = self.grid.a_star(next_n, dest_n, k_penalty=k_penalty, is_emergency=self.is_emergency)
        
        if new_subpath and len(new_subpath) >= 2:
            current_subpath = self.path[self.path_idx + 1:]
            
            # If the new route avoids a bottleneck, adopt it!
            if new_subpath != current_subpath:
                self.path = self.path[:self.path_idx + 1] + new_subpath[1:]
                self.reroute_count += 1

    def update(self, dt, controllers, k_penalty):
        if self.completed:
            return
            
        self.travel_time += dt
        if self.speed < 2.0:
            self.wait_time += dt
            
        # Dynamic reroute evaluation
        self.reroute_cooldown -= dt
        if self.reroute_cooldown <= 0:
            self.reroute_cooldown = 2.0 if self.is_emergency else 3.5
            # Evaluate reroute when waiting or approaching intersection
            if self.speed < 15.0 or (self.current_edge and self.current_edge.queue_density >= 2):
                self.try_dynamic_reroute(k_penalty)

        # 1. Evaluate distance to vehicle ahead
        lead_car, dist_to_lead = self.get_lead_vehicle()
        
        # 2. Evaluate distance to traffic light stop line
        must_stop_light, dist_to_stop = self.should_stop_for_traffic_light(controllers)
        
        # Target speed computation (Car following + Signal obedience)
        desired_speed = self.max_speed
        
        # Handle lead vehicle braking
        effective_safe = SAFE_DISTANCE + (VEHICLE_LENGTH if not self.is_emergency else VEHICLE_LENGTH + 2)
        if lead_car:
            if dist_to_lead < effective_safe:
                desired_speed = 0.0
            elif dist_to_lead < effective_safe * 2.2:
                desired_speed = min(desired_speed, lead_car.speed * 0.8)
                
        # Handle traffic light stop
        if must_stop_light:
            if dist_to_stop < 6.0:
                desired_speed = 0.0
            elif dist_to_stop < 55.0:
                slow_factor = dist_to_stop / 55.0
                desired_speed = min(desired_speed, self.max_speed * slow_factor)

        # Physics acceleration / braking
        if self.speed < desired_speed:
            self.speed = min(desired_speed, self.speed + self.acceleration * dt)
        else:
            self.speed = max(desired_speed, self.speed - self.deceleration * dt)
            
        # Advance along edge
        self.dist_along_edge += self.speed * dt
        
        # Check transition to next edge
        if self.current_edge and self.dist_along_edge >= self.current_edge.length:
            self._transition_to_next_edge()
            
        # Update (x, y) coordinates along edge line
        if self.current_edge and not self.completed:
            frac = min(1.0, max(0.0, self.dist_along_edge / max(1.0, self.current_edge.length)))
            s_x, s_y = self.current_edge.start_pos
            e_x, e_y = self.current_edge.end_pos
            self.x = s_x + (e_x - s_x) * frac
            self.y = s_y + (e_y - s_y) * frac
            self.angle = self.current_edge.angle_deg

    def _transition_to_next_edge(self):
        """Move vehicle onto the subsequent road segment in its path."""
        if self.current_edge and self in self.current_edge.vehicles:
            self.current_edge.vehicles.remove(self)
            
        self.path_idx += 1
        
        # If reached end of path
        if self.path_idx >= len(self.path) - 1:
            self.completed = True
            if self.sound_manager:
                self.sound_manager.play('car_clear')
            return
            
        # Transition to next road edge
        from_n = self.path[self.path_idx]
        to_n = self.path[self.path_idx + 1]
        next_edge = self.grid.get_edge(from_n, to_n)
        
        if next_edge:
            self.current_edge = next_edge
            self.current_edge.vehicles.append(self)
            # Carry over surplus distance for seamless continuous motion
            self.dist_along_edge = max(0.0, self.dist_along_edge - (self.current_edge.length if False else self.dist_along_edge))
            self.dist_along_edge = 0.0
            self.angle = next_edge.angle_deg
        else:
            self.completed = True

    def draw(self, surface, is_selected=False, camera_offset=(0, 0)):
        """Draw Vehicle Masters stylized car sprite with drop shadow, wheels, and headlights."""
        ox, oy = camera_offset
        draw_x = self.x - ox
        draw_y = self.y - oy

        rad = math.radians(self.angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        
        # Dimensions
        hw = VEHICLE_WIDTH / 2.0
        hl = VEHICLE_LENGTH / 2.0
        
        # 1. Soft Dynamic Drop Shadow
        shadow_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        s_corners = [(-hl - 1, -hw - 1), (hl + 1, -hw - 1), (hl + 1, hw + 1), (-hl - 1, hw + 1)]
        s_poly = []
        for cx, cy in s_corners:
            rx = draw_x + (cx * cos_a - cy * sin_a) + 2
            ry = draw_y + (cx * sin_a + cy * cos_a) + 3
            s_poly.append((rx, ry))
        pygame.draw.polygon(shadow_surf, (20, 35, 15, 80), s_poly)
        surface.blit(shadow_surf, (0, 0))

        # 2. 4 Rubber Tires
        wheel_l, wheel_w = 5.0, 2.5
        wheel_offsets = [(hl * 0.6, -hw * 0.95), (hl * 0.6, hw * 0.95), (-hl * 0.6, -hw * 0.95), (-hl * 0.6, hw * 0.95)]
        for w_rx, w_ry in wheel_offsets:
            wx = draw_x + (w_rx * cos_a - w_ry * sin_a)
            wy = draw_y + (w_rx * sin_a + w_ry * cos_a)
            w_pts = [
                (wx + (-wheel_l * cos_a - (-wheel_w) * sin_a), wy + (-wheel_l * sin_a + (-wheel_w) * cos_a)),
                (wx + (wheel_l * cos_a - (-wheel_w) * sin_a), wy + (wheel_l * sin_a + (-wheel_w) * cos_a)),
                (wx + (wheel_l * cos_a - wheel_w * sin_a), wy + (wheel_l * sin_a + wheel_w * cos_a)),
                (wx + (-wheel_l * cos_a - wheel_w * sin_a), wy + (-wheel_l * sin_a + wheel_w * cos_a)),
            ]
            pygame.draw.polygon(surface, (20, 24, 33), w_pts)

        # 3. Chassis Corners
        corners = [
            (-hl, -hw),
            (hl, -hw),
            (hl, hw),
            (-hl, hw)
        ]
        poly_points = []
        for cx, cy in corners:
            rx = draw_x + (cx * cos_a - cy * sin_a)
            ry = draw_y + (cx * sin_a + cy * cos_a)
            poly_points.append((rx, ry))
            
        # Draw chassis
        if getattr(self, 'is_police', False):
            # GTA Police Interceptor Black & White Livery
            pygame.draw.polygon(surface, POLICE_BODY, poly_points)
            d_corners = [(-hl * 0.35, -hw), (hl * 0.35, -hw), (hl * 0.35, hw), (-hl * 0.35, hw)]
            d_pts = []
            for cx, cy in d_corners:
                d_pts.append((draw_x + (cx * cos_a - cy * sin_a), draw_y + (cx * sin_a + cy * cos_a)))
            pygame.draw.polygon(surface, POLICE_DOOR, d_pts)
            pygame.draw.polygon(surface, (255, 255, 255), poly_points, 1)
        elif getattr(self, 'vehicle_type', '') == "taxi":
            # Downtown Yellow Taxi Cab
            pygame.draw.polygon(surface, TAXI_YELLOW, poly_points)
            pygame.draw.polygon(surface, (255, 255, 255), poly_points, 1)
            # Checker stripe down sides
            c_p1 = (draw_x + (-hl * 0.5 * cos_a), draw_y + (-hl * 0.5 * sin_a))
            c_p2 = (draw_x + (hl * 0.5 * cos_a), draw_y + (hl * 0.5 * sin_a))
            pygame.draw.line(surface, TAXI_CHECKER, c_p1, c_p2, 2)
        else:
            chassis_color = getattr(self, 'body_color', CAR_COLOR)
            border_color = getattr(self, 'accent_color', CAR_ACCENT)
            pygame.draw.polygon(surface, chassis_color, poly_points)
            pygame.draw.polygon(surface, border_color, poly_points, 1)
        
        # Windshield / Roof
        roof_corners = [
            (-hl * 0.45, -hw * 0.65),
            (hl * 0.25, -hw * 0.65),
            (hl * 0.4, -hw * 0.5),
            (hl * 0.4, hw * 0.5),
            (hl * 0.25, hw * 0.65),
            (-hl * 0.45, hw * 0.65)
        ]
        roof_pts = []
        for cx, cy in roof_corners:
            rx = draw_x + (cx * cos_a - cy * sin_a)
            ry = draw_y + (cx * sin_a + cy * cos_a)
            roof_pts.append((rx, ry))
        pygame.draw.polygon(surface, (24, 28, 42), roof_pts)
        
        # Rooftop accessories: Ambulance Siren
        if self.is_emergency:
            siren_toggle = (pygame.time.get_ticks() // 150) % 2 == 0
            siren_col = (59, 130, 246) if siren_toggle else (239, 68, 68)
            pygame.draw.circle(surface, siren_col, (int(draw_x), int(draw_y)), 4)
            halo_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            pygame.draw.circle(halo_surf, (*siren_col, 80), (int(draw_x), int(draw_y)), 12)
            surface.blit(halo_surf, (0, 0))

        # Headlights (front corners)
        f_left = poly_points[1]
        f_right = poly_points[2]
        pygame.draw.circle(surface, (254, 240, 138), (int(f_left[0]), int(f_left[1])), 2)
        pygame.draw.circle(surface, (254, 240, 138), (int(f_right[0]), int(f_right[1])), 2)
        
        # Taillights (rear corners)
        r_left = poly_points[0]
        r_right = poly_points[3]
        brake_color = (239, 68, 68) if self.speed < 5.0 else (185, 28, 28)
        pygame.draw.circle(surface, brake_color, (int(r_left[0]), int(r_left[1])), 2)
        pygame.draw.circle(surface, brake_color, (int(r_right[0]), int(r_right[1])), 2)

    def draw_path_overlay(self, surface, camera_offset=(0, 0)):
        """Render planned route as a glowing cyan path with waypoint nodes."""
        if not self.path or self.path_idx >= len(self.path):
            return
            
        ox, oy = camera_offset
        points = [(self.x - ox, self.y - oy)]
        for i in range(self.path_idx + 1, len(self.path)):
            points.append((self.path[i].x - ox, self.path[i].y - oy))
            
        if len(points) >= 2:
            path_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            color = (236, 72, 153, 140) if self.is_emergency else (6, 182, 212, 110)
            pygame.draw.lines(path_surf, color, False, points, 3)
            
            # Destination marker
            dest_x, dest_y = points[-1]
            pygame.draw.circle(path_surf, color, (int(dest_x), int(dest_y)), 7, 2)
            surface.blit(path_surf, (0, 0))


class EmergencyAmbulance(Vehicle):
    """Priority emergency vehicle with mission timer and siren sounds."""
    def __init__(self, vehicle_id, path, grid, sound_manager=None, mission_time_limit=45.0):
        super().__init__(vehicle_id, path, grid, sound_manager, is_emergency=True)
        self.mission_time_limit = mission_time_limit
        self.time_remaining = mission_time_limit
        self.siren_timer = 0.0

    def update(self, dt, controllers, k_penalty):
        super().update(dt, controllers, k_penalty)
        self.time_remaining -= dt
        
        # Periodic siren chirp
        self.siren_timer += dt
        if self.siren_timer >= 2.5:
            self.siren_timer = 0.0
            if self.sound_manager and not self.completed:
                self.sound_manager.play('siren')


