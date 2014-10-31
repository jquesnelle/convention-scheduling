#!/bin/bash
echo "Generating database"
python main.py --generate-db schedule2013.html
echo "Setting up database with $1 talks"
python main.py --setup-db schedule2013.html.db $1 $2 $3
echo "Generating model"
python main.py --generate-model-ecttd schedule2013.html.db
echo "Solving model"
cbc schedule2013.html.db.lp -solve -solu output.sol
echo "Importing solution"
python main.py --import-solution schedule2013.html.db output.sol
echo "Generating report"
python main.py --generate-report schedule2013.html.db