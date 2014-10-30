set terminal latex
set output "ecttd_model_run_time.tex"
set format xy "$%g$"
set xlabel "number of talks"
set ylabel 'run \\ time'
plot "ecttd_model_run_time.dat" using 1:2 title '' with linespoints
