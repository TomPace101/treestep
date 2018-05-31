# Overall Process

1) Unrotate/mirror
2) Generate children
3) Rotate/mirror to get standard form
4) Sort
5) Filter
and repeat

# Requirements

- IN PROGRESS: jindex table (need to output to YAML file)
- rotation/mirror table
    For all 7 non-trivial transformations, a sequence
    of the source indices,
    so that transformed states can be generated with a list comprehension.
    Or, maybe we just need two such sequences: one for rotation, one for mirroring,
    and apply transformations sequentially:
      - 1 = mirror 0
      - 2 = rotate 0
      - 3 = mirror 2
      - 4 = rotate 2
      - 5 = mirror 4
      - 6 = rotate 4
      - 7 = mirror 6
- starting state bytes