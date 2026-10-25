# Analysis

## Run and test

Python 3.12+ is needed. No extra packages or build step are needed. Run from the project folder:

```sh
python tools/run.py --setup
python tools/run.py --check
python tests/verify.py
python tools/run.py --input tests/my_cases.jsonl
python src/Python/main.py < tests/my_cases.jsonl
```

The program reads and writes one JSON object per line. Ping is kept. Each call creates new data, so requests do not share state. Edge IDs are original input positions. Python integers support large sums. DFS uses a stack with the next neighbor position, so deep graphs do not cause recursion errors or repeated scans.

Here n is the number of vertices, m is the number of edges and q is the number of unions. Memory bounds include results.

## DSU

Steps: start with one set per vertex. Find uses path compression. Union joins the smaller set to the larger set. After each operation, save the component count and largest size.

Invariant: each set is exactly one current connected component, and its root stores the correct size. Joining two different roots merges two components. This keeps the invariant and gives correct states after every operation.

Cases: self unions and repeated unions change nothing. For n=0, states is empty and the largest size starts at 0.

Time: O(n + q alpha(n)) amortized, where alpha is the inverse Ackermann function. Memory: O(n+q).

## Kruskal

Steps: sort edge IDs by weight. Use DSU and select an edge only if its endpoints are in different sets.

Invariant: selected edges form a forest that can be part of a minimum spanning forest. A selected edge is a cheapest edge across a cut between current sets. The cut property makes this choice safe. At the end every input component is connected, so the forest is minimum and has n-components edges.

Cases: loops are skipped. Parallel edges, equal weights and negative weights work normally. Isolates count as components. For n=0, cost and components are 0 and edge_ids is empty.

Time: O(n + m log(m+1)). Memory: O(n+m).

## Prim

Steps: build undirected adjacency lists. Start at an unvisited vertex and put its outgoing edges in a minimum heap. Take the cheapest edge to an unvisited vertex. Skip old entries. Restart at each remaining unvisited vertex.

Invariant: the heap contains all edges from visited to unvisited vertices, and the chosen tree can be part of a minimum tree. The cheapest crossing edge is safe by the cut property. Every accepted edge adds one new vertex, so it cannot make a cycle. Restarts give a minimum forest for all components.

Cases: isolates start separate components. Loops are skipped. Parallel edges, ties and negative weights are allowed. An empty graph returns zero cost, zero components and no edges.

Time: O(n + m log(m+1)) with the lazy heap. Memory: O(n+m).

## Kosaraju SCC

Steps: build the graph and its transpose. First DFS saves vertices when they finish. Run DFS on the transpose in reverse finish order and give each new group a label. Use a set to remove duplicate edges between different labels.

Invariant: each second-pass search finds one whole SCC. If one SCC has an edge to another, the first has a larger maximum finish time. The next unassigned SCC in reverse finish order therefore cannot reach another unassigned SCC in the transpose. Each search labels exactly one SCC. The pair set then gives exactly the condensation edges.

Cases: isolates have separate labels. Loops and repeated edges are allowed. Internal edges are excluded from condensation. Empty input returns two empty lists.

Expected time: O(n+m), using a hash set. Memory: O(n+m).

## Topological sort

Steps: use DFS states 0 (new), 1 (active) and 2 (finished). An edge to an active vertex means a cycle. Check every component. If there is no cycle, reverse the finish order.

Invariant: active vertices form the current DFS path. An edge back to this path closes a cycle. Every directed cycle causes such an edge during DFS. Without cycles, each edge's destination finishes before its source, so reversing the order puts the source first.

Cases: an edge to a finished vertex is allowed. A loop or a disconnected cycle returns false and an empty order. Isolates are included. An empty graph is acyclic.

Time: O(n+m). Memory: O(n+m).

## DAG shortest paths

Steps: check the whole graph for cycles. If acyclic, set source distance to 0 and other distances to None. Process vertices in topological order. Relax outgoing edges only from reachable vertices and save the original edge ID on improvement.

Invariant: when a vertex is processed, its distance is already shortest because all its predecessors were processed first. Relaxation checks every possible last edge of a path. Thus all distances are correct. Parent edges achieve these distances and go backward in topological order to the source.

Cases: any cycle, even unreachable from the source, returns false and two empty arrays. Negative weights and parallel edges are allowed. Equal paths may use either valid parent. Unreachable vertices keep None (JSON null) and parent -1. Source keeps distance 0 and parent -1. A one-vertex graph without edges works.

