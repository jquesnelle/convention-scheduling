#!/bin/bash
s=.40
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39
do
	echo "------------ sigma_ratio = $s -----------"
	for i in 1 2 3 4 5
	do
		python main.py --generate-db schedule2013.html
		python main.py --setup-db-2013normalclass schedule2013.html.db 100 14 1000 0 $s
		python main.py --generate-model-pco schedule2013.html.db
		mv schedule2013.html.db.lp ../instances/2013_normal-class_pco_decreasing_sigma/instance$s-$i.lp
	done
	s=$(echo "$s - 0.01"|bc)
done
