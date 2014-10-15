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

import sys
import sqlite3
import xml.etree.ElementTree as ET
import os
import datetime

def make_db(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    with open('schema.sql') as f:
        lines = f.readlines()
        for line in lines:
            c.execute(line)
    conn.commit()
    conn.close()

def generate_db(xml_path, full):
    db_path = xml_path + '.db'
    try:
        os.remove(db_path)
    except:
        pass
    make_db(db_path)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    with open(xml_path) as f:
        tid = 0
        pid = 0
        rid = 0
        hid = 0
        presenter_to_pid = {}
        room_to_rid = {}
        tid_to_track = {}
        tid_to_type = {} # from tid to 0 for day/evening, 1 for night
        type_to_hids = {0: [], 1: []}
        start_time = datetime.datetime(year=2013, month=4, day=26, hour=16)
        end_time = datetime.datetime(year=2013, month=4, day=28, hour=16)
        current_day = start_time.date()
        current_time = None
        tree = ET.fromstring(f.read())
        events = tree.find('document')
        for section in events:
            if section.tag == 'time':
                time_text= section.text.split(' ')
                hour = int(time_text[0])
                if time_text[1] == 'PM' and hour != 12:
                    hour += 12
                elif time_text[1] == 'AM' and hour == 12:
                    hour = 0
                new_time = datetime.time(hour = hour)
                if not current_time is None and new_time.hour < current_time.hour:
                    current_day = current_day + datetime.timedelta(days=1)
                current_time = new_time
                c.execute('INSERT INTO hours VALUES (?, ?)', (hid, datetime.datetime(current_day.year, current_day.month, current_day.day, current_time.hour, current_time.minute, current_time.second, current_time.microsecond)))
                type_to_hids[0 if 9 <= current_time.hour <= 19 else 1].append(hid)
                hid += 1
            if section.tag == 'div' and section.attrib['class'] == 'section':
                name = section[0].text
                track = section[1].text
                room = section[2].text
                presenters = section[3][0].text
                description = section[3][0].tail
                c.execute('INSERT INTO talks VALUES (?, ?, ?)', (tid, name, description))
                talk_pids = []
                for presenter_name in [presenter.strip() for presenter in presenters.split(',')]:
                    if presenter == 'Open':
                        continue #"Open" person will cause the schedule to become infesible
                    if presenter_name not in presenter_to_pid:
                        c.execute('INSERT INTO presenters VALUES (?,?)', (pid, presenter_name))
                        presenter_to_pid[presenter_name] = pid
                        pid += 1
                    talk_pids.append(presenter_to_pid[presenter_name])
                for talk_pid in talk_pids:
                    c.execute('INSERT INTO gives_talk VALUES (?, ?)', (talk_pid, tid))
                if room not in room_to_rid:
                    c.execute('INSERT INTO rooms VALUES (?, ?)', (rid, room))
                    room_to_rid[room] = rid
                    rid += 1
                if full == True:
                    c.execute('INSERT INTO schedule VALUES (?, ?, ?)', (tid, hid - 1, room_to_rid[room]))
                tid_to_type[tid] = 0 if 9 <= current_time.hour <= 19 else 1
                tid_to_track[tid] = track
                tid += 1
    conn.commit()
    food_rid = -1
    hackerspace_rids = []
    general_rids = []
    max_hid = hid
    max_pid = pid
    for room, rid in room_to_rid.iteritems():
        if room == 'Food':
            food_rid = rid
        elif room == 'Hackerspace A' or room == 'Hackerspace B':
            hackerspace_rids.append(rid)
        else:
            general_rids.append(rid)
        # for now, all rooms are available all the time
        for hid_it in range(0, max_hid):
            c.execute('INSERT INTO room_available VALUES (?, ?)', (rid, hid_it))
    for tid, track in tid_to_track.iteritems():
        if track == 'Food':
            c.execute('INSERT INTO room_suitable_for VALUES (?, ?)', (food_rid, tid))
        elif track == 'Hackerspace':
            for hackerspace_rid in hackerspace_rids:
                c.execute('INSERT INTO room_suitable_for VALUES (?, ?)', (hackerspace_rid, tid))
        else:
            for general_rid in general_rids:
                c.execute('INSERT INTO room_suitable_for VALUES (?, ?)', (general_rid, tid))
        for hid in type_to_hids[tid_to_type[tid]]:
            c.execute('INSERT INTO talk_available VALUES (?, ?)', (tid, hid)) #things that were really scheduled at night can only be at night, and day things can only be during the day
    for pid_it in range(0, max_pid):
        for hid_it in range(0, max_hid):
            c.execute('INSERT INTO presenter_available VALUES (?, ?)', (pid_it, hid_it))
    conn.commit()
    conn.close()