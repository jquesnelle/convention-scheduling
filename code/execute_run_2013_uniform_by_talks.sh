#!/bin/bash
s=10
while [ $s -le 250 ]
do
	python main.py --generate-db schedule2013.html
	echo "$s talks"
	for i in 1 2 3 4 5
	do
		python main.py --setup-db-2013 schedule2013.html.db $s 1000 1000 0
		python main.py --generate-model-pco schedule2013.html.db
		cbc schedule2013.html.db.lp -threads 6 -solve -solu output.sol | grep "Total time"
	done
	s=$((s + 10))
done