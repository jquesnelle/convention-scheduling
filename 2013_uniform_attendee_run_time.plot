set terminal png
set output "2013_uniform_attendee_run_time.png"
set tics out nomirror
set xlabel "Number of talks"
set ylabel "Run time"
plot "2013_uniform_attendee_run_time.dat" using 1:2 title ''