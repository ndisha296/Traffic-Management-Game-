"""
Grid, Graph, Vehicle Masters Stylized Architecture, and Dynamic A* Engine for GridLock AI.
Handles city topology, stylized 3D buildings, manicured lawns, zebra crosswalks,
street trees, dynamic A* routing, the green target parking bay, and the Mini-Map GPS overlay.
"""

import math
import heapq
import random
import pygame
from config import (
    GRID_COLS, GRID_ROWS, CELL_WIDTH, CELL_HEIGHT,
    GRID_OFFSET_X, GRID_OFFSET_Y, ROAD_WIDTH, LANE_OFFSET,
    ROAD_COLOR, ROAD_BORDER, LANE_MARKING, INTERSECTION_BOX,
    ZEBRA_CROSSING, STOP_LINE,
    GRASS_BASE, GRASS_STRIPE, SIDEWALK_COLOR, SIDEWALK_CURB,
    BUILDING_PALETTES, BUILDING_SHADOW,
    TREE_SHADOW, TREE_CANOPY_DARK, TREE_CANOPY_LIGHT, TREE_TRUNK,
    PARKING_BAY_GREEN, PARKING_BAY_BG, PARKING_BAY_BORDER, PARKING_CHEVRON,
    PATH_OVERLAY, HEATMAP_LOW, HEATMAP_MED, HEATMAP_HIGH,
    WINDOW_LIT_AMBER, WINDOW_LIT_CYAN, WINDOW_UNLIT,
    STREETLIGHT_POLE, STREETLIGHT_GLOW, STREETLIGHT_BULB,
    MINIMAP_X, MINIMAP_Y, MINIMAP_WIDTH, MINIMAP_HEIGHT,
    DEFAULT_K_PENALTY, PLAYER_COLOR, EMERGENCY_COLOR,
    WINDOW_WIDTH, WINDOW_HEIGHT
)

class Node:
    """Represents an intersection or a perimeter entry/exit point."""
    def __init__(self, node_id, x, y, is_perimeter=False, grid_pos=None):
        self.id = node_id
        self.x = float(x)
        self.y = float(y)
        self.is_perimeter = is_perimeter
        self.grid_pos = grid_pos  # (row, col) if intersection
        self.outgoing_edges = []   # List of RoadEdge objects
        self.incoming_edges = []   # List of RoadEdge objects

    def __repr__(self):
        return f"Node({self.id}, x={int(self.x)}, y={int(self.y)})"


class RoadEdge:
    """Represents a directed one-way road lane connecting two nodes."""
    def __init__(self, from_node, to_node):
        self.from_node = from_node
        self.to_node = to_node
        
        dx = to_node.x - from_node.x
        dy = to_node.y - from_node.y
        self.length = math.hypot(dx, dy)
        
        if self.length > 0:
            ux = dx / self.length
            uy = dy / self.length
        else:
            ux, uy = 1.0, 0.0
            
        nx = -uy
        ny = ux
        
        self.start_pos = (from_node.x + nx * LANE_OFFSET, from_node.y + ny * LANE_OFFSET)
        self.end_pos = (to_node.x + nx * LANE_OFFSET, to_node.y + ny * LANE_OFFSET)
        
        self.direction = (ux, uy)
        self.angle_rad = math.atan2(dy, dx)
        self.angle_deg = math.degrees(self.angle_rad)
        
        self.vehicles = []       # Active vehicles on this edge
        self.queue_density = 0   # Count of queued cars
        self.base_cost = self.length

    def update_density(self):
        """Update count of queued or slow-moving vehicles on this edge."""
        self.queue_density = sum(1 for v in self.vehicles if getattr(v, 'speed', 10) < 12.0)

    def get_dynamic_cost(self, k_penalty=DEFAULT_K_PENALTY, is_emergency=False):
        multiplier = 25.0
        k = k_penalty * (1.6 if is_emergency else 1.0)
        return self.base_cost + (k * self.queue_density * multiplier)


class StreetTree:
    """Stylized Vehicle Masters street tree with rounded layered canopies and drop shadow."""
    def __init__(self, x, y, radius=13):
        self.x = x
        self.y = y
        self.radius = radius


