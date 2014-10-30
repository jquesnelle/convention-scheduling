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

def setup_db(db_path, num_talks, num_attendees, num_rsvps):
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
        while aid < num_attendees:
            c.execute('INSERT INTO attendee VALUES (?)', (aid,))
            for i in range(0, num_rsvps):
                tid = random.choice(tid_range)
                c.execute('INSERT INTO attendee_interest VALUES (?, ?)', (aid, tid))
            aid += 1

    conn.commit()
    conn.close()