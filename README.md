satellite
=========

satellite.py script to interact with a satellite5.X/spacewalk server
can list machines,software and configuration channels,schedules file deployment and command execution, view last command executed, retrieves and uploads configuration files,...
needs a .satelliterc (will possibly be changed to satellite.ini or something like that in the future) to define credentials (and also custominfo that you want to be retrieved when running satellite.py -m)

Examples

MACHINE
#list machines
satellite.py -m

AK
#clone a AK
satellite.py --cloneak --ak 1-base-6.4 prout
#same with filters to change destinations
satellite.py --cloneak -8 6_4 -9 6_3 --ak 1-base-6_4 base-6_3


PROFILES
#list profiles
satellite.py -k
#clone profile
satellite.py  --cloneprofile --profile  testdev-ib-base-6_4 testpro-ib-base-6_4
#the same with filters
satellite.py  -8 6_4 -9 6_3 --cloneprofile --profile  testdev-ib-base-6_4 testpro-ib-base-6_3

#delete profile
satellite.py -7 testpro-ib-base-6_4