class BuildingBlock:
    """Stylized Vehicle Masters 3D architectural block with pastel colors, rooftop helipad, and drop shadow."""
    def __init__(self, rect, palette_idx=0):
        self.rect = pygame.Rect(rect)
        # Surrounding sidewalk apron
        self.sidewalk_rect = self.rect.inflate(14, 14)
        # Drop shadow
        self.shadow_rect = self.rect.move(6, 8)
        # 3D rooftop elevation
        self.roof_rect = self.rect.inflate(-4, -4).move(-1, -3)
        
        palette = BUILDING_PALETTES[palette_idx % len(BUILDING_PALETTES)]
        self.base_color = palette["base"]
        self.roof_color = palette["roof"]
        self.edge_color = palette["edge"]
        
        # Helipad on select buildings
        self.has_helipad = (palette_idx % 3 == 0)

        
        # Windows on roof/facade
        self.windows = []
        rng = random.Random(rect[0] * 1000 + rect[1])
        win_w, win_h = 6, 6
        pad_x, pad_y = 13, 13
        
        start_x = self.roof_rect.left + 10
        end_x = self.roof_rect.right - 10
        start_y = self.roof_rect.top + 10
        end_y = self.roof_rect.bottom - 10
        
        for wx in range(start_x, end_x, pad_x):
            for wy in range(start_y, end_y, pad_y):
                rand_val = rng.random()
                if rand_val < 0.45:
                    col = WINDOW_LIT_AMBER
                elif rand_val < 0.70:
                    col = WINDOW_LIT_CYAN
                else:
                    col = WINDOW_UNLIT
                self.windows.append((pygame.Rect(wx, wy, win_w, win_h), col))


