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

def generate_report(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    with open(db_path + '.html', 'w') as html:
        html.write('<!DOCTYPE html><head><meta charset=\"UTF-8\"></head><body>\n')

        schedule = c.execute("SELECT t.tid, t.name, h.hid, h.time, r.rid, r.name FROM "
                             "talks t, schedule s, rooms r, hours h "
                             "WHERE t.tid == s.tid and r.rid=s.rid and s.hid=h.hid GROUP BY s.tid, s.hid, s.rid ORDER BY h.hid ASC").fetchall()

        z = {}
        for scheduled in schedule:
            tid = int(scheduled[0])
            hid = int(scheduled[2])
            if not tid in z:
                z[tid] = set()
            z[tid].add(hid)

        #TODO: Calculate attendee conflicts
        attendees = [int(attendee_row[0]) for attendee_row in c.execute('SELECT aid FROM attendee').fetchall()]
        conflicts = 0
        total_rsvps = 0
        for aid in attendees:
            attendee_interests = c.execute('SELECT tid FROM attendee_interest WHERE aid=?', (aid,)).fetchall()
            total_rsvps += len(attendee_interests)
            if len(attendee_interests) < 2:
                continue # no possible conflicts for this attendee
            for i in range(0, len(attendee_interests)):
                tid_1 = int(attendee_interests[i][0])
                for j in range(i + 1, len(attendee_interests)): # the c matrix is symmetric for a given attendee, i.e c_eij = c_eji
                    tid_2 = int(attendee_interests[j][0])
                    intersection = z[tid_1].intersection(z[tid_2])
                    conflict = len(intersection)
                    conflicts += conflict
                    if conflict > 0:
                        html.write('Attendee %d wants to go to talks %d and %d but they are both at hour %d!<br/>\n' % (aid, tid_1, tid_2, next(iter(intersection))))
        html.write('Total attendee RSVPS: %d<br/>\n' % (total_rsvps))
        html.write('Attendee RSVP conflicts: %d<br/>\n' % (conflicts, ))


        #Presenter conflicts
        presenter_conflicts = c.execute("SELECT DISTINCT s1.tid, s1.talk_name, s2.tid, s2.talk_name, s1.pid, s1.presenter_name, s1.hid, s1.time  FROM "
                  "(SELECT t.tid, t.name as talk_name, p.pid as pid, p.name as presenter_name, h.hid as hid, h.time as time FROM "
                  "talks t, schedule s, gives_talk gt, presenters p, hours h "
                  "WHERE t.tid==s.tid and gt.tid==t.tid and gt.pid=p.pid and s.hid=h.hid) s1, "
                  "(SELECT t.tid, t.name as talk_name, p.pid, p.name as presenter_name, h.hid, h.time FROM "
                  "talks t, schedule s, gives_talk gt, presenters p, hours h "
                  "WHERE t.tid==s.tid and gt.tid==t.tid and gt.pid=p.pid and s.hid=h.hid) s2 "
                  "WHERE s1.tid != s2.tid and s1.hid==s2.hid and s1.pid==s2.pid;").fetchall()
        if len(presenter_conflicts) == 0:
            html.write('No presenter conflicts!<br/>\n')
        else:
            html.write('Presenter conflicts:<br/>\n<table><tr><td>tid1</td><td>talk_name1</td><td>tid2</td><td>talk_name2</td><td>pid</td><td>presenter_name</td><td>hid</td><td>time</td></tr>\n')
            for presenter_conflict in presenter_conflicts:
                html.write('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>\n' %
                           (str(presenter_conflict[0]), str(presenter_conflict[1]), str(presenter_conflict[2]), str(presenter_conflict[3]),
                           str(presenter_conflict[4]), str(presenter_conflict[5]), str(presenter_conflict[6]), str(presenter_conflict[7])))
            html.write('</td><br/>')

        current_hid = -1
        for scheduled in schedule:
            if int(scheduled[2]) != current_hid:
                if current_hid != -1:
                    html.write('</table><br/>\n')
                html.write('%s<br/>\n' % scheduled[3])
                html.write('<table><tr><td>tid</td><td>talk_name</td><td>rid</td><td>room</td></tr>\n')
                current_hid = int(scheduled[2])
            html.write('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>\n' %
                      (scheduled[0], scheduled[1], scheduled[4], scheduled[5]))
        html.write('</table><br/><body></html>\n')


