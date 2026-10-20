"""
GridLock AI: Driver Edition - Main Game Loop & Vehicle Masters Simulation Engine.
Combines Vehicle Masters mobile cockpit controls (interactive Steering Wheel, PRND Shifter,
Gas & Brake Pedals, Turn Indicators, Horn), dynamic Follow Camera, stylized 3D city architecture,
iconic Green Target Parking Bay, live dynamic A* GPS navigation, and slide-out Command Center telemetry.
"""

import sys
import math
import random
import argparse
import pygame

from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS,
    BG_COLOR, CARD_BG, CARD_BORDER, TEXT_PRIMARY, TEXT_SECONDARY,
    DEFAULT_K_PENALTY, CRITICAL_WAIT_LIMIT, AMBULANCE_TIME_LIMIT,
    DEFAULT_SPAWN_INTERVAL, EMERGENCY_COLOR, GREEN_LIGHT, RED_LIGHT,
    PLAYER_COLOR, MISSION_TIME_LIMIT, GRID_ROWS, GRID_COLS,
    GRID_OFFSET_X, GRID_OFFSET_Y, CELL_WIDTH, CELL_HEIGHT
)
from sound import SoundManager
from grid import CityGrid
from traffic_light import TrafficLightController
from vehicle import Vehicle, EmergencyAmbulance
from player import PlayerCar
from ui import CommandCenterHUD

class Particle:
    """Celebration or collision particle with camera offset support."""
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(30, 110)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = 1.0
        self.decay = random.uniform(1.2, 2.5)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= self.decay * dt

    def draw(self, surface, camera_offset=(0, 0)):
        if self.life > 0:
            ox, oy = camera_offset
            alpha = int(255 * max(0.0, self.life))
            size = max(1, int(4 * self.life))
            surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*self.color[:3], alpha), (size, size), size)
            surface.blit(surf, (self.x - ox - size, self.y - oy - size))


class Camera:
    """
    Dynamic Camera System for Vehicle Masters.
    Supports first-person driver cabin ("cockpit"), smooth lookahead chase ("follow"),
    and full metropolitan map ("overview").
    """
    def __init__(self, mode="cockpit"):
        self.mode = mode  # "cockpit", "follow", or "overview"
        self.x = 0.0
        self.y = 0.0

    def cycle_mode(self):
        modes = ["cockpit", "follow", "overview"]
        cur_idx = modes.index(self.mode) if self.mode in modes else 0
        self.mode = modes[(cur_idx + 1) % len(modes)]
        return self.mode

    def update(self, player, dt):
        if self.mode == "cockpit":
            # Direct centered tracking for cockpit windshield view
            self.x = player.x - WINDOW_WIDTH / 2
            self.y = player.y - WINDOW_HEIGHT / 2
        elif self.mode == "follow":
            rad = math.radians(player.angle)
            lookahead = min(65.0, abs(player.speed) * 0.45)
            desired_x = player.x + math.cos(rad) * lookahead - WINDOW_WIDTH / 2
            desired_y = player.y + math.sin(rad) * lookahead - WINDOW_HEIGHT / 2
            
            # City boundaries
            min_x = -40
            max_x = (GRID_OFFSET_X + (GRID_COLS - 1) * CELL_WIDTH + 140) - WINDOW_WIDTH + 40
            min_y = -40
            max_y = (GRID_OFFSET_Y + (GRID_ROWS - 1) * CELL_HEIGHT + 140) - WINDOW_HEIGHT + 40
            
            if max_x > min_x:
                desired_x = max(min_x, min(max_x, desired_x))
            else:
                desired_x = (min_x + max_x) / 2
                
            if max_y > min_y:
                desired_y = max(min_y, min(max_y, desired_y))
            else:
                desired_y = (min_y + max_y) / 2
                
            self.x += (desired_x - self.x) * min(1.0, 7.5 * dt)
            self.y += (desired_y - self.y) * min(1.0, 7.5 * dt)
        else:
            # City Overview
            city_center_x = GRID_OFFSET_X + 1.5 * CELL_WIDTH
            city_center_y = GRID_OFFSET_Y + 1.5 * CELL_HEIGHT
            target_x = city_center_x - WINDOW_WIDTH / 2
            target_y = city_center_y - WINDOW_HEIGHT / 2
            self.x += (target_x - self.x) * min(1.0, 8.0 * dt)
            self.y += (target_y - self.y) * min(1.0, 8.0 * dt)

    def get_offset(self):
        return (int(self.x), int(self.y))


