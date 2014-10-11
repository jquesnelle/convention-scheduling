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

def multi_presenter_graph(db_path, labels):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    file = open(db_path + '.gv', 'w')
    file.write('graph multipresentergraph {\n')
    existing_vertices = set()
    conflicted = 0
    not_conflicted = 0
    for presenter_row in c.execute('SELECT pid, name FROM presenters').fetchall():
        pid = presenter_row[0]
        presenter_name = presenter_row[1]
        gives_talk_rows = c.execute('SELECT t.tid, t.name FROM talks t, gives_talk gt WHERE gt.pid=? and t.tid=gt.tid', (pid,)).fetchall()
        if len(gives_talk_rows) == 1:
            not_conflicted += 1
            continue # This presenter only gives one talk, he can't have any conflicts
        tids = []
        for gives_talk_row in gives_talk_rows:
            tid = gives_talk_row[0]
            if not tid in existing_vertices:
                if labels == True:
                    file.write('\"%d\";\n' % tid)
                else:
                    file.write('%d [label=\"\"];\n' % tid)
                existing_vertices.add(tid)
            tids.append(tid)
        for tid_1 in range(0, len(tids)):
            for tid_2 in range(tid_1 + 1, len(tids)):
                if labels == True:
                    file.write('\"%d\" -- \"%d\" [label=%d];\n' % (tids[tid_1], tids[tid_2], pid))
                else:
                    file.write('%d -- %d;\n' % (tids[tid_1], tids[tid_2]))
        conflicted += 1
    file.write('}')
    conn.close()
    file.close()
    print 'Conflicted: ' + str(conflicted)
    print 'Not conflicted: ' + str(not_conflicted)


