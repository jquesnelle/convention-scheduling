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

class room_class:

    def __init__(self, available, suitable):
        self.available = frozenset(available)
        self.suitable = frozenset(suitable)

    def __eq__(self, other):
        return self.available == other.available and self.suitable == other.suitable

    def __ne__(self, other):
        return self.available != other.available or self.suitable != other.suitable

    def __hash__(self):
        return hash(self.suitable) ^ hash(self.available)

    def __repr__(self):
        return "available: %s, suitable %s" % (str(self.available), str(self.suitable))


def setup_db(db_path, num_talks, num_hours, num_attendees, num_rsvps, distribution, sigma_ratio):
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

        if distribution.startswith('2013'):
            tdist = 0 if 'normal' in distribution else 1

            if 'class' in distribution:
                room_classes = {}
                rooms = {}
                for room_row in c.execute('SELECT rid, name FROM rooms').fetchall():
                    rid = int(room_row[0])
                    room_name = room_row[1]
                    if room_name == 'Food':
                        room_name = 'Food'
                    rooms[rid] = room_name

                    room_available = set()
                    room_suitable = set()
                    for available_row in c.execute('SELECT hid FROM room_available WHERE rid = ?', (rid,)).fetchall():
                        room_available.add(int(available_row[0]))
                    for suitable_row in c.execute('SELECT tid FROM room_suitable_for WHERE rid = ?', (rid,)).fetchall():
                        room_suitable.add(int(suitable_row[0]))

                    rclass = room_class(room_available, room_suitable)
                    if not rclass in room_classes:
                        room_classes[rclass] = set()
                    room_classes[rclass].add(rid)

                c.execute('DELETE FROM rooms')
                c.execute('DELETE FROM room_available')
                c.execute('DELETE FROM room_suitable_for')
                c.execute('DELETE FROM room_class_member')
                c.execute('DELETE FROM room_class_members')
                conn.commit()

                rclass_id = 0
                member_defined = set()
                for rclass, rooms_in_class in room_classes.iteritems():
                    c.execute('INSERT INTO rooms values (?, ?, ?)', (rclass_id, 'Room class %d' % rclass_id, len(rooms_in_class)))
                    for room_in_class in rooms_in_class:
                        if not room_in_class in member_defined:
                            c.execute('INSERT INTO room_class_member VALUES (?, ?)', (room_in_class, rooms[room_in_class]))
                            member_defined.add(room_in_class)
                        c.execute('INSERT INTO room_class_members VALUES (?, ?)', (rclass_id, room_in_class))
                    for hid in rclass.available:
                        c.execute('INSERT INTO room_available VALUES (?, ?)', (rclass_id, hid))
                    for tid in rclass.suitable:
                        c.execute('INSERT INTO room_suitable_for VALUES (?, ?)', (rclass_id, tid))
                    rclass_id += 1
                conn.commit()

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
                        if tdist == 1:
                            aid = random.choice(aid_range)
                        else:
                            aid = int(sigma_ratio * max_aid * numpy.random.randn()) + int(max_aid / 2)
                            while aid < 0 or aid > max_aid:
                                aid = int(sigma_ratio * max_aid * numpy.random.randn()) + int(max_aid / 2)
                        while (tid in attendee_rsvps[aid]) or (len(attendee_rsvps[aid]) >= num_hours):
                            if tdist == 1:
                                aid = random.choice(aid_range)
                            else:
                                aid = int(sigma_ratio * max_aid * numpy.random.randn()) + int(max_aid / 2)
                                while aid < 0 or aid > max_aid:
                                    aid = int(sigma_ratio * max_aid * numpy.random.randn()) + int(max_aid / 2)
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
                        tid = int(sigma_ratio * max_tid * numpy.random.randn()) + int((max_tid/2))
                        while tid < 0 or tid > max_tid:
                            tid = int(sigma_ratio * max_tid * numpy.random.randn()) + int((max_tid/2))
                    if tid in rsvps:
                        continue
                    else:
                        rsvps.add(tid)
                        i += 1
                    c.execute('INSERT INTO attendee_interest VALUES (?, ?)', (aid, tid))
                aid += 1

    conn.commit()
    conn.close()
