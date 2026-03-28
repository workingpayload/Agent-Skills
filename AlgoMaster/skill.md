---
name: algomaster
description: Analyzes algorithmic complexity, selects optimal data structures, and rewrites inefficient solutions using DP, greedy, graph, and divide-and-conquer strategies. Use when a user needs Big-O analysis, a faster algorithm, or help solving a competitive-programming or production performance problem.
---

# AlgoMaster

## Domain Scope

Covers: complexity analysis, data structure selection, algorithm design patterns (DP, greedy, graph algorithms, binary search, divide-and-conquer, two-pointer, sliding window), and production-level optimization.

---

## Workflow

### 1. Understand and Classify the Problem
- State the problem constraints: input size `n`, value ranges, time/memory limits.
- Classify the problem type:
  - **Sequence/array**: sliding window, two-pointer, prefix sums, binary search
  - **Optimization (overlapping subproblems)**: dynamic programming
  - **Optimization (greedy choice property)**: greedy
  - **Graph/tree**: BFS, DFS, Dijkstra, Bellman-Ford, Union-Find, topological sort
  - **String**: KMP, Z-algorithm, Aho-Corasick, suffix arrays
  - **Combinatorics/math**: number theory, modular arithmetic, FFT

### 2. Analyze Existing Complexity
Provide a formal Big-O analysis:
- **Time**: worst case, average case, amortized (for operations on data structures)
- **Space**: auxiliary space, recursion stack depth
- Use recurrence relations for recursive algorithms; apply Master Theorem where applicable.

Example annotation format:
```
current: O(n²) time — nested loop scanning for duplicates
target:  O(n) time, O(n) space — HashSet for seen values
```

### 3. Design the Optimal Solution

**Dynamic Programming checklist**:
1. Define the state: `dp[i]` means...
2. Write the recurrence relation.
3. Identify base cases.
4. Determine traversal order (top-down with memoization vs. bottom-up tabulation).
5. Check if space can be reduced (rolling array, O(1) if only adjacent states needed).

**Graph algorithms selection**:
- Unweighted shortest path → BFS (O(V+E))
- Weighted, non-negative → Dijkstra with min-heap (O((V+E) log V))
- Negative weights, no negative cycles → Bellman-Ford (O(VE))
- All-pairs shortest path → Floyd-Warshall (O(V³))
- Minimum spanning tree → Kruskal (O(E log E)) or Prim (O((V+E) log V))
- Connectivity / cycle detection → Union-Find with path compression + union by rank (O(α(n)) ≈ O(1))

**Data structure selection guide**:
| Need | Structure | Time complexity |
|------|-----------|----------------|
| O(1) lookup by key | HashMap / HashSet | O(1) avg |
| Sorted order + fast insert/delete | TreeMap / SortedSet | O(log n) |
| Frequent min/max queries | Min/Max Heap | O(log n) push/pop |
| Range sum queries | Fenwick Tree (BIT) | O(log n) update/query |
| Range update + query | Segment Tree | O(log n) |
| Prefix queries on strings | Trie | O(L) where L = key length |
| Stack with min/max | Monotonic stack | O(n) total |

### 4. Implement with Clarity
- Name variables after their semantic role, not `i`, `j`, `k` for non-loop indexes.
- Add a comment block before the function:
  ```
  # Approach: [algorithm name]
  # Time: O(...)  Space: O(...)
  # Invariant: [what holds at each iteration]
  ```
- Prefer iterative over recursive when stack depth may exceed ~10,000 (Python default recursion limit).

### 5. Write Test Cases
Cover these categories:
- **Base cases**: empty input, single element, n=1
- **Small cases**: manually verifiable correctness
- **Edge cases**: all-same elements, already sorted/reverse-sorted, max `n`, integer overflow boundaries
- **Stress tests**: compare brute-force output against optimized output on random inputs

### 6. Validate the Optimization
- Measure actual runtime with `timeit` (Python) or `System.nanoTime()` (Java) on representative inputs.
- Profile memory with `tracemalloc` (Python), `valgrind --tool=massif` (C/C++), or VisualVM (JVM).
- For competitive programming: estimate ops/second (~10⁸ simple ops/sec in C++, ~10⁷ in Python) and verify n × complexity fits within time limit.

### 7. Floating-Point Precision
Never use `==` to compare floats. Use epsilon comparison for near-equality, or integer arithmetic for exact results:
```python
# Epsilon comparison
EPSILON = 1e-9
def nearly_equal(a, b): return abs(a - b) < EPSILON

# Exact integer arithmetic for geometry (avoid floats entirely)
# Cross product sign to determine orientation — stays in integers
def cross(o, a, b): return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
```
For financial or competitive-programming problems requiring exact decimals, use Python's `fractions.Fraction` or `decimal.Decimal`. In geometry, prefer integer coordinates scaled by a constant factor over floating-point coordinates.

### 8. HashMap Worst-Case O(n) Warning
HashMap average O(1) lookup degrades to O(n) under adversarial hash collisions. In competitive programming or user-controlled key scenarios:
- Use a **custom hash** with randomization: `hash(key) ^ random_salt` to prevent collision attacks.
- In Java: prefer `TreeMap` (O(log n) guaranteed) when keys are attacker-controlled. Enable JVM hash randomization (`-XX:+UseStringDeduplication`).
- In C++: replace `unordered_map` with a custom hash (e.g., splitmix64) when solving problems that may be designed to exploit standard hash functions.

---

## Output Format

Provide the solution as:
1. **Complexity summary**: Before / After table (time + space)
2. **Annotated code**: with approach comment block and inline invariant notes
3. **Test cases**: at minimum 5, grouped by category
4. **Trade-off note**: when a faster algorithm sacrifices readability or requires a more complex data structure, state the trade-off explicitly

---

## Edge Cases

1. **Integer overflow in intermediate calculations**: When computing products, sums of squares, or coordinates, intermediate values may exceed 32-bit int range. Use 64-bit integers (`long` in Java/C++, Python ints are arbitrary precision). For modular arithmetic problems, apply `(a * b) % MOD` at each multiplication step, not at the end.

2. **Greedy fails when local optimum ≠ global optimum**: Verify greedy correctness via an exchange argument proof — show that swapping any two adjacent elements in a greedy ordering cannot improve the solution. If this cannot be shown, switch to DP. Classic failure case: fractional knapsack is greedy-correct; 0/1 knapsack is not.

3. **Graph problems on disconnected inputs**: BFS/DFS starting from one node will not visit disconnected components. Always iterate over all nodes as potential starting points (outer loop over `V`) and check `visited` status before starting a traversal. Dijkstra returning `∞` for unreachable nodes is expected — handle it explicitly rather than treating `∞` as a valid distance.
