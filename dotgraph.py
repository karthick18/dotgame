import sys
from collections import defaultdict

class Vertex(object):
    def __init__(self, row, col, weight = 0):
        self.row = row
        self.col = col
        self.weight = weight
        self.used = False

    def __str__(self):
        return '{}:{}'.format(self.row, self.col)

    def mark(self):
        self.used = True

    def is_marked(self):
        return self.used

    def __eq__(self, obj):
        assert isinstance(obj, Vertex)
        return self.row == obj.row and self.col == obj.col

    def __cmp__(self, obj):
        assert isinstance(obj, Vertex)
        diff = self.weight - obj.weight
        if diff > 0:
            return 1
        elif diff < 0:
            return -1
        return 0

class Edge(object):

    neighbor_map = {}

    def __init__(self, v1, v2):
        self.v1 = v1
        self.v2 = v2

    def mark(self):
        self.v1.mark()
        self.v2.mark()
        print('Marked: %s' %str(self))

    def is_marked(self):
        return self.v1.is_marked() and self.v2.is_marked()

    def __str__(self):
        return '{}<->{}'.format(str(self.v1), str(self.v2))

    def __eq__(self, obj):
        assert isinstance(obj, Edge)
        return self.v1 == obj.v1 and self.v2 == obj.v2

    def __cmp__(self, obj):
        assert isinstance(obj, Edge)
        diff_row1, diff_row2 = self.v1.row - obj.v1.row, self.v2.row - obj.v2.row
        diff_col1, diff_col2 = self.v1.col - obj.v1.col, self.v1.col - obj.v1.col
        diff_row = diff_row1 - diff_row2
        diff_col = diff_col1 - diff_col2
        if diff_row < 0:
            return -1
        elif diff_row > 0:
            return 1
        elif diff_col < 0:
            return -1
        elif diff_col > 0:
            return 1
        return 0

    def neighbors_get(self, max_vertex):
        key1 = (self.v1.row, self.v1.col, self.v2.row, self.v2.col)
        key2 = (self.v2.row, self.v2.col, self.v1.row, self.v1.col)
        if key1 in self.neighbor_map:
            return self.neighbor_map[key1]
        if key2 in self.neighbor_map:
            return self.neighbor_map[key2]
        neighbors = self.neighbors(max_vertex)
        self.neighbor_map[key1] = neighbors
        self.neighbor_map[key2] = neighbors
        return neighbors

    #given an edge, find the neighbors that can close the grid
    def neighbors(self, max_vertex):
        rows, cols = max_vertex.row, max_vertex.col
        r1, c1 = self.v1.row, self.v1.col
        r2, c2 = self.v2.row, self.v2.col
        if r1 == r2:
            #neighbors are upper and lower
            neighbors = [ Edge(Vertex(r1, c1), Vertex(r1+1, c1)),
                          Edge(Vertex(r1+1, c1), Vertex(r1+1, c2)),
                          Edge(Vertex(r1, c2), Vertex(r1+1, c2)),
                          Edge(Vertex(r1, c1), Vertex(r1-1, c1)),
                          Edge(Vertex(r1-1, c1), Vertex(r1-1, c2)),
                          Edge(Vertex(r1, c2), Vertex(r1-1, c2)),
                        ]
        elif c1 == c2:
            #neighbors are left and right
            neighbors = [ Edge(Vertex(r1, c1), Vertex(r1, c1+1)),
                          Edge(Vertex(r1, c1+1), Vertex(r2, c1+1)),
                          Edge(Vertex(r2, c1), Vertex(r2, c1+1)),
                          Edge(Vertex(r1, c1), Vertex(r1, c1-1)),
                          Edge(Vertex(r1, c1-1), Vertex(r2, c1-1)),
                          Edge(Vertex(r2, c1), Vertex(r2, c1-1)),
            ]

        neighbors = filter(lambda e: e.v1.row >= 0 and e.v1.col >= 0 and e.v2.row >= 0 and e.v2.col >= 0 and \
                           e.v1.row <= rows and e.v1.col <= cols and e.v2.row <= rows and e.v2.col <= cols, neighbors)
        return neighbors


class Graph(object):

    def __init__(self, edges = []):
        self.graph = defaultdict(list)
        for edge in edges:
            self.add(edge)

    def add(self, edge):
        key = (edge.v1.row, edge.v1.col)
        self.graph[key].append(edge.v2)
        self.heapify(self.graph[key])
        key = (edge.v2.row, edge.v2.col)
        self.graph[key].append(edge.v1)
        self.heapify(self.graph[key])

    def parent(self, index):
        if index == 0:
            return index
        return (index-1)/2

    def left_child(self, index):
        return 2*index + 1

    def right_child(self, index):
        return 2*index + 2

    def heapify(self, arr):
        count = len(arr)-1
        if count < 1:
            return
        start = self.parent(count)
        while start >= 0:
            self.sift_down(arr, start, count)
            start -= 1

    def swap(self, arr, i, j):
        arr[i], arr[j] = arr[j], arr[i]

    def sift_down(self, arr, start, end):
        root = start
        while self.left_child(root) <= end:
            target = root
            child = self.left_child(root)
            if arr[target] < arr[child]:
                target = child
            if child + 1 <= end and arr[target] < arr[child+1]:
                target = child+1
            if target == root:
                return
            self.swap(arr, root, target)
            root = target

    def is_connected(self, edge):
        key = (edge.v1.row, edge.v1.col)
        return (edge.v1.row, edge.v1.col) in self.graph and edge.v2 in self.graph[key]

    def remove(self, vertex):
        if (vertex.row, vertex.col) not in self.graph:
            return False
        for v, connections in self.graph.iteritems():
            try:
                first_vertex = connections[0]
                connections.remove(vertex)
                if first_vertex == vertex:
                    #we heapify if the first connection is removed
                    self.heapify(connections)
            except: pass
        del self.graph[ (vertex.row, vertex.col) ]
        return True

    def find_path(self, vertex1, vertex2, path = []):
        path = path + [vertex1]
        if (vertex1.row, vertex1.col) not in self.graph:
            return None
        if vertex1 == vertex2:
            return path
        for connection in self.graph[ (vertex1.row, vertex1.col) ]:
            if connection in path:
                continue
            new_path = self.find_path(connection, vertex2, path)
            if new_path:
                return new_path
        return None

def get_all_edges(rows, cols):
    num_grids = rows * cols * 4
    #subtract the common edges
    num_grids_shared = rows * (cols - 1) + cols * (rows - 1)
    num_grids -= num_grids_shared
    #print('Num grids: %d' %num_grids)
    #lets connect the columns to each row
    row_points = rows + 1
    col_points = cols + 1
    connections = []
    weight = rows * cols
    for r in xrange(0, row_points):
        for c in xrange(0, col_points):
            if c < cols:
                v1 = Vertex(r, c, weight = weight)
                v2 = Vertex(r, c+1, weight = weight)
                connections.append(Edge(v1, v2))

    for c in xrange(0, col_points):
        for r in xrange(0, row_points):
            if r < rows:
                v1 = Vertex(r, c, weight = weight)
                v2 = Vertex(r+1, c, weight = weight)
                connections.append(Edge(v1, v2))

    return connections