Time: O(n+m). Memory: O(n+m).

## Route helper

`reconstruct_route(edges, parent_edge, source, target)` follows parent edges backward and reverses the route. Source returns [source]. An unreachable target returns []. For a route of L vertices, time and result memory are O(L). Use it with a valid acyclic DAG result.

Actual test data:

```python
edges = [[0,1,3], [0,1,3], [0,2,8], [1,2,-7], [2,3,4]]
parent = [-1,0,3,4,-1]
reconstruct_route(edges, parent, 0, 3)  # [0,1,2,3]
reconstruct_route(edges, parent, 0, 0)  # [0]
reconstruct_route(edges, parent, 0, 4)  # []
reconstruct_route(edges, parent, 0, 1)  # [0,1]
```

The route to 3 uses IDs [0,3,4] and costs 3-7+4=0. The source route costs 0. Target 4 is unreachable. The route to 1 uses ID 0 and costs 3; parallel edge ID 1 is also valid. Tests check edge direction and total weight. Results are in tests/routes.json.

## Test results

Setup passed. All 36 public cases and their repeated-batch state reset check passed. Own tests passed 132 cases and 264 mixed requests in one process.

Inputs, expected answers, actual outputs and reasons are in tests/my_cases.jsonl, expected.jsonl, actual.jsonl and case_reasons.json. Non-unique answers are checked by validity, not exact order or labels. Small forest tests try every possible edge subset to find the true minimum. They use 60 random graphs with seed 31025 and check both methods.

Tests cover empty graphs, isolates, disconnected graphs, repeated and self unions, loops, parallel edges, equal answers, negative weights, large sums, unreachable vertices and unreachable cycles. verify.py also prints checks that accept alternative valid forests, SCC labels, topological orders and DAG parents, and reject invalid answers.

Full-limit tests use n=100000 and 250000 edges or operations for each method. The generator in verify.py creates a full chain and repeated shortcuts, or repeated self unions for DSU. Expected results:

- DSU: one component of size 100000.
- Forests: 99999 edges of weight 10^9, total 99999000000000.
- SCC: 100000 separate components and 100000 distinct condensation edges.
- Topological sort: order 0 through 99999.
- DAG: distance[i] = -i*10^9; last distance -99999000000000 and route length 100000.

The chain also checks deep DFS. Large inputs are regenerated; results are saved in tests/scale_results.json.

## Kruskal and Prim timing

Command: `python tests/verify.py`. For each size, the generator makes a spanning chain, then adds random endpoint pairs. Weights are random integers from -10^9 to 10^9. Both methods use the same graph. Before timing, tests check forest validity and equal costs and component counts.

Environment: Python 3.12.14, Windows 11 build 26200, Intel64 Family 6 Model 142 Stepping 12, 8 logical CPUs. Timer: time.perf_counter. Each method has one extra untimed warm-up per size after correctness calls, then three timed runs. Timing includes the algorithm, graph/DSU building and result building. It excludes input generation, input parsing, IO, checks and compilation. Full results are in tests/benchmark_results.json. Times below are seconds.

| n | m | Seed | Method | Run 1 | Run 2 | Run 3 | Median |
|---|---|---|---|---|---|---|---|
| 1000 | 2500 | 32025 | Kruskal | 0.005112 | 0.005304 | 0.003923 | 0.005112 |
| 1000 | 2500 | 32025 | Prim | 0.008890 | 0.005471 | 0.006902 | 0.006902 |
| 10000 | 25000 | 41025 | Kruskal | 0.301257 | 0.182379 | 0.143375 | 0.182379 |
| 10000 | 25000 | 41025 | Prim | 0.131270 | 0.134915 | 0.133201 | 0.133201 |
| 100000 | 250000 | 131025 | Kruskal | 0.682285 | 0.723423 | 0.717000 | 0.717000 |
| 100000 | 250000 | 131025 | Prim | 1.664459 | 1.683831 | 1.858585 | 1.683831 |

Kruskal was faster at the smallest and largest sizes. Prim was faster at the middle size. Built-in sorting helps Kruskal; Prim does more adjacency and heap work. Both have O(n + m log(m+1)) time. These are only three runs per method on one machine and one graph type. System load can change times, so the results do not show that one method is always faster.

## Sources

The supplied assignment PDF, starter code and public validator were used for requirements and checks.

