"""
Traffic Light Controller for GridLock AI.
Monitors queue densities, dynamically adjusts phase timers, supports emergency
vehicle preemption, and allows player manual override.
"""

import math
import pygame
from config import (
    BASE_GREEN_TIME, MIN_GREEN_TIME, MAX_GREEN_TIME, YELLOW_TIME, ALL_RED_TIME,
    QUEUE_WEIGHT_FACTOR, EMERGENCY_PREEMPTION_RADIUS,
    RED_LIGHT, YELLOW_LIGHT, GREEN_LIGHT,
    RED_LIGHT_GLOW, YELLOW_LIGHT_GLOW, GREEN_LIGHT_GLOW,
    ROAD_WIDTH
)

# Phases
PHASE_EW_GREEN = 0
PHASE_EW_YELLOW = 1
PHASE_ALL_RED_1 = 2
PHASE_NS_GREEN = 3
PHASE_NS_YELLOW = 4
PHASE_ALL_RED_2 = 5

class TrafficLightController:
    """Manages signals for a single 4-way intersection."""
    def __init__(self, node, sound_manager=None):
        self.node = node
        self.sound_manager = sound_manager
        
        # Phase State Machine
        self.current_phase = PHASE_EW_GREEN
        self.phase_timer = 0.0
        self.current_green_duration = BASE_GREEN_TIME
        self.ai_mode = True  # True = AI Dynamic Density, False = Fixed Timer / Manual
        
        # Preemption
        self.preempted_by_emergency = False
        self.preempted_direction = None  # 'EW' or 'NS'
        
        # Manual Override Flag
        self.manual_override_requested = False

        # Queues per approach
        self.queue_north = 0  # Coming from North (going South)
        self.queue_south = 0  # Coming from South (going North)
        self.queue_west = 0   # Coming from West (going East)
        self.queue_east = 0   # Coming from East (going West)

    def is_green(self, approach_direction):
        """
        Check if given approach direction has a green light.
        approach_direction: 'EW' (horizontal) or 'NS' (vertical)
        """
        if approach_direction == 'EW':
            return self.current_phase == PHASE_EW_GREEN
        elif approach_direction == 'NS':
            return self.current_phase == PHASE_NS_GREEN
        return False

    def is_yellow(self, approach_direction):
        if approach_direction == 'EW':
            return self.current_phase == PHASE_EW_YELLOW
        elif approach_direction == 'NS':
            return self.current_phase == PHASE_NS_YELLOW
        return False

    def is_red(self, approach_direction):
        return not self.is_green(approach_direction) and not self.is_yellow(approach_direction)

    def update_queues(self):
        """Query incoming road segments to count stopped vehicles approaching this node."""
        q_n, q_s, q_w, q_e = 0, 0, 0, 0
        
        for edge in self.node.incoming_edges:
            from_n = edge.from_node
            dx = self.node.x - from_n.x
            dy = self.node.y - from_n.y
            
            # Count queued cars near the intersection (within 180px)
            count = 0
            for v in edge.vehicles:
                if v.speed < 12.0 and math.hypot(self.node.x - v.x, self.node.y - v.y) < 180:
                    count += 1
                    
            if abs(dx) > abs(dy):
                # Horizontal road
                if dx > 0:
                    q_w += count  # Came from West
                else:
                    q_e += count  # Came from East
            else:
                # Vertical road
                if dy > 0:
                    q_n += count  # Came from North
                else:
                    q_s += count  # Came from South
                    
        self.queue_north = q_n
        self.queue_south = q_s
        self.queue_west = q_w
        self.queue_east = q_e

    def check_emergency_preemption(self, vehicles):
        """Detect incoming emergency vehicles and grant priority corridor."""
        self.preempted_by_emergency = False
        self.preempted_direction = None
        
        for v in vehicles:
            if not getattr(v, 'is_emergency', False):
                continue
            dist = math.hypot(self.node.x - v.x, self.node.y - v.y)
            if dist < EMERGENCY_PREEMPTION_RADIUS and v.next_node == self.node:
                # Ambulance is approaching this intersection!
                dx = self.node.x - v.x
                dy = self.node.y - v.y
                direction = 'EW' if abs(dx) > abs(dy) else 'NS'
                self.preempted_by_emergency = True
                self.preempted_direction = direction
                break

    def trigger_cycle(self):
        """Force the light to advance immediately (player click or AI interrupt)."""
        if self.current_phase == PHASE_EW_GREEN:
            self.current_phase = PHASE_EW_YELLOW
            self.phase_timer = 0.0
        elif self.current_phase == PHASE_NS_GREEN:
            self.current_phase = PHASE_NS_YELLOW
            self.phase_timer = 0.0
        elif self.current_phase in (PHASE_ALL_RED_1, PHASE_ALL_RED_2):
            self.phase_timer = ALL_RED_TIME
        if self.sound_manager:
            self.sound_manager.play('light_change')

    def calculate_adaptive_green(self, direction):
        """Calculates dynamic green duration: Base + (Queue * Weight)."""
        if direction == 'EW':
            q = self.queue_west + self.queue_east
        else:
            q = self.queue_north + self.queue_south
        duration = BASE_GREEN_TIME + (q * QUEUE_WEIGHT_FACTOR)
        return max(MIN_GREEN_TIME, min(MAX_GREEN_TIME, duration))

    def update(self, dt):
        """Advance timers and execute adaptive phase transitions."""
        self.phase_timer += dt
        
        # 1. Handle Emergency Vehicle Preemption Priority (Ambulance Corridor)
        if self.preempted_by_emergency and self.preempted_direction:
            target_green = PHASE_EW_GREEN if self.preempted_direction == 'EW' else PHASE_NS_GREEN
            if self.current_phase != target_green:
                # If currently green for the other direction, immediately switch to amber
                if self.current_phase in (PHASE_EW_GREEN, PHASE_NS_GREEN):
                    self.current_phase = PHASE_EW_YELLOW if self.current_phase == PHASE_EW_GREEN else PHASE_NS_YELLOW
                    self.phase_timer = 0.0
            else:
                # Keep green while emergency vehicle is clearing intersection
                self.phase_timer = min(self.phase_timer, 1.0)
                return

        # 2. State Machine Transitions
        if self.current_phase == PHASE_EW_GREEN:
            q_ew = self.queue_west + self.queue_east
            q_ns = self.queue_north + self.queue_south
            
            # AI early switch check: EW empty and NS piling up
            early_switch = (
                self.ai_mode and
                self.phase_timer >= MIN_GREEN_TIME and
                q_ew == 0 and
                q_ns >= 2
            )
            
            if self.phase_timer >= self.current_green_duration or early_switch or self.manual_override_requested:
                self.manual_override_requested = False
                self.current_phase = PHASE_EW_YELLOW
                self.phase_timer = 0.0

        elif self.current_phase == PHASE_EW_YELLOW:
            if self.phase_timer >= YELLOW_TIME:
                self.current_phase = PHASE_ALL_RED_1
                self.phase_timer = 0.0

        elif self.current_phase == PHASE_ALL_RED_1:
            if self.phase_timer >= ALL_RED_TIME:
                self.current_phase = PHASE_NS_GREEN
                self.phase_timer = 0.0
                self.current_green_duration = self.calculate_adaptive_green('NS') if self.ai_mode else BASE_GREEN_TIME

        elif self.current_phase == PHASE_NS_GREEN:
            q_ew = self.queue_west + self.queue_east
            q_ns = self.queue_north + self.queue_south
            
            # AI early switch check: NS empty and EW piling up
            early_switch = (
                self.ai_mode and
                self.phase_timer >= MIN_GREEN_TIME and
                q_ns == 0 and
                q_ew >= 2
            )
            
            if self.phase_timer >= self.current_green_duration or early_switch or self.manual_override_requested:
                self.manual_override_requested = False
                self.current_phase = PHASE_NS_YELLOW
                self.phase_timer = 0.0

        elif self.current_phase == PHASE_NS_YELLOW:
            if self.phase_timer >= YELLOW_TIME:
                self.current_phase = PHASE_ALL_RED_2
                self.phase_timer = 0.0

        elif self.current_phase == PHASE_ALL_RED_2:
            if self.phase_timer >= ALL_RED_TIME:
                self.current_phase = PHASE_EW_GREEN
                self.phase_timer = 0.0
                self.current_green_duration = self.calculate_adaptive_green('EW') if self.ai_mode else BASE_GREEN_TIME

    def draw(self, surface, is_selected=False, camera_offset=(0, 0)):
        """Render overhead traffic signals and pedestrian walk indicators."""
        ox, oy = camera_offset
        cx = self.node.x - ox
        cy = self.node.y - oy
        half_w = ROAD_WIDTH // 2
        light_radius = 5
        glow_radius = 9
        
        # Determine EW & NS signal light colors
        if self.current_phase == PHASE_EW_GREEN:
            ew_color, ew_glow = GREEN_LIGHT, GREEN_LIGHT_GLOW
        elif self.current_phase == PHASE_EW_YELLOW:
            ew_color, ew_glow = YELLOW_LIGHT, YELLOW_LIGHT_GLOW
        else:
            ew_color, ew_glow = RED_LIGHT, RED_LIGHT_GLOW

        if self.current_phase == PHASE_NS_GREEN:
            ns_color, ns_glow = GREEN_LIGHT, GREEN_LIGHT_GLOW
        elif self.current_phase == PHASE_NS_YELLOW:
            ns_color, ns_glow = YELLOW_LIGHT, YELLOW_LIGHT_GLOW
        else:
            ns_color, ns_glow = RED_LIGHT, RED_LIGHT_GLOW

        glow_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        # West approach indicator (left of junction, facing cars coming East)
        pos_w = (cx - half_w - 7, cy - 8)
        pygame.draw.rect(surface, (15, 23, 42), (pos_w[0] - 5, pos_w[1] - 5, 10, 10), border_radius=2)
        pygame.draw.circle(glow_surf, ew_glow, pos_w, glow_radius)
        pygame.draw.circle(surface, ew_color, pos_w, light_radius)

        # East approach indicator (right of junction, facing cars coming West)
        pos_e = (cx + half_w + 7, cy + 8)
        pygame.draw.rect(surface, (15, 23, 42), (pos_e[0] - 5, pos_e[1] - 5, 10, 10), border_radius=2)
        pygame.draw.circle(glow_surf, ew_glow, pos_e, glow_radius)
        pygame.draw.circle(surface, ew_color, pos_e, light_radius)

        # North approach indicator (top of junction, facing cars coming South)
        pos_n = (cx + 8, cy - half_w - 7)
        pygame.draw.rect(surface, (15, 23, 42), (pos_n[0] - 5, pos_n[1] - 5, 10, 10), border_radius=2)
        pygame.draw.circle(glow_surf, ns_glow, pos_n, glow_radius)
        pygame.draw.circle(surface, ns_color, pos_n, light_radius)

        # South approach indicator (bottom of junction, facing cars coming North)
        pos_s = (cx - 8, cy + half_w + 7)
        pygame.draw.rect(surface, (15, 23, 42), (pos_s[0] - 5, pos_s[1] - 5, 10, 10), border_radius=2)
        pygame.draw.circle(glow_surf, ns_glow, pos_s, glow_radius)
        pygame.draw.circle(surface, ns_color, pos_s, light_radius)

        # Pedestrian Crosswalk Signals (Small white walk / orange hand indicators)
        ped_ew_col = (255, 255, 255) if ew_color == RED_LIGHT else (239, 68, 68)
        ped_ns_col = (255, 255, 255) if ns_color == RED_LIGHT else (239, 68, 68)
        pygame.draw.circle(surface, ped_ew_col, (int(cx - half_w - 14), int(cy - 8)), 2)
        pygame.draw.circle(surface, ped_ew_col, (int(cx + half_w + 14), int(cy + 8)), 2)
        pygame.draw.circle(surface, ped_ns_col, (int(cx + 8), int(cy - half_w - 14)), 2)
        pygame.draw.circle(surface, ped_ns_col, (int(cx - 8), int(cy + half_w + 14)), 2)

        surface.blit(glow_surf, (0, 0))


        # Selected ring if inspected by user
        if is_selected:
            pygame.draw.circle(surface, (6, 182, 212), (int(cx), int(cy)), half_w + 12, 2)
            
        # Emergency Priority Glow (Police / Ambulance Corridor)
        if self.preempted_by_emergency:
            s_toggle = (pygame.time.get_ticks() // 120) % 2 == 0
            p_col = (37, 99, 235) if s_toggle else (236, 72, 153)
            pygame.draw.circle(surface, p_col, (int(cx), int(cy)), half_w + 16, 2)
