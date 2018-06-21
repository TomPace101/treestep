"""Solving Peg Solitaire using a Brute Force approach

There are probably more efficient ways. This is just for fun.

"Brute Force" in this case means the following:

  - The types of moves considered are single jumps, not "packages" of jumps.
  - There is no heuristic used to prune the search tree: all possible moves are considered.

The approach is to generate all possible valid board configurations ("boards", for short)
throughout all the steps of the puzzle.
Rotations and reflections of a given board are considered equivalent.
For each possible board, there may be more than one set of valid moves that
results in that board, but only one such "history" is retained for each board.

This work is licensed under the
Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.
To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/4.0/
or send a letter to Creative Commons, PO Box 1866, Mountain View, CA 94042, USA.

Copyright (C) 2018 Tom Pace - All Rights Reserved"""

#Standard Library
import argparse
import os
import datetime

# Constants
BUFFER_SIZE=1024**3//2//256 #consume half a gigabyte (gibibyte?) with 256 files (half the RAM of a raspberry pi 3)
RADIX_TMPL="tmp/byte_%d_%03d.boards"
MOVE_TMPL="data/move_%02d.boards"
STATS_TMPL="stats/move_%02d.yaml"
LOG_TMPL="logs/from_%02d.txt"
BOOTSTRAP_LOG="logs/bootstrap.txt"
TIMESTAMP_FMT="%a %d-%b-%Y %I:%M:%S.%f %p"
STATS_DATA_TMPL="""#Results for step forward from move {0} to move {1}
inboards: {2}
inboards_childcounts:
{3}
outboards_unfil: {4}
outboards_fil: {5}
runtime: {6}
"""

# Classes for stats recording and logging
class Logger:
  def __init__(self,outfpath=None):
    self.start=datetime.datetime.now()
    self.last=self.start
    if outfpath is None:
      self.fp = None
    else:
      self.open(outfpath)
  def open(self,outfpath):
    self.fp=open(outfpath,'w')
  def close(self):
    if self.fp is not None:
      self.fp.close()
  def log(self,msg):
    msgtime=datetime.datetime.now()
    tstmp=msgtime.strftime(TIMESTAMP_FMT)
    lastdelta=msgtime-self.last
    rundelta=msgtime-self.start
    outstr="+%f %s [%s] %s"%(lastdelta.total_seconds(),tstmp,str(rundelta),msg)
    print(outstr)
    if self.fp is not None:
      self.fp.write(outstr+'\n')
    self.last=msgtime

logger=Logger()

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
    # abbr=bytes(bytearray((33+ci,)))
    # history_chars.append(abbr)
    history_chars.append(33+ci)


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

  def duplicate(self,other):
    """Turn this board into a duplicate of the other
    
    Arguments:
    
      - other = the board to be duplicated
      
    No return value.
    This board is modified."""
    self.pegs=other.pegs
    self.history=other.history

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
    for jindex in range(self.numjumps):
      if self.move_applies(jindex):
        count += 1
    return count

  def iter_children(self):
    """Generator teturn all the children of this board, as ExpandedBoard instances
    
    No arguments.
    Yields one child each pass."""
    for jindex in range(self.numjumps):
      if self.move_applies(jindex):
        yield self.apply_move(jindex)

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
    tindex_rev=self.reverse_transforms[tindex_fwd-self.numjumps]
    self.pegs=[self.pegs[idx] for idx in self.transforms[tindex_rev]]
    return

  def find_standard_form(self):
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

  def standardize(self):
    """Put the board in standard form

    The result from find_standard_form replaces this board.
    
    No arguments.
    No return value.
    The board is altered."""
    board=self.find_standard_form()
    self.duplicate(board)

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
      outarr.append(self.history_bytes[h])
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
      while divisor >= 1 and len(pegs)<33:
        quotient=dividend//divisor
        pegs.append(quotient>0)
        dividend-=divisor*quotient
        divisor//=2
    #History data
    history=[]
    for c in bstr[5:]:
      if c>32: #Ignore newlines, etc.
        history.append(c-33)
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

# The starting board, and its bytes string
startpegs=[True]*16+[False]+[True]*16
startboard=ExpandedBoard(startpegs,[])
startbytesboard=ExpandedBoard(startpegs,[])
startbytesboard.standardize()
startbytes=startbytesboard.compress()

# Processing functions

