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
    presenter_available = {}
    talk_available = {}
    room_available = {}
    times_talk_given = {}
    has_conflict = set()
    conflict_pairs = set()

    for gives_talk_row in c.execute('SELECT pid, tid FROM gives_talk'):
        pid = gives_talk_row[0]
        tid = gives_talk_row[1]
        if pid not in gives_talk:
            gives_talk[pid] = {}
        if tid not in gives_talk[pid]:
            gives_talk[pid][tid] = 0
        gives_talk[pid][tid] += 1
        if tid not in talk_given_by:
            talk_given_by[tid] = [pid]
        else:
            talk_given_by[tid].append(pid)

    for tid in talks:
        times_talk_given[tid] = gives_talk[next(iter(talk_given_by[tid]))][tid] # the schedule is infeasible by requirement (c) if this doesn't match for all presenters, so just pick the first

    f_vars = {}
    g_vars = {}
    z_vars = {}
    c_vars = {}
    constraint_count = 0

    if not 'naive' in type:
        # this will generate the feasible schedule. for any row in this query, pid is available at hid,
        # tid is available at gid, rid is suitable for tid and tid is available at hid.
        # by only using these variables, we effectively enforce constraint (a)
        possible_schedule = c.execute("SELECT gt.pid, gt.tid, h.hid, rs.rid FROM hours h, gives_talk gt, "
                                      "talk_available ta, room_suitable_for rs, room_available ra, "
                                      "presenter_available pa WHERE rs.rid=ra.rid and rs.tid=gt.tid and ra.hid=h.hid "
                                      "and ta.tid=gt.tid and h.hid=ta.hid and gt.pid=pa.pid and h.hid=pa.hid GROUP BY "
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
    else:
        for presenter_available_row in c.execute('SELECT pid, hid FROM presenter_available'):
            pid = int(presenter_available_row[0])
            hid = int(presenter_available_row[1])
            if not pid in presenter_available:
                presenter_available[pid] = set()
            presenter_available[pid].add(hid)
        for talk_available_row in c.execute('SELECT tid, hid FROM talk_available'):
            tid = int(talk_available_row[0])
            hid = int(talk_available_row[1])
            if not tid in talk_available:
                talk_available[tid] = set()
            talk_available[tid].add(hid)
        for room_available_row in c.execute('SELECT rid, hid FROM room_available'):
            rid = int(room_available_row[0])
            hid = int(room_available_row[1])
            if not rid in room_available:
                room_available[rid] = set()
            room_available[rid].add(hid)

    with open(db_path + '.lp', 'w') as f:
        f.write('Minimize\nobj: ')

        if 'ecttd' in type:
            if not 'naive' in type:
                # Note, this doesn't include the extended f_vars when copresenters have different availabilities --
                # but as of now this never happens
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
                first = True
                for pid in presenters:
                    for tid in talks:
                        for hid in hours:
                            for rid in rooms:
                                if first == True:
                                    first = False
                                else:
                                    f.write(' + ')
                                f.write('f_p%d_t%d_h%d_r%d' % (pid,tid,hid,rid))
        elif 'pco' in type:
            # Minimize "c" which will be matrix of  talk x talk x hour -> rsvp conflicts
            first = True
            for aid in attendees:
                attendee_interests = c.execute('SELECT tid FROM attendee_interest WHERE aid=? ORDER BY tid ASC', (aid,)).fetchall()
                if len(attendee_interests) < 2:
                    continue # no possible conflicts for this attendee
                for i in range(0, len(attendee_interests)):
                    tid_1 = int(attendee_interests[i][0])
                    for j in range(i + 1, len(attendee_interests)): # the c matrix is symmetric for a given attendee, i.e c_eij = c_eji
                        tid_2 = int(attendee_interests[j][0])
                        for hid in set(talk_really_available[tid_1].keys()).intersection(set(talk_really_available[tid_2].keys())):
                            # these two talks can be scheduled at the same time and this attendee has indicated interest; there will be a penalty if these two are scheduled at the same time
                            if tid_2 in c_vars.keys():
                                if tid_1 in c_vars[tid_2].keys():
                                    break
                            if not tid_1 in c_vars:
                                c_vars[tid_1] = {}
                            if not tid_2 in c_vars[tid_1]:
                                c_vars[tid_1][tid_2] = {}
                            if not hid in c_vars[tid_1][tid_2]:
                                c_vars[tid_1][tid_2][hid] = 0
                            c_vars[tid_1][tid_2][hid] += 1
                            if c_vars[tid_1][tid_2][hid] == 1:
                                if first == True:
                                    first = False
                                else:
                                    f.write(' + ')
                                f.write('c_t%d_t%d_h%d' % (tid_1, tid_2, hid))
                                has_conflict.add(tid_1)
                                has_conflict.add(tid_2)
                                conflict_pairs.add((tid_1, tid_2))
                                conflict_pairs.add((tid_2, tid_1))

        f.write('\nSubject To\n')

        if 'naive' in type:
            # constraint (a)
                for hid in hours:
                    for pid in presenters:
                        avail = True
                        if not hid in presenter_available[pid]:
                            avail = False
                            # f.write('\\* Presenter %d is not available at hour %d *\\\n' % (pid, hid))
                        for tid in talks:
                            if not hid in talk_available[tid]:
                                avail = False
                                # f.write('\\* Talk %d is not available at hour %d *\\\n' % (tid, hid))
                            for rid in rooms:
                                if not hid in room_available[rid]:
                                    avail = False
                                    # f.write('\\* Room %d is not available at hour %d *\\\n' % (rid, hid))
                                if avail == False:
                                    f.write('C%d: f_p%d_t%d_h%d_r%d = 0\n' % (constraint_count, pid,tid,hid,rid))
                                    constraint_count += 1

        # constraint (b)
        if not 'naive' in type:
            for pid in f_vars.keys():
                for tid in f_vars[pid].keys():
                    talk_instances = gives_talk[pid][tid]
                    f.write('\\* Presenter %d is scheduled for talk %d exactly %d times *\\\n' % (pid, tid, talk_instances))
                    first = True
                    constraint = ''
                    for hid in f_vars[pid][tid].keys():
                        for rid in f_vars[pid][tid][hid]:
                            if first == True:
                                first = False
                            else:
                                constraint += ' + '
                            constraint += 'f_p%d_t%d_h%d_r%d' % (pid,tid,hid,rid)
                    if first == True:
                        constraint += '0'
                    constraint += ' = %d\n' % (talk_instances,)
                    f.write('C%d: %s' % (constraint_count, constraint))
                    constraint_count += 1
        else:
            for pid in presenters:
                for tid in talks:
                    if not pid in gives_talk:
                        continue
                    if tid in gives_talk[pid]:
                        talk_instances = gives_talk[pid][tid]
                        # f.write('\\* Presenter %d is scheduled for talk %d exactly %d times *\\\n' % (pid, tid, talk_instances))
                        first = True
                        constraint = ''
                        for hid in hours:
                            for rid in rooms:
                                if first == True:
                                    first = False
                                else:
                                    constraint += ' + '
                                constraint += 'f_p%d_t%d_h%d_r%d' % (pid,tid,hid,rid)
                        if first == True:
                            constraint += '0'
                        constraint += ' = %d\n' % (talk_instances,)
                        f.write('C%d: %s' % (constraint_count, constraint))
                        constraint_count += 1



        # constraint (c)
        if not 'naive' in type:
            for pid_1_it in range(0, len(presenters)):
                pid_1 = presenters[pid_1_it]
                if not pid_1 in gives_talk:
                    continue
                for tid in gives_talk[pid_1].keys():
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
        else:
            for pid_1 in presenters:
                for pid_2 in presenters:
                    if pid_2 <= pid_1:
                        continue
                    for tid in talks:
                        if pid_1 in talk_given_by[tid] and pid_2 in talk_given_by[tid]:
                            for hid in hours:
                                for rid in rooms:
                                    # f.write('\\* Presenter %d and %d share talk %d, so they must have the same schedule for for this talk at hour %d in room %d *\\\n' % (pid_1, pid_2, tid, hid, rid))
                                    f.write('C%d: f_p%d_t%d_h%d_r%d - f_p%d_t%d_h%d_r%d = 0\n' % (constraint_count, pid_1, tid, hid, rid, pid_2, tid, hid, rid))
                                    constraint_count += 1

        # constraint (d)
        if not 'naive' in type:
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
                        # f.write('\\* Presenter %d can only give at most one talk at hour %d *\\\n' % (pid, hid))
                        f.write('C%d: %s <= 1\n' % (constraint_count, constraint))
                        constraint_count += 1
        else:
            for pid in presenters:
                for hid in hours:
                    first = True
                    constraint = ''
                    for tid in talks:
                        for rid in rooms:
                            if first == True:
                                first = False
                            else:
                                constraint += ' + '
                            constraint += 'f_p%d_t%d_h%d_r%d' % (pid, tid, hid, rid)
                    if first == False:
                        #f.write('\\* Presenter %d can only give at most one talk at hour %d *\\\n' % (pid, hid))
                        f.write('C%d: %s <= 1\n' % (constraint_count, constraint))
                        constraint_count += 1


        # constraint (e)
        # We use a bool cast/implication trick to make g : talk x hour x room -> 0,1 == 1 <=> the jth talk is being given at hour h in room r
        upper_bound = 2 * len(presenters)
        if not 'naive' in type:
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
                        '''
                        for pid in talk_given_by[tid]:
                            if not tid in g_vars:
                                g_vars[tid] = {}
                            if not hid in g_vars[tid]:
                                g_vars[tid][hid] = set()
                            g_vars[tid][hid].add(rid)
                            f.write('C%d: f_p%d_t%d_h%d_r%d - g_t%d_h%d_r%d <= 0\n' % (constraint_count, pid,tid,hid,rid, tid,hid,rid)) # gives the correct answer with = 0, but this is WRONG?!?!?!?!?
                            constraint_count += 1
                        '''
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
        else:
            for tid in talks:
                for hid in hours:
                    for rid in rooms:
                        first = True
                        constraint = ''
                        for pid in presenters:
                            if first == True:
                                first = False
                            else:
                                constraint += ' + '
                            constraint += 'f_p%d_t%d_h%d_r%d' % (pid,tid,hid,rid)
                        constraint += ' - %d g_t%d_h%d_r%d <= 0' % (upper_bound,tid,hid,rid)
                        # f.write('\\* Sum the presenter entries for talk %d at hour %d in room %d; creates g *\\\n' % (tid, hid, rid))
                        f.write('C%d: %s\n' % (constraint_count, constraint))
                        constraint_count += 1
            for hid in hours:
                for rid in rooms:
                    first = True
                    constraint = ''
                    for tid in talks:
                        if first == True:
                            first = False
                        else:
                            constraint += ' + '
                        constraint += 'g_t%d_h%d_r%d' % (tid,hid,rid)
                    # f.write('\\* Of all talks that can be scheduled at hour %d in room %d, at most 1 is *\\\n' % (hid, rid))
                    f.write('C%d: %s <= 1\n' % (constraint_count, constraint))
                    constraint_count += 1


        # deal with rsvp conflicts
        upper_bound = 2 *len(rooms)
        if 'pco' in type:
            # use the boolean cast trick again to collapse G to Z : talk x hour
            for tid in has_conflict:
                for hid in talk_really_available[tid].keys():
                    first = True
                    constraint = ''
                    for rid in talk_really_available[tid][hid]:
                        if not tid in z_vars:
                            z_vars[tid] = set()
                        z_vars[tid].add(hid)
                        if first == True:
                            first = False
                        else:
                            constraint += ' + '
                        constraint += 'g_t%d_h%d_r%d' % (tid,hid,rid)
                    constraint += ' - %d z_t%d_h%d <= 0' % (upper_bound,tid,hid)
                    f.write('\\* Sum the room entries for talk %d at hour %d; creates z *\\\n' % (tid, hid))
                    f.write('C%d: %s\n' % (constraint_count, constraint))
                    constraint_count += 1
            for tid in has_conflict:
                first = True
                constraint = ''
                for hid in talk_really_available[tid].keys():
                    if first == True:
                        first = False
                    else:
                        constraint += ' + '
                    constraint += 'z_t%d_h%d' % (tid,hid)
                constraint += ' = %d' % (times_talk_given[tid])
                f.write('\\* Talk %d must be given exactly %d times *\\\n' % (tid, times_talk_given[tid]))
                f.write('C%d: %s\n' % (constraint_count, constraint))
                constraint_count += 1
            # use boolean cast trick to calculate z' : talk x talk x hour
            for tid_1 in c_vars.keys():
                for tid_2 in c_vars[tid_1].keys():
                    for hid in c_vars[tid_1][tid_2]:
                        f.write('C%d: z_t%d_h%d + z_t%d_h%d - 2 zp_t%d_t%d_h%d <= 1\n' % (constraint_count, tid_1,hid, tid_2,hid, tid_1,tid_2,hid))
                        constraint_count += 1

            # give c matrix the correct values
            for tid_1 in c_vars.keys():
                for tid_2 in c_vars[tid_1].keys():
                    for hid in c_vars[tid_1][tid_2]:
                        f.write('C%d: c_t%d_t%d_h%d - %d zp_t%d_t%d_h%d = 0\n' % (constraint_count, tid_1,tid_2,hid, c_vars[tid_1][tid_2][hid], tid_1,tid_2,hid))
                        constraint_count += 1

        f.write('Generals\n')
        for tid_1 in c_vars.keys():
            for tid_2 in c_vars[tid_1].keys():
                for hid in c_vars[tid_1][tid_2]:
                    f.write('c_t%d_t%d_h%d\n' % (tid_1, tid_2, hid))

        # The f and g values are binaries
        f.write('Binaries\n')
        if not 'naive' in type:
            for pid in f_vars.keys():
                    for tid in f_vars[pid].keys():
                        for hid in f_vars[pid][tid].keys():
                            for rid in f_vars[pid][tid][hid]:
                                f.write('f_p%d_t%d_h%d_r%d\n' % (pid,tid,hid,rid))
            for tid in g_vars.keys():
                for hid in g_vars[tid].keys():
                    for rid in g_vars[tid][hid]:
                        f.write('g_t%d_h%d_r%d\n' % (tid,hid,rid))
            size_of_z = 0
            for tid in z_vars.keys():
                size_of_z += len(z_vars[tid])
                for hid in z_vars[tid]:
                    f.write('z_t%d_h%d\n' % (tid, hid))
            size_of_c = 0
            for tid_1 in c_vars.keys():
                for tid_2 in c_vars[tid_1].keys():
                    size_of_c += len(c_vars[tid_1][tid_2])
                    for hid in c_vars[tid_1][tid_2]:
                        f.write('zp_t%d_t%d_h%d\n' % (tid_1, tid_2, hid))
            print '|z| = %d' % (size_of_z,)
            print '|c| = %d' % (size_of_c,)
        else:
            for pid in presenters:
                    for tid in talks:
                        for hid in hours:
                            for rid in rooms:
                                f.write('f_p%d_t%d_h%d_r%d\n' % (pid,tid,hid,rid))
            for tid in talks:
                for hid in hours:
                    for rid in rooms:
                        f.write('g_t%d_h%d_r%d\n' % (tid,hid,rid))

        f.write('End\n')