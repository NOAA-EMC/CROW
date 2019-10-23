This example is the problem statement that I am experiencing:

I am trying to set up some kind of central place where all 
information of resource settings (case, user, platform, default)
being merged together. However, as shown in execution, the
variables of resource_sum is still "!calc" string instead of
actual values

In this example, the dump of resource_sum comes from default and case. 
run_job1 is overriden by case settings and with clear 
final value, while run_job2 is still with the original
!calc string.

It will be much better if final values could be parsed into all
the fields of resource_sum
