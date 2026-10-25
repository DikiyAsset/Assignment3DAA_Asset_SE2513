# Assignment 3: Graph Algorithms

Python 3.12+

algorithms DSU, Kruskal, Prim, Kosaraju SCC, DFS topological sort and DAG shortest paths. Route reconstruction is included.

## Files

- src/Python/algorithms.py: algorithms
- src/Python/main.py: JSON Lines input and output
- tests/: own tests and results
- tools/: supplied runner and public tests
- ANALYSIS.md: explanations, complexity and benchmark results
- submission.json: selected language

## Run

Run commands from folders
```sh
python tools/run.py --setup
python tools/run.py --check
python tests/verify.py
python tools/run.py --input tests/my_cases.jsonl
```

For interactive input:

```sh
python src/Python/main.py
```

Enter one JSON request per line. Example:

```json
{"task":"ping"}
```
