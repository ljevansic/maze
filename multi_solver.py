#!/usr/bin/env python3
import sqlite3
import sys

# Constants used in this program:
EMPTY = ' '
START = 'S'
EXIT = 'E'
PATH = '.'
WALL = chr(9608)  # '█' character

# Direction constants
NORTH, SOUTH, EAST, WEST = 0, 1, 2, 3
DIRECTIONS = [NORTH, SOUTH, EAST, WEST]
DIR_NAMES = {NORTH: 'N', SOUTH: 'S', EAST: 'E', WEST: 'W'}
DIR_VECTORS = {
    NORTH: (0, -1),
    SOUTH: (0, 1),
    EAST: (1, 0),
    WEST: (-1, 0),
}

def load_maze_from_db(seed, config=1):
    conn = sqlite3.connect('mazes.db')
    cursor = conn.cursor()
    cursor.execute('SELECT maze FROM mazes WHERE seed = ? AND config = ?', (seed, config))
    result = cursor.fetchone()
    conn.close()
    if result is None:
        raise ValueError(f"No maze found for seed {seed}, config {config}")
    maze_text = result[0]
    return maze_text.split('\n')

def get_maze_dimensions(maze):
    """Get the height and width of the maze."""
    height = len(maze)
    width = 0
    for row in maze:
        if len(row) > width:
            width = len(row)
    return width, height

def normalize_maze(maze):
    """Convert maze rows to lists and pad to consistent width."""
    width, height = get_maze_dimensions(maze)
    for i in range(len(maze)):
        maze[i] = list(maze[i])
        if len(maze[i]) != width:
            maze[i] = [EMPTY] * width
    return maze, width, height

def printMaze(maze, width, height):
    """Display the maze."""
    for y in range(height):
        for x in range(width):
            print(maze[y][x], end='')
        print()
    print()

def findStart(maze, width, height):
    """Find the starting position marked with 'S'."""
    for x in range(width):
        for y in range(height):
            if maze[y][x] == START:
                return (x, y)
    return None

def turn_right(direction):
    """Return the direction 90 degrees to the right."""
    right_turn = {NORTH: EAST, EAST: SOUTH, SOUTH: WEST, WEST: NORTH}
    return right_turn[direction]

def turn_left(direction):
    """Return the direction 90 degrees to the left."""
    left_turn = {NORTH: WEST, WEST: SOUTH, SOUTH: EAST, EAST: NORTH}
    return left_turn[direction]

def turn_back(direction):
    """Return the direction 180 degrees (opposite)."""
    back_turn = {NORTH: SOUTH, SOUTH: NORTH, EAST: WEST, WEST: EAST}
    return back_turn[direction]

def get_next_pos(x, y, direction):
    """Get the next position in a given direction."""
    dx, dy = DIR_VECTORS[direction]
    return (x + dx, y + dy)

def is_valid_move(x, y, width, height, maze):
    """Check if a position is valid (empty or exit, not a wall)."""
    if x < 0 or x >= width or y < 0 or y >= height:
        return False
    if maze[y][x] not in (EMPTY, EXIT, PATH):
        return False
    return True

def has_wall_on_right(x, y, direction, width, height, maze):
    """Check if there is a wall immediately to the right of current direction."""
    right_dir = turn_right(direction)
    rx, ry = get_next_pos(x, y, right_dir)
    if rx < 0 or rx >= width or ry < 0 or ry >= height:
        return True  # Out of bounds counts as wall
    return maze[ry][rx] == WALL

def solveMaze_RightHand(maze, x, y, width, height, direction=EAST):
    """
    Right-hand rule solver: DFS preferring right turns.
    Tries directions in order: right, straight, left, back.
    """
    steps = [0]  # Use list to allow mutation in nested function
    path = []

    def dfs(cx, cy, cdir):
        if maze[cy][cx] == EXIT:
            maze[cy][cx] = PATH
            path.append((cx, cy))
            return True

        if maze[cy][cx] != START:
            maze[cy][cx] = PATH
        path.append((cx, cy))
        steps[0] += 1

        # Priority: right, straight, left, back
        for next_dir in [turn_right(cdir), cdir, turn_left(cdir), turn_back(cdir)]:
            nx, ny = get_next_pos(cx, cy, next_dir)
            if is_valid_move(nx, ny, width, height, maze):
                if dfs(nx, ny, next_dir):
                    return True

        # Backtrack
        if maze[cy][cx] != START:
            maze[cy][cx] = EMPTY
        path.pop()
        steps[0] += 1  # Count backtrack step
        return False

    dfs(x, y, direction)
    return steps[0], path

