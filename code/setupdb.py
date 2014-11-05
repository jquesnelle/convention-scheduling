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

def setup_db(db_path, num_talks, num_hours, num_attendees, num_rsvps, distribution):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('DELETE FROM talks WHERE tid >= ?', (num_talks,))
    c.execute('DELETE FROM gives_talk WHERE tid >= ?', (num_talks,))
    c.execute('DELETE FROM talk_available WHERE tid >= ?', (num_talks,))
    c.execute('DELETE FROM room_suitable_for WHERE tid >= ?', (num_talks,))
    c.execute('DELETE FROM hours WHERE hid >= ?', (num_hours,))
    c.execute('DELETE FROM presenter_available WHERE hid >= ?', (num_hours,))
    c.execute('DELETE FROM room_available WHERE hid >= ?', (num_hours,))
    c.execute('DELETE FROM talk_available WHERE hid >= ?', (num_hours,))
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
                attendee_rsvps = {}
                tids_already_processed = {}
                while aid < num_attendees:
                    c.execute('INSERT INTO attendee VALUES (?)', (aid,))
                    attendee_rsvps[aid] = set()
                    aid += 1
                aid_range = range(0, num_attendees)
                for row in reader:
                    talk_name = row[0]
                    row_tids = c.execute('SELECT tid FROM talks WHERE name = ?', (talk_name,)).fetchall()
                    if len(row_tids) == 0:
                        #print 'Unable to find tid for %s' % talk_name
                        continue
                    tid = int(row_tids[0][0])
                    if tid > max_tid:
                        continue
                    if not tid in tids_already_processed:
                        tids_already_processed[tid] = 0
                    real_attendance = int(row[3])
                    if real_attendance >= num_attendees:
                        real_attendance = num_attendees
                    for i in range(tids_already_processed[tid], real_attendance):
                        max_aid = len(aid_range) - 1
                        # aid = random.choice(aid_range)
                        aid = int(.1 * max_aid * numpy.random.randn()) + int(max_aid / 2)
                        if aid < 0:
                            aid = 0
                        elif aid > max_aid:
                            aid = max_aid
                        while tid in attendee_rsvps[aid]:
                            # aid = random.choice(aid_range)
                            aid = int(.1 * max_aid * numpy.random.randn()) + int(max_aid / 2)
                            if aid < 0:
                                aid = 0
                            elif aid > max_aid:
                                aid = max_aid
                        attendee_rsvps[aid].add(tid)
                        c.execute('INSERT INTO attendee_interest VALUES (?, ?)', (aid, tid))
                    tids_already_processed[tid] = real_attendance

        else:
            while aid < num_attendees:
                c.execute('INSERT INTO attendee VALUES (?)', (aid,))
                rsvps = set()
                i = 0
                while i < num_rsvps:
                    if distribution == 'uniform':
                        tid = random.choice(tid_range)
                    else:
                        tid = int(.1 * max_tid * numpy.random.randn()) + int((max_tid/2))
                        if tid < 0:
                            tid = 0
                        if tid >= max_tid:
                            tid = max_tid
                    if tid in rsvps:
                        continue
                    else:
                        rsvps.add(tid)
                        i += 1
                    c.execute('INSERT INTO attendee_interest VALUES (?, ?)', (aid, tid))
                aid += 1

    conn.commit()
    conn.close()