class Streetlight:
    """Ambient streetlight casting warm illumination."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.glow_radius = 24


class CityGrid:
    """Manages city road graph, architectural blocks, lighting, and dynamic A* queries."""
    def __init__(self):
        self.nodes = {}          # id -> Node
        self.intersections = {}  # (row, col) -> Node
        self.edges = []          # List of RoadEdge objects
        self.perimeter_nodes = []
        self.buildings = []      # List of BuildingBlock objects
        self.streetlights = []   # List of Streetlight objects
        self.trees = []          # List of StreetTree objects
        
        self._build_grid()
        self._generate_architecture()
        self._generate_streetlights()
        self._generate_trees()

    def _build_grid(self):

        node_id = 0
        
        # 1. Create Intersections
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                x = GRID_OFFSET_X + c * CELL_WIDTH
                y = GRID_OFFSET_Y + r * CELL_HEIGHT
                node = Node(node_id, x, y, is_perimeter=False, grid_pos=(r, c))
                self.nodes[node_id] = node
                self.intersections[(r, c)] = node
                node_id += 1

        # 2. Create Perimeter Entry/Exit Nodes
        perimeter_dist = 85
        for c in range(GRID_COLS):
            x = GRID_OFFSET_X + c * CELL_WIDTH
            top_node = Node(node_id, x, GRID_OFFSET_Y - perimeter_dist, is_perimeter=True)
            self.nodes[node_id] = top_node
            self.perimeter_nodes.append(top_node)
            node_id += 1
            
            bottom_node = Node(node_id, x, GRID_OFFSET_Y + (GRID_ROWS - 1) * CELL_HEIGHT + perimeter_dist, is_perimeter=True)
            self.nodes[node_id] = bottom_node
            self.perimeter_nodes.append(bottom_node)
            node_id += 1

        for r in range(GRID_ROWS):
            y = GRID_OFFSET_Y + r * CELL_HEIGHT
            left_node = Node(node_id, GRID_OFFSET_X - perimeter_dist, y, is_perimeter=True)
            self.nodes[node_id] = left_node
            self.perimeter_nodes.append(left_node)
            node_id += 1
            
            right_node = Node(node_id, GRID_OFFSET_X + (GRID_COLS - 1) * CELL_WIDTH + perimeter_dist, y, is_perimeter=True)
            self.nodes[node_id] = right_node
            self.perimeter_nodes.append(right_node)
            node_id += 1

        # 3. Connect Internal Intersections
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                curr = self.intersections[(r, c)]
                if c < GRID_COLS - 1:
                    right = self.intersections[(r, c + 1)]
                    self._create_bidirectional_edges(curr, right)
                if r < GRID_ROWS - 1:
                    down = self.intersections[(r + 1, c)]
                    self._create_bidirectional_edges(curr, down)

        # 4. Connect Perimeter Nodes
        for c in range(GRID_COLS):
            top_perim = [n for n in self.perimeter_nodes if abs(n.x - (GRID_OFFSET_X + c * CELL_WIDTH)) < 5 and n.y < GRID_OFFSET_Y][0]
            top_inter = self.intersections[(0, c)]
            self._create_bidirectional_edges(top_perim, top_inter)
            
            bottom_perim = [n for n in self.perimeter_nodes if abs(n.x - (GRID_OFFSET_X + c * CELL_WIDTH)) < 5 and n.y > GRID_OFFSET_Y + 100][0]
            bottom_inter = self.intersections[(GRID_ROWS - 1, c)]
            self._create_bidirectional_edges(bottom_inter, bottom_perim)

        for r in range(GRID_ROWS):
            left_perim = [n for n in self.perimeter_nodes if abs(n.y - (GRID_OFFSET_Y + r * CELL_HEIGHT)) < 5 and n.x < GRID_OFFSET_X][0]
            left_inter = self.intersections[(r, 0)]
            self._create_bidirectional_edges(left_perim, left_inter)
            
            right_perim = [n for n in self.perimeter_nodes if abs(n.y - (GRID_OFFSET_Y + r * CELL_HEIGHT)) < 5 and n.x > GRID_OFFSET_X + 100][0]
            right_inter = self.intersections[(r, GRID_COLS - 1)]
            self._create_bidirectional_edges(right_inter, right_perim)

    def _create_bidirectional_edges(self, node_a, node_b):
        edge_ab = RoadEdge(node_a, node_b)
        node_a.outgoing_edges.append(edge_ab)
        node_b.incoming_edges.append(edge_ab)
        self.edges.append(edge_ab)
        
        edge_ba = RoadEdge(node_b, node_a)
        node_b.outgoing_edges.append(edge_ba)
        node_a.incoming_edges.append(edge_ba)
        self.edges.append(edge_ba)

    def _generate_architecture(self):
        """Construct realistic urban city blocks between avenues."""
        inset = ROAD_WIDTH // 2 + 10
        palette_idx = 0
        for r in range(GRID_ROWS - 1):
            for c in range(GRID_COLS - 1):
                n_tl = self.intersections[(r, c)]
                n_br = self.intersections[(r + 1, c + 1)]
                
                bx = n_tl.x + inset
                by = n_tl.y + inset
                bw = (n_br.x - inset) - bx
                bh = (n_br.y - inset) - by
                
                if bw > 20 and bh > 20:
                    self.buildings.append(BuildingBlock((bx, by, bw, bh), palette_idx=palette_idx))
                    palette_idx += 1

    def _generate_streetlights(self):
        """Place ambient streetlamps along the road sidewalks."""
        inset = ROAD_WIDTH // 2 + 6
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS - 1):
                n1 = self.intersections[(r, c)]
                n2 = self.intersections[(r, c + 1)]
                mid_x = (n1.x + n2.x) / 2
                self.streetlights.append(Streetlight(mid_x, n1.y - inset))
                self.streetlights.append(Streetlight(mid_x, n1.y + inset))

        for c in range(GRID_COLS):
            for r in range(GRID_ROWS - 1):
                n1 = self.intersections[(r, c)]
                n2 = self.intersections[(r + 1, c)]
                mid_y = (n1.y + n2.y) / 2
                self.streetlights.append(Streetlight(n1.x - inset, mid_y))
                self.streetlights.append(Streetlight(n1.x + inset, mid_y))

    def _generate_trees(self):
        """Place lush stylized street trees on corners and green verges."""
        for b in self.buildings:
            self.trees.append(StreetTree(b.sidewalk_rect.left - 4, b.sidewalk_rect.top - 4, 11))
            self.trees.append(StreetTree(b.sidewalk_rect.right + 4, b.sidewalk_rect.bottom + 4, 12))
            self.trees.append(StreetTree(b.sidewalk_rect.centerx, b.sidewalk_rect.top - 5, 12))

    def get_edge(self, from_node, to_node):
        for edge in from_node.outgoing_edges:
            if edge.to_node == to_node:
                return edge
        return None

    def update_densities(self):
        for edge in self.edges:
            edge.update_density()

    def get_congestion_percentage(self):
        if not self.edges:
            return 0.0
        congested_count = sum(1 for e in self.edges if e.queue_density >= 2)
        return (congested_count / len(self.edges)) * 100.0

    def a_star(self, start_node, goal_node, k_penalty=DEFAULT_K_PENALTY, is_emergency=False):
        if start_node == goal_node:
            return [start_node]
            
        counter = 0
        open_set = []
        heapq.heappush(open_set, (0.0, counter, start_node, [start_node]))
        g_scores = {start_node.id: 0.0}
        
        while open_set:
            f, _, current, path = heapq.heappop(open_set)
            
            if current == goal_node:
                return path
                
            for edge in current.outgoing_edges:
                neighbor = edge.to_node
                
                if len(path) >= 2 and neighbor == path[-2] and len(current.outgoing_edges) > 1:
                    continue
                    
                dynamic_cost = edge.get_dynamic_cost(k_penalty, is_emergency=is_emergency)
                tentative_g = g_scores[current.id] + dynamic_cost
                
                if neighbor.id not in g_scores or tentative_g < g_scores[neighbor.id]:
                    g_scores[neighbor.id] = tentative_g
                    h = math.hypot(neighbor.x - goal_node.x, neighbor.y - goal_node.y)
                    total_f = tentative_g + h
                    counter += 1
                    heapq.heappush(open_set, (total_f, counter, neighbor, path + [neighbor]))
                    
        return []

    def get_random_perimeter_pair(self):
        start = random.choice(self.perimeter_nodes)
        candidates = [n for n in self.perimeter_nodes if math.hypot(n.x - start.x, n.y - start.y) > 300]
        goal = random.choice(candidates) if candidates else random.choice(self.perimeter_nodes)
        return start, goal

    def draw_environment(self, surface, show_heatmap=False, camera_offset=(0, 0)):
        """Draws stylized Vehicle Masters city: lawn striping, sidewalks, 3D buildings, zebra crossings, and trees."""
        ox, oy = camera_offset

        # 1. Manicured Lawn Grass Striping
        stripe_h = 36
        for y_pos in range(0, WINDOW_HEIGHT + stripe_h, stripe_h):
            stripe_col = GRASS_BASE if (y_pos // stripe_h) % 2 == 0 else GRASS_STRIPE
            pygame.draw.rect(surface, stripe_col, (0, y_pos, WINDOW_WIDTH, stripe_h))

        # 2. Sidewalk Concrete Aprons around building blocks
        for b in self.buildings:
            sw_rect = b.sidewalk_rect.move(-ox, -oy)
            pygame.draw.rect(surface, SIDEWALK_CURB, sw_rect.inflate(2, 2), border_radius=8)
            pygame.draw.rect(surface, SIDEWALK_COLOR, sw_rect, border_radius=7)

        # 3. Building Ambient Drop Shadows
        shadow_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for b in self.buildings:
            sh_rect = b.shadow_rect.move(-ox, -oy)
            pygame.draw.rect(shadow_surf, BUILDING_SHADOW, sh_rect, border_radius=8)
        surface.blit(shadow_surf, (0, 0))

        # 4. Roads & Smooth Dark Asphalt
        drawn_pairs = set()
        for edge in self.edges:
            pair_key = tuple(sorted([edge.from_node.id, edge.to_node.id]))
            if pair_key in drawn_pairs:
                continue
            drawn_pairs.add(pair_key)
            
            p1 = (edge.from_node.x - ox, edge.from_node.y - oy)
            p2 = (edge.to_node.x - ox, edge.to_node.y - oy)
            # White road boundary curb line
            pygame.draw.line(surface, ROAD_BORDER, p1, p2, ROAD_WIDTH + 4)
            # Smooth dark asphalt
            pygame.draw.line(surface, ROAD_COLOR, p1, p2, ROAD_WIDTH)

        # 5. Intersections (junction squares)
        for (r, c), node in self.intersections.items():
            rect = pygame.Rect(
                node.x - ROAD_WIDTH // 2 - 2 - ox,
                node.y - ROAD_WIDTH // 2 - 2 - oy,
                ROAD_WIDTH + 4,
                ROAD_WIDTH + 4
            )
            pygame.draw.rect(surface, INTERSECTION_BOX, rect, border_radius=3)

        # 6. Zebra Crosswalks & Stop Bars at Intersections
        half_rw = ROAD_WIDTH // 2
        f_arrow = pygame.font.SysFont("Segoe UI, Arial", 9, bold=True)
        
        for (r, c), node in self.intersections.items():
            nx = node.x - ox
            ny = node.y - oy
            
            # West crosswalk
            self._draw_crosswalk(surface, nx - half_rw - 12, ny - half_rw + 2, 8, ROAD_WIDTH - 4, vertical=True)
            # East crosswalk
            self._draw_crosswalk(surface, nx + half_rw + 4, ny - half_rw + 2, 8, ROAD_WIDTH - 4, vertical=True)
            # North crosswalk
            self._draw_crosswalk(surface, nx - half_rw + 2, ny - half_rw - 12, ROAD_WIDTH - 4, 8, vertical=False)
            # South crosswalk
            self._draw_crosswalk(surface, nx - half_rw + 2, ny + half_rw + 4, ROAD_WIDTH - 4, 8, vertical=False)

            # Tire skid marks near intersection stop lines
            pygame.draw.line(surface, (28, 38, 52), (nx - half_rw - 28, ny + 4), (nx - half_rw - 14, ny + 4), 2)
            pygame.draw.line(surface, (28, 38, 52), (nx - half_rw - 28, ny + 10), (nx - half_rw - 14, ny + 10), 2)
            pygame.draw.line(surface, (28, 38, 52), (nx + half_rw + 28, ny - 4), (nx + half_rw + 14, ny - 4), 2)
            pygame.draw.line(surface, (28, 38, 52), (nx + half_rw + 28, ny - 10), (nx + half_rw + 14, ny - 10), 2)
            pygame.draw.line(surface, (28, 38, 52), (nx - 4, ny - half_rw - 28), (nx - 4, ny - half_rw - 14), 2)
            pygame.draw.line(surface, (28, 38, 52), (nx - 10, ny - half_rw - 28), (nx - 10, ny - half_rw - 14), 2)
            pygame.draw.line(surface, (28, 38, 52), (nx + 4, ny + half_rw + 28), (nx + 4, ny + half_rw + 14), 2)
            pygame.draw.line(surface, (28, 38, 52), (nx + 10, ny + half_rw + 28), (nx + 10, ny + half_rw + 14), 2)

            # Directional painted lane arrows
            ar_w = f_arrow.render("➔", True, (241, 245, 249))
            ar_e = f_arrow.render("⬅", True, (241, 245, 249))
            ar_n = f_arrow.render("⬇", True, (241, 245, 249))
            ar_s = f_arrow.render("⬆", True, (241, 245, 249))
            surface.blit(ar_w, (nx - half_rw - 38, ny + 2))
            surface.blit(ar_e, (nx + half_rw + 28, ny - 12))
            surface.blit(ar_n, (nx - 12, ny - half_rw - 38))
            surface.blit(ar_s, (nx + 2, ny + half_rw + 28))

        # 7. Crisp White Dashed Lane Markings
        for edge in self.edges:
            if edge.from_node.id < edge.to_node.id:
                p1 = (edge.from_node.x - ox, edge.from_node.y - oy)
                p2 = (edge.to_node.x - ox, edge.to_node.y - oy)
                self._draw_dashed_line(surface, LANE_MARKING, p1, p2, dash_len=8, space_len=10, width=1)

        # 9. Building Facades, 3D Rooftops & Helipads
        for b in self.buildings:
            b_rect = b.rect.move(-ox, -oy)
            r_rect = b.roof_rect.move(-ox, -oy)
            
            # Base facade
            pygame.draw.rect(surface, b.base_color, b_rect, border_radius=6)
            # Rooftop surface
            pygame.draw.rect(surface, b.roof_color, r_rect, border_radius=5)
            pygame.draw.rect(surface, b.edge_color, r_rect, width=1, border_radius=5)
            
            # Helipad on designated rooftop
            if b.has_helipad and r_rect.width > 50 and r_rect.height > 50:
                hc_x = r_rect.centerx
                hc_y = r_rect.centery
                pygame.draw.circle(surface, (245, 158, 11), (hc_x, hc_y), 18, 2)
                # White 'H'
                h_font = pygame.font.SysFont("Segoe UI, Arial", 14, bold=True)
                h_surf = h_font.render("H", True, (254, 240, 138))
                surface.blit(h_surf, h_surf.get_rect(center=(hc_x, hc_y)))
            else:
                # Windows
                for win_rect, win_col in b.windows:
                    w_pos = win_rect.move(-ox, -oy)
                    pygame.draw.rect(surface, win_col, w_pos, border_radius=1)


        # 9. Stylized Street Trees with Layered Foliage & Shadows
        tree_shadow_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for tr in self.trees:
            tx = tr.x - ox
            ty = tr.y - oy
            pygame.draw.circle(tree_shadow_surf, TREE_SHADOW, (int(tx + 3), int(ty + 4)), tr.radius)
        surface.blit(tree_shadow_surf, (0, 0))

        for tr in self.trees:
            tx = tr.x - ox
            ty = tr.y - oy
            # Outer dark canopy
            pygame.draw.circle(surface, TREE_CANOPY_DARK, (int(tx), int(ty)), tr.radius)
            # Inner lighter highlight
            pygame.draw.circle(surface, TREE_CANOPY_LIGHT, (int(tx - 2), int(ty - 2)), tr.radius - 4)
            # Center tree trunk/stem
            pygame.draw.circle(surface, TREE_TRUNK, (int(tx), int(ty)), 2)

        # 10. Streetlights
        light_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for lamp in self.streetlights:
            pygame.draw.circle(light_surf, STREETLIGHT_GLOW, (int(lamp.x - ox), int(lamp.y - oy)), lamp.glow_radius)
        surface.blit(light_surf, (0, 0))

        for lamp in self.streetlights:
            pygame.draw.circle(surface, STREETLIGHT_POLE, (int(lamp.x - ox), int(lamp.y - oy)), 3)
            pygame.draw.circle(surface, STREETLIGHT_BULB, (int(lamp.x - ox), int(lamp.y - oy)), 2)

        # 11. Congestion Heatmap Overlay
        if show_heatmap:
            heatmap_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            for edge in self.edges:
                if edge.queue_density > 0:
                    density = edge.queue_density
                    color = HEATMAP_LOW if density == 1 else (HEATMAP_MED if density <= 3 else HEATMAP_HIGH)
                    sp = (edge.start_pos[0] - ox, edge.start_pos[1] - oy)
                    ep = (edge.end_pos[0] - ox, edge.end_pos[1] - oy)
                    pygame.draw.line(heatmap_surf, color, sp, ep, 10)
            surface.blit(heatmap_surf, (0, 0))



    def _draw_crosswalk(self, surface, x, y, w, h, vertical=True):
        """Draw bold white zebra crosswalk bars."""
        if vertical:
            stripe_gap = 5
            for sy in range(int(y), int(y + h), stripe_gap):
                pygame.draw.rect(surface, ZEBRA_CROSSING, (int(x), sy, int(w), 3))
        else:
            stripe_gap = 5
            for sx in range(int(x), int(x + w), stripe_gap):
                pygame.draw.rect(surface, ZEBRA_CROSSING, (sx, int(y), 3, int(h)))

    def _draw_dashed_line(self, surface, color, start_pos, end_pos, dash_len=8, space_len=8, width=1):
        x1, y1 = start_pos
        x2, y2 = end_pos
        dx = x2 - x1
        dy = y2 - y1
        dist = math.hypot(dx, dy)
        if dist == 0:
            return
            
        ux = dx / dist
        uy = dy / dist
        step = dash_len + space_len
        num_dashes = int(dist // step)
        
        for i in range(num_dashes):
            s_x = x1 + (i * step) * ux
            s_y = y1 + (i * step) * uy
            e_x = s_x + dash_len * ux
            e_y = s_y + dash_len * uy
            pygame.draw.line(surface, color, (s_x, s_y), (e_x, e_y), width)

    def draw_parking_bay(self, surface, destination_node, destination_name, font, camera_offset=(0, 0)):
        """
        Iconic Vehicle Masters Target Parking Bay.
        Renders an illuminated green parking stall with glowing animated borders,
        chevrons, corner brackets, and floating destination banner.
        """
        if not destination_node:
            return

        ox, oy = camera_offset
        dx = destination_node.x - ox
        dy = destination_node.y - oy

        # Parking stall dimensions
        bw, bh = 54, 38
        bay_rect = pygame.Rect(dx - bw // 2, dy - bh // 2, bw, bh)

        # 1. Translucent glowing green asphalt fill
        bay_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
        pygame.draw.rect(bay_surf, PARKING_BAY_BG, (0, 0, bw, bh), border_radius=4)
        surface.blit(bay_surf, bay_rect.topleft)

        # 2. Glowing animated dashed border
        t = pygame.time.get_ticks() / 150.0
        border_pulse = abs(math.sin(t))
        glow_color = (
            int(34 + 40 * border_pulse),
            int(197 + 58 * border_pulse),
            int(94 + 34 * border_pulse)
        )
        pygame.draw.rect(surface, glow_color, bay_rect, width=2, border_radius=4)

        # 3. Corner alignment brackets (White)
        corner_len = 8
        pygame.draw.line(surface, (255, 255, 255), (bay_rect.left, bay_rect.top), (bay_rect.left + corner_len, bay_rect.top), 2)
        pygame.draw.line(surface, (255, 255, 255), (bay_rect.left, bay_rect.top), (bay_rect.left, bay_rect.top + corner_len), 2)
        pygame.draw.line(surface, (255, 255, 255), (bay_rect.right, bay_rect.top), (bay_rect.right - corner_len, bay_rect.top), 2)
        pygame.draw.line(surface, (255, 255, 255), (bay_rect.right, bay_rect.top), (bay_rect.right, bay_rect.top + corner_len), 2)
        pygame.draw.line(surface, (255, 255, 255), (bay_rect.left, bay_rect.bottom), (bay_rect.left + corner_len, bay_rect.bottom), 2)
        pygame.draw.line(surface, (255, 255, 255), (bay_rect.left, bay_rect.bottom), (bay_rect.left, bay_rect.bottom - corner_len), 2)
        pygame.draw.line(surface, (255, 255, 255), (bay_rect.right, bay_rect.bottom), (bay_rect.right - corner_len, bay_rect.bottom), 2)
        pygame.draw.line(surface, (255, 255, 255), (bay_rect.right, bay_rect.bottom), (bay_rect.right, bay_rect.bottom - corner_len), 2)

        # 4. "PARK HERE" Stencil Text
        p_font = pygame.font.SysFont("Segoe UI, Arial", 10, bold=True)
        p_surf = p_font.render("PARK HERE", True, (255, 255, 255))
        surface.blit(p_surf, p_surf.get_rect(center=(bay_rect.centerx, bay_rect.centery)))

        # 5. Floating Vehicle Masters Beacon Pin
        bounce = math.sin(pygame.time.get_ticks() / 200.0) * 4
        pin_y = bay_rect.top - 18 + bounce
        
        # Bouncing Chevron Arrow
        ch_pts = [
            (bay_rect.centerx - 7, pin_y - 6),
            (bay_rect.centerx, pin_y),
            (bay_rect.centerx + 7, pin_y - 6)
        ]
        pygame.draw.lines(surface, PARKING_CHEVRON, False, ch_pts, 3)

        # Target Destination Badge
        badge_surf = font.render(f"🎯 {destination_name}", True, (255, 255, 255))
        badge_rect = badge_surf.get_rect(center=(bay_rect.centerx, pin_y - 14))
        bg_b = badge_rect.inflate(14, 6)
        
        badge_box = pygame.Surface(bg_b.size, pygame.SRCALPHA)
        pygame.draw.rect(badge_box, (15, 23, 42, 220), badge_box.get_rect(), border_radius=5)
        pygame.draw.rect(badge_box, PARKING_BAY_BORDER, badge_box.get_rect(), width=1, border_radius=5)
        surface.blit(badge_box, bg_b.topleft)
        surface.blit(badge_surf, badge_rect)

    def draw_minimap(self, surface, player, font):
        """
        Renders the iconic GTA Circular Radar Mini-Map with compass ring,
        player heading arrow, destination blip, traffic nodes, and active street name readout.
        """
        # Outer Radar Center & Radius
        rc_x = MINIMAP_X + MINIMAP_WIDTH // 2
        rc_y = MINIMAP_Y + (MINIMAP_HEIGHT // 2) - 6
        rad = 76
        
        # 1. Dark Glass Radar Disc
        radar_surf = pygame.Surface((rad * 2 + 10, rad * 2 + 10), pygame.SRCALPHA)
        pygame.draw.circle(radar_surf, (15, 23, 42, 235), (rad + 5, rad + 5), rad)
        # Outer Glowing Ring
        pygame.draw.circle(radar_surf, (71, 85, 105), (rad + 5, rad + 5), rad, 3)
        pygame.draw.circle(radar_surf, (6, 182, 212, 190), (rad + 5, rad + 5), rad + 1, 1)

        # Coordinate grid scale factor
        grid_min_x = GRID_OFFSET_X - 70
        grid_max_x = GRID_OFFSET_X + (GRID_COLS - 1) * CELL_WIDTH + 70
        grid_min_y = GRID_OFFSET_Y - 70
        grid_max_y = GRID_OFFSET_Y + (GRID_ROWS - 1) * CELL_HEIGHT + 70
        gw = grid_max_x - grid_min_x
        gh = grid_max_y - grid_min_y
        
        def to_radar(gx, gy):
            mx = (rad + 5) + ((gx - (grid_min_x + gw / 2)) / gw) * (rad * 1.6)
            my = (rad + 5) + ((gy - (grid_min_y + gh / 2)) / gh) * (rad * 1.6)
            return mx, my

        # Draw Mini Roads on radar
        for edge in self.edges:
            if edge.from_node.id < edge.to_node.id:
                p1 = to_radar(edge.from_node.x, edge.from_node.y)
                p2 = to_radar(edge.to_node.x, edge.to_node.y)
                pygame.draw.line(radar_surf, (51, 65, 85), p1, p2, 4)

        # Draw Mini Intersection Nodes
        for node in self.intersections.values():
            mx, my = to_radar(node.x, node.y)
            pygame.draw.circle(radar_surf, (100, 116, 139), (int(mx), int(my)), 2)

        # Draw Glowing A* Route on radar
        if player and player.gps_path:
            pts = [to_radar(player.x, player.y)]
            for n in player.gps_path:
                pts.append(to_radar(n.x, n.y))
            if len(pts) >= 2:
                pygame.draw.lines(radar_surf, (6, 182, 212, 220), False, pts, 3)
                pygame.draw.lines(radar_surf, (250, 204, 21, 240), False, pts, 1)

        # Draw Destination Parking Bay on radar
        if player and player.destination_node:
            hx, hy = to_radar(player.destination_node.x, player.destination_node.y)
            pygame.draw.circle(radar_surf, PARKING_BAY_GREEN, (int(hx), int(hy)), 5)
            pygame.draw.circle(radar_surf, (255, 255, 255), (int(hx), int(hy)), 2)

        # Draw Live Player Arrow on radar
        if player:
            px, py = to_radar(player.x, player.y)
            p_rad = math.radians(player.angle)
            f_x = px + math.cos(p_rad) * 6
            f_y = py + math.sin(p_rad) * 6
            b_l = (px + math.cos(p_rad + 2.5) * 5, py + math.sin(p_rad + 2.5) * 5)
            b_r = (px + math.cos(p_rad - 2.5) * 5, py + math.sin(p_rad - 2.5) * 5)
            pygame.draw.polygon(radar_surf, PLAYER_COLOR, [(f_x, f_y), b_l, b_r])
            pygame.draw.circle(radar_surf, (255, 255, 255), (int(px), int(py)), 1)

        # Radar Sweep Line
        sweep_angle = (pygame.time.get_ticks() / 10.0) % 360
        s_rad = math.radians(sweep_angle)
        e_x = (rad + 5) + math.cos(s_rad) * rad
        e_y = (rad + 5) + math.sin(s_rad) * rad
        pygame.draw.line(radar_surf, (6, 182, 212, 50), (rad + 5, rad + 5), (e_x, e_y), 1)

        # Blit circular radar onto screen
        surface.blit(radar_surf, (rc_x - rad - 5, rc_y - rad - 5))

        # Compass North indicator 'N'
        n_surf = font.render("N", True, (250, 204, 21))
        surface.blit(n_surf, n_surf.get_rect(center=(rc_x, rc_y - rad + 8)))

