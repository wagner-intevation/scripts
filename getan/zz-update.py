#!/usr/bin/python3
import sqlite3
import os
import re
import argparse
import subprocess
import tempfile
import configparser
from collections import defaultdict
from pathlib import Path
from datetime import datetime
from typing import List
from pprint import pprint

_cfg = configparser.ConfigParser()
_cfg.read(Path('~/.getan/config.ini').expanduser())


def _parse_keys(raw: str) -> set:
    return {k.strip() for k in raw.split(',') if k.strip()}

parser = argparse.ArgumentParser(description='Update zeiterfassung.txt files with getan entries')
parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
parser.add_argument('-d', '--days', type=int, default=7, help='Number of days to look back (default: 7)')
parser.add_argument('-q', '--akquise', help='Only deal with this Akquise (Project) number')
parser.add_argument('-a', '--automatic', action='store_true', help='Automatically add the entries to the destination files')
parser.add_argument('--initials', help='Initials to use in zeiterfassung.txt')
args = parser.parse_args()

if args.initials is None:
    args.initials = _cfg.get('zz-update', 'initials', fallback=None)
if args.initials is None:
    parser.error("initials is required (pass as argument or set 'initials' in [zz-update] in ~/.getan/config.ini)")

# ANSI formatting codes
BOLD = '\033[1m'
UNDERLINE = '\033[4m'
RESET = '\033[0m'

project_id_pattern = re.compile(r'#[0-9]+')
TODAY = datetime.now().strftime('%d.%m.%Y')

# zeiterfassung.txt format
zz_format = '{day} {hours:2}:{minutes:02}h ? {initials:3} {entry_desc}'

query = f"""
WITH
    ent(project_id, day, hours, description)
    AS
    (
        SELECT
            project_id,
            DATE(start_time) as day,
            printf('%.2f', cast(strftime('%s', stop_time) - strftime('%s', start_time) as float))/3600 as hours,
            description
        FROM entries
        ORDER BY start_time ASC
    )
SELECT
    strftime('%d.%m.%Y', day) as day,
    cast(FLOOR(hours) as integer) as hours,
    cast(ROUND((hours - FLOOR(hours)) * 60) as integer) AS minutes,
    ent.description as entry_desc,
    p.key as project_key,
    p.description as project_desc
FROM ent
JOIN projects p ON p.id = project_id
WHERE day >= date('now', '-{args.days} days')
ORDER BY day ASC;
"""

def normalize_entry_line(line):
    if len(line) > 18:
        return line[:18] + line[19:]
    return line


def print_impossible(project_name: str, project_entries: List[dict]):
    print(f'    {UNDERLINE}{project_name}{RESET}')
    for entry in project_entries:
        print(f"{entry['day']} {entry['hours']:2d}:{entry['minutes']:02d} {entry['project_desc']:15} {entry['entry_desc']}")


database = os.path.expanduser("~/.getan/time.db")

# A=regel. Arbeitsorganisation*, w=IT-Infrastruktur, o=Organisieren und verbessern*,
# Q=Qualifikation, B=Buchhaltung, ü=Büro, M=Menschen fördern, u=Unternehmen*, k=Marketing allg+streut*
ignored_keys = _parse_keys(_cfg.get(
    'zz-update', 'ignored_keys', fallback='A,w,o,Q,B,ü,M,u,k'
))
# q=Akquise#
impossible_keys = _parse_keys(_cfg.get(
    'zz-update', 'impossible_keys', fallback='q'
))
impossible_entries = defaultdict(list)
projects = defaultdict(list)

manual_mappings: dict[str, Path] = {}
if _cfg.has_section('zz-update:manual-mappings'):
    for _pid, _raw_path in _cfg.items('zz-update:manual-mappings'):
        manual_mappings[_pid] = Path(_raw_path)

# open getan database read-only
conn = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

try:
    cursor.execute(query)
    for row in cursor.fetchall():
        if row['project_key'] in ignored_keys:
            continue
        if row['project_key'] in impossible_keys:
            impossible_entries[row['project_desc']].append(row)
            continue

        if row['project_desc'].lower().startswith('pflege'):
            # If "Pflege", then it's an activity
            proj_id = row['project_desc'].split(' ')[1].lower()
        else:
            # Extract project ID from project description
            match = project_id_pattern.search(row['project_desc'])
            proj_id = match.group(0)[1:] if match else ''

        projects[proj_id].append(row)
finally:
    conn.close()

if impossible_entries:
    if args.verbose:
        print(f'{BOLD}Impossible to handle these entries{RESET}:')
        for proj, entries in impossible_entries.items():
            print_impossible(project_name=proj, project_entries=entries)
    else:
        print(f"Impossible to handle entries for {', '.join(impossible_entries)}")

