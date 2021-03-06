This document contains the programmer's notes such as TODO items.

# Current Status

- better interfaces: high-level API, more command line options
- doctests
- document the conversions between jindex, tindex, and hindex
- optional: the whole board inversion thing, with matchup

# Inversion and matchup

The basic idea is that there is a symmetry between
starting at the first move and going forward,
and starting at the last move and going backward.
Forward, you start with one hole and 32 pegs,
and each move adds a hole and takes away a peg.
Backward, you start with one peg and 32 holes,
and each move adds a peg and takes away a hole.
They are the same moves other than that "inversion".
So if you can get to move 16, then invert all those boards,
you could generate a set of boards for move 17 that are only reachable from the goal state.
Versus if you continue going forward, a lot of the boards you have can't get to the goal state.
So you'd still need to step forward to move 17,
then find a match between one (or more) of the boards and an inverted board from move 16.
Of course, inverting the pegs and holes is easy.
The tricky part is inverting the move history.
You need to develop a table of how to do that.

# Overall Process

We have a list of board bytestrings (maybe even in a file).
The desired outcome of that is a filtered list of board bytestrings for the next move.

So the process is like this:
1) For each board:
  a) uncompress
  b) unstandardize
  c) generate children, and for each child:
    i) collect/update statistics
    ii) standardize
    iii) compress
    iv) put the resulting bytestring in the new list
2) Sort the new list of bytestrings
3) Filter the new list of bytestrings
4) Produce the inverted list from the forward list
5) Do a search through the forward and reverse lists, to look for a match

The goal is to keep the number of uncompressed boards at any time to the bare minimum.
Towards that end, maybe we want to create an Iterator:
https://docs.python.org/3/tutorial/classes.html#iterators

The real question is this:
try to process in-memory, or use files.
Perhaps we can create an interface for both.

BoardIterator:
Can yield boards, but also we need a way to add boards to it.
In preparation for using files, we should keep the interface restricted to
"read" or "write" mode.
Not really sure what the benefit of this class is over just some functions.

So I just decided to go straight to using files.

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

# Combine sorting and filtering?
For that matter, the process could also be combined with board generation.
This would reduce the number of boards that must be stored,
but at the cost of doing more comparisons for filtering.
So it's a time-memory tradeoff.
For now, we won't make this trade.

