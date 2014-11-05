set terminal latex
set output "ecttd_model_run_time.tex"
set format xy "$%g$"
set tics out nomirror
set xlabel "Number of talks"
set ylabel "\\rotatebox{90}{Run time}"
plot "ecttd_model_run_time.dat" using 1:2 title '' with linespoints
