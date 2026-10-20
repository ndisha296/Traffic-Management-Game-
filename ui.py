"""
Vehicle Masters Mobile Cockpit HUD and Command Center Engine for GridLock AI.
Provides interactive On-Screen Steering Wheel, PRND Gear Shifter, 3D Gas & Brake Pedals,
Turn Indicators, Horn, Top Mission Bar, collapsible Slide-Out Command Center Telemetry Drawer,
AND the complete First-Person Driver's Seat Interior Cockpit View ("Sit in Car").
"""

import pygame
import math
from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT,
    PANEL_BG, CARD_BG, CARD_BORDER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    GREEN_LIGHT, YELLOW_LIGHT, RED_LIGHT, CAR_COLOR, EMERGENCY_COLOR,
    PATH_OVERLAY, ACCENT_PURPLE, ACCENT_CYAN, PLAYER_COLOR,
    MISSION_TIME_LIMIT, CRITICAL_WAIT_LIMIT,
    STEERING_X, STEERING_Y, STEERING_RADIUS, STEERING_MAX_ANGLE,
    SHIFTER_X, SHIFTER_Y, SHIFTER_WIDTH, SHIFTER_HEIGHT,
    BRAKE_PEDAL_RECT, GAS_PEDAL_RECT,
    BLINKER_LEFT_RECT, HAZARD_RECT, BLINKER_RIGHT_RECT,
    BG_COLOR
)

class UIButton:
    """Interactive modern rounded button with hover states and callbacks."""
    def __init__(self, rect, text, callback, color=CARD_BG, text_color=TEXT_PRIMARY, border_color=CARD_BORDER, border_radius=8):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.base_color = color
        self.text_color = text_color
        self.border_color = border_color
        self.border_radius = border_radius
        self.is_hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.callback:
                    self.callback()
                return True
        return False

    def draw(self, surface, font):
        bg = (
            min(255, self.base_color[0] + 25),
            min(255, self.base_color[1] + 25),
            min(255, self.base_color[2] + 25)
        ) if self.is_hovered else self.base_color
        border = ACCENT_CYAN if self.is_hovered else self.border_color
        
        pygame.draw.rect(surface, bg, self.rect, border_radius=self.border_radius)
        pygame.draw.rect(surface, border, self.rect, width=1, border_radius=self.border_radius)
        
        txt_surf = font.render(self.text, True, self.text_color)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        surface.blit(txt_surf, txt_rect)


class SteeringWheelUI:
    """
    Interactive 3D-styled Steering Wheel.
    Can be clicked and dragged with the mouse to steer the vehicle in real-time,
    and smoothly rotates when keyboard steering keys (A/D/Arrows) are pressed.
    Center hub clicks honk the car horn.
    """
    def __init__(self, center_x=STEERING_X, center_y=STEERING_Y, radius=STEERING_RADIUS):
        self.cx = center_x
        self.cy = center_y
        self.radius = radius
        self.hub_radius = 26
        self.is_dragging = False

    def handle_event(self, event, player):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            dist = math.hypot(mx - self.cx, my - self.cy)
            
            # Click inside center hub: Honk horn!
            if dist <= self.hub_radius:
                player.honk_horn()
                return True
            # Click inside steering wheel outer rim: Begin mouse steering drag!
            elif dist <= self.radius + 20:
                self.is_dragging = True
                player.is_dragging_wheel = True
                self._update_steer_from_mouse(mx, my, player)
                return True

        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                mx, my = event.pos
                self._update_steer_from_mouse(mx, my, player)
                return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_dragging:
                self.is_dragging = False
                player.is_dragging_wheel = False
                return True

        return False

    def _update_steer_from_mouse(self, mx, my, player):
        dx = mx - self.cx
        norm_x = max(-1.0, min(1.0, dx / (self.radius * 0.9)))
        player.set_steering_input(norm_x)

    def draw(self, surface, player):
        angle_deg = player.steering_wheel_angle

        # 1. Outer Shadow
        shadow_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pygame.draw.circle(shadow_surf, (15, 23, 42, 110), (int(self.cx + 4), int(self.cy + 5)), self.radius + 3)
        surface.blit(shadow_surf, (0, 0))

        # 2. Outer Rim (Textured dark slate leather)
        pygame.draw.circle(surface, (30, 41, 59), (int(self.cx), int(self.cy)), self.radius, 14)
        pygame.draw.circle(surface, (71, 85, 105), (int(self.cx), int(self.cy)), self.radius + 7, 2)
        pygame.draw.circle(surface, (15, 23, 42), (int(self.cx), int(self.cy)), self.radius - 7, 2)

        # 3. Top Red Centering Alignment Marker
        marker_rad = math.radians(angle_deg - 90)
        m_x = self.cx + math.cos(marker_rad) * self.radius
        m_y = self.cy + math.sin(marker_rad) * self.radius
        pygame.draw.circle(surface, (239, 68, 68), (int(m_x), int(m_y)), 7)

        # 4. Chrome Spokes (3 spokes: left, right, bottom)
        spoke_angles = [angle_deg, angle_deg + 180, angle_deg + 90]
        for sp_ang in spoke_angles:
            sp_rad = math.radians(sp_ang)
            inner_x = self.cx + math.cos(sp_rad) * (self.hub_radius - 2)
            inner_y = self.cy + math.sin(sp_rad) * (self.hub_radius - 2)
            outer_x = self.cx + math.cos(sp_rad) * (self.radius - 7)
            outer_y = self.cy + math.sin(sp_rad) * (self.radius - 7)
            pygame.draw.line(surface, (148, 163, 184), (inner_x, inner_y), (outer_x, outer_y), 6)
            pygame.draw.line(surface, (226, 232, 240), (inner_x, inner_y), (outer_x, outer_y), 2)

        # 5. Center Hub Cap
        pygame.draw.circle(surface, (15, 23, 42), (int(self.cx), int(self.cy)), self.hub_radius)
        pygame.draw.circle(surface, (203, 213, 225), (int(self.cx), int(self.cy)), self.hub_radius, 2)
        pygame.draw.circle(surface, (30, 41, 59), (int(self.cx), int(self.cy)), self.hub_radius - 4)

        # 6. Center Horn Icon
        font_horn = pygame.font.SysFont("Segoe UI, Arial", 11, bold=True)
        horn_surf = font_horn.render("HORN", True, (248, 250, 252))
        surface.blit(horn_surf, horn_surf.get_rect(center=(self.cx, self.cy)))


