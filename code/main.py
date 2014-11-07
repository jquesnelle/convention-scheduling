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

def main():
    i = 1
    if sys.argv[i].startswith('--generate-db'):
        from generatedb import generate_db
        generate_db(sys.argv[i+1], sys.argv[i].endswith('-full'))
    elif sys.argv[i].startswith('--make-multi-presenter-graph'):
        from multipresentgraph import multi_presenter_graph
        multi_presenter_graph(sys.argv[i+1], sys.argv[i].endswith('-labels'))
    elif sys.argv[i] == '--generate-report':
        from generatereport import generate_report
        generate_report(sys.argv[i+1])
    elif sys.argv[i].startswith('--generate-model'):
        from generatemodel import generate_model
        generate_model(sys.argv[i+1], sys.argv[i].split('-')[-1])
    elif sys.argv[i] == '--import-solution':
        from importsolution import import_solution
        import_solution(sys.argv[i+1], sys.argv[i+2])
    elif sys.argv[i].startswith('--setup-db'):
        from setupdb import setup_db
        if len(sys.argv) == 4:
            setup_db(sys.argv[i+1], int(sys.argv[i+2]), None, None)
        elif len(sys.argv) == 8:
            setup_db(sys.argv[i+1], int(sys.argv[i+2]), int(sys.argv[i+3]), int(sys.argv[i+4]), int(sys.argv[i+5]), sys.argv[i].split('-')[-1], float(sys.argv[i+6]))
    elif sys.argv[i] == '--make-rsvp-conflict-graph':
        from rsvpconflictgraph import rsvp_conflict_graph
        rsvp_conflict_graph(sys.argv[i+1])

if __name__ == '__main__':
    main()
