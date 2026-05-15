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


def generate_maze(seed, width, height):
    output = subprocess.check_output(
        [sys.executable, MAZE_SCRIPT, '--seed', str(seed)],
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
            seed INTEGER PRIMARY KEY,
            maze TEXT UNIQUE
        )
        '''
    )
    conn.commit()
    return conn


def main():
    width, height = read_maze_dimensions(MAZE_SCRIPT)
    conn = create_database(DB_PATH)
    cursor = conn.cursor()

    inserted = 0
    skipped = 0
    mazes = 1000

    for seed in range(mazes):
        maze_text = generate_maze(seed, width, height)
        cursor.execute('INSERT OR IGNORE INTO mazes (seed, maze) VALUES (?, ?)', (seed, maze_text))
        if cursor.rowcount:
            inserted += 1
        else:
            skipped += 1
            print(f'Skipped duplicate maze for seed {seed}')
        conn.commit()

    conn.close()

    print(f'Generated {mazes} mazes. Inserted {inserted} unique mazes, skipped {skipped} duplicates.')
    print(f'Database written to: {DB_PATH}')


if __name__ == '__main__':
    main()
