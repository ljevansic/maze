import sqlite3
import sys

# Constants used in this program:
EMPTY = ' '
START = 'S'
EXIT = 'E'
PATH = '.'

def load_maze_from_db(seed):
    conn = sqlite3.connect('mazes.db')
    cursor = conn.cursor()
    cursor.execute('SELECT maze FROM mazes WHERE seed = ?', (seed,))
    result = cursor.fetchone()
    conn.close()
    if result is None:
        raise ValueError(f"No maze found for seed {seed}")
    maze_text = result[0]
    return maze_text.split('\n')

# Get the seed from command line argument
if len(sys.argv) != 2:
    print("Usage: python simple_solver.py <seed>")
    sys.exit(1)

seed = int(sys.argv[1])
MAZE = load_maze_from_db(seed)

# Get the height and width of the maze:
HEIGHT = len(MAZE)
WIDTH = 0
for row in MAZE: # Set WIDTH to the widest row's width.
    if len(row) > WIDTH:
        WIDTH = len(row)
# Make each row in the maze a list as wide as the WIDTH:
for i in range(len(MAZE)):
    MAZE[i] = list(MAZE[i])
    if len(MAZE[i]) != WIDTH:
        MAZE[i] = [EMPTY] * WIDTH # Make this a blank row.

steps = 0  # Counter for the number of steps

def printMaze(maze):
    for y in range(HEIGHT):
        # Print each row.
        for x in range(WIDTH):
            # Print each column in this row.
            print(maze[y][x], end='')
        print() # Print a newline at the end of the row.
    print()

def findStart(maze):
    for x in range(WIDTH):
        for y in range(HEIGHT):
            if maze[y][x] == START:
                return (x, y) # Return the starting coordinates.

def solveMaze(maze, x=None, y=None, visited=None):
    global steps
    if x == None or y == None:
        x, y = findStart(maze)
        maze[y][x] = EMPTY # Get rid of the 'S' from the maze.
    if visited == None:
        visited = [] # Create a new list of visited points.

    if maze[y][x] == EXIT:
         return True # Found the exit, return True.

    maze[y][x] = PATH # Mark the path in the maze.
    steps += 1  # Count this move
    visited.append(str(x) + ',' + str(y))
    # printMaze(maze) # Uncomment to view each forward step.

    # Explore the north neighboring point:
    if y + 1 < HEIGHT and maze[y + 1][x] in (EMPTY, EXIT) and \
    str(x) + ',' + str(y + 1) not in visited:
        # RECURSIVE CASE
        if solveMaze(maze, x, y + 1, visited):
            return True # BASE CASE
    # Explore the south neighboring point:
    if y - 1 >= 0 and maze[y - 1][x] in (EMPTY, EXIT) and \
    str(x) + ',' + str(y - 1) not in visited:
        # RECURSIVE CASE
        if solveMaze(maze, x, y - 1, visited):
            return True # BASE CASE
    # Explore the east neighboring point:
    if x + 1 < WIDTH and maze[y][x + 1] in (EMPTY, EXIT) and \
    str(x + 1) + ',' + str(y) not in visited:
        # RECURSIVE CASE
        if solveMaze(maze, x + 1, y, visited):
            return True # BASE CASE
    # Explore the west neighboring point:
    if x - 1 >= 0 and maze[y][x - 1] in (EMPTY, EXIT) and \
    str(x - 1) + ',' + str(y) not in visited:
        # RECURSIVE CASE
        if solveMaze(maze, x - 1, y, visited):
            return True # BASE CASE

    steps += 1  # Count backtracking move
    maze[y][x] = EMPTY # Reset the empty space.
    #printMaze(maze) # Uncomment to view each backtrack step.

    return False # BASE CASE

printMaze(MAZE)  # Display the original maze.
solveMaze(MAZE)
printMaze(MAZE)  # Display the solved maze.
print(f"Total steps: {steps}")