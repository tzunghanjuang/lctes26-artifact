grep -E "required [0-9]+ cycles" $BASEDIR/pre_synthesis_cleaned/expt-5/real_run.log | awk '{print "Latency (ms) : " $3/200000000*1000}'
grep -E "required [0-9]+ cycles" $BASEDIR/pre_synthesis_cleaned/expt-5/real_run.log | awk '{print "OP/cycle : " 2063692800*2/$3}'
grep -E "required [0-9]+ cycles" $BASEDIR/pre_synthesis_cleaned/expt-5/real_run.log | awk '{print "GOP/s : " 2063692800*2*0.2/$3}'
grep -E "required [0-9]+ cycles" $BASEDIR/pre_synthesis_cleaned/expt-5/real_run.log | awk '{print "DSP efficiency : " 2063692800*2/$3/1216/2}'
grep "ALM" $BASEDIR/pre_synthesis_cleaned/expt-5/build_synth/build/output_files/afu_default.fit.summary
grep "DSP" $BASEDIR/pre_synthesis_cleaned/expt-5/build_synth/build/output_files/afu_default.fit.summary
grep "Average interconnect usage" $BASEDIR/pre_synthesis_cleaned/expt-5/build_synth/build/output_files/afu_default.fit.rpt | grep -oP '\d+(\.\d+)?%' | head -n1 | awk '{print "Average Routing Congestion: " $0}'
grep "Peak interconnect usage" $BASEDIR/pre_synthesis_cleaned/expt-5/build_synth/build/output_files/afu_default.fit.rpt | grep -oP '\d+(\.\d+)?%' | head -n1 | awk '{print "Peak Routing Congestion: " $0}'