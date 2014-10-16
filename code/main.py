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
    for i in range(1, len(sys.argv)):
        if sys.argv[i].startswith('--generate-db'):
            from generatedb import generate_db
            generate_db(sys.argv[i+1], sys.argv[i].endswith('-full'))
            i += 2
        elif sys.argv[i].startswith('--make-multi-presenter-graph'):
            from multipresentgraph import multi_presenter_graph
            multi_presenter_graph(sys.argv[i+1], sys.argv[i].endswith('-labels'))
            i += 2
        elif sys.argv[i] == '--generate-report':
            from generatereport import generate_report
            generate_report(sys.argv[i+1])
            i += 2
        elif sys.argv[i] == '--setup-db':
            pass
        elif sys.argv[i].startswith('--generate-model'):
            from generatemodel import generate_model
            generate_model(sys.argv[i+1], sys.argv[i].split('-')[-1])
            i += 2
        elif sys.argv[i] == '--import-solution':
            from importsolution import import_solution
            import_solution(sys.argv[i+1], sys.argv[i+2])

if __name__ == '__main__':
    main()