class PassFiles(dict):
  """A dictionary of opened input/output files for the radix sort
  
  The dictionary is of the form {byte value as integer: file handle}"""
  @classmethod
  def open_all(cls,position,mode):
    """Open the 128 files for the radix sort
    
    Arguments:
    
      - position = the radix position as integer, for use in the filenames
      - mode = 'rb' or 'wb', mode to open the files in"""
    logger.log("Opening passfiles for position %d mode %s."%(position,mode))
    self=cls()
    self.position=position
    for k in range(128,256):
      partfname=RADIX_TMPL%(position,k)
      self[k]=open(partfname,mode,BUFFER_SIZE)
    logger.log("Passfiles open.")
    return self

  def close_all(self):
    """Close the opened pass files
    
    No arguments.
    No return value.
    The files are closed."""
    logger.log("Closing passfiles for position %d."%self.position)
    for fh in self.values():
      fh.close()
    return
  
  def delete_file(self,k):
    """Close and remove the file the requested byte on this pass.
    
    Arguments:
    
      - k = integer 128-256 identifying the file to be removed
      
    No return value."""
    self[k].close()
    os.remove(RADIX_TMPL%(self.position,k))
    return

def bootstrap():
  """Create the move 0 input file
  
  No arguments.
  No return value."""
  logger.log("Bootstrapping.")
  outfpath=MOVE_TMPL%0
  with open(outfpath,'wb') as fp:
    fp.write(startbytes+b'\n')
  return

def forward(startmove):
  """Generate boards for the next move, and sort, and filter
  
  Note that this can't create the file for move 0.
  See `bootstrap()` for that.
  
  Arguments:
  
    - startmove = integer for move number to start from (0 for the beginning)
    - infpath = path to input boards file
    - outfpath = path to output boards file
  
  No return value."""
  logger.log("Starting step forward.")
  #Initialize stats vars
  inboards=0
  outboards_unfil=0
  outboards_fil=0
  inboards_childcounts={}
  #Input and output file paths
  infpath=MOVE_TMPL%startmove
  outfpath=MOVE_TMPL%(startmove+1)
  #Generating pass
  position=4
  logger.log("Generating pass (position %d)"%position)
  run_start=datetime.datetime.now()
  infp=open(infpath,'rb',BUFFER_SIZE)
  passdict_out=PassFiles.open_all(position,'wb')
  for bstr in infp: #for each input board
    inboards += 1
    board = ExpandedBoard.uncompress(bstr)
    board.unstandardize()
    #for each child board
    num_children=0
    for child in board.iter_children():
      num_children+=1
      outboards_unfil += 1
      #standardize, compress, and put in proper bin
      child.standardize()
      outstr=child.compress()+b'\n'
      passdict_out[outstr[position]].write(outstr)
    if not num_children in inboards_childcounts.keys():
      inboards_childcounts[num_children]=1
    else:
      inboards_childcounts[num_children]+=1
  infp.close()
  passdict_out.close_all()
  #Remaining passes
  while position>0:
    logger.log("Starting pass for position %d."%position)
    passdict_in=PassFiles.open_all(position,'rb')
    position-=1
    passdict_out=PassFiles.open_all(position,'wb')
    for k in range(128,256):
      for bstr in passdict_in[k]:
        passdict_out[bstr[position]].write(bstr)
      passdict_in.delete_file(k)
    passdict_out.close_all()
  #Filtering pass
  logger.log("Starting filtering pass.")
  passdict_in=PassFiles.open_all(position,'rb')
  outfp=open(outfpath,'wb',BUFFER_SIZE)
  lastdat=''
  for k in range(128,256):
    for bstr in passdict_in[k]:
      if bstr[:5]!=lastdat:
        outboards_fil+=1
        outfp.write(bstr)
        lastdat=bstr[:5]
    passdict_in.delete_file(k)
  outfp.close()
  run_end=datetime.datetime.now()
  runtime=(run_end-run_start).total_seconds()
  #Write stats
  logger.log("Writing stats.")
  keylist=list(inboards_childcounts.keys())
  keylist.sort()
  childcounts_str="\n".join(["  %d: %d"%(k,inboards_childcounts[k]) for k in keylist])
  statstup=(startmove,startmove+1,inboards,childcounts_str,outboards_unfil,outboards_fil,runtime)
  with open(STATS_TMPL%startmove,'w') as statfp:
    statdata=STATS_DATA_TMPL.format(*statstup)
    statfp.write(statdata)
  logger.log("Step forward complete.")
  return

# Support for command-line usage
if __name__=='__main__':
  parser = argparse.ArgumentParser(description='Advance the puzzle forward one step.')
  parser.add_argument("startmove",type=int,help="Move number to start from, used for calculating input filename. Use -1 to bootstrap.")
  args = parser.parse_args()
  if args.startmove==-1:
    logger.open(BOOTSTRAP_LOG)
    bootstrap()
    logger.close()
  else:
    logger.open(LOG_TMPL%args.startmove)
    forward(args.startmove)
    logger.close()
