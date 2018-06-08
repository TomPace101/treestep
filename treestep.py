
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
  return indices.get(newloc,None)

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

# Board class

class ExpandedBoard:
  """An uncompressed board
  
  Instance Attributes:
  
    - pegs = list of boolean values for each peg: True for filled space, False for empty
    - history = list of indices in the complete moves and transformations to generate this board
  
  Class Attributes:
  
    - jumps = table of moves as list of tuples, each tuple a triple of peg indices: (start, middle, end)
        The list includes moves in both the forward and backward directions.
    - numjumps = len(jumps)
    - transforms = table of transformations (rotations and mirroring) as a list of lists of peg indices,
        ordered to produce the new state from the old by list comprehension
    - numtransforms = len(transforms)
    - boardshape = shape of the board, for display purposes, as list of lists of booleans, True for spaces, False for non-spaces"""

  jumps=moves_all
  numjumps=len(jumps)
  transforms=transtable
  numtransforms=len(transforms)
  boardshape=boardshape

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

  def apply_transform(self),tindex):
    """Apply the requested transform to the board
    
    Arguments:
    
      - tindex = integer index of entry in class attribute ``transforms`` specifying which transform to perform"""
    return ExpandedBoard([self[idx] for idx in self.transforms[tindex]], self.history+[tindex+self.numjumps])

  def display(self):
    """Return a string suitable for showing what a board looks like"""
    out=""
    nxtdx=0
    for row in self.boardshape:
      for space in row:
        if not space:
          out += " "
        else:
          out += "+" if board[nxtdx] else "."
          nxtdx += 1
      out+="\n"
    return out
  