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
- starting state bytes

# Rotations and Mirroring

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
I guess it would be better to have all the transformations worked out so they can be applied more quickly.

How do you undo a transformation?
Mirroring undoes itself.
For rotation,
you could either derive the rotation in the opposite direction,
or apply the rotation again until the total number of times is 4.

Again, for purposes of speed, we should probably work out all reverse rotations as well.
But it's the same set of transformations.
You just have to know which transformation undoes each other one.
I worked it out on a piece of paper.
Most of them undo themselves.
The only exception is R1n and R3n, which undo each other.

