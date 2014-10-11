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

def make_db(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    with open('schema.sql') as f:
        lines = f.readlines()
        for line in lines:
            c.execute(line)
    conn.commit()
    conn.close()

def setup_db(xml_path):
    db_path = xml_path + '.db'
    make_db(db_path)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    with open(xml_path) as f:
        tid = 0
        pid = 0
        rid = 0
        presenter_to_pid = {}
        room_to_rid = {}
        tid_to_track = {}
        tree = ET.fromstring(f.read())
        events = tree.find('document')
        for section in events:
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
                tid_to_track[tid] = track
                tid += 1
        
    conn.commit()
    conn.close()

if __name__ == '__main__':
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print 'Need a file to import!'