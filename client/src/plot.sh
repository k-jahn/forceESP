#!/bin/bash
gnuplot -persist <<-EOFMarker
    set title "$2, max $3[kg * g_e]" font ",14" textcolor rgbcolor "royalblue"
	set key autotitle columnhead
	unset key
	set xrange [0:$4]
	set xlabel "t [s]"
	set ylabel "f [kg * g_e]"
	set datafile separator ','
    plot "$1" with points
EOFMarker
