grep -E "required [0-9]+ cycles" real_run.log | awk '{print "Latency (ms) : " $3/200000000*1000}'
grep -E "required [0-9]+ cycles" real_run.log | awk '{print "OP/cycle : " 2005750000*2/$3}'
grep -E "required [0-9]+ cycles" real_run.log | awk '{print "GOP/s : " 2005750000*2*0.2/$3}'
grep -E "required [0-9]+ cycles" real_run.log | awk '{print "DSP efficiency : " 2005750000*2/$3/414/2}'
grep "ALM: " build_synth/build/output_files/afu_default.fit.summary
grep "DSP: " build_synth/build/output_files/afu_default.fit.summary
grep "Average interconnect usage" build_synth/build/output_files/afu_default.fit.rpt | grep -oP '\d+(\.\d+)?%' | head -n1 | awk '{print "Average Routing Congestion: " $0}'
grep "Peak interconnect usage" build_synth/build/output_files/afu_default.fit.rpt | grep -oP '\d+(\.\d+)?%' | head -n1 | awk '{print "Peak Routing Congestion: " $0}'