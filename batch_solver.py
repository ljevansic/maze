#!/usr/bin/env python3
"""
Batch solver: solves every maze in mazes.db with all 4 methods
and records the Total steps in the solver_steps table.
"""

import sqlite3
import multi_solver as ms


def create_solver_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS solver_steps (
            seed INTEGER,
            config INTEGER,
            right_hand INTEGER,
            left_hand INTEGER,
            alternate_left INTEGER,
            alternate_right INTEGER,
            PRIMARY KEY (seed, config)
        )
    ''')
    conn.commit()


def solve_maze_with_method(seed, config, method):
    """Load maze fresh and solve with the given method. Returns total steps."""
    maze = ms.load_maze_from_db(seed, config)
    maze, width, height = ms.normalize_maze(maze)
    start_pos = ms.findStart(maze, width, height)
    if start_pos is None:
        return None
    x, y = start_pos
    maze[y][x] = ms.EMPTY

    if method == 0:
        steps, _ = ms.solveMaze_RightHand(maze, x, y, width, height)
    elif method == 1:
        steps, _ = ms.solveMaze_LeftHand(maze, x, y, width, height)
    elif method == 2:
        steps, _ = ms.solveMaze_AlternateLeft(maze, x, y, width, height)
    else:  # method == 3
        steps, _ = ms.solveMaze_AlternateRight(maze, x, y, width, height)

    return steps


def main():
    db_path = 'mazes.db'
    conn = sqlite3.connect(db_path)
    create_solver_table(conn)
    cursor = conn.cursor()

    # Get all mazes
    cursor.execute('SELECT seed, config FROM mazes ORDER BY seed, config')
    mazes = cursor.fetchall()
    total = len(mazes)

    print(f"Found {total} mazes. Solving with all 4 methods...\n")

    method_names = {
        0: "right_hand",
        1: "left_hand",
        2: "alternate_left",
        3: "alternate_right"
    }

    for idx, (seed, config) in enumerate(mazes, 1):
        print(f"[{idx}/{total}] seed={seed}, config={config} ... ", end="", flush=True)

        results = {}
        for method in [0, 1, 2, 3]:
            steps = solve_maze_with_method(seed, config, method)
            results[method_names[method]] = steps if steps is not None else -1

        # Insert or replace the row
        cursor.execute('''
            INSERT OR REPLACE INTO solver_steps
            (seed, config, right_hand, left_hand, alternate_left, alternate_right)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (seed, config,
              results["right_hand"],
              results["left_hand"],
              results["alternate_left"],
              results["alternate_right"]))

        print(f"RH={results['right_hand']}, LH={results['left_hand']}, "
              f"AL={results['alternate_left']}, AR={results['alternate_right']}")

    conn.commit()
    conn.close()
    print("\nDone! All results saved to solver_steps table.")


if __name__ == '__main__':
    main()
