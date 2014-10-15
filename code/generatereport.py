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

        #TODO: Calculate attendee conflicts

        #Presenter conflicts
        presenter_conflicts = c.execute("SELECT s1.tid, s1.talk_name, s2.tid, s2.talk_name FROM "
                  "(SELECT t.tid, t.name as talk_name, p.pid, p.name as presenter_time, h.hid, h.time FROM "
                  "talks t, schedule s, gives_talk gt, presenters p, hours h "
                  "WHERE t.tid==s.tid and gt.tid==t.tid and gt.pid=p.pid and s.hid=h.hid) s1, "
                  "(SELECT t.tid, t.name as talk_name, p.pid, p.name as presenter_time, h.hid, h.time FROM "
                  "talks t, schedule s, gives_talk gt, presenters p, hours h "
                  "WHERE t.tid==s.tid and gt.tid==t.tid and gt.pid=p.pid and s.hid=h.hid) s2 "
                  "WHERE s1.tid != s2.tid and s1.hid==s2.hid and s1.pid==s2.pid;").fetchall()
        if len(presenter_conflicts) == 0:
            html.write('No presenter conflicts!<br/>\n')
        else:
            html.write('Presenter conflicts:<br/>\n<table><tr><td>tid1</td><td>talk_name1</td><td>tid2</td><td>talk_name2</td><td>pid</td><td>presenter_name</td><td>hid</td><td>time</td></tr>\n')
            for presenter_conflict in presenter_conflicts:
                html.write('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>\n' %
                           (str(presenter_conflict[0]), str(presenter_conflict[1]), str(presenter_conflict[2]), str(presenter_conflict[3]),
                           str(presenter_conflict[4]), str(presenter_conflict[5]), str(presenter_conflict[6]), str(presenter_conflict[7])))
            html.write('</td><br/>')


        schedule = c.execute("SELECT t.tid, t.name, h.hid, h.time, r.rid, r.name FROM "
                             "talks t, schedule s, rooms r, hours h "
                             "WHERE t.tid == s.tid and r.rid=s.rid and s.hid=h.hid;").fetchall()
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


