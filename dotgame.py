#!/usr/bin/env python
import pygame
from pygame.locals import *
from dotgraph import *
import sys
import time
import random
import json
import os

class GameGraphics(object):
    RED = (255, 0, 0)
    BLUE = (0, 0, 255)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)

    def __init__(self, width = 1024, height = 768, col_width = 50, row_width = 50, spacing = 6):
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode( (width, height) )
        self.clock = pygame.time.Clock()
        self.line_buffer = []
        self.boxes = []
        self.grids = []
        self.grids_taken_list = []
        self.col_width = col_width
        self.row_width = row_width
        self.spacing = spacing
        self.text_font = pygame.font.SysFont(pygame.font.get_default_font(), 30)

    def add_line(self, color, r1, c1, r2, c2):
        self.line_buffer.append( [ False, color, (r1, c1), (r2, c2) ] )

    def find_grid(self, c, r):
        rows, cols = self.rows, self.cols
        max_width = cols * self.col_width
        max_height = rows * self.row_width
        if r > max_height or r < self.row_width:
            return None
        if c > max_width or c < self.col_width:
            return None
        row_index = r/self.row_width - 1
        col_index = c/self.col_width - 1
        match_index = None
        print('Row index %d, column index %d' %(row_index, col_index))
        grid_map = [ (row_index, col_index, row_index+1, col_index),
                     (row_index, col_index, row_index, col_index+1),
                     (row_index, col_index+1, row_index+1, col_index+1),
                     (row_index+1, col_index,  row_index+1, col_index+1),
        ]
        spacing_map = []
        spacing = self.spacing
        for grid in grid_map:
            r1, c1, r2, c2 = grid
            spacing_c1, spacing_r1, spacing_c2, spacing_r2 = (c1+1)*self.col_width - spacing, (r1+1)*self.row_width - spacing,\
                                                             (c2+1)*self.col_width + spacing, (r2+1)*self.row_width + spacing
            spacing_map.append( (spacing_c1, spacing_r1, spacing_c2, spacing_r2) )

        print('Spacing map: %s' %spacing_map)
        print('Grid map: %s' %grid_map)
        for i in xrange(len(grid_map)):
            c1, r1, c2, r2 = spacing_map[i]
            if c1 <= c and c2 >= c and r1 <= r and r2 >= r:
                match_index = i
                break

        if match_index is not None:
            print('Matched index: %d %d' %(row_index, col_index))
            print('Matched grid: %s' %(str (grid_map[match_index]) ) )
            print('Matched spacing: %s' %(str (spacing_map[match_index]) ) )
            return grid_map[match_index]
        #if nothing matched, ask for input again
        print('No matches for pos: %d/%d' %(c, r))
        return None

    def take_grid(self, color, grid):
        self.grids_taken += 1
        self.grids_taken_list.append((color, grid))

    def draw_status(self):
        human = 'Human: %d' %self.player.grids
        ai = 'AI: %d' %self.grids_ai
        text_human = self.text_font.render(human, True, self.player.color)
        text_ai = self.text_font.render(ai, True, GameGraphics.BLACK)
        width, height = self.col_width, (self.rows + 1) * self.row_width
        self.screen.blit(text_human, (width, height))
        self.screen.blit(text_ai, (width + self.col_width*2, height))

    def draw(self):
        self.screen.fill(self.WHITE)
        self.draw_boxes()
        self.draw_grids()
        self.draw_taken_grids()
        self.draw_status()
        pygame.display.update()

    def game_finished(self):
        return self.grids_taken == self.grids_total

    def winner_decided(self):
        majority = self.grids_total/2 + 1
        return self.grids_ai >= majority or self.player.grids >= majority
        
    def run_ai(self, player = False, last_move = None):
        if player is False:
            color = GameGraphics.BLACK
        else:
            color = self.player.color
        while True:
            self.draw()
            if self.game_finished() == True:
                break
            grid = self.make_move(last_move = last_move)
            if grid == None:
                print('No more moves available.')
                break
            last_move = Edge(Vertex(grid[0], grid[1]), Vertex(grid[2], grid[3]))
            self.add_grid(color, grid)
            marked_grids = self.mark_move(*grid)
            if marked_grids:
                for marked_grid in marked_grids:
                    self.take_grid(color, marked_grid)
                    if player is False:
                        self.grids_ai += 1
                    else:
                        self.player.mark_grid()
            elif not self.winner_decided():
                break
        
    def run(self):
        while self.game_finished() == False:
            grid = None
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    return
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    grid = self.find_grid(*pos)
                    break
            if grid == None:
                self.draw()
                continue
            status = self.mark_grid(*grid)
            #if grid was already marked, continue
            if status == False:
                self.draw()
                print('Grid %s already marked' %str(grid))
                continue
            self.add_grid(self.player.color, grid)
            marked_grids = self.mark_move(*grid)
            if marked_grids:
                for marked_grid in marked_grids:
                    self.take_grid(self.player.color, marked_grid)
                    self.player.mark_grid()
                self.draw()
                if self.winner_decided():
                    self.run_ai(player = True)
                    break
                continue
            
            last_move = Edge(Vertex(grid[0], grid[1]), Vertex(grid[2], grid[3]))
            #now make the move for the AI
            self.run_ai(last_move = last_move)
            self.draw()

        print('Player %s took %d grids. AI took %d grids' %(self.player, self.player.grids, self.grids_ai))
        print('Finishing game')
        time.sleep(3)

    def draw_box(self, color, r1, c1, r2, c2, thickness = 3):
        top_left =  ( (c1+1)*self.col_width, (r1+1) * self.row_width )
        pygame.draw.rect(self.screen, color, [ top_left[0], top_left[1], self.col_width, self.row_width ], 3)
        top_left = ( (c1+1)*self.col_width + self.spacing, (r1+1) * self.row_width + self.spacing)
        width = self.col_width - self.spacing*2
        height = self.row_width - self.spacing*2
        pygame.draw.rect(self.screen, color, [ top_left[0], top_left[1], width, height ], thickness)

    def draw_boxes(self):
        for box in self.boxes:
            color, grid, thickness = box
            self.draw_box(color, *grid, thickness = thickness)

    def add_box(self, color, r1, c1, r2, c2, thickness = 3):
        grid = (r1, c1, r2, c2)
        self.boxes.append((color, grid, thickness))

    def draw_grids(self):
        rows = self.rows
        cols = self.cols
        for color, grid in self.grids:
            r1, c1, r2, c2 = grid
            #swap r1,c1 if the second vertex is lesser
            if (r2, c2) < (r1, c1):
                r1, c1, r2, c2 = r2, c2, r1, c1
            width = self.col_width
            height = self.row_width
            spacing_c1, spacing_r1 = (c1+1)*width, (r1+1)*height
            if r1 == r2:
                if r1 == 0 or r1 >= rows - 1:
                    height = self.spacing
                    if r1 >= rows - 1:
                        spacing_r1 -= self.spacing
                else:
                    height = self.spacing * 2
                    spacing_r1 -= self.spacing
            if c1 == c2:
                if c1 == 0 or c1 >= cols - 1:
                    width = self.spacing
                    if c1 >= cols - 1:
                        spacing_c1 -= self.spacing
                else:
                    width = self.spacing * 2
                    spacing_c1 -= self.spacing
            pygame.draw.rect(self.screen, color, [ spacing_c1, spacing_r1, width, height] )

    def draw_taken_grid(self, color, grid_list):
        #when the grid is taken, we mark the inside rectangle
        min_p = (65535, 65535)
        max_p = (0, 0)
        for r1, c1, r2, c2 in grid_list:
            points = [ (r1, c1), (r2, c2) ]
            for p in points:
                if p < min_p:
                    min_p = p
                if p > max_p:
                    max_p = p

        grid = min_p + max_p
        r1, c1, r2, c2 = grid
        #start_c1, start_r1 = (c1+1)*self.col_width + self.spacing, (r1+1)*self.row_width + self.spacing
        start_c1, start_r1 = (c1+1)*self.col_width, (r1+1)*self.row_width
        #width, height = self.col_width - self.spacing*2, self.row_width - self.spacing*2
        width, height = self.col_width, self.row_width
        pygame.draw.rect(self.screen, color, [ start_c1, start_r1, width, height ])

    def draw_taken_grids(self):
        for color, grid_list in self.grids_taken_list:
            self.draw_taken_grid(color, grid_list)

    def add_grid(self, color, grid):
        self.grids.append((color, grid))

