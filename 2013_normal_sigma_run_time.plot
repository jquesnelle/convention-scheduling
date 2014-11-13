set terminal latex
set output "2013_normal_sigma_run_time.tex"
set format xy "$%g$"
set tics out nomirror
set xlabel "$\\sigma$"
set ylabel "\\rotatebox{90}{Run time (log scale)}"
set logscale y
plot [400:100] "2013_normal_sigma_run_time.dat" using 1:2 title 'normal rooms' with linespoints, "2013_normal_sigma_run_time.dat" using 1:3 title 'room classes' with linespoints
