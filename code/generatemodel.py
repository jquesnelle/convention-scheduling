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

def generate_model(db_path, type):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    hours = [int(hour_row[0]) for hour_row in c.execute('SELECT hid, time FROM hours').fetchall()]
    talks = [int(talk_row[0]) for talk_row in c.execute('SELECT tid FROM talks').fetchall()]
    attendees = [int(attendee_row[0]) for attendee_row in c.execute('SELECT aid FROM attendee').fetchall()]
    presenters = [int(presenter_row[0]) for presenter_row in c.execute('SELECT pid FROM presenters').fetchall()]
    rooms = [int(room_row[0]) for room_row in c.execute('SELECT rid FROM rooms').fetchall()]
    gives_talk={}
    talk_given_by={}
    talk_really_available = {}
    real_availability_of_talks = {}
    for gives_talk_row in c.execute('SELECT pid, tid FROM gives_talk'):
        pid = gives_talk_row[0]
        tid = gives_talk_row[1]
        if pid not in gives_talk:
            gives_talk[pid] = [tid]
        else:
            gives_talk[pid].append(tid)
        if tid not in talk_given_by:
            talk_given_by[tid] = [pid]
        else:
            talk_given_by[tid].append(pid)


    conflict_vars = set()
    f_vars = {}
    g_vars = {}
    constraint_count = 0

    # this will generate the feasible schedule. for any row in this query, pid is available at hid,
    # tid is available at gid, rid is suitable for tid and tid is available at hid.
    # by only using these variables, we effectively enforce constraint (a)
    possible_schedule = c.execute("SELECT gt.pid, gt.tid, h.hid, rs.rid FROM hours h, gives_talk gt, "
                                  "talk_available ta, room_suitable_for rs, room_available ra WHERE rs.rid=ra.rid "
                                  "and rs.tid=gt.tid and ra.hid=h.hid and ta.tid=gt.tid and h.hid=ta.hid GROUP BY "
                                  "gt.pid, gt.tid, h.hid, rs.rid")
    for possible_schedule_row in possible_schedule:
        pid = int(possible_schedule_row[0])
        tid = int(possible_schedule_row[1])
        hid = int(possible_schedule_row[2])
        rid = int(possible_schedule_row[3])

        if pid not in f_vars:
            f_vars[pid] = {}
        if tid not in f_vars[pid]:
            f_vars[pid][tid] = {}
        if hid not in f_vars[pid][tid]:
            f_vars[pid][tid][hid] = set()
        f_vars[pid][tid][hid].add(rid)

        if not tid in talk_really_available:
            talk_really_available[tid] = {}
        if not hid in talk_really_available[tid]:
            talk_really_available[tid][hid] = set()
        talk_really_available[tid][hid].add(rid)

        if not hid in real_availability_of_talks:
            real_availability_of_talks[hid] = {}
        if not rid in real_availability_of_talks[hid]:
            real_availability_of_talks[hid][rid] = set()
        real_availability_of_talks[hid][rid].add(tid)

    with open(db_path + '.lp', 'w') as f:
        f.write('Minimize\nOBJ: ')

        if type == 'ecttd':
            # Note, this doesn't include the extended f_vars when copresenters have different availabilities -- but as of now this never happens
            first = True
            for pid in f_vars.keys():
                for tid in f_vars[pid].keys():
                    for hid in f_vars[pid][tid].keys():
                        for rid in f_vars[pid][tid][hid]:
                            if first == True:
                                first = False
                            else:
                                f.write(' + ')
                            f.write('f_p%d_t%d_h%d_r%d' % (pid,tid,hid,rid))
        else:
            # Minimize "c" which will be matrix of hour x talk x talk -> rsvp conflicts
            total_conflict_vars = 0
            for aid in attendees:
                attendee_interests = c.execute('SELECT tid FROM attendee_interest WHERE aid=?', (aid,)).fetchall()
                if len(attendee_interests) < 2:
                    continue # no possible conflicts for this attendee
                for i in range(0, len(attendee_interests)):
                    tid_1 = int(attendee_interests[i][0])
                    for j in range(i + 1, len(attendee_interests)): # the c matrix is symmetric for a given attendee, i.e c_eij = c_eji
                        tid_2 = int(attendee_interests[j][0])
                        overlapping_hours = [int(overlapping_hour_row[0]) for overlapping_hour_row in c.execute('SELECT t1.hid FROM talk_available t1, talk_available t2 WHERE t1.hid=t2.hid and t1.tid=? and t2.tid=?', (tid_1, tid_2)).fetchall()]
                        for hid in overlapping_hours:
                            # these two talks can be scheduled at the same time and this attendee has indicated interest; there will be a penalty if these two are scheduled at the same time
                            if total_conflict_vars > 0:
                                f.write(' + ')
                            conflict_var = 'c_h%d_t%d_t%d' % (hid, tid_1, tid_2)
                            conflict_vars.add(conflict_var)
                            f.write(conflict_var)

        f.write('\nSubject To\n')


        # constraint (b)
        for pid in f_vars.keys():
            for tid in f_vars[pid].keys():
                f.write('\\* Presenter %d is only scheduled for talk %d once *\\\n' % (pid, tid))
                first = True
                constraint = ''
                # the mere fact that tid is here means that G_pid,tid=1
                for hid in f_vars[pid][tid].keys():
                    for rid in f_vars[pid][tid][hid]:
                        if first == True:
                            first = False
                        else:
                            constraint += ' + '
                        constraint += 'f_p%d_t%d_h%d_r%d' % (pid,tid,hid,rid)
                if first == True:
                    constraint += '0'
                constraint += ' = 1\n'
                f.write('C%d: %s' % (constraint_count, constraint))
                constraint_count += 1

        # constraint (c)
        for pid_1_it in range(0, len(presenters)):
            pid_1 = presenters[pid_1_it]
            for tid in gives_talk[pid_1]:
                if len(talk_given_by[tid]) == 1:
                    continue # single presenter, constraint (c) is inert
                for pid_2_it in range(0, len(talk_given_by[tid])):
                    pid_2 = talk_given_by[tid][pid_2_it]
                    if pid_2 <= pid_1:
                        continue # the arrays are sorted so we know we already dealt with this one
                    # index by pid_1 for hour and room availability. when we get to pid_2
                    # if these sets don't have some intersection then this will make the schedule
                    # infeasible. we may have to slightly expand f_vars in this case
                    pid1_hours_not_in_pid2 = []
                    pid2_hours_not_in_pid1 = []
                    rooms_union = set()
                    for hid in f_vars[pid_1][tid].keys():
                        if hid not in f_vars[pid_2][tid].keys():
                            pid1_hours_not_in_pid2.append(hid)
                        rooms_union = rooms_union.union(f_vars[pid_1][tid][hid])
                    for hid in f_vars[pid_2][tid].keys():
                        if hid not in f_vars[pid_2][tid].keys():
                            pid2_hours_not_in_pid1.append(hid)
                        rooms_union = rooms_union.union(f_vars[pid_1][tid][hid])
                    hours_union = set(f_vars[pid_1][tid].keys()).union(set(f_vars[pid_2][tid].keys()))
                    # we now know which hours are missing from each presenter
                    # we will expand f_vars to include these, but explicitly say that they must be zero
                    for hid in pid1_hours_not_in_pid2:
                        f.write('\\* Presenter %d and %d share talk %d, but %d is not available at %d, so make sure they can\'t be scheduled then *\\\n' % (pid_1, pid_2, tid, pid_2, hid))
                        f_vars[pid_2][tid][hid] = rooms_union()
                        first = True
                        constraint = ''
                        for rid in f_vars[pid_2][tid][hid]:
                            if first == True:
                                first = False
                            else:
                                constraint += ' + '
                            constraint += 'f_p%d_t%d_h%d_r%d' % (pid_2, tid, hid, rid)
                        constraint += ' = 0\n'
                        f.write('C%d: %s' % (constraint_count, constraint))
                        constraint_count += 1
                    for hid in pid2_hours_not_in_pid1:
                        f.write('\\* Presenter %d and %d share talk %d, but %d is not available at %d, so make sure they can\'t be scheduled then *\\\n' % (pid_1, pid_2, tid, pid_1, hid))
                        f_vars[pid_1][tid][hid] = rooms_union()
                        first = True
                        constraint = ''
                        for rid in f_vars[pid_1][tid][hid]:
                            if first == True:
                                first = False
                            else:
                                constraint += ' + '
                            constraint += 'f_p%d_t%d_h%d_r%d' % (pid_1, tid, hid, rid)
                        constraint += ' = 0\n'
                        f.write('C%d: %s' % (constraint_count, constraint))
                        constraint_count += 1
                    for hid in hours_union:
                        for rid in rooms_union:
                            f.write('\\* Presenter %d and %d share talk %d, so they must have the same schedule for for this talk at hour %d in room %d *\\\n' % (pid_1, pid_2, tid, hid, rid))
                            f.write('C%d: f_p%d_t%d_h%d_r%d - f_p%d_t%d_h%d_r%d = 0\n' % (constraint_count, pid_1, tid, hid, rid, pid_2, tid, hid, rid))
                            constraint_count += 1

        # constraint (d)
        for pid in f_vars.keys():
            for hid in hours:
                first = True
                constraint = ''
                for tid in f_vars[pid].keys():
                    if hid not in f_vars[pid][tid].keys():
                        continue
                    for rid in f_vars[pid][tid][hid]:
                        if first == True:
                            first = False
                        else:
                            constraint += ' + '
                        constraint += 'f_p%d_t%d_h%d_r%d' % (pid, tid, hid, rid)
                if first == False:
                    f.write('\\* Presenter %d can only give at most one talk at hour %d *\\\n' % (pid, hid))
                    f.write('C%d: %s <= 1\n' % (constraint_count, constraint))
                    constraint_count += 1

        # constraint (e)
        # We use a bool cast/implication trick to make g : talk x hour x room -> 0,1 == 1 <=> the jth talk is being given at hour h in room r
        upper_bound = 2 * len(presenters) * len(rooms) * len(talks)
        for tid in talks:
            for hid in talk_really_available[tid].keys():
                for rid in talk_really_available[tid][hid]:
                    first = True
                    constraint = ''
                    for pid in talk_given_by[tid]:

                        # Our previous code created the union of possibly nonequal hid/rid combos for copresenters
                        # So, we know f_vars really has this varirable -- the following code asserts this
                        a = rid in f_vars[pid][tid][hid]
                        if a == False:
                            raise 'Inconsistent f_vars'

                        if not tid in g_vars:
                            g_vars[tid] = {}
                        if not hid in g_vars[tid]:
                            g_vars[tid][hid] = set()
                        g_vars[tid][hid].add(rid)
                        if first == True:
                            first = False
                        else:
                            constraint += ' + '
                        constraint += 'f_p%d_t%d_h%d_r%d' % (pid,tid,hid,rid)
                    constraint += ' - %d g_t%d_h%d_r%d <= 0' % (upper_bound,tid,hid,rid)
                    f.write('\\* Sum the presenter entries for talk %d at hour %d in room %d; creates g *\\\n' % (tid, hid, rid))
                    f.write('C%d: %s\n' % (constraint_count, constraint))
                    constraint_count += 1
        for hid in real_availability_of_talks.keys():
            for rid in real_availability_of_talks[hid].keys():
                first = True
                constraint = ''
                for tid in real_availability_of_talks[hid][rid]:
                    # assert the consistency of g
                    a = rid in g_vars[tid][hid]
                    if a == False:
                        raise 'Inconsistent g_vars'
                    if first == True:
                        first = False
                    else:
                        constraint += ' + '
                    constraint += 'g_t%d_h%d_r%d' % (tid,hid,rid)
                f.write('\\* Of all talks that can be scheduled at hour %d in room %d, at most 1 is *\\\n' % (hid, rid))
                f.write('C%d: %s <= 1\n' % (constraint_count, constraint))
                constraint_count += 1




        # TODO: Bounds for the c matrix

        # The f and g values are binaries
        f.write('Binaries\n')
        for pid in f_vars.keys():
                for tid in f_vars[pid].keys():
                    for hid in f_vars[pid][tid].keys():
                        for rid in f_vars[pid][tid][hid]:
                            f.write('f_p%d_t%d_h%d_r%d\n' % (pid,tid,hid,rid))
        for tid in g_vars.keys():
            for hid in g_vars[tid].keys():
                for rid in g_vars[tid][hid]:
                    f.write('g_t%d_h%d_r%d\n' % (tid,hid,rid))

        f.write('End\n')