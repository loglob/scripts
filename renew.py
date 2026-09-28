#!/usr/bin/python
# acme-renew.py: Performs ACME renewal using acme-tiny. Automatically generates fresh CSRs (possibly with domain aliases) from available keys
import os
import sys
from pathlib import Path
from datetime import date, datetime
import subprocess

# dir in which keys live
KEY_DIR="/srv/acme"
# dir in which certificates live
CERT_DIR="/var/ssl"
# dir in which we host challenge files
ACME_DIR="/var/www/acme-challenge"
# dir in which alias configurations live
ALIAS_DIR=KEY_DIR
# set to true to only print required commands (May not be shell-safe due to subpar escaping)
DRY=False
# minimum age of a cert (in seconds) to refresh (key or alias change always forces refresh)
MIN_AGE=60*60*24*3

account_key = Path(KEY_DIR).joinpath("account.key")

if not account_key.is_file():
	print(f"No account key configured; Generate it with e.g. 'openssl genrsa 4096 > {account_key}'", file=sys.stderr)

any_fail=False
any_succeed=False

def fmt_cmd(cmd : list[str], redirect : Path|None = None) -> str:
	reserved = " <>#$"
	e = lambda s: f"'{s}'" if any(c in s for c in reserved) else s

	esc = [ e(s) for s in cmd ]

	if redirect:
		esc += [ '>', e(str(redirect)) ]

	return " ".join(esc)

for key_file in Path(KEY_DIR).glob("*.key"):
	domain = key_file.name.removesuffix(".key")

	if domain == "account":
		continue

	alias_file = Path(ALIAS_DIR).joinpath(f"{domain}.alias")
	all_domains = [domain] + (alias_file.read_text().split() if alias_file.is_file() else [])

	t=date.today().isoformat()
	csr_file = Path(CERT_DIR).joinpath(f"{domain}.{t}.csr")
	tmp_cert = Path(CERT_DIR).joinpath(f"{domain}.{t}.crt")
	real_cert = Path(CERT_DIR).joinpath(f"{domain}.crt")

	def age(f : Path) -> float:
		return (datetime.now().timestamp() - f.stat().st_mtime) if f.is_file() else float("inf")

	cert_age = age(real_cert)

	if cert_age < min(MIN_AGE, age(key_file), age(alias_file)):
		print(f"{"# " if DRY else ""}{str(real_cert)} is up to date ({round(cert_age / 60, 1)}min old)")
		continue


	csr_cmd = [ "openssl", "req", "-new", "-sha256", "-key", str(key_file) ]

	if len(all_domains) == 1:
		csr_cmd += [ "-subj", f"/CN={all_domains[0]}" ]
	else:
		dn = ", ".join([ f"DNS:{str(x)}" for x in all_domains ])
		csr_cmd += [ "-subj", "/", "-addext", f"subjectAltName = {dn}" ]

	if DRY:
		print(fmt_cmd(csr_cmd, csr_file))
	else:
		with csr_file.open("w") as f:
			r = subprocess.run(csr_cmd, stdout = f)

		if r.returncode != 0:
			any_fail = True
			print(f"Failed to generate signing request for {domain}!")
			csr_file.unlink(True)
			continue

	acme_cmd = [ "acme-tiny", "--account-key", str(account_key), "--csr", str(csr_file), "--acme-dir", ACME_DIR ]

	if DRY:
		print(fmt_cmd(acme_cmd, tmp_cert))
		print(fmt_cmd([ "chmod", "440", str(tmp_cert) ]))
		print(fmt_cmd([ "mv", str(tmp_cert), str(real_cert) ]))
	else:
		tmp_cert.unlink(True)
		# atomic create to avoid race condition where cert may be temporarily readable 
		fd = os.open(tmp_cert, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o640)

		with os.fdopen(fd, "w") as f:
			r = subprocess.run(acme_cmd, stdout = f)

		if r.returncode != 0:
			print(f"Renewal failed! Rejected CSR kept at {str(csr_file)}")
			any_fail = True
			tmp_cert.unlink(True)
			continue

		tmp_cert.chmod(0o440) # make readonly
		tmp_cert.move(real_cert)

	any_succeed = True

if any_succeed:
	reload_cmd = [ "sudo", "systemctl", "reload", "nginx.service" ]

	if DRY:
		print(fmt_cmd(reload_cmd))
	else:
		print("Loading new certificates...")
		subprocess.run(reload_cmd)

if any_fail:
	exit(1)
else:
	print("Renewal OK!")
