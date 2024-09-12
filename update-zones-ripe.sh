
#!/bin/bash

for z in db/*.zone
do
	echo -n "Updating $z..."
	country="$(basename "$z" .zone)"

	if (curl -s "https://stat.ripe.net/data/country-resource-list/data.json?v4_format=prefix&resource=$country" | jq -r '.data.resources.ipv4.[]' > "$z")
	then
		echo "OK"
	else
		echo $'\nFailed!'
		return 1
	fi
done

echo "Updated database. Run 'sudo load-ipset YOUR_SET' now"
