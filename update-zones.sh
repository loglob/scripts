#!/bin/bash

for z in db/*.zone
do
	echo -n "Updating $z..."

	if wget -q -O "$z" "https://www.ipdeny.com/ipblocks/data/countries/$(basename "$z")"
	then
		echo "OK"
	else
		echo $'\nFailed!'
		return 1
	fi
done

echo "Updated database. Run 'sudo load-ipset YOUR_SET' now"
