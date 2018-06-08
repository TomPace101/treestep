# Current Status

__TODO__
- document the distinction between jindex, tindex, and hindex, and their mathematical relationships
- method to undo the last transformation to a board
- method to place a board in standard form
- method to return human-readable string from board history
- method to compress a board into a bytes string
- classmethod to expand a bytes string into a board
- method, or whatever else, to collect all child boards (see discussion below)
- something for sorting and filtering (see below)
- the whole board inversion thing, with matchup

# Overall Process

1) Unrotate/mirror
2) Generate children
3) Rotate/mirror to get standard form
4) Sort
5) Filter
and repeat

So, we have a list of board bytestrings (maybe even in a file).
The desired outcome of that is a filtered list of board bytestrings for the next move.

So the process is really like this:
1) For each board:
  a) uncompress
  b) unstandardize
  c) generate children, and for each child:
    i) standardize
    ii) compress
    ii) put the resulting bytestring in the new list
2) Sort the new list of bytestrings
3) Filter the new list of bytestrings
4) Produce the inverted list from the forward list
5) Do a search through the forward and reverse lists, to look for a match

The goal is to keep the number of uncompressed boards at any time to the bare minimum.

# Requirements

- DONE: jindex table (need to output to YAML file)
- DONE: rotation/mirror table
- ALMOST: starting state bytes

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

