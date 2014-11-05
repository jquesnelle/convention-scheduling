set terminal png
set output "2013_uniform_rsvp_distribution.png"
set style fill solid 0.5 #fillstyle
set boxwidth 1
set tics out nomirror
set xlabel "Attendees"
set ylabel "Cumulative RSVPs"
plot "2013_uniform_rsvp_distribution.dat" u 1:2 smooth cumulative w lines notitle