class GameState:
    """Manages player state, mission goals, background AI traffic, and telemetry."""
    def __init__(self, grid, sound_manager):
        self.grid = grid
        self.sound_manager = sound_manager
        self.camera = Camera(mode="cockpit")
        
        # Traffic signal controllers for each intersection
        self.controllers = {}
        for (r, c), node in self.grid.intersections.items():
            self.controllers[node.id] = TrafficLightController(node, sound_manager)
            
        # Background AI Vehicles
        self.vehicles = []
        self.vehicle_id_counter = 0
        self.active_ambulance = None
        self.hospital_node = None
        
        # Player Car Instance
        start_node = self.grid.intersections.get((0, 0), list(self.grid.nodes.values())[0])
        self.player = PlayerCar(start_node.x, start_node.y, self.grid, self.sound_manager)
        
        # Mission Goals & Landmarks
        self.landmark_names = [
            "CITY HOSPITAL", "DOWNTOWN AIRPORT", "TECH DISTRICT",
            "METRO CENTRAL", "HARBOR PORT", "CIVIC CENTER"
        ]
        self.missions_completed = 0
        self.mission_time_remaining = MISSION_TIME_LIMIT
        self.assign_next_mission(initial=True)
        
        # Telemetry & Game Stats
        self.cars_cleared = 0
        self.ambulance_missions_passed = 0
        self.avg_wait_time = 0.0
        self.congestion_pct = 0.0
        self.fps = 60.0
        
        # Controls & Settings
        self.k_penalty = DEFAULT_K_PENALTY
        self.ai_signals_enabled = True
        self.show_paths = True
        self.show_heatmap = False
        self.speed_multiplier = 1.0
        self.paused = False
        self.game_over = False
        self.game_over_reason = ""
        
        # Spawning Timers
        self.car_spawn_timer = 0.0
        self.ambulance_spawn_timer = 20.0
        
        # Visual particles
        self.particles = []

    def assign_next_mission(self, initial=False):
        """Pick a new destination node across the grid for player GPS co-pilot."""
        candidates = [
            n for n in self.grid.nodes.values()
            if math.hypot(n.x - self.player.x, n.y - self.player.y) > 280
        ]
        if not candidates:
            candidates = list(self.grid.nodes.values())
            
        next_node = random.choice(candidates)
        next_name = random.choice(self.landmark_names)
        self.player.set_destination(next_node, next_name)
        self.mission_time_remaining = MISSION_TIME_LIMIT

    def spawn_car(self):
        """Spawn an AI commuter vehicle navigating with dynamic A*."""
        start_n, goal_n = self.grid.get_random_perimeter_pair()
        path = self.grid.a_star(start_n, goal_n, k_penalty=self.k_penalty)
        if path and len(path) >= 2:
            self.vehicle_id_counter += 1
            car = Vehicle(self.vehicle_id_counter, path, self.grid, self.sound_manager)
            self.vehicles.append(car)
            return car
        return None

    def spawn_ambulance(self):
        """Dispatch a priority emergency ambulance with sirens."""
        if self.active_ambulance and not self.active_ambulance.completed:
            return None
            
        start_n, goal_n = self.grid.get_random_perimeter_pair()
        self.hospital_node = goal_n
        
        path = self.grid.a_star(start_n, goal_n, k_penalty=self.k_penalty, is_emergency=True)
        if path and len(path) >= 2:
            self.vehicle_id_counter += 1
            amb = EmergencyAmbulance(
                self.vehicle_id_counter, path, self.grid,
                self.sound_manager, mission_time_limit=AMBULANCE_TIME_LIMIT
            )
            self.vehicles.append(amb)
            self.active_ambulance = amb
            if self.sound_manager:
                self.sound_manager.play('siren')
            return amb
        return None


    def update_metrics(self):
        """Calculate system-wide congestion percentage and driver stats."""
        self.congestion_pct = self.grid.get_congestion_percentage()
        if self.vehicles:
            total_wait = sum(v.wait_time for v in self.vehicles)
            self.avg_wait_time = total_wait / len(self.vehicles)
        else:
            self.avg_wait_time = 0.0

    def trigger_success_particles(self, x, y, color):
        for _ in range(25):
            self.particles.append(Particle(x, y, color))


