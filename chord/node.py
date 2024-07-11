import duckdb
import click
from rich.console import Console
from rich.table import Table
from rich.markdown import Markdown
import pandas as pd

console = Console()

class ChordNode:
  def __init__(self, nodeID, nodeSet, nodePosition, nBits=5):
        self.nBits = nBits # key space m
        self.MAXPROC = 2**self.nBits # key space m=5 bits => 2^5 = 32
        self.nodeSet = nodeSet # finger table ⊆ node set ⊆ {x | x \in [0,MAXPROC-1]}
        self.nodeID = nodeID  # random in key space or provided by a central node
        self.FT = [0] * (self.nBits+2) # finger table
        self.nodePosition = nodePosition # position in the 0 <= ring < len(nodeSet)
        self.db = duckdb.connect(database=':memory:')
        self.db.execute('create table store(key int, value text)')


  def heartbeat(self):
        while True:
            self.__pingNodeSet()
            self.__recomputeFingerTable()
            yield (self.nodeID, self.nodeSet, [node.nodeID for node in self.FT])

  def __pingNodeSet(self):
        pass

  def __succNode(self, key):
    if (key <= self.nodeSet[0] or
        key > self.nodeSet[len(self.nodeSet)-1]): # key is in segment for which
      return self.nodeSet[0]                      # this node is responsible
    for i in range(1,len(self.nodeSet)):
      if (key <= self.nodeSet[i]):                # key is in segment for which 
        return self.nodeSet[i]                    # node (i+1) may be responsible

  def __eq__(self, other):
    return (self.nodeID == other)

  def __lt__(self, other):
    return (self.nodeID < other)

  def __le__(self, other):
    return (self.nodeID <= other)

  def __ge__(self, other):
    return (self.nodeID >= other)

  def __gt__(self, other):
    return (self.nodeID >= other)

  def __add__(self, other):
    return (self.nodeID + other)

  def __sub__(self, other):
    return (self.nodeID - other)

  def __finger(self, i):
    return self.__succNode((self.nodeID + pow(2,i-1)) % self.MAXPROC) # succ(p+2^(i-1))

  def __recomputeFingerTable(self):
    self.FT[0] = self.nodeSet[self.nodePosition-1] # Predecessor.
    self.FT[1:] = [self.__finger(i) for i in range(1,self.nBits+1)]  # Successors 
    self.FT.append(self)                                      # This node 

  def __inbetween(self, key, left, right):
    key = key % self.MAXPROC
    return (key >= left and key < right) or (key >= left and right <= self.nodeSet[0]+1)

  def __localSuccNode(self, key):
    if self.__inbetween(key, self.FT[0]+1, self.nodeID+1):  # key in (pred,self]
      return self                                           # this node is responsible
    elif self.__inbetween(key, self.nodeID+1, self.FT[1]):  # key in (self,FT[1]]
      console.print(f"\t The succesor {self.FT[1]} is responsible for the key {key}.")
      return self.FT[1]                                     # successor responsible
    for i in range(1, self.nBits+1):                        # go through rest of FT
      if self.__inbetween(key, self.FT[i], self.FT[(i+1)]): # key in [FT[i],FT[i+1])
        console.print(f"\t The node {self.FT[i]} is responsible for the key {key}.")
        return self.FT[i]                                   # FT[i] is responsible
    maximum = max(self.FT)
    if key >= maximum:
       console.print(f"\t The supremum node {maximum} is responsible for the key {key}.")
       return maximum
    minimum = min(self.FT)
    console.print(f"\t The infimum node {minimum} is responsible for the key {key}.")
    return minimum


  def __repr__(self):
        return str(self.nodeID)
  
  def get(self, key, default=None):
        node = self.find_node(key)
        if node is None:
          return default
        result = self.db.execute(f'select * from store where key = {key}')
        return result.fetchall()[0][1]

  def set(self, key, value):
        node = self.find_node(key)
        result = self.db.execute(f"INSERT INTO store (key, value) VALUES ({key}, '{value}')")

  def find_node(self, key):
        current = self
        console.print(current.nodeID)
        for i in range(0, self.MAXPROC):
          next_node = current.__localSuccNode(key)
          if next_node.nodeID == current.nodeID:
            console.print(f"We found the jurisdiction. The node {current.nodeID} is responsible for the key {key}.")
            return next_node
          console.print("->", next_node.nodeID)
          current = next_node
        console.print(f"We've not found the jurisdiction.")
        return None
      

def draw_finger_print(index, rows):
    table = Table(title=f"Node {index}. Finger Table. ")
    for column in ["i", "succ(p+2^(i-1))"]:
        table.add_column(column)
    for i in range(len(rows)):
        table.add_row(*[str(i), str(rows[i])])
    console.print(table)


@click.command()
@click.option('--start', default=1, help='Start node')
@click.option('--key', default=29, help='Goal key')
@click.option('--new-node', '-nn', multiple=True, type=int, default=[])
def path(start, key, new_node):
    node_set = sorted([1,4,9,11,14,18,20,21,28, *new_node])
    console.print("Chrod Algorithm by Carlos Sanchez and López-Nava, I. H")
    console.print(f"Node set: {node_set}")
    indexes = {node: i for i, node in enumerate(node_set)}
    ring = []
    for i in range(len(node_set)):
        ring.append(ChordNode(node_set[i], ring, i))
    heartbeats = [iter(node.heartbeat()) for node in ring]
    click.echo(f"Setup. Loading the Finger Tables...")
    for index in range(len(heartbeats)):
        draw_finger_print(node_set[index], next(heartbeats[index])[2])
    click.echo(f"Finding path from {start} to key {key}")
    try:
        ring[indexes[start%ring[0].MAXPROC]].find_node(key)
    except:
        ring[0].find_node(key)



if __name__ == '__main__':
    path()