class Game(GameGraphics):
    coin_flip = 0
    def __init__(self, player, rows = 3, cols = 3, **kwargs):
        super(Game, self).__init__(**kwargs)
        self.rows = rows
        self.cols = cols
        self.player = player
        self.grid_map = {}
        self.grids_ai = 0
        self.grids_taken  = 0
        self.grids_total = (rows-1) * (cols-1)
        self.edge_neighbor_map = {}
        self.edges = get_all_edges(rows-1, cols-1)
        self.graph = Graph(edges = [])
        self.max_vertex = Vertex(rows-1, cols-1)
        #populate the edge neighbors cache
        for edge in self.edges:
            edge.neighbors_get(self.max_vertex)
        self.make_box()

    def make_box(self):
        self.box_map = {}
        for r in xrange(self.rows-1):
            self.box_map[r] = []
            for c in xrange(self.cols-1):
                top_left = (r,c)
                bottom_right = (r+1, c+1)
                self.box_map[r].append( (top_left + bottom_right) )

        for r in xrange(self.rows-1):
            for box in self.box_map[r]:
                self.add_box(GameGraphics.BLACK, *box)

    def mark_grid(self, r1, c1, r2, c2):
        edge = Edge( Vertex(r1, c1), Vertex(r2, c2) )
        if self.graph.is_connected(edge):
            return False
        self.graph.add(edge)
        self.remove_edge(edge)
        return True

    #given an edge, find the neighbor edges and see if some grid can be closed
    def find_unmarked_neighbor_edges(self, edge, num_unmarked = 1):
        neighbors = edge.neighbors_get(self.max_vertex)
        unmarked = {}
        neighbor_map = { 'left' : neighbors[:3], 'right' : neighbors[3:] }
        for k, edges in neighbor_map.iteritems():
            unmarked[k] = filter(lambda edge: self.graph.is_connected(edge) == False, edges)

        for k, edges in unmarked.iteritems():
            if len(edges) == num_unmarked:
                return unmarked[k]

        return None

    def find_marked_neighbor_edges(self, edge, num_marked = 4):
        neighbors = edge.neighbors_get(self.max_vertex)
        marked = {}
        start_edge = [edge] if num_marked == 4 else []
        neighbor_map = { 'left' : start_edge + neighbors[:3], 'right' : start_edge + neighbors[3:] }

        for k, edges in neighbor_map.iteritems():
            marked[k] = filter(lambda edge: self.graph.is_connected(edge), edges)

        edges_marked = filter(lambda v: len(v) == num_marked, marked.values())
        return edges_marked

    #find unconnected edges that can be closed
    def find_edges_that_can_be_closed(self):
        for edge in self.edges:
            assert self.graph.is_connected(edge) == False
            marked = self.find_marked_neighbor_edges(edge, num_marked = 3)
            if marked:
                return edge
        return None

    def remove_edge(self, edge):
        try:
            self.edges.remove(edge)
        except ValueError: pass
        connected_edge = Edge(edge.v2, edge.v1)
        try:
            self.edges.remove(connected_edge)
        except ValueError: pass

    def make_move(self, last_move = None):
        #see if anything can be closed
        edge = None
        if last_move is not None:
            unmarked_edges = self.find_unmarked_neighbor_edges(last_move)
            if unmarked_edges:
                edge = unmarked_edges[0]
                self.remove_edge(edge)
        if edge is None:
            #find an edge that can be closed to make a grid
            edge = self.find_edges_that_can_be_closed()
            if edge is not None:
                self.remove_edge(edge)
        if edge is None and len(self.edges) > 0:
            #edge = self.edges.pop()
            #print('Popped edge: %s' %edge)
            #assert self.graph.is_connected(edge) == False
            #we try to skip edges with 2 marked edges opening up a grid
            for edge in self.edges:
                marked = self.find_marked_neighbor_edges(edge, num_marked=2)
                if marked:
                    continue
                else:
                    self.remove_edge(edge)
                    break
            else:
                edge = self.edges.pop()
        if edge:
            assert self.graph.is_connected(edge) == False
            print('Returned edge: %s' %edge)
            return (edge.v1.row, edge.v1.col, edge.v2.row, edge.v2.col)
        return None

    def mark_move(self, r1, c1, r2, c2):
        edge = Edge( Vertex(r1, c1), Vertex(r2, c2) )
        self.graph.add(edge)
        #print('Adding edge: %s' %edge)
        edges_list = self.find_marked_neighbor_edges(edge, num_marked = 4)
        grid_map = {}
        if edges_list:
            nr_edges = 0
            for edges in edges_list:
                grid_map[nr_edges] = []
                for edge in edges:
                    grid_map[nr_edges].append( (edge.v1.row, edge.v1.col, edge.v2.row, edge.v2.col) )
                nr_edges += 1
        return grid_map.values()

class Player(object):

    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.grids = 0

    def __repr__(self):
        return self.name

    def mark_grid(self):
        self.grids += 1

def load_config(config, default_cfg):
    with open(config, 'r') as f:
        cfg = json.load(f)

    for k in default_cfg.keys():
        if not cfg.has_key(k):
            cfg[k] = default_cfg[k]

    return cfg

if __name__ == '__main__':
    cfg = { 'rows' : 3, 'cols' : 3, 'width' : 1440, 'height' : 900, 'spacing' : 12, 'col_width' : 100, 'row_width' : 100 }
    if len(sys.argv) == 2 and os.access(sys.argv[1], os.F_OK):
        cfg = load_config(sys.argv[1], cfg)
    if len(sys.argv) == 3:
        cfg['rows'] = int(sys.argv[1])
        cfg['cols'] = int(sys.argv[2])
    print('Playing the %d x %d game\n' %(cfg['rows'], cfg['cols']))
    p = Player('Human', GameGraphics.RED)
    cfg['rows'] += 1
    cfg['cols'] += 1
    game = Game(p, **cfg)
    game.run()