def solveMaze_LeftHand(maze, x, y, width, height, direction=EAST):
    """
    Left-hand rule solver: DFS preferring left turns.
    Tries directions in order: left, straight, right, back.
    """
    steps = [0]
    path = []

    def dfs(cx, cy, cdir):
        if maze[cy][cx] == EXIT:
            maze[cy][cx] = PATH
            path.append((cx, cy))
            return True

        if maze[cy][cx] != START:
            maze[cy][cx] = PATH
        path.append((cx, cy))
        steps[0] += 1

        # Priority: left, straight, right, back
        for next_dir in [turn_left(cdir), cdir, turn_right(cdir), turn_back(cdir)]:
            nx, ny = get_next_pos(cx, cy, next_dir)
            if is_valid_move(nx, ny, width, height, maze):
                if dfs(nx, ny, next_dir):
                    return True

        # Backtrack
        if maze[cy][cx] != START:
            maze[cy][cx] = EMPTY
        path.pop()
        steps[0] += 1
        return False

    dfs(x, y, direction)
    return steps[0], path

def solveMaze_AlternateLeft(maze, x, y, width, height, direction=EAST):
    """
    Straight-first with left bias using iterative DFS.
    Tries directions in order: straight, left, right, back.
    """
    steps = 0
    path = []
    stack = [(x, y, direction, [])]   # (x, y, direction, current_path)
    visited = set()

    while stack:
        cx, cy, cdir, current_path = stack.pop()
        steps += 1

        if (cx, cy) in visited:
            continue
        visited.add((cx, cy))

        if maze[cy][cx] == EXIT:
            maze[cy][cx] = PATH
            path = current_path + [(cx, cy)]
            return steps, path

        if maze[cy][cx] != START:
            maze[cy][cx] = PATH

        new_path = current_path + [(cx, cy)]

        # Priority: straight, left, right, back
        for next_dir in [cdir, turn_left(cdir), turn_right(cdir), turn_back(cdir)]:
            nx, ny = get_next_pos(cx, cy, next_dir)
            if is_valid_move(nx, ny, width, height, maze) and (nx, ny) not in visited:
                stack.append((nx, ny, next_dir, new_path))

    return steps, path


def solveMaze_AlternateRight(maze, x, y, width, height, direction=EAST):
    """
    Straight-first with right bias using iterative DFS.
    Tries directions in order: straight, right, left, back.
    """
    steps = 0
    path = []
    stack = [(x, y, direction, [])]
    visited = set()

    while stack:
        cx, cy, cdir, current_path = stack.pop()
        steps += 1

        if (cx, cy) in visited:
            continue
        visited.add((cx, cy))

        if maze[cy][cx] == EXIT:
            maze[cy][cx] = PATH
            path = current_path + [(cx, cy)]
            return steps, path

        if maze[cy][cx] != START:
            maze[cy][cx] = PATH

        new_path = current_path + [(cx, cy)]

        # Priority: straight, right, left, back
        for next_dir in [cdir, turn_right(cdir), turn_left(cdir), turn_back(cdir)]:
            nx, ny = get_next_pos(cx, cy, next_dir)
            if is_valid_move(nx, ny, width, height, maze) and (nx, ny) not in visited:
                stack.append((nx, ny, next_dir, new_path))

    return steps, path

def main():
    # Increase recursion limit for deep maze solving
    sys.setrecursionlimit(10000)

    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python multi_solver.py <seed> [method] [config]")
        print("Methods: 0=right-hand, 1=left-hand, 2=alternate-left, 3=alternate-right")
        print("Config: 1-4 (default: 1)")
        sys.exit(1)

    seed = int(sys.argv[1])
    method = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    config = int(sys.argv[3]) if len(sys.argv) > 3 else 1

    # Validate method
    if method not in [0, 1, 2, 3]:
        print("Invalid method. Use 0=right-hand, 1=left-hand, 2=alternate-left, 3=alternate-right")
        sys.exit(1)

    # Load maze
    maze = load_maze_from_db(seed, config)
    maze, width, height = normalize_maze(maze)

    # Find starting position
    start_pos = findStart(maze, width, height)
    if start_pos is None:
        print("No starting position found in maze!")
        sys.exit(1)

    x, y = start_pos
    maze[y][x] = EMPTY  # Remove the 'S' marker

    method_names = [
        "Right-Hand Rule",
        "Left-Hand Rule",
        "Straight then Alternate Left",
        "Straight then Alternate Right",
    ]

    print(f"Solving maze with {method_names[method]} (seed={seed}, config={config})")
    print("Original maze:")
    printMaze(maze, width, height)

    # Solve using the selected method
    if method == 0:
        steps, path = solveMaze_RightHand(maze, x, y, width, height)
    elif method == 1:
        steps, path = solveMaze_LeftHand(maze, x, y, width, height)
    elif method == 2:
        steps, path = solveMaze_AlternateLeft(maze, x, y, width, height)
    else:  # method == 3
        steps, path = solveMaze_AlternateRight(maze, x, y, width, height)

    print("Solved maze:")
    printMaze(maze, width, height)
    print(f"Method: {method_names[method]}")
    print(f"Total steps: {steps}")
    print(f"Path length: {len(path)}")

if __name__ == '__main__':
    main()