def main():
    parser = argparse.ArgumentParser(description="GridLock AI: Vehicle Masters Edition")
    parser.add_argument("--test", action="store_true", help="Run 120 frames headless test and exit")
    args = parser.parse_args()

    pygame.init()
    pygame.display.set_caption("Vehicle Masters - Precision Driving & Dynamic A* Traffic Navigator")

    if args.test:
        import os
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        screen = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    else:
        screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

    clock = pygame.time.Clock()
    sound_mgr = SoundManager(enabled=not args.test)
    grid = CityGrid()
    state = GameState(grid, sound_mgr)
    hud = CommandCenterHUD(sound_mgr)
    hud.setup_controls(state)

    # Spawn initial AI commuter traffic
    for _ in range(8):
        state.spawn_car()

    font_large = pygame.font.SysFont("Segoe UI, Arial", 32, bold=True)
    font_med = pygame.font.SysFont("Segoe UI, Arial", 15, bold=True)
    font_small = pygame.font.SysFont("Segoe UI, Arial", 12)

    running = True
    frame_count = 0

    while running:
        raw_dt = clock.tick(FPS) / 1000.0
        dt = min(0.1, raw_dt) * state.speed_multiplier
        state.fps = clock.get_fps()
        frame_count += 1

        if args.test and frame_count >= 120:
            print("[Test] Successfully ran 120 player-driven simulation frames!")
            running = False
            break

        # 1. Player Key Inputs (WASD / Arrows)
        keys = pygame.key.get_pressed()
        if not state.paused and not state.game_over:
            state.player.handle_input(keys, dt)

        # 2. Event Handling
        cam_offset = state.camera.get_offset() if not args.test else (0, 0)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    state.paused = not state.paused
                    sound_mgr.play('click')
                elif event.key == pygame.K_q:
                    # Q - Live Reroute / GPS Refresh
                    state.player.trigger_manual_reroute()
                elif event.key == pygame.K_v:
                    # V - Toggle Camera View (Cycles: Cockpit [Sit in Car] -> Follow Cam -> City Overview)
                    state.camera.cycle_mode()
                    sound_mgr.play('click')
                elif event.key == pygame.K_TAB:
                    # Tab - Toggle Slide-out Command Deck
                    hud.drawer_open = not hud.drawer_open
                    sound_mgr.play('click')
                elif event.key == pygame.K_h:
                    # H - Honk Horn
                    state.player.honk_horn()
                elif event.key == pygame.K_z:
                    # Z - Left Turn Signal
                    state.player.toggle_turn_signal("LEFT")
                elif event.key == pygame.K_x:
                    # X - Hazard Flasher
                    state.player.toggle_turn_signal("HAZARD")
                elif event.key == pygame.K_c and not (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    # C - Right Turn Signal (or spawn car if drawer focused)
                    state.player.toggle_turn_signal("RIGHT")
                elif event.key == pygame.K_p:
                    state.player.set_gear("P")
                elif event.key == pygame.K_1:
                    state.speed_multiplier = 1.0
                elif event.key == pygame.K_2:
                    state.speed_multiplier = 2.0
                elif event.key == pygame.K_m:
                    sound_mgr.toggle_mute()
                elif event.key == pygame.K_r and state.game_over:
                    # Restart simulation
                    grid = CityGrid()
                    state = GameState(grid, sound_mgr)
                    hud.setup_controls(state)
                    hud.select_intersection(None, None)
                    for _ in range(8):
                        state.spawn_car()

                        
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # 1. Let HUD handle click first (Steering wheel, Shifter, Pedals, Buttons, Drawer)
                handled = hud.handle_event(event, state)
                
                # 2. If not consumed by HUD controls, map click in world coordinates
                if not handled:
                    mx, my = event.pos
                    world_x = mx + cam_offset[0]
                    world_y = my + cam_offset[1]
                    
                    if event.button == 1:
                        # Left Click: Inspect intersection node
                        clicked_node = None
                        for node in grid.nodes.values():
                            if math.hypot(node.x - world_x, node.y - world_y) < 28:
                                clicked_node = node
                                break
                        if clicked_node:
                            ctrl = state.controllers.get(clicked_node.id)
                            hud.select_intersection(clicked_node, ctrl)
                            sound_mgr.play('click')
                        else:
                            hud.select_intersection(None, None)
                            
                    elif event.button == 3:
                        # Right Click: Directly set destination parking target
                        for node in grid.nodes.values():
                            if math.hypot(node.x - world_x, node.y - world_y) < 32:
                                state.player.set_destination(node, f"POINT ({int(node.x)}, {int(node.y)})")
                                state.mission_time_remaining = MISSION_TIME_LIMIT
                                sound_mgr.play('perfect_park')
                                break
            else:
                hud.handle_event(event, state)

        # 3. Simulation & Gameplay Step
        if not state.paused and not state.game_over:
            # Update Player Car
            state.player.update(dt, state.controllers, state.vehicles)
            
            # Update Camera
            state.camera.update(state.player, dt)
            cam_offset = state.camera.get_offset() if not args.test else (0, 0)

            # Update HUD Shifter Animation
            hud.update(state, dt)

            # Check Vehicle Masters Parking Destination Arrival
            dest_node = state.player.destination_node
            if dest_node:
                dist_to_dest = math.hypot(state.player.x - dest_node.x, state.player.y - dest_node.y)
                # Successful arrival inside green target parking bay!
                if dist_to_dest < 28.0:
                    state.missions_completed += 1
                    time_bonus = int(state.mission_time_remaining * 25)
                    bonus = 600 + max(0, time_bonus)
                    state.player.score += bonus
                    state.trigger_success_particles(dest_node.x, dest_node.y, (34, 197, 94))
                    state.trigger_success_particles(dest_node.x, dest_node.y, (250, 204, 21))
                    
                    state.player.last_violation_msg = f"PERFECT PARK! ★★★ +{bonus} PTS"
                    state.player.violation_msg_timer = 2.8
                    sound_mgr.play('perfect_park')
                    state.assign_next_mission()

            # Mission Countdown Timer
            state.mission_time_remaining -= dt
            if state.mission_time_remaining <= 0:
                # Timer expired penalty
                state.player.score = max(0, state.player.score - 150)
                state.player.last_violation_msg = "MISSION TIMEOUT! -150 PTS"
                state.player.violation_msg_timer = 2.5
                sound_mgr.play('alert')
                state.assign_next_mission()

            # Check Game Over if score runs out
            if state.player.score <= 0:
                state.game_over = True
                state.game_over_reason = "LICENSE REVOKED: Driver score depleted to 0 from violations & crashes!"
                sound_mgr.play('alert')

            # Auto-spawn AI Commuter Cars
            state.car_spawn_timer += dt
            if state.car_spawn_timer >= DEFAULT_SPAWN_INTERVAL:
                state.car_spawn_timer = 0.0
                if len(state.vehicles) < 22:
                    state.spawn_car()

            # Update Road Congestion and Queues
            grid.update_densities()

            # Update Traffic Signal Controllers
            for ctrl in state.controllers.values():
                ctrl.update_queues()
                ctrl.check_emergency_preemption(state.vehicles)
                ctrl.update(dt)

            # Update AI Vehicles
            remaining_vehicles = []
            for v in state.vehicles:
                v.update(dt, state.controllers, state.k_penalty)
                if getattr(v, 'is_emergency', False) and v.completed:
                    state.ambulance_missions_passed += 1
                    sound_mgr.play('mission_success')
                    state.active_ambulance = None
                if v.completed:
                    state.cars_cleared += 1
                else:
                    remaining_vehicles.append(v)
            state.vehicles = remaining_vehicles
            state.update_metrics()

            # Update visual particles
            for p in state.particles[:]:
                p.update(dt)
                if p.life <= 0:
                    state.particles.remove(p)

        # 4. Rendering
        if state.camera.mode == "cockpit":
            # First-Person Interior Driver Cabin ("Sit in Car")
            # CockpitRenderer renders the world streaming past through the windshield,
            # cyber-yellow car hood, instrument binnacle, steering wheel in driver's hands,
            # center console GPS tablet & PRND shifter, and floorboard pedals.
            hud.draw(screen, state, state.camera, dt=dt)
            state.player.draw_hud_notifications(screen, font_med, is_cockpit=True)
        else:
            # Exterior 3rd-Person Follow Camera or Full City Overview Camera
            screen.fill(BG_COLOR)

            # Draw Stylized Environment (Lawn stripes, Sidewalks, 3D Architecture, Roads, Zebra Crossings, Trees)
            grid.draw_environment(screen, show_heatmap=state.show_heatmap, camera_offset=cam_offset)

            # Draw Vehicle Masters Glowing Green Target Parking Bay
            if state.player.destination_node:
                grid.draw_parking_bay(
                    screen, state.player.destination_node, state.player.destination_name,
                    font_med, camera_offset=cam_offset
                )

            # Draw Traffic Lights at Intersections
            for (r, c), node in grid.intersections.items():
                ctrl = state.controllers.get(node.id)
                if ctrl:
                    is_sel = (hud.selected_node == node)
                    ctrl.draw(screen, is_selected=is_sel, camera_offset=cam_offset)

            # Draw Live Dynamic A* GPS Co-Pilot Route
            if state.show_paths:
                state.player.draw_gps_overlay(screen, camera_offset=cam_offset)
                for v in state.vehicles:
                    if getattr(v, 'is_emergency', False):
                        v.draw_path_overlay(screen, camera_offset=cam_offset)

            # Draw AI Commuter Vehicles
            for v in state.vehicles:
                v.draw(screen, camera_offset=cam_offset)

            # Draw Player Car with front-wheel steering, lighting, and seated driver avatar
            state.player.draw(screen, camera_offset=cam_offset)

            # Draw Top-Left Mini-Map GPS Overlay
            grid.draw_minimap(screen, state.player, font_small)

            # Draw Celebration/Collision Particles
            for p in state.particles:
                p.draw(screen, camera_offset=cam_offset)

            # Draw Notification Popups (Violations, Reroute alerts, Perfect Park)
            state.player.draw_hud_notifications(screen, font_med, camera_offset=cam_offset, is_cockpit=False)

            # Draw Vehicle Masters Cockpit HUD & Controls
            hud.draw(screen, state, state.camera, dt=dt)

        # Draw Game Over Modal
        if state.game_over:
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((15, 23, 42, 220))
            screen.blit(overlay, (0, 0))
            
            box_w, box_h = 600, 250
            box_rect = pygame.Rect((WINDOW_WIDTH - box_w) // 2, (WINDOW_HEIGHT - box_h) // 2, box_w, box_h)
            pygame.draw.rect(screen, CARD_BG, box_rect, border_radius=14)
            pygame.draw.rect(screen, RED_LIGHT, box_rect, width=2, border_radius=14)
            
            t_surf = font_large.render("LICENSE REVOKED / GAME OVER", True, RED_LIGHT)
            screen.blit(t_surf, t_surf.get_rect(center=(WINDOW_WIDTH // 2, box_rect.top + 45)))
            
            r_surf = font_med.render(state.game_over_reason, True, TEXT_PRIMARY)
            screen.blit(r_surf, r_surf.get_rect(center=(WINDOW_WIDTH // 2, box_rect.top + 105)))
            
            hint_surf = font_med.render("Press 'R' to Restart Driving Simulation", True, (6, 182, 212))
            screen.blit(hint_surf, hint_surf.get_rect(center=(WINDOW_WIDTH // 2, box_rect.top + 175)))

        # Draw Paused Banner
        elif state.paused:
            p_surf = font_large.render("GAME PAUSED [SPACE]", True, (245, 158, 11))
            p_rect = p_surf.get_rect(center=(WINDOW_WIDTH // 2, 85))
            bg_p = p_rect.inflate(32, 14)
            pygame.draw.rect(screen, (15, 23, 42, 230), bg_p, border_radius=10)
            pygame.draw.rect(screen, (245, 158, 11), bg_p, width=1, border_radius=10)
            screen.blit(p_surf, p_rect)

        if not args.test:
            pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
