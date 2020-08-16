zone1.com - Check import for sample zone file with all record type in it.
zone2.com - Check import for preserving TXT record space preservation, long text record. SPF record to be imported as TXT and default TTL for record
zone3.com – Check import for zone file with Missing name in record set to reuse previous name, Missing class, Multi line record
zone4.com – Check TTL calculation to take lowest for record, Check for conflicting TTLs on records with the same name
zone5.com - checks fqdn with different $ORIGIN, checks different $ORIGIN are picked up and Check $ORIGIN from outside zone is permitted (but not for record names), Also check that $ORIGIN without '.' terminator has one added (and a warning)
zone6.com - Check @ A record import
zone7.com - Check @ TXT record import
zone8.com – Check * A record import
zone.local – Check for the warning while creating private DNS zones with .local at end.
