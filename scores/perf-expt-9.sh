total_cycles=$(awk '/Execution time \(cycles\):/ {sum += $4} END {print sum}' $BASEDIR/tmp/expt-9.txt)
mean_cycles=$(awk -v c="$total_cycles" 'BEGIN {print c / 256}')

latency_ms=$(awk -v c="$mean_cycles" 'BEGIN {print c / 200000000 * 1000}')
echo "Latency (ms) : $latency_ms"
op_c=$(awk -v c="$mean_cycles" 'BEGIN {print 3987001832 * 2 / c}')
echo "OP/cycle : $op_c"
gops=$(awk -v c="$mean_cycles" 'BEGIN {print 3987001832 * 2 * 0.2 / c}')
echo "GOP/s : $gops"
dsp_eff=$(awk -v c="$mean_cycles" 'BEGIN {print 3987001832 / c / 510 / 2 * 100}')
echo "DSP efficiency (%) : $dsp_eff"

grep "ALM" $BASEDIR/pre_synthesis_cleaned/expt-9/build_synth/build/output_files/afu_default.fit.summary
grep "DSP" $BASEDIR/pre_synthesis_cleaned/expt-9/build_synth/build/output_files/afu_default.fit.summary
grep "Average interconnect usage" $BASEDIR/pre_synthesis_cleaned/expt-9/build_synth/build/output_files/afu_default.fit.rpt | grep -oP '\d+(\.\d+)?%' | head -n1 | awk '{print "Average Routing Congestion: " $0}'
grep "Peak interconnect usage" $BASEDIR/pre_synthesis_cleaned/expt-9/build_synth/build/output_files/afu_default.fit.rpt | grep -oP '\d+(\.\d+)?%' | head -n1 | awk '{print "Peak Routing Congestion: " $0}'