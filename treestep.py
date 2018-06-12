"""Solving Peg Solitaire using the Brute Force approach

Yes, there are more efficient ways. This is just for fun.

This work is licensed under the
Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.
To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/4.0/
or send a letter to Creative Commons, PO Box 1866, Mountain View, CA 94042, USA.

Copyright (C) 2018 Tom Pace - All Rights Reserved"""

# Mapping between indices and 2D locations
boardsize=(7,7)
endrows=[False]*2+[True]*3+[False]*2
midrows=[True]*7
boardshape=[endrows]*2+[midrows]*3+[endrows]*2
locs2d=[]
for i,row in enumerate(boardshape):
  for j,stat in enumerate(row):
    if stat:
      locs2d.append((i,j))
assert len(locs2d)==33

#Mapping between 2D locations and indices
locs1d={}
for idx,loc in enumerate(locs2d):
  locs1d[loc]=idx

# Long names for spaces
rownames=['A','B','C','D','E','F','G']
colnames=[str(i+1) for i in range(boardsize[1])]
names=[rownames[i]+colnames[j] for i,j in locs2d]

# Locate adjacent holes from index and direction
deltas={'u':(-1,0),'d':(1,0),'l':(0,-1),'r':(0,1)}

def point_to_point(start,direction):
  """Locate adjacent holes from index and direction
  Arguments:
    - start = index of the starting hole
    - direction = string specifying direction: u,d,l,r
  Returns:
    - idx = index of the requested hole, or None if off board"""
  i,j=locs2d[start]
  di,dj=deltas[direction]
  newloc=(i+di,j+dj)
  return locs1d.get(newloc,None)

# Listing of all valid moves

revdir={'u':'d','d':'u','l':'r','r':'l'}

#This may seem a bit weird, but it's to match the old order
moves_forward=[]
names_forward=[]
names_backward=[]
for middle,loc in enumerate(locs2d):
  for direc in ['u','r']:
    ender = point_to_point(middle,direc)
    if ender is not None:
      revd = revdir[direc]
      starter = point_to_point(middle,revd)
      if starter is not None:
        moves_forward.append((starter,middle,ender))
        names_forward.append(names[starter]+direc)
        names_backward.append(names[ender]+revd)
assert len(moves_forward)==38

moves_backward=[]
for a,b,c in moves_forward:
  moves_backward.append((c,b,a))

moves_all=moves_forward+moves_backward
names_all=names_forward+names_backward

# Transformation vectors
r0n=[idx for idx,loc in enumerate(locs2d)]

r1n=[]
for idx, loc in enumerate(locs2d):
  src=(loc[1],6-loc[0])
  r1n.append(locs2d.index(src))

r2n=[r1n[idx] for idx in r1n]
r3n=[r2n[idx] for idx in r1n]

r0f=[]
for idx, loc in enumerate(locs2d):
  src=(loc[0],6-loc[1])
  r0f.append(locs2d.index(src))

r1f=[r1n[idx] for idx in r0f]
r2f=[r2n[idx] for idx in r0f]
r3f=[r3n[idx] for idx in r0f]

transtable=[r0n,r1n,r2n,r3n,r0f,r1f,r2f,r3f]
transnames=['R0n','R1n','R2n','R3n','R0f','R1f','R2f','R3f']
revtrans=[0,3,2,1,4,5,6,7]

# Information for compression
names_everything=names_all+transnames
assert len(names_everything)==84

history_chars=[]
for ci,nm in enumerate(names_everything):
    abbr=bytes(bytearray((33+ci,)))
    history_chars.append(abbr)


# Board class

