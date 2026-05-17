#!/usr/bin/env python3
import os
import re
import sqlite3
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAZE_SCRIPT = os.path.join(SCRIPT_DIR, 'mazegen.py')
DB_PATH = os.path.join(SCRIPT_DIR, 'mazes.db')

WIDTH_PATTERN = re.compile(r'^WIDTH\s*=\s*(\d+)', re.MULTILINE)
HEIGHT_PATTERN = re.compile(r'^HEIGHT\s*=\s*(\d+)', re.MULTILINE)


def read_maze_dimensions(script_path):
    '''
    This function reads the maze dimensions (WIDTH and HEIGHT) from the mazegen.py script
    using regular expressions. It returns the width and height as integers.
    '''
    with open(script_path, 'r', encoding='utf-8') as file:
        source = file.read()

    width_match = WIDTH_PATTERN.search(source)
    height_match = HEIGHT_PATTERN.search(source)

    if not width_match or not height_match:
        raise ValueError('Could not determine WIDTH and HEIGHT from mazegen.py')

    return int(width_match.group(1)), int(height_match.group(1))


def generate_maze(seed, width, height, start_x, start_y, end_x, end_y):
    output = subprocess.check_output(
        [sys.executable, MAZE_SCRIPT, '--seed', str(seed),
         '--start-x', str(start_x), '--start-y', str(start_y),
         '--end-x', str(end_x), '--end-y', str(end_y)],
        text=True,
        cwd=SCRIPT_DIR,
    )

    lines = output.splitlines()
    maze_lines = [line for line in lines if line != '']

    return '\n'.join(maze_lines[:height])


def create_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS mazes (
            seed INTEGER,
            config INTEGER,
            maze TEXT UNIQUE,
            PRIMARY KEY (seed, config)
        )
        '''
    )
    conn.commit()
    return conn


def main():
    width, height = read_maze_dimensions(MAZE_SCRIPT)
    conn = create_database(DB_PATH)
    cursor = conn.cursor()

    # Define the 4 corner configurations:
    # (config_id, start_x, start_y, end_x, end_y, description)
    configs = [
        (1, 1, 1, width - 2, height - 2, "Upper-left to lower-right"),
        (2, width - 2, 1, 1, height - 2, "Upper-right to lower-left"),
        (3, 1, height - 2, width - 2, 1, "Lower-left to upper-right"),
        (4, width - 2, height - 2, 1, 1, "Lower-right to upper-left"),
    ]

    inserted = 0
    skipped = 0
    total_mazes = 1000

    for seed in range(total_mazes):
        for config_id, start_x, start_y, end_x, end_y, desc in configs:
            maze_text = generate_maze(seed, width, height, start_x, start_y, end_x, end_y)
            cursor.execute(
                'INSERT OR IGNORE INTO mazes (seed, config, maze) VALUES (?, ?, ?)',
                (seed, config_id, maze_text)
            )
            if cursor.rowcount:
                inserted += 1
            else:
                skipped += 1
                print(f'Skipped duplicate maze for seed {seed}, config {config_id}')
            conn.commit()

    conn.close()

    total_generated = total_mazes * 4
    print(f'Generated {total_generated} mazes ({total_mazes} seeds × 4 configs). Inserted {inserted} unique mazes, skipped {skipped} duplicates.')
    print(f'Database written to: {DB_PATH}')


if __name__ == '__main__':
    main()
