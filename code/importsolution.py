'''
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import sqlite3

def import_solution(db_path, solution_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    with open(solution_path, 'r') as f:
        lines = f.readlines()
        if not 'Optimal' in lines[0] and not 'optimal' in lines[0]:
            print 'Non-optimal solution'
            return

        c.execute('DELETE FROM schedule')
        conn.commit()

        start_line = 1
        if lines[start_line].startswith('o'):
            start_line += 1 # puts objectvie value on second line, cbc on first

        for line in lines[start_line:]:
            parts = line.split()
            if parts[1].startswith('f'):
                f_parts = parts[1].split('_')
                pid = int(f_parts[1][1:])
                tid = int(f_parts[2][1:])
                hid = int(f_parts[3][1:])
                rid = int(f_parts[4][1:])
                c.execute('INSERT INTO schedule VALUES (?, ?, ?, ?)', (pid,tid,hid,rid))

    conn.commit()
    conn.close()