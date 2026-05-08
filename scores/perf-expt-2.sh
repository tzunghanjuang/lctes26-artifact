grep "The Fitter failed to successfully route the design." $BASEDIR/pre_synthesis_cleaned/expt-2/build_synth/build/output_files/afu_default.fit.route.rpt
grep "ALM" $BASEDIR/pre_synthesis_cleaned/expt-2/build_synth/build/output_files/afu_default.fit.summary
grep "DSP" $BASEDIR/pre_synthesis_cleaned/expt-2/build_synth/build/output_files/afu_default.fit.summary
grep "Average interconnect usage" $BASEDIR/pre_synthesis_cleaned/expt-2/build_synth/build/output_files/afu_default.fit.rpt | grep -oP '\d+(\.\d+)?%' | head -n1 | awk '{print "Average Routing Congestion: " $0}'
grep "Peak interconnect usage" $BASEDIR/pre_synthesis_cleaned/expt-2/build_synth/build/output_files/afu_default.fit.rpt | grep -oP '\d+(\.\d+)?%' | head -n1 | awk '{print "Peak Routing Congestion: " $0}'