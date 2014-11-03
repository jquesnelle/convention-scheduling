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
import random
import numpy
import csv

def setup_db(db_path, num_talks, num_attendees, num_rsvps, distribution):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('DELETE FROM talks WHERE tid >= ?', (num_talks,))
    c.execute('DELETE FROM gives_talk WHERE tid >= ?', (num_talks,))
    c.execute('DELETE FROM talk_available WHERE tid >= ?', (num_talks,))
    c.execute('DELETE FROM room_suitable_for WHERE tid >= ?', (num_talks,))
    c.execute('DELETE FROM schedule')
    if num_attendees != None:
        c.execute('DELETE FROM attendee')
        c.execute('DELETE FROM attendee_interest')
        conn.commit()
        max_tid = c.execute('SELECT MAX(tid) FROM talks').fetchone()[0]
        tid_range = range(0, max_tid + 1)
        aid = 0

        if distribution == '2013':
            with open('2013_real_attendance.csv') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    row_tids = c.execute('SELECT tid FROM talks WHERE name = ?', (row[0],)).fetchall()
                    if len(row_tids) == 0:
                        print 'Unable to find tid for %s' % row[0]
                    row_tid = int(row_tids[0][0])

        else:
            while aid < num_attendees:
                c.execute('INSERT INTO attendee VALUES (?)', (aid,))
                rsvps = set()
                i = 0
                while i < num_rsvps:
                    if distribution == 'uniform':
                        tid = random.choice(tid_range)
                    elif distribution == 'normal':
                        tid = int(10 * numpy.random.randn()) + int((max_tid/2))
                    if tid in rsvps:
                        continue
                    else:
                        rsvps.add(tid)
                        i += 1
                    c.execute('INSERT INTO attendee_interest VALUES (?, ?)', (aid, tid))
                aid += 1

    conn.commit()
    conn.close()