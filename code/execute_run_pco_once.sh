#!/bin/bash
echo "Generating database"
python main.py --generate-db schedule2013.html
echo "Setting up database with at most $1 talks/$2 hours, and $3 attendees with $4 rsvps each and sigma ratio $5"
python main.py --setup-db-2013normalclass schedule2013.html.db $1 $2 $3 $4 $5
echo "Generating model"
python main.py --generate-model-pcodualize schedule2013.html.db
echo "Solving model"
cbc schedule2013.html.db.lp -threads 6 -solve -solu output.sol 
echo "Importing solution"
python main.py --import-solution schedule2013.html.db output.sol
echo "Generating report"
python main.py --generate-report schedule2013.html.db