class GearShifterUI:
    """
    Vehicle Masters PRND Vertical Shifter Lever.
    Allows clicking or dragging between Park, Reverse, Neutral, and Drive.
    """
    def __init__(self, x=SHIFTER_X, y=SHIFTER_Y, w=SHIFTER_WIDTH, h=SHIFTER_HEIGHT):
        self.rect = pygame.Rect(x, y, w, h)
        self.gears = ["P", "R", "N", "D"]
        self.slot_centers = {}
        slot_step = (h - 36) / (len(self.gears) - 1)
        for i, g in enumerate(self.gears):
            self.slot_centers[g] = (x + w // 2, int(y + 18 + i * slot_step))
        self.knob_y = float(self.slot_centers["D"][1])

    def handle_event(self, event, player):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.rect.collidepoint(mx, my):
                closest_g = "D"
                min_d = float('inf')
                for g, (gx, gy) in self.slot_centers.items():
                    d = abs(my - gy)
                    if d < min_d:
                        min_d = d
                        closest_g = g
                player.set_gear(closest_g)
                return True
        return False

    def update(self, player, dt):
        target_y = float(self.slot_centers[player.gear][1])
        self.knob_y += (target_y - self.knob_y) * min(1.0, 18.0 * dt)

    def draw(self, surface, player, font):
        # 1. Bezel & Track
        pygame.draw.rect(surface, (15, 23, 42, 230), self.rect, border_radius=10)
        pygame.draw.rect(surface, (71, 85, 105), self.rect, width=2, border_radius=10)
        
        top_y = self.slot_centers["P"][1]
        bot_y = self.slot_centers["D"][1]
        cx = self.rect.centerx
        pygame.draw.line(surface, (30, 41, 59), (cx, top_y), (cx, bot_y), 10)
        pygame.draw.line(surface, (15, 23, 42), (cx, top_y), (cx, bot_y), 6)

        # 2. Gear Letter Badges
        for g, (gx, gy) in self.slot_centers.items():
            is_active = (player.gear == g)
            if is_active:
                col = (34, 197, 94) if g == "D" else ((239, 68, 68) if g == "R" else ((245, 158, 11) if g == "P" else (56, 189, 248)))
                pygame.draw.circle(surface, (*col, 80), (gx, gy), 14)
            else:
                col = (148, 163, 184)
            
            txt = font.render(g, True, col)
            surface.blit(txt, txt.get_rect(center=(gx, gy)))

        # 3. Metallic Chrome Knob
        knob_rect = pygame.Rect(cx - 15, int(self.knob_y - 12), 30, 24)
        pygame.draw.rect(surface, (148, 163, 184), knob_rect, border_radius=6)
        pygame.draw.rect(surface, (241, 245, 249), knob_rect.inflate(-4, -4), border_radius=4)
        pygame.draw.circle(surface, (30, 41, 59), (cx, int(self.knob_y)), 4)


class PedalsUI:
    """
    Vehicle Masters 3D-styled Gas & Brake Pedals.
    Depress with tactile animation when clicked or triggered via keyboard.
    """
    def __init__(self):
        self.brake_rect = pygame.Rect(BRAKE_PEDAL_RECT)
        self.gas_rect = pygame.Rect(GAS_PEDAL_RECT)
        self.brake_mouse_down = False
        self.gas_mouse_down = False

    def handle_event(self, event, player):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.brake_rect.collidepoint(event.pos):
                self.brake_mouse_down = True
                player.brake_pressed = True
                return True
            elif self.gas_rect.collidepoint(event.pos):
                self.gas_mouse_down = True
                player.gas_pressed = True
                return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.brake_mouse_down:
                self.brake_mouse_down = False
                player.brake_pressed = False
            if self.gas_mouse_down:
                self.gas_mouse_down = False
                player.gas_pressed = False

        return False

    def draw(self, surface, player, font):
        is_braking = player.brake_pressed or getattr(player, 'is_keyboard_brake', False) or (player.speed < 2.0 and player.gear == "P")
        is_gassing = player.gas_pressed or getattr(player, 'is_keyboard_gas', False)

        # 1. BRAKE PEDAL
        b_offset = 6 if is_braking else 0
        b_rect = self.brake_rect.move(0, b_offset)
        
        pygame.draw.rect(surface, (15, 23, 42, 140), self.brake_rect.move(3, 5), border_radius=8)
        pygame.draw.rect(surface, (71, 85, 105), b_rect, border_radius=8)
        b_fill = (239, 68, 68) if is_braking else (51, 65, 85)
        pygame.draw.rect(surface, b_fill, b_rect.inflate(-4, -4), border_radius=6)
        
        for ry in range(b_rect.top + 16, b_rect.bottom - 22, 12):
            pygame.draw.rect(surface, (15, 23, 42), (b_rect.left + 10, ry, b_rect.width - 20, 4), border_radius=2)
            
        b_lbl = font.render("BRAKE", True, (255, 255, 255))
        surface.blit(b_lbl, b_lbl.get_rect(center=(b_rect.centerx, b_rect.bottom - 12)))

        # 2. GAS PEDAL
        g_offset = 7 if is_gassing else 0
        g_rect = self.gas_rect.move(0, g_offset)
        
        pygame.draw.rect(surface, (15, 23, 42, 140), self.gas_rect.move(3, 5), border_radius=8)
        pygame.draw.rect(surface, (71, 85, 105), g_rect, border_radius=8)
        g_fill = (34, 197, 94) if is_gassing else (51, 65, 85)
        pygame.draw.rect(surface, g_fill, g_rect.inflate(-4, -4), border_radius=6)
        
        for ry in range(g_rect.top + 18, g_rect.bottom - 26, 12):
            pygame.draw.rect(surface, (15, 23, 42), (g_rect.left + 8, ry, g_rect.width - 16, 4), border_radius=2)
            
        ch_y = g_rect.bottom - 20
        pygame.draw.lines(surface, (250, 204, 21), False, [
            (g_rect.centerx - 8, ch_y + 4),
            (g_rect.centerx, ch_y - 4),
            (g_rect.centerx + 8, ch_y + 4)
        ], 3)
        g_lbl = font.render("GAS", True, (255, 255, 255))
        surface.blit(g_lbl, g_lbl.get_rect(center=(g_rect.centerx, g_rect.bottom - 8)))


class TurnSignalsUI:
    """Turn indicators and hazard buttons positioned near steering wheel."""
    def __init__(self):
        self.left_rect = pygame.Rect(BLINKER_LEFT_RECT)
        self.hazard_rect = pygame.Rect(HAZARD_RECT)
        self.right_rect = pygame.Rect(BLINKER_RIGHT_RECT)

    def handle_event(self, event, player):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.left_rect.collidepoint(event.pos):
                player.toggle_turn_signal("LEFT")
                return True
            elif self.hazard_rect.collidepoint(event.pos):
                player.toggle_turn_signal("HAZARD")
                return True
            elif self.right_rect.collidepoint(event.pos):
                player.toggle_turn_signal("RIGHT")
                return True
        return False

    def draw(self, surface, player, font):
        is_left = (player.turn_signal in ("LEFT", "HAZARD") or player.steer_angle < -22.0) and player.blink_on
        is_hazard = (player.turn_signal == "HAZARD") and player.blink_on
        is_right = (player.turn_signal in ("RIGHT", "HAZARD") or player.steer_angle > 22.0) and player.blink_on

        col_l = (245, 158, 11) if is_left else (51, 65, 85)
        pygame.draw.rect(surface, col_l, self.left_rect, border_radius=6)
        pygame.draw.rect(surface, (71, 85, 105), self.left_rect, width=1, border_radius=6)
        txt_l = font.render("◀", True, (255, 255, 255))
        surface.blit(txt_l, txt_l.get_rect(center=self.left_rect.center))

        col_h = (239, 68, 68) if is_hazard else (51, 65, 85)
        pygame.draw.rect(surface, col_h, self.hazard_rect, border_radius=6)
        pygame.draw.rect(surface, (71, 85, 105), self.hazard_rect, width=1, border_radius=6)
        txt_h = font.render("⚠", True, (255, 255, 255))
        surface.blit(txt_h, txt_h.get_rect(center=self.hazard_rect.center))

        col_r = (245, 158, 11) if is_right else (51, 65, 85)
        pygame.draw.rect(surface, col_r, self.right_rect, border_radius=6)
        pygame.draw.rect(surface, (71, 85, 105), self.right_rect, width=1, border_radius=6)
        txt_r = font.render("▶", True, (255, 255, 255))
        surface.blit(txt_r, txt_r.get_rect(center=self.right_rect.center))


class DashboardCluster:
    """Bottom center dashboard display with Speedometer, Active Gear, and Status."""
    def __init__(self):
        self.rect = pygame.Rect(490, 745, 280, 85)

    def draw(self, surface, player, font_large, font_med, font_small):
        pygame.draw.rect(surface, (15, 23, 42, 230), self.rect, border_radius=12)
        pygame.draw.rect(surface, (71, 85, 105), self.rect, width=1, border_radius=12)

        p_speed = abs(player.speed) if player else 0.0
        mph = int(p_speed * 0.45)
        spd_surf = font_large.render(f"{mph}", True, (255, 255, 255))
        surface.blit(spd_surf, (self.rect.left + 22, self.rect.top + 16))
        
        unit_surf = font_small.render("MPH", True, (148, 163, 184))
        surface.blit(unit_surf, (self.rect.left + 22 + spd_surf.get_width() + 4, self.rect.top + 34))

        gear_col = (34, 197, 94) if player.gear == "D" else ((239, 68, 68) if player.gear == "R" else ((245, 158, 11) if player.gear == "P" else (56, 189, 248)))
        g_badge_rect = pygame.Rect(self.rect.right - 65, self.rect.top + 18, 42, 42)
        pygame.draw.rect(surface, (30, 41, 59), g_badge_rect, border_radius=8)
        pygame.draw.rect(surface, gear_col, g_badge_rect, width=2, border_radius=8)
        g_surf = font_large.render(player.gear, True, gear_col)
        surface.blit(g_surf, g_surf.get_rect(center=g_badge_rect.center))

        steer_pct = int(player.steer_angle)
        status_str = f"Score: ${player.score:,}  |  Steer: {steer_pct:+d}°"
        st_surf = font_small.render(status_str, True, (203, 213, 225))
        surface.blit(st_surf, (self.rect.left + 22, self.rect.top + 62))


class CockpitRenderer:
    """
    Renders First-Person Driver's Seat Interior View ("Sit in Car").
    Features realistic forward-looking windshield, car hood extending forward,
    full interior dashboard with glowing analog/digital speedometer, tachometer,
    center GPS tablet, rear-view mirror, interactive steering wheel in driver's hands,
    center console PRND shifter, and pedals.
    """
    def __init__(self):
        # Reusable buffer surface for rendering the rotated world ahead
        self.buf_size = 1000
        self.world_buffer = pygame.Surface((self.buf_size, self.buf_size))
        
        # Interactive Cockpit Steering Wheel (Centered in driver's hands at x=285, y=685)
        self.steer_cx = 285
        self.steer_cy = 685
        self.steer_radius = 92
        self.hub_radius = 28
        self.is_dragging_wheel = False

        # Cockpit Center Console Shifter
        self.shifter_rect = pygame.Rect(630, 640, 52, 175)
        self.slot_centers = {}
        gears = ["P", "R", "N", "D"]
        step = 135 / (len(gears) - 1)
        for i, g in enumerate(gears):
            self.slot_centers[g] = (630 + 26, int(658 + i * step))
        self.knob_y = float(self.slot_centers["D"][1])

        # Cockpit Pedals (Bottom right floorboard)
        self.brake_rect = pygame.Rect(870, 715, 80, 95)
        self.gas_rect = pygame.Rect(975, 680, 62, 130)

        # Cockpit Hazard Button
        self.hazard_rect = pygame.Rect(700, 640, 38, 38)

        # Cockpit GPS Tablet Area (Clickable to trigger manual A* GPS reroute)
        self.tablet_rect = pygame.Rect(515, 485 + 25, 230, 150)

        # Cockpit Turn Signal Blinkers on Binnacle
        self.turn_left_rect = pygame.Rect(140 + 8, 485 + 25 + 6, 36, 36)
        self.turn_right_rect = pygame.Rect(140 + 340 - 44, 485 + 25 + 6, 36, 36)

    def handle_event(self, event, player):
        """Handle clicks on the interior cockpit steering wheel, shifter, pedals, and instruments."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            
            # 1. Steering Wheel & Horn
            dist = math.hypot(mx - self.steer_cx, my - self.steer_cy)
            if dist <= self.hub_radius:
                player.honk_horn()
                return True
            elif dist <= self.steer_radius + 20:
                self.is_dragging_wheel = True
                player.is_dragging_wheel = True
                dx = mx - self.steer_cx
                norm_x = max(-1.0, min(1.0, dx / (self.steer_radius * 0.9)))
                player.set_steering_input(norm_x)
                return True

            # 2. Shifter Slots
            if self.shifter_rect.collidepoint(mx, my):
                closest_g = "D"
                min_d = float('inf')
                for g, (gx, gy) in self.slot_centers.items():
                    d = abs(my - gy)
                    if d < min_d:
                        min_d = d
                        closest_g = g
                player.set_gear(closest_g)
                return True

            # 3. Pedals
            if self.brake_rect.collidepoint(mx, my):
                player.brake_pressed = True
                return True
            if self.gas_rect.collidepoint(mx, my):
                player.gas_pressed = True
                return True

            # 4. Hazard Button
            if self.hazard_rect.collidepoint(mx, my):
                player.toggle_turn_signal("HAZARD")
                return True

            # 5. Turn Indicators on Binnacle
            if self.turn_left_rect.collidepoint(mx, my):
                player.toggle_turn_signal("LEFT")
                return True
            if self.turn_right_rect.collidepoint(mx, my):
                player.toggle_turn_signal("RIGHT")
                return True

            # 6. GPS Tablet (Click to recalculate optimal route)
            if self.tablet_rect.collidepoint(mx, my):
                player.trigger_manual_reroute()
                return True

        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging_wheel:
                mx, my = event.pos
                dx = mx - self.steer_cx
                norm_x = max(-1.0, min(1.0, dx / (self.steer_radius * 0.9)))
                player.set_steering_input(norm_x)
                return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_dragging_wheel:
                self.is_dragging_wheel = False
                player.is_dragging_wheel = False
            player.brake_pressed = False
            player.gas_pressed = False

        return False

    def update(self, player, dt):
        target_y = float(self.slot_centers[player.gear][1])
        self.knob_y += (target_y - self.knob_y) * min(1.0, 18.0 * dt)

    def render(self, screen, game_state, dt, font_large, font_med, font_small):
        """Complete First-Person Driver's Seat Interior View ("Sit in Car")."""
        player = game_state.player
        grid = game_state.grid
        self.update(player, dt)

        # ------------------------------------------------------------------
        # 1. RENDER WORLD THROUGH WINDSHIELD
        # ------------------------------------------------------------------
        half_buf = self.buf_size // 2
        # Center camera on player car position
        cam_offset = (int(player.x - half_buf), int(player.y - half_buf))

        # Clear buffer with green lawn
        self.world_buffer.fill(BG_COLOR)

        # Draw Environment
        grid.draw_environment(self.world_buffer, show_heatmap=game_state.show_heatmap, camera_offset=cam_offset)

        # Draw Destination Green Target Parking Bay
        if player.destination_node:
            grid.draw_parking_bay(
                self.world_buffer, player.destination_node, player.destination_name,
                font_med, camera_offset=cam_offset
            )

        # Draw Traffic Lights
        for (r, c), node in grid.intersections.items():
            ctrl = game_state.controllers.get(node.id)
            if ctrl:
                ctrl.draw(self.world_buffer, is_selected=False, camera_offset=cam_offset)

        # Draw GPS Routes
        if game_state.show_paths:
            player.draw_gps_overlay(self.world_buffer, camera_offset=cam_offset)
            for v in game_state.vehicles:
                if getattr(v, 'is_emergency', False):
                    v.draw_path_overlay(self.world_buffer, camera_offset=cam_offset)

        # Draw AI Vehicles
        for v in game_state.vehicles:
            v.draw(self.world_buffer, camera_offset=cam_offset)

        # Draw Particles
        for p in game_state.particles:
            p.draw(self.world_buffer, camera_offset=cam_offset)

        # Rotate world buffer so car heading is always facing UP!
        rot_angle = -player.angle - 90
        rot_world = pygame.transform.rotate(self.world_buffer, rot_angle)
        
        # Blit rotated world onto screen
        rot_rect = rot_world.get_rect(center=(WINDOW_WIDTH // 2, 335))
        screen.blit(rot_world, rot_rect)

        # ------------------------------------------------------------------
        # 2. CAR HOOD / BONNET (Tapered Yellow Sports Hood extending forward)
        # ------------------------------------------------------------------
        # Inertia tilt when steering or braking
        steer_tilt = (player.steer_angle / STEERING_MAX_ANGLE) * 3.0
        pitch_drop = 3.0 if (player.brake_pressed or player.gear == "P") else 0.0

        hood_top_w = 420
        hood_bot_w = 820
        hood_top_y = 390 + pitch_drop
        hood_bot_y = 520 + pitch_drop
        cx = WINDOW_WIDTH // 2 + steer_tilt

        hood_pts = [
            (cx - hood_top_w // 2, hood_top_y),
            (cx + hood_top_w // 2, hood_top_y),
            (cx + hood_bot_w // 2, hood_bot_y),
            (cx - hood_bot_w // 2, hood_bot_y)
        ]
        # Cyber Yellow hood body
        pygame.draw.polygon(screen, PLAYER_COLOR, hood_pts)
        pygame.draw.polygon(screen, (202, 138, 4), hood_pts, 2)

        # Hood power creases & center racing scoop
        pygame.draw.line(screen, (234, 179, 8), (cx - 70, hood_top_y + 15), (cx - 150, hood_bot_y - 10), 3)
        pygame.draw.line(screen, (234, 179, 8), (cx + 70, hood_top_y + 15), (cx + 150, hood_bot_y - 10), 3)
        
        # Center hood scoop
        scoop_rect = pygame.Rect(cx - 36, hood_top_y + 25, 72, 18)
        pygame.draw.rect(screen, (15, 23, 42), scoop_rect, border_radius=4)
        pygame.draw.rect(screen, (71, 85, 105), scoop_rect, width=1, border_radius=4)

        # Headlight lens corners on hood fenders
        pygame.draw.circle(screen, (254, 240, 138), (int(cx - hood_top_w // 2 + 18), int(hood_top_y + 8)), 8)
        pygame.draw.circle(screen, (254, 240, 138), (int(cx + hood_top_w // 2 - 18), int(hood_top_y + 8)), 8)

        # ------------------------------------------------------------------
        # 3. WINDSHIELD FRAME & A-PILLARS
        # ------------------------------------------------------------------
        # Left A-Pillar
        pygame.draw.polygon(screen, (15, 23, 42), [(0, 0), (140, 0), (220, 520), (0, 520)])
        pygame.draw.line(screen, (51, 65, 85), (140, 0), (220, 520), 2)
        # Right A-Pillar
        pygame.draw.polygon(screen, (15, 23, 42), [(WINDOW_WIDTH - 140, 0), (WINDOW_WIDTH, 0), (WINDOW_WIDTH, 520), (WINDOW_WIDTH - 220, 520)])
        pygame.draw.line(screen, (51, 65, 85), (WINDOW_WIDTH - 140, 0), (WINDOW_WIDTH - 220, 520), 2)

        # Top Sun Visor Tint Band
        sun_surf = pygame.Surface((WINDOW_WIDTH, 50), pygame.SRCALPHA)
        sun_surf.fill((15, 23, 42, 190))
        screen.blit(sun_surf, (0, 0))

        # Rearview Mirror (Hanging from top center)
        rm_rect = pygame.Rect(WINDOW_WIDTH // 2 - 95, 42, 190, 52)
        pygame.draw.rect(screen, (15, 23, 42), rm_rect.inflate(8, 8), border_radius=10)
        pygame.draw.rect(screen, (71, 85, 105), rm_rect.inflate(8, 8), width=2, border_radius=10)
        
        # Mirror Glass Reflection (Sky, Road Horizon, Center Lane Divider)
        pygame.draw.rect(screen, (24, 33, 47), rm_rect, border_radius=8)
        m_cx = rm_rect.centerx
        m_bot = rm_rect.bottom
        # Sky reflection
        pygame.draw.rect(screen, (38, 52, 73), (rm_rect.left, rm_rect.top, rm_rect.width, rm_rect.height // 2))
        # Road receding perspective
        pygame.draw.polygon(screen, (30, 41, 59), [
            (m_cx - 16, rm_rect.top + rm_rect.height // 2),
            (m_cx + 16, rm_rect.top + rm_rect.height // 2),
            (m_cx + 45, m_bot),
            (m_cx - 45, m_bot)
        ])
        # Yellow lane divider
        pygame.draw.line(screen, (250, 204, 21), (m_cx, rm_rect.top + rm_rect.height // 2), (m_cx, m_bot), 2)
        # Specular glass glare stripe
        glare_surf = pygame.Surface((rm_rect.width, rm_rect.height), pygame.SRCALPHA)
        pygame.draw.line(glare_surf, (255, 255, 255, 70), (18, 6), (55, rm_rect.height - 6), 2)
        screen.blit(glare_surf, rm_rect.topleft)
        
        rm_text = font_small.render("REARVIEW MIRROR", True, (203, 213, 225))
        screen.blit(rm_text, rm_text.get_rect(center=(m_cx, rm_rect.top + 14)))

        # Left Wing Mirror
        lm_rect = pygame.Rect(18, 410, 85, 50)
        pygame.draw.rect(screen, (15, 23, 42), lm_rect.inflate(6, 6), border_radius=8)
        pygame.draw.rect(screen, (71, 85, 105), lm_rect.inflate(6, 6), width=2, border_radius=8)
        pygame.draw.rect(screen, (24, 33, 47), lm_rect, border_radius=6)
        # Wing mirror road reflection
        pygame.draw.line(screen, (250, 204, 21), (lm_rect.left + 15, lm_rect.bottom), (lm_rect.right - 25, lm_rect.top + 20), 2)
        lm_lbl = font_small.render("SIDE MIRROR", True, (203, 213, 225))
        screen.blit(lm_lbl, lm_lbl.get_rect(center=lm_rect.center))

        # ------------------------------------------------------------------
        # 4. LUXURY COCKPIT DASHBOARD (Spans y=485 to y=860)
        # ------------------------------------------------------------------
        dash_y = 485
        dash_rect = pygame.Rect(0, dash_y, WINDOW_WIDTH, WINDOW_HEIGHT - dash_y)
        pygame.draw.rect(screen, (15, 23, 42), dash_rect)
        pygame.draw.line(screen, (71, 85, 105), (0, dash_y), (WINDOW_WIDTH, dash_y), 3)

        # Subtle leather stitching line across dashboard
        pygame.draw.line(screen, (245, 158, 11), (180, dash_y + 12), (WINDOW_WIDTH - 180, dash_y + 12), 1)

        # ------------------------------------------------------------------
        # 5. DRIVER'S INSTRUMENT BINNACLE (Behind steering wheel on left)
        # ------------------------------------------------------------------
        gauge_panel = pygame.Rect(140, dash_y + 25, 340, 140)
        pygame.draw.rect(screen, (30, 41, 59), gauge_panel, border_radius=14)
        pygame.draw.rect(screen, (71, 85, 105), gauge_panel, width=2, border_radius=14)

        # Speedometer Dial (Left of binnacle)
        spd_cx, spd_cy = 225, gauge_panel.centery - 5
        spd_rad = 48
        pygame.draw.circle(screen, (15, 23, 42), (spd_cx, spd_cy), spd_rad)
        pygame.draw.circle(screen, (6, 182, 212), (spd_cx, spd_cy), spd_rad, 2)

        # Dial Tick Marks
        for deg in range(-130, 135, 30):
            d_rad = math.radians(deg)
            x1 = spd_cx + math.cos(d_rad) * (spd_rad - 2)
            y1 = spd_cy + math.sin(d_rad) * (spd_rad - 2)
            x2 = spd_cx + math.cos(d_rad) * (spd_rad - 8)
            y2 = spd_cy + math.sin(d_rad) * (spd_rad - 8)
            pygame.draw.line(screen, (148, 163, 184), (x1, y1), (x2, y2), 1)

        # Red Speedometer Needle
        p_speed = abs(player.speed)
        mph = int(p_speed * 0.45)
        needle_deg = -130 + (min(140, mph) / 140.0) * 260
        n_rad = math.radians(needle_deg)
        nx = spd_cx + math.cos(n_rad) * (spd_rad - 6)
        ny = spd_cy + math.sin(n_rad) * (spd_rad - 6)
        pygame.draw.line(screen, (239, 68, 68), (spd_cx, spd_cy), (nx, ny), 3)
        pygame.draw.circle(screen, (255, 255, 255), (spd_cx, spd_cy), 4)

        # Digital Speed Number
        spd_txt = font_large.render(f"{mph}", True, (255, 255, 255))
        screen.blit(spd_txt, (spd_cx - spd_txt.get_width() // 2, spd_cy + 12))
        unit_lbl = font_small.render("MPH", True, (148, 163, 184))
        screen.blit(unit_lbl, (spd_cx - unit_lbl.get_width() // 2, spd_cy + 34))

        # Tachometer / Rev Meter (Right of binnacle)
        tach_cx, tach_cy = 390, gauge_panel.centery - 5
        tach_rad = 42
        pygame.draw.circle(screen, (15, 23, 42), (tach_cx, tach_cy), tach_rad)
        pygame.draw.circle(screen, (168, 85, 247), (tach_cx, tach_cy), tach_rad, 2)
        
        gear_badge_col = (34, 197, 94) if player.gear == "D" else ((239, 68, 68) if player.gear == "R" else ((245, 158, 11) if player.gear == "P" else (56, 189, 248)))
        g_txt = font_large.render(player.gear, True, gear_badge_col)
        screen.blit(g_txt, g_txt.get_rect(center=(tach_cx, tach_cy - 4)))
        gear_lbl = font_small.render("GEAR", True, (148, 163, 184))
        screen.blit(gear_lbl, gear_lbl.get_rect(center=(tach_cx, tach_cy + 22)))

        # Turn Signal LEDs on Binnacle
        is_left = (player.turn_signal in ("LEFT", "HAZARD") or player.steer_angle < -20.0) and player.blink_on
        is_right = (player.turn_signal in ("RIGHT", "HAZARD") or player.steer_angle > 20.0) and player.blink_on
        col_l = (34, 197, 94) if is_left else (51, 65, 85)
        col_r = (34, 197, 94) if is_right else (51, 65, 85)
        
        l_arr = font_med.render("◀", True, col_l)
        r_arr = font_med.render("▶", True, col_r)
        screen.blit(l_arr, (gauge_panel.left + 16, gauge_panel.top + 10))
        screen.blit(r_arr, (gauge_panel.right - 28, gauge_panel.top + 10))

        # ------------------------------------------------------------------
        # 6. CENTER CONSOLE: GPS NAV TABLET & SHIFTER
        # ------------------------------------------------------------------
        # Built-in GPS Navigation Tablet
        tab_rect = pygame.Rect(515, dash_y + 25, 230, 150)
        pygame.draw.rect(screen, (15, 23, 42), tab_rect, border_radius=10)
        pygame.draw.rect(screen, (6, 182, 212), tab_rect, width=2, border_radius=10)
        
        tab_title = font_small.render("GPS CO-PILOT • A* LIVE", True, (6, 182, 212))
        screen.blit(tab_title, (tab_rect.left + 12, tab_rect.top + 8))
        
        dest_txt = player.destination_name if player.destination_name else "CITY HOSPITAL"
        d_lbl = font_med.render(f"🎯 {dest_txt}", True, (255, 255, 255))
        screen.blit(d_lbl, (tab_rect.left + 12, tab_rect.top + 26))

        # ETA & Distance
        dist_to_dest = 0
        if player.destination_node:
            dist_to_dest = int(math.hypot(player.x - player.destination_node.x, player.y - player.destination_node.y))
        eta_txt = font_small.render(f"Distance: {dist_to_dest}m  |  Q: Reroute", True, (148, 163, 184))
        screen.blit(eta_txt, (tab_rect.left + 12, tab_rect.top + 50))

        # Mini radar display inside tablet
        rad_box = pygame.Rect(tab_rect.left + 12, tab_rect.top + 72, tab_rect.width - 24, 66)
        pygame.draw.rect(screen, (30, 41, 59), rad_box, border_radius=6)
        pygame.draw.circle(screen, (34, 197, 94), rad_box.center, 5)
        # Radar line
        sw_a = (pygame.time.get_ticks() / 12.0) % 360
        sw_rad = math.radians(sw_a)
        pygame.draw.line(screen, (6, 182, 212, 90), rad_box.center, (rad_box.centerx + math.cos(sw_rad) * 28, rad_box.centery + math.sin(sw_rad) * 28), 1)

        # Center Console PRND Shifter
        pygame.draw.rect(screen, (30, 41, 59), self.shifter_rect, border_radius=8)
        pygame.draw.rect(screen, (71, 85, 105), self.shifter_rect, width=1, border_radius=8)
        
        # Track line
        cx = self.shifter_rect.centerx
        pygame.draw.line(screen, (15, 23, 42), (cx, self.slot_centers["P"][1]), (cx, self.slot_centers["D"][1]), 6)
        
        for g, (gx, gy) in self.slot_centers.items():
            is_act = (player.gear == g)
            g_col = (34, 197, 94) if g == "D" else ((239, 68, 68) if g == "R" else ((245, 158, 11) if g == "P" else (56, 189, 248)))
            if is_act:
                pygame.draw.circle(screen, (*g_col, 80), (gx, gy), 12)
            txt_g = font_med.render(g, True, g_col if is_act else (148, 163, 184))
            screen.blit(txt_g, txt_g.get_rect(center=(gx, gy)))

        # Chrome Shift Knob
        knob_r = pygame.Rect(cx - 14, int(self.knob_y - 10), 28, 20)
        pygame.draw.rect(screen, (148, 163, 184), knob_r, border_radius=5)
        pygame.draw.circle(screen, (15, 23, 42), (cx, int(self.knob_y)), 3)

        # Hazard Button
        pygame.draw.rect(screen, (239, 68, 68) if player.turn_signal == "HAZARD" else (51, 65, 85), self.hazard_rect, border_radius=8)
        pygame.draw.rect(screen, (71, 85, 105), self.hazard_rect, width=1, border_radius=8)
        hz_txt = font_med.render("⚠", True, (255, 255, 255))
        screen.blit(hz_txt, hz_txt.get_rect(center=self.hazard_rect.center))

        # ------------------------------------------------------------------
        # 7. INTERACTIVE STEERING WHEEL WITH DRIVER'S HANDS
        # ------------------------------------------------------------------
        steer_angle = player.steering_wheel_angle
        scx, scy = self.steer_cx, self.steer_cy
        srad = self.steer_radius

        # Outer Rim
        pygame.draw.circle(screen, (15, 23, 42), (scx, scy), srad, 16)
        pygame.draw.circle(screen, (71, 85, 105), (scx, scy), srad + 8, 2)
        pygame.draw.circle(screen, (30, 41, 59), (scx, scy), srad - 8, 2)

        # Top Red Center Marker
        t_rad = math.radians(steer_angle - 90)
        pygame.draw.circle(screen, (239, 68, 68), (int(scx + math.cos(t_rad) * srad), int(scy + math.sin(t_rad) * srad)), 8)

        # Chrome Spokes
        for spk in [steer_angle, steer_angle + 180, steer_angle + 90]:
            spr = math.radians(spk)
            x1 = scx + math.cos(spr) * (self.hub_radius - 2)
            y1 = scy + math.sin(spr) * (self.hub_radius - 2)
            x2 = scx + math.cos(spr) * (srad - 8)
            y2 = scy + math.sin(spr) * (srad - 8)
            pygame.draw.line(screen, (148, 163, 184), (x1, y1), (x2, y2), 8)
            pygame.draw.line(screen, (241, 245, 249), (x1, y1), (x2, y2), 2)

        # Center Horn Hub
        pygame.draw.circle(screen, (15, 23, 42), (scx, scy), self.hub_radius)
        pygame.draw.circle(screen, (203, 213, 225), (scx, scy), self.hub_radius, 2)
        h_txt = font_small.render("HORN", True, (255, 255, 255))
        screen.blit(h_txt, h_txt.get_rect(center=(scx, scy)))

        # DRIVER'S HANDS IN RACING GLOVES (Gripping wheel at 9 and 3 o'clock)
        h_left_ang = math.radians(steer_angle + 180)
        h_right_ang = math.radians(steer_angle)
        
        # Left Hand
        hl_x = scx + math.cos(h_left_ang) * srad
        hl_y = scy + math.sin(h_left_ang) * srad
        pygame.draw.circle(screen, (239, 68, 68), (int(hl_x), int(hl_y)), 12)  # Red racing glove
        pygame.draw.circle(screen, (15, 23, 42), (int(hl_x), int(hl_y)), 7)
        # Left Forearm extending towards driver
        pygame.draw.line(screen, (30, 58, 138), (hl_x, hl_y), (hl_x - 70, WINDOW_HEIGHT), 14)

        # Right Hand
        hr_x = scx + math.cos(h_right_ang) * srad
        hr_y = scy + math.sin(h_right_ang) * srad
        pygame.draw.circle(screen, (239, 68, 68), (int(hr_x), int(hr_y)), 12)  # Red racing glove
        pygame.draw.circle(screen, (15, 23, 42), (int(hr_x), int(hr_y)), 7)
        # Right Forearm extending towards driver
        pygame.draw.line(screen, (30, 58, 138), (hr_x, hr_y), (hr_x + 50, WINDOW_HEIGHT), 14)

        # ------------------------------------------------------------------
        # 8. FLOORBOARD PEDALS (Bottom Right)
        # ------------------------------------------------------------------
        is_brk = player.brake_pressed or getattr(player, 'is_keyboard_brake', False) or (player.speed < 2.0 and player.gear == "P")
        b_off = 6 if is_brk else 0
        b_r = self.brake_rect.move(0, b_off)
        pygame.draw.rect(screen, (71, 85, 105), b_r, border_radius=8)
        pygame.draw.rect(screen, (239, 68, 68) if is_brk else (51, 65, 85), b_r.inflate(-4, -4), border_radius=6)
        b_lbl = font_small.render("BRAKE", True, (255, 255, 255))
        screen.blit(b_lbl, b_lbl.get_rect(center=(b_r.centerx, b_r.bottom - 12)))

        is_gas = player.gas_pressed or getattr(player, 'is_keyboard_gas', False)
        g_off = 7 if is_gas else 0
        g_r = self.gas_rect.move(0, g_off)
        pygame.draw.rect(screen, (71, 85, 105), g_r, border_radius=8)
        pygame.draw.rect(screen, (34, 197, 94) if is_gas else (51, 65, 85), g_r.inflate(-4, -4), border_radius=6)
        g_lbl = font_small.render("GAS", True, (255, 255, 255))
        screen.blit(g_lbl, g_lbl.get_rect(center=(g_r.centerx, g_r.bottom - 10)))


class CommandCenterHUD:
    """
    Main UI Engine combining Vehicle Masters Mobile Cockpit controls,
    Top Mission Pill Bar, Slide-out Command Center Telemetry Drawer,
    AND First-Person Driver Cabin View ("Sit in Car").
    """
    def __init__(self, sound_manager=None):
        self.sound_manager = sound_manager
        
        # Cockpit First-Person Driver Cabin Renderer ("Sit in Car")
        self.cockpit = CockpitRenderer()

        # Exterior View Controls
        self.steering_wheel = SteeringWheelUI()
        self.gear_shifter = GearShifterUI()
        self.pedals = PedalsUI()
        self.turn_signals = TurnSignalsUI()
        self.dashboard = DashboardCluster()
        
        # Drawer State
        self.drawer_open = False
        self.drawer_width = 390
        self.drawer_rect = pygame.Rect(WINDOW_WIDTH - self.drawer_width, 0, self.drawer_width, WINDOW_HEIGHT)
        
        # Fonts
        pygame.font.init()
        self.title_font = pygame.font.SysFont("Segoe UI, Arial", 18, bold=True)
        self.header_font = pygame.font.SysFont("Segoe UI, Arial", 13, bold=True)
        self.body_font = pygame.font.SysFont("Segoe UI, Arial", 12)
        self.metric_font = pygame.font.SysFont("Segoe UI, Arial", 26, bold=True)
        self.small_font = pygame.font.SysFont("Segoe UI, Arial", 11)
        
        # Top Bar Buttons
        self.btn_toggle_cam = None
        self.btn_toggle_drawer = None
        
        # Drawer Buttons
        self.drawer_buttons = []
        self.selected_node = None
        self.selected_controller = None

    def setup_controls(self, game_state):
        # 1. Top Bar Camera & Drawer Toggles
        def toggle_camera():
            if hasattr(game_state, 'camera'):
                modes = ["cockpit", "follow", "overview"]
                cur_idx = modes.index(game_state.camera.mode) if game_state.camera.mode in modes else 0
                game_state.camera.mode = modes[(cur_idx + 1) % len(modes)]
            if self.sound_manager:
                self.sound_manager.play('click')
        self.btn_toggle_cam = UIButton((WINDOW_WIDTH - 325, 14, 155, 34), "🚗 SIT IN CAR: ON", toggle_camera, color=(16, 185, 129))

        def toggle_drawer():
            self.drawer_open = not self.drawer_open
            if self.sound_manager:
                self.sound_manager.play('click')
        self.btn_toggle_drawer = UIButton((WINDOW_WIDTH - 155, 14, 135, 34), "⚙ Command Deck", toggle_drawer, color=(79, 70, 229))

        # 2. Drawer Control Deck Buttons
        self.drawer_buttons.clear()
        bx = self.drawer_rect.left + 20
        bw = (self.drawer_width - 50) // 2
        y = 485

        def toggle_ai():
            game_state.ai_signals_enabled = not game_state.ai_signals_enabled
            for c in game_state.controllers.values():
                c.ai_mode = game_state.ai_signals_enabled
            if self.sound_manager:
                self.sound_manager.play('click')
        self.btn_ai = UIButton((bx, y, bw, 32), "AI Signals: ON", toggle_ai)

        def toggle_paths():
            game_state.show_paths = not game_state.show_paths
            if self.sound_manager:
                self.sound_manager.play('click')
        self.btn_paths = UIButton((bx + bw + 10, y, bw, 32), "GPS Route [P]", toggle_paths)

        y += 40
        def toggle_heatmap():
            game_state.show_heatmap = not game_state.show_heatmap
            if self.sound_manager:
                self.sound_manager.play('click')
        self.btn_heat = UIButton((bx, y, bw, 32), "Heatmap [H]", toggle_heatmap)

        def spawn_car_click():
            game_state.spawn_car()
            if self.sound_manager:
                self.sound_manager.play('click')
        self.btn_spawn_car = UIButton((bx + bw + 10, y, bw, 32), "+ Spawn AI Car [C]", spawn_car_click, color=(37, 99, 235))

        y += 40
        def dispatch_amb():
            game_state.spawn_ambulance()
            if self.sound_manager:
                self.sound_manager.play('click')
        self.btn_amb = UIButton((bx, y, bw, 32), "🚨 Amb Run [A]", dispatch_amb, color=(190, 24, 93))

        def toggle_speed():
            game_state.speed_multiplier = 2.0 if game_state.speed_multiplier == 1.0 else 1.0
            if self.sound_manager:
                self.sound_manager.play('click')
        self.btn_speed = UIButton((bx + bw + 10, y, bw, 32), "Speed: 1x", toggle_speed)

        y += 40
        def dec_k():
            game_state.k_penalty = max(0.0, round(game_state.k_penalty - 1.0, 1))
            if self.sound_manager:
                self.sound_manager.play('click')
        def inc_k():
            game_state.k_penalty = min(20.0, round(game_state.k_penalty + 1.0, 1))
            if self.sound_manager:
                self.sound_manager.play('click')
        self.btn_k_dec = UIButton((bx, y, (bw - 10) // 2, 32), "- k", dec_k)
        self.btn_k_inc = UIButton((bx + (bw - 10) // 2 + 10, y, (bw - 10) // 2, 32), "+ k", inc_k)

        def toggle_pause():
            game_state.paused = not game_state.paused
            if self.sound_manager:
                self.sound_manager.play('click')
        self.btn_pause = UIButton((bx + bw + 10, y, bw, 32), "Pause [Space]", toggle_pause)

        # Inspector Actions
        def set_as_dest():
            if self.selected_node and game_state.player:
                game_state.player.set_destination(self.selected_node, f"TARGET NODE {self.selected_node.id}")
                game_state.mission_time_remaining = MISSION_TIME_LIMIT
                if self.sound_manager:
                    self.sound_manager.play('mission_success')
        self.btn_set_dest = UIButton((bx, 795, (self.drawer_width - 50) // 2, 32), "🎯 Route Here", set_as_dest, color=(16, 185, 129))

        def force_cycle():
            if self.selected_controller:
                self.selected_controller.trigger_cycle()
        self.btn_force_cycle = UIButton((bx + (self.drawer_width - 50) // 2 + 10, 795, (self.drawer_width - 50) // 2, 32), "⚡ Cycle Light", force_cycle, color=(79, 70, 229))

        self.drawer_buttons = [
            self.btn_ai, self.btn_paths,
            self.btn_heat, self.btn_spawn_car,
            self.btn_amb, self.btn_speed,
            self.btn_k_dec, self.btn_k_inc, self.btn_pause,
            self.btn_set_dest, self.btn_force_cycle
        ]

    def select_intersection(self, node, controller):
        self.selected_node = node
        self.selected_controller = controller
        if node and not self.drawer_open:
            self.drawer_open = True

    def handle_event(self, event, game_state):
        player = game_state.player
        camera = game_state.camera

        # 1. In Cockpit Mode: route clicks to Cockpit controls
        if camera.mode == "cockpit":
            if self.cockpit.handle_event(event, player):
                return True
        else:
            # 2. In Exterior Modes: route clicks to floating cockpit controls
            if self.pedals.handle_event(event, player):
                return True
            if self.gear_shifter.handle_event(event, player):
                return True
            if self.steering_wheel.handle_event(event, player):
                return True
            if self.turn_signals.handle_event(event, player):
                return True

        # 3. Top Bar Buttons
        if self.btn_toggle_cam and self.btn_toggle_cam.handle_event(event):
            return True
        if self.btn_toggle_drawer and self.btn_toggle_drawer.handle_event(event):
            return True

        # 4. Drawer Controls (if open)
        if self.drawer_open:
            for btn in self.drawer_buttons:
                if btn in (self.btn_set_dest, self.btn_force_cycle) and not self.selected_node:
                    continue
                if btn.handle_event(event):
                    return True
            if event.type == pygame.MOUSEBUTTONDOWN and self.drawer_rect.collidepoint(event.pos):
                return True

        return False

    def update(self, game_state, dt):
        self.gear_shifter.update(game_state.player, dt)

    def draw(self, surface, game_state, camera, dt=0.016):
        player = game_state.player

        # 1. RENDER INTERIOR CABIN if in "cockpit" mode
        if camera.mode == "cockpit":
            self.cockpit.render(surface, game_state, dt, self.metric_font, self.header_font, self.small_font)
        else:
            # RENDER EXTERIOR COCKPIT OVERLAY if in "follow" or "overview" mode
            self.steering_wheel.draw(surface, player)
            self.gear_shifter.draw(surface, player, self.header_font)
            self.pedals.draw(surface, player, self.small_font)
            self.turn_signals.draw(surface, player, self.small_font)
            self.dashboard.draw(surface, player, self.metric_font, self.header_font, self.small_font)

        # 2. Draw Top Mission Bar (Vehicle Masters Style)
        self._draw_top_mission_bar(surface, game_state)

        # 3. Draw Camera View Toggle Button
        if camera.mode == "cockpit":
            cam_text = "🚗 SIT IN CAR: ON"
            cam_color = (16, 185, 129)
        elif camera.mode == "follow":
            cam_text = "🎥 Cam: FOLLOW"
            cam_color = (37, 99, 235)
        else:
            cam_text = "🎥 Cam: CITY"
            cam_color = (75, 85, 99)
            
        self.btn_toggle_cam.text = cam_text
        self.btn_toggle_cam.base_color = cam_color
        self.btn_toggle_cam.draw(surface, self.small_font)

        # 4. Draw Drawer Toggle Button
        self.btn_toggle_drawer.text = "✕ Close Deck" if self.drawer_open else "⚙ Command Deck"
        self.btn_toggle_drawer.base_color = (190, 24, 93) if self.drawer_open else (79, 70, 229)
        self.btn_toggle_drawer.draw(surface, self.small_font)

        # 5. Draw Slide-Out Command Center Drawer (if open)
        if self.drawer_open:
            self._draw_drawer(surface, game_state)




    def _draw_top_mission_bar(self, surface, game_state):
        """Vehicle Masters iconic top navigation & mission target pill."""
        player = game_state.player
        bar_w, bar_h = 490, 48
        bar_x = (WINDOW_WIDTH - bar_w) // 2
        bar_y = 10
        bar_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)

        pygame.draw.rect(surface, (15, 23, 42, 230), bar_rect, border_radius=14)
        pygame.draw.rect(surface, (71, 85, 105), bar_rect, width=1, border_radius=14)

        dest_name = player.destination_name if player and player.destination_name else "CITY HOSPITAL"
        t_surf = self.header_font.render(f"🎯 MISSION: PARK AT {dest_name}", True, (255, 255, 255))
        surface.blit(t_surf, (bar_x + 18, bar_y + 8))

        rem_time = max(0.0, game_state.mission_time_remaining)
        timer_col = GREEN_LIGHT if rem_time > 18.0 else (YELLOW_LIGHT if rem_time > 8.0 else RED_LIGHT)
        time_surf = self.small_font.render(f"{rem_time:.1f}s", True, timer_col)
        surface.blit(time_surf, (bar_x + bar_w - 55, bar_y + 8))

        p_w = bar_w - 36
        p_h = 6
        p_y = bar_y + 28
        frac = min(1.0, rem_time / MISSION_TIME_LIMIT)
        pygame.draw.rect(surface, (51, 65, 85), (bar_x + 18, p_y, p_w, p_h), border_radius=3)
        if frac > 0:
            pygame.draw.rect(surface, timer_col, (bar_x + 18, p_y, int(p_w * frac), p_h), border_radius=3)

    def _draw_drawer(self, surface, game_state):
        """Slide-out command center telemetry dashboard matching original metrics & controls."""
        pygame.draw.rect(surface, PANEL_BG, self.drawer_rect)
        pygame.draw.line(surface, CARD_BORDER, (self.drawer_rect.left, 0), (self.drawer_rect.left, WINDOW_HEIGHT), 2)
        
        header_y = 15
        title_surf = self.title_font.render("SIMULATION TELEMETRY", True, TEXT_PRIMARY)
        surface.blit(title_surf, (self.drawer_rect.left + 20, header_y))
        
        sub_surf = self.small_font.render("COMMAND CENTER • TRAFFIC AI", True, ACCENT_CYAN)
        surface.blit(sub_surf, (self.drawer_rect.left + 20, header_y + 24))
        
        # 1. Traffic Efficiency Metric
        c1_y = 56
        self._draw_card(surface, self.drawer_rect.left + 15, c1_y, self.drawer_width - 30, 85)
        self._draw_text(surface, "TRAFFIC EFFICIENCY METRIC", self.header_font, TEXT_SECONDARY, self.drawer_rect.left + 25, c1_y + 8)
        
        avg_wait = game_state.avg_wait_time
        wait_color = GREEN_LIGHT if avg_wait < 8.0 else (YELLOW_LIGHT if avg_wait < 18.0 else RED_LIGHT)
        self._draw_text(surface, f"{avg_wait:.1f}s avg", self.metric_font, wait_color, self.drawer_rect.left + 25, c1_y + 26)
        self._draw_text(surface, f"Limit: {CRITICAL_WAIT_LIMIT:.1f}s threshold", self.small_font, TEXT_MUTED, self.drawer_rect.left + 140, c1_y + 36)
        
        bar_x = self.drawer_rect.left + 25
        bar_w = self.drawer_width - 50
        w_bar_y = c1_y + 60
        w_frac = min(1.0, avg_wait / CRITICAL_WAIT_LIMIT)
        pygame.draw.rect(surface, (45, 49, 66), (bar_x, w_bar_y, bar_w, 6), border_radius=3)
        if w_frac > 0:
            pygame.draw.rect(surface, wait_color, (bar_x, w_bar_y, int(bar_w * w_frac), 6), border_radius=3)

        # 2. Congestion & Active Vehicles
        c2_y = 152
        self._draw_card(surface, self.drawer_rect.left + 15, c2_y, self.drawer_width - 30, 85)
        self._draw_text(surface, "SYSTEM-WIDE CONGESTION", self.header_font, ACCENT_PURPLE, self.drawer_rect.left + 25, c2_y + 8)
        
        c_pct = game_state.congestion_pct
        c_col = GREEN_LIGHT if c_pct < 25.0 else (YELLOW_LIGHT if c_pct < 60.0 else RED_LIGHT)
        self._draw_text(surface, f"{c_pct:.1f}%", self.metric_font, c_col, self.drawer_rect.left + 25, c2_y + 26)
        self._draw_text(surface, f"Active AI Cars: {len(game_state.vehicles)}", self.small_font, TEXT_MUTED, self.drawer_rect.left + 130, c2_y + 36)
        
        c_bar_y = c2_y + 60
        c_frac = min(1.0, c_pct / 100.0)
        pygame.draw.rect(surface, (45, 49, 66), (bar_x, c_bar_y, bar_w, 6), border_radius=3)
        if c_frac > 0:
            pygame.draw.rect(surface, c_col, (bar_x, c_bar_y, int(bar_w * c_frac), 6), border_radius=3)

        # 3. Dynamic A* Heuristic Formula Box
        c3_y = 248
        self._draw_card(surface, self.drawer_rect.left + 15, c3_y, self.drawer_width - 30, 95)
        self._draw_text(surface, "DYNAMIC A* HEURISTIC BOX", self.header_font, ACCENT_CYAN, self.drawer_rect.left + 25, c3_y + 8)
        
        formula = f"g(n) = C_base + (k × N_cars)   [k = {game_state.k_penalty:.1f}]"
        self._draw_text(surface, formula, self.small_font, TEXT_PRIMARY, self.drawer_rect.left + 25, c3_y + 28)
        
        desc = "Queued cars dynamically inflate road segment weights. Press 'Q' anytime to recalculate the optimal bypass route."
        self._draw_multiline_text(surface, desc, self.small_font, TEXT_MUTED, self.drawer_rect.left + 25, c3_y + 48, self.drawer_width - 50)

        # 4. Inspector Card
        insp_y = 354
        self._draw_card(surface, self.drawer_rect.left + 15, insp_y, self.drawer_width - 30, 108)
        if self.selected_node:
            node_title = f"INTERSECTION {self.selected_node.grid_pos}" if self.selected_node.grid_pos else f"NODE #{self.selected_node.id}"
            self._draw_text(surface, f"INSPECTOR: {node_title}", self.header_font, ACCENT_PURPLE, self.drawer_rect.left + 25, insp_y + 8)
            
            ctrl = self.selected_controller
            if ctrl:
                p_name = "EW GREEN" if ctrl.current_phase == 0 else ("EW YELLOW" if ctrl.current_phase == 1 else ("NS GREEN" if ctrl.current_phase == 3 else ("NS YELLOW" if ctrl.current_phase == 4 else "ALL RED")))
                self._draw_text(surface, f"Signal Phase: {p_name} ({ctrl.phase_timer:.1f}s / {ctrl.current_green_duration:.1f}s)", self.small_font, TEXT_PRIMARY, self.drawer_rect.left + 25, insp_y + 28)
                queues_str = f"Queues -> N:{ctrl.queue_north}  S:{ctrl.queue_south}  W:{ctrl.queue_west}  E:{ctrl.queue_east}"
                self._draw_text(surface, queues_str, self.small_font, TEXT_SECONDARY, self.drawer_rect.left + 25, insp_y + 48)
            else:
                self._draw_text(surface, "Perimeter Transit Portal Gateway", self.small_font, TEXT_MUTED, self.drawer_rect.left + 25, insp_y + 28)
            self._draw_text(surface, "Use buttons below to cycle or route here!", self.small_font, ACCENT_CYAN, self.drawer_rect.left + 25, insp_y + 72)
        else:
            self._draw_text(surface, "INSPECTOR: CLICK AN INTERSECTION", self.header_font, ACCENT_PURPLE, self.drawer_rect.left + 25, insp_y + 8)
            self._draw_text(surface, "• Left-Click any intersection to inspect signal queues", self.small_font, TEXT_SECONDARY, self.drawer_rect.left + 25, insp_y + 28)
            self._draw_text(surface, "• Right-Click any map point to set GPS target immediately", self.small_font, TEXT_SECONDARY, self.drawer_rect.left + 25, insp_y + 48)
            self._draw_text(surface, "• Press 'Q' anytime to refresh optimal route", self.small_font, ACCENT_CYAN, self.drawer_rect.left + 25, insp_y + 68)

        # 5. Control Deck Header
        self._draw_text(surface, "SIMULATION CONTROL DECK", self.header_font, TEXT_SECONDARY, self.drawer_rect.left + 25, 468)

        self.btn_ai.text = f"AI Signals: {'ON' if game_state.ai_signals_enabled else 'OFF'}"
        self.btn_ai.base_color = (16, 185, 129) if game_state.ai_signals_enabled else (75, 85, 99)
        self.btn_paths.text = f"GPS Route: {'ON' if game_state.show_paths else 'OFF'}"
        self.btn_heat.text = f"Heatmap: {'ON' if game_state.show_heatmap else 'OFF'}"
        self.btn_speed.text = f"Speed: {game_state.speed_multiplier:.0f}x"
        self.btn_pause.text = "Resume" if game_state.paused else "Pause [Space]"

        for btn in self.drawer_buttons:
            if btn in (self.btn_set_dest, self.btn_force_cycle) and not self.selected_node:
                continue
            btn.draw(surface, self.small_font)

    def _draw_card(self, surface, x, y, w, h):
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, CARD_BG, rect, border_radius=8)
        pygame.draw.rect(surface, CARD_BORDER, rect, width=1, border_radius=8)

    def _draw_text(self, surface, text, font, color, x, y):
        surf = font.render(text, True, color)
        surface.blit(surf, (x, y))

    def _draw_multiline_text(self, surface, text, font, color, x, y, max_w):
        words = text.split(' ')
        line = ""
        cur_y = y
        for word in words:
            test_line = line + (" " if line else "") + word
            if font.size(test_line)[0] < max_w:
                line = test_line
            else:
                surface.blit(font.render(line, True, color), (x, cur_y))
                cur_y += font.get_linesize()
                line = word
        if line:
            surface.blit(font.render(line, True, color), (x, cur_y))



