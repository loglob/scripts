#!/bin/env python3
import glob
import requests
import ipaddress

sets={}

for z in glob.glob("db/*.zone"):
	k = z.split('/')[1][:-5]
	sets[k] = []

print("Loading DB...", end= "")
raw = requests.get("https://raw.githubusercontent.com/sapics/ip-location-db/main/dbip-country/dbip-country-ipv4.csv").text
print("OK")

print("Parsing DB...", end= "")
for ln in raw.split('\n'):
	if(len(ln) == 0):
		continue

	f = ln.split(',')
	k = f[2].lower()

	if k in sets:
		start = ipaddress.IPv4Address(f[0])
		end = ipaddress.IPv4Address(f[1])
		sets[k] += [ str(cidr) + '\n' for cidr in ipaddress.summarize_address_range(start, end) ]
print("OK")

print("Writing zones...", end= "")
for k in sets:
	h = open(f"db/{k}.zone", "w")
	h.writelines(sets[k])
	h.close()
print("OK")