for proj_id, entries in projects.items():
    try:
        int(proj_id)
        activity = False
    except ValueError:
        activity = True

    if args.akquise and proj_id != args.akquise:
        if args.verbose:
            print(f'Skipping Akquise {proj_id}')
        continue

    if proj_id in manual_mappings:
        print(f'{BOLD}Handle {"Activity Pflege" if activity else "Project #"}{proj_id} (manual mapping){RESET}')
        target_dir = manual_mappings[proj_id]
        if not target_dir.is_dir():
            print(f'  Error: Manual mapping for {proj_id} points to non-existent directory: {target_dir}')
            print_impossible(proj_id, entries)
            continue
        if args.verbose:
            print(f'  Using manual mapping: {target_dir}')
    elif activity:
        print(f'{BOLD}Handle Activity Pflege {proj_id}{RESET}')
        # Find the project directory by globbing
        matches = list(Path('/home/activities').glob(f'pflege-{proj_id}*'))
        if len(matches) == 0:
            print(f'  Error: No directory found matching pattern /home/activities/*/{proj_id}*')
            print_impossible(proj_id, entries)
            continue
        elif len(matches) > 1:
            print(f'  Error: Multiple directories found: {[str(m) for m in matches]!r}')
            print_impossible(proj_id, entries)
            continue
        target_dir = matches[0]
        if args.verbose:
            print(f'  Found directory: {target_dir}')
    else:
        print(f'{BOLD}Handle Project #{proj_id}{RESET}')

        # Find the project directory by globbing
        matches = list(Path('/home/clients').glob(f'*/{proj_id}*')) + list(Path('/home/projects/Intern').glob(f'{proj_id}*'))
        if len(matches) == 0:
            print(f'  Error: No directory found matching pattern /home/clients/*/{proj_id}* and /home/projects/Intern/{proj_id}*')
            print_impossible(proj_id, entries)
            continue
        elif len(matches) > 1:
            print(f'  Error: Multiple directories found: {[str(m) for m in matches]!r}')
            print_impossible(proj_id, entries)
            continue
        target_dir = matches[0]
        if args.verbose:
            print(f'  Found directory: {target_dir}')

    # Probe for zeiterfassung.txt in Management or Projekt-Management
    zeiterfassung_paths = [
        target_dir / 'Management' / 'zeiterfassung.txt',
        target_dir / 'Projekt-Management' / 'zeiterfassung.txt'
    ]
    zeiterfassung_file = None
    for path in zeiterfassung_paths:
        if path.exists():
            zeiterfassung_file = path
            break
    if zeiterfassung_file is None:
        print(f'  Error: No zeiterfassung.txt found in Management/ or Projekt-Management/')
        print_impossible(proj_id, entries)
        continue
    print(f'  {UNDERLINE}zeiterfassung.txt{RESET}: {zeiterfassung_file}')

    # Open zeiterfassung_file read-only
    with open(zeiterfassung_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find the end of the Abrechnungsblock
    separator = '==============================================================================\n'
    last_separator_idx = None
    for i in range(len(lines) - 1, -1, -1):
        if lines[i] == separator:
            last_separator_idx = i
            break
    if last_separator_idx is None:
        print(f'  Error: No separator line found in {zeiterfassung_file}')
        continue

    # Check that the last Block is not Abgerechnet
    # The line can contain a dot at the end, so only check the start of the line
    # lower/upper case is not standardised, so compare case-insensitive
    next_line = lines[last_separator_idx + 1].strip().lower()
    if not (next_line.startswith('abgerechnet: noch nicht')
        or next_line.startswith('abgerechnet: teilweise')):
        print(f'  Error: Last Abrechnungsblock is abgerechnet, create a new block manually.')
        print(f'  Error: Blockpostfix was: {next_line!r}')
        continue

    # Create a set of all the lines for quick lookups
    existing_lines = set(normalize_entry_line(line).rstrip('\n') for line in lines)

    new_entries = []
    existing_entries = []
    for entry in entries:
        formatted_entry = zz_format.format(initials=args.initials, **entry)

        if normalize_entry_line(formatted_entry) in existing_lines:
            existing_entries.append(formatted_entry)
        else:
            new_entries.append(formatted_entry)

    if args.verbose and existing_entries:
        print('  Skipping already existing entries:')
        # intentionally indented to make it non-copiable
        for entry in existing_entries:
            print(f'  {entry}')
    if new_entries:
        print('  New entries:')
        for entry in new_entries:
            print(entry)
        if args.automatic and zeiterfassung_file:
            # Write all lines from new_entries to a temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt') as tmpfile:
                tmpfile_path = tmpfile.name
                tmpfile.writelines([f"{entry}\n" for entry in new_entries])
                tmpfile.flush()  # otherwise vim reads the file before the data is written

                try:
                    # change directory
                    previous_dir = os.getcwd()
                    os.chdir(zeiterfassung_file.parent)

                    # Check if directory is under version control
                    hg_root = subprocess.run(['hg', 'root'], capture_output=True, text=True)
                    is_hg_repo = hg_root.returncode == 0
                    if is_hg_repo:
                        # update hg Repository
                        subprocess.run(['hg', 'update'], check=True)
                        # only pull a remote is configured
                        result = subprocess.run(['hg', 'paths'], capture_output=True, text=True)
                        if result.stdout.strip():
                            subprocess.run(['hg', 'pull', '--update'], check=True)

                    # Insert text before the last occurrence of ^=====
                    subprocess.run(['vim', '-c',
                                    f'$?^=====?-1 read {tmpfile_path}',
                                    str(zeiterfassung_file)])

                    if is_hg_repo:
                        subprocess.run(['hg', 'diff'], check=True)
                        diff_accepted = input("Commit this (y)? Or (a)bort ")
                        if diff_accepted == 'y':
                            subprocess.run(['hg', 'commit',
                                            '-e',  # open editor even with -m given
                                            '-m', f'{args.initials.upper()} {TODAY}'],
                                           check=True)
                        else:
                            exit(-1)
                finally:
                    # change back to the previous directory
                    os.chdir(previous_dir)
                    # delete the temporary file
