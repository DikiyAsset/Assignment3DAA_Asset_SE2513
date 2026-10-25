from heapq import heappop, heappush


class DSU:
    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n
        self.components = n
        self.largest = int(n > 0)

    def find(self, v):
        while v != self.parent[v]:
            self.parent[v] = self.parent[self.parent[v]]
            v = self.parent[v]
        return v

    def union(self, u, v):
        u, v = self.find(u), self.find(v)
        if u == v:
            return False
        if self.size[u] < self.size[v]:
            u, v = v, u
        self.parent[v] = u
        self.size[u] += self.size[v]
        self.components -= 1
        self.largest = max(self.largest, self.size[u])
        return True


def dsu(request):
    sets = DSU(request['n'])
    states = []
    for u, v in request['operations']:
        sets.union(u, v)
        states.append([sets.components, sets.largest])
    return {'states': states}


def kruskal(request):
    sets = DSU(request['n'])
    edges = request['edges']
    chosen, cost = [], 0
    for i in sorted(range(len(edges)), key=lambda i: edges[i][2]):
        u, v, weight = edges[i]
        if sets.union(u, v):
            chosen.append(i)
            cost += weight
    return {'cost': cost, 'edge_ids': chosen, 'components': sets.components}


def prim(request):
    n, edges = request['n'], request['edges']
    adj = [[] for _ in range(n)]
    for i, (u, v, w) in enumerate(edges):
        adj[u].append((w, i, v))
        adj[v].append((w, i, u))
    visited = bytearray(n)
    chosen, cost, components = [], 0, 0
    for root in range(n):
        if visited[root]:
            continue
        components += 1
        visited[root] = 1
        heap = []
        for entry in adj[root]:
            if not visited[entry[2]]:
                heappush(heap, entry)
        while heap:
            w, i, v = heappop(heap)
            if visited[v]:
                continue
            visited[v] = 1
            cost += w
            chosen.append(i)
            for entry in adj[v]:
                if not visited[entry[2]]:
                    heappush(heap, entry)
    return {'cost': cost, 'edge_ids': chosen, 'components': components}


def _finish_order(adj, check_cycles=False):
    state = bytearray(len(adj))
    order = []
    for root in range(len(adj)):
        if state[root]:
            continue
        state[root] = 1
        stack = [(root, 0)]
        while stack:
            v, pos = stack[-1]
            if pos == len(adj[v]):
                stack.pop()
                state[v] = 2
                order.append(v)
                continue
            u = adj[v][pos]
            stack[-1] = (v, pos + 1)
            if state[u] == 1 and check_cycles:
                return None
            if state[u] == 0:
                state[u] = 1
                stack.append((u, 0))
    return order


def scc(request):
    n, edges = request['n'], request['edges']
    adj, reverse = [[] for _ in range(n)], [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        reverse[v].append(u)
    labels = [-1] * n
    count = 0
    for root in reversed(_finish_order(adj)):
        if labels[root] != -1:
            continue
        labels[root] = count
        stack = [root]
        while stack:
            v = stack.pop()
            for u in reverse[v]:
                if labels[u] == -1:
                    labels[u] = count
                    stack.append(u)
        count += 1
    pairs = {(labels[u], labels[v]) for u, v in edges if labels[u] != labels[v]}
    return {'component': labels, 'condensation': [list(pair) for pair in pairs]}


def topo(request):
    adj = [[] for _ in range(request['n'])]
    for u, v in request['edges']:
        adj[u].append(v)
    order = _finish_order(adj, True)
    return {'acyclic': order is not None, 'order': order[::-1] if order is not None else []}


def dag(request):
    n, edges, source = request['n'], request['edges'], request['source']
    adj, outgoing = [[] for _ in range(n)], [[] for _ in range(n)]
    for i, (u, v, w) in enumerate(edges):
        adj[u].append(v)
        outgoing[u].append(i)
    order = _finish_order(adj, True)
    if order is None:
        return {'acyclic': False, 'distance': [], 'parent_edge': []}
    distance, parent = [None] * n, [-1] * n
    distance[source] = 0
    for u in reversed(order):
        if distance[u] is None:
            continue
        for i in outgoing[u]:
            _, v, w = edges[i]
            candidate = distance[u] + w
            if distance[v] is None or candidate < distance[v]:
                distance[v] = candidate
                parent[v] = i
    return {'acyclic': True, 'distance': distance, 'parent_edge': parent}


def reconstruct_route(edges, parent_edge, source, target):
    if target == source:
        return [source]
    if parent_edge[target] == -1:
        return []
    route = [target]
    while target != source:
        i = parent_edge[target]
        if i < 0 or edges[i][1] != target or len(route) > len(parent_edge):
            raise ValueError('Invalid parent witness')
        target = edges[i][0]
        route.append(target)
    route.reverse()
    return route