class ExpandedBoard:
  """An uncompressed board
  
  Instance Attributes:
  
    - pegs = list of boolean values for each peg: True for filled space, False for empty
    - history = list of indices (hindex) in the complete moves and transformations to generate this board
  
  Class Attributes:
  
    - jumps = table of moves as list of tuples, each tuple a triple of peg indices: (start, middle, end)
        The list includes moves in both the forward and backward directions.
        Indices to this table are referred to as `jindex` values.
    - numjumps = len(jumps)
    - transforms = table of transformations (rotations and mirroring) as a list of lists of peg indices,
        ordered to produce the new state from the old by list comprehension
        Indices to this table are referred to as `tindex` values.
    - numtransforms = len(transforms)
    - reverse_transforms = tindex values to reverse the transformations done by those in transforms
        That is, transforms[reverse_transforms[tindex]] will undo transforms[tindex].
    - boardshape = shape of the board, for display purposes, as list of lists of booleans, True for spaces, False for non-spaces
    - history_names = table to translate history to human readable form
        Indices to this table are reffered to as `hindex` values.
    - history_bytes = table of bytes to represent compressed history information"""

  jumps=moves_all
  numjumps=len(jumps)
  transforms=transtable
  numtransforms=len(transforms)
  reverse_transforms=revtrans
  boardshape=boardshape
  history_names=names_everything
  history_bytes=history_chars

  def __init__(self,pegs,history):
    self.pegs=pegs
    self.history=history

  def move_applies(self,jindex):
    """True if the given move applies to the board

    Arguments:

      - jindex = integer index of entry in class attribute ``jumps``"""
    st,md,en=self.jumps[jindex]
    return self.pegs[st] and self.pegs[md] and not self.pegs[en]

  def apply_move(self,jindex):
    """Create the child indicated.
    
    Arguments:
    
      - jindex = integer index of entry in class attribute ``jumps`` specifying which jump to perform
    
    Returns:
    
      - an ExpandedBoard instance for the resulting board
    
    This function does not check that the move is valid.
    See `move_applies` for that."""
    move=self.jumps[jindex]
    return ExpandedBoard([p if not i in move else not p for i,p in enumerate(self.pegs)], self.history+[jindex])

  def countchildren(self):
    """Count the number of children of this board
    
    No arguments.
    
    Returns the number as an integer."""
    count=0
    for mov in self.jumps:
      if move_applies(board,mov):
        count += 1
    return count

  def apply_transform(self,tindex):
    """Apply the requested transform to the board
    
    Arguments:
    
      - tindex = integer index of entry in class attribute ``transforms`` specifying which transform to perform"""
    return ExpandedBoard([self.pegs[idx] for idx in self.transforms[tindex]], self.history+[tindex+self.numjumps])

  def unstandardize(self):
    """Undo the last transform applied to the board
    
    No arguments.
    No return value.
    The board is altered."""
    tindex_fwd=self.history.pop()
    tindex_rev=reverse_transforms[tindex_fwd-self.numjumps]
    self.pegs=[self.pegs[idx] for idx in self.transforms[tindex_rev]]
    return

  def standardize(self):
    """Return the board in standard form
    
    This involves doing all possible transformations to the board,
    and finding the "lowest" one.
    
    No arguments.
    
    Returns the standardized board."""
    for tindex in range(self.numtransforms):
      tboard = self.apply_transform(tindex)
      if tindex==0 or tboard.pegs<minboard.pegs:
        minboard=tboard
    return minboard

  def compress(self):
    """Return the bytes string representing the board"""
    #Peg data
    outarr=bytearray()
    nxtchar=0
    for pos,p in enumerate(self.pegs):
      if p:
        nxtchar+=2**(6-pos%7)
      if (pos+1)%7==0 or pos+1==len(self.pegs):
        outarr.append(128+nxtchar)
        nxtchar=0
    #History data
    for h in self.history:
      outarr.append(history_bytes[h])
    #Done
    return bytes(outarr)

  @classmethod
  def uncompress(cls,bstr):
    """Return a board from a bytes string of compressed data"""
    #Peg data
    pegs=[]
    for c in bstr[:5]:
      dividend=c-128
      divisor=64
      while divisor >= 1 and len(board)<33:
        quotient=dividend//divisor
        pegs.append(quotient>0)
        dividend-=divisor*quotient
        divisor//=2
    #History data
    history=[]
    for c in bstr[5:]:
      history.append(ord(c)-33)
    #Class instance
    return cls(pegs,history)

  def history_string(self):
    """Return a string containing the board history in human readable form"""
    return ",".join([self.history_names[hindex] for hindex in self.history])

  def peg_display_string(self):
    """Return a string suitable for showing what the board looks like"""
    out=""
    nxtdx=0
    for row in self.boardshape:
      for space in row:
        if not space:
          out += " "
        else:
          out += "+" if self.pegs[nxtdx] else "."
          nxtdx += 1
      out+="\n"
    return out
  
  def show(self):
    """Return a string with history and peg display"""
    out=self.history_string()
    out+="\n"
    out+=self.peg_display_string()
    return out
