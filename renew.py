#!/usr/bin/python
# acme-renew.py: Performs ACME renewal using acme-tiny. Automatically generates fresh CSRs (possibly with domain aliases) from available keys
# You need a sudoers config like `acme ALL=(root) NOPASSWD: /bin/systemctl reload nginx.service` to install certs into a live nginx instance
import os
import sys
from pathlib import Path
from datetime import date, datetime
import subprocess
import shlex
import re

# dir in which keys live (RSA keys named {domain}.key along with one {account}.key)
KEY_DIR="/srv/acme"
# dir in which certificates live (also used for temporary CSR files)
CERT_DIR="/var/ssl"
# dir in which we host challenge files
ACME_DIR="/var/www/acme-challenge"
# dir in which alias configurations live (plain text files that list out every alias domain. Domain names (including the key name) must not be repeated)
ALIAS_DIR=KEY_DIR
# set to true to only print required commands
DRY=False
# minimum age of a cert (in seconds) to refresh (key or alias change always forces refresh)
MIN_AGE=60*60*24*3

account_key = Path(KEY_DIR).joinpath("account.key")

if not account_key.is_file():
	print(f"No account key configured; Generate it with e.g. 'openssl genrsa 4096 > {account_key}'", file=sys.stderr)
	sys.exit(1)

def fmt_cmd(cmd : list[str], redirect : Path|None = None) -> str:
	return shlex.join(cmd) + (f" > {shlex.quote(str(redirect))}" if redirect else "")

def age(f : Path) -> float:
	""" The age of the given file in seconds, or positive infinity if it doesn't exist """
	return (datetime.now().timestamp() - f.stat().st_mtime) if f.is_file() else float("inf")

HOST_LABEL = r"(?!-)[a-z0-9-]{1,63}(?<!-)"
HOSTNAME = re.compile(rf"(?:{HOST_LABEL}\.)*{HOST_LABEL}", re.ASCII | re.IGNORECASE)

def valid_hostname(name : str) -> bool:
	""" Whether name is a plain ASCII (LDH) DNS name; IDNs must be given in punycode """
	return len(name) <= 253 and HOSTNAME.fullmatch(name) is not None

def renew_cert(domain : str, key_file : Path, alias_file : Path, csr_file : Path, tmp_cert : Path, real_cert : Path) -> bool:
	""" Renews a cert if required. Returns false if its up-to-date and true if it was changed. """
	all_domains = [domain]

	if alias_file.is_file():
		all_domains += alias_file.read_text().split()

	if bad := [ d for d in all_domains if not valid_hostname(d) ]:
		raise ValueError(f"Invalid domain name(s): {', '.join(map(repr, bad))}")

	cert_age = age(real_cert)

	if cert_age < min(MIN_AGE, age(key_file), age(alias_file)):
		print(f"{"# " if DRY else ""}{str(real_cert)} is up to date ({round(cert_age / 60, 1)}min old)")
		return False


	csr_cmd = [ "openssl", "req", "-new", "-sha256", "-key", str(key_file) ]

	dn = ", ".join([ f"DNS:{str(x)}" for x in all_domains ])
	csr_cmd += [ "-subj", "/", "-addext", f"subjectAltName = {dn}" ]

	if DRY:
		print(fmt_cmd(csr_cmd, csr_file))
	else:
		with csr_file.open("w") as f:
			r = subprocess.run(csr_cmd, stdout = f)

		if r.returncode != 0:
			csr_file.unlink(True)
			raise RuntimeError(f"Failed to generate signing request for {domain}!")

	acme_cmd = [ "acme-tiny", "--account-key", str(account_key), "--csr", str(csr_file), "--acme-dir", ACME_DIR ]

	if DRY:
		print(fmt_cmd(acme_cmd, tmp_cert))
		print(fmt_cmd([ "chmod", "440", str(tmp_cert) ]))
		print(fmt_cmd([ "mv", str(tmp_cert), str(real_cert) ]))
	else:
		tmp_cert.unlink(True)
		# atomic create to avoid race condition where cert may be temporarily readable
		fd = os.open(tmp_cert, os.O_CREAT | os.O_WRONLY | os.O_EXCL | os.O_NOFOLLOW, 0o640)

		with os.fdopen(fd, "w") as f:
			r = subprocess.run(acme_cmd, stdout = f)

		if r.returncode != 0:
			tmp_cert.unlink(True)
			raise RuntimeError(f"Renewal failed! Rejected CSR kept at {str(csr_file)}")

		csr_file.unlink()
		tmp_cert.chmod(0o440) # make readonly
		tmp_cert.move(real_cert)

	return True

any_fail=False
any_succeed=False

for key_file in Path(KEY_DIR).glob("*.key"):
	domain = key_file.name.removesuffix(".key")

	if domain == "account":
		continue

	alias_file = Path(ALIAS_DIR).joinpath(f"{domain}.alias")
	t=date.today().isoformat()
	csr_file = Path(CERT_DIR).joinpath(f"{domain}.{t}.csr")
	tmp_cert = Path(CERT_DIR).joinpath(f"{domain}.{t}.crt")
	real_cert = Path(CERT_DIR).joinpath(f"{domain}.crt")

	try:
		if renew_cert(domain, key_file, alias_file, csr_file, tmp_cert, real_cert):
			any_succeed = True
	except Exception as e:
		print(f"{domain}: {e}", file=sys.stderr)
		any_fail = True

if any_succeed:
	reload_cmd = [ "sudo", "systemctl", "reload", "nginx.service" ]

	if DRY:
		print(fmt_cmd(reload_cmd))
	else:
		print("Loading new certificates...")
		r = subprocess.run(reload_cmd)

		if r.returncode != 0:
			print("Could not update live nginx certs!", file=sys.stderr)
			sys.exit(1)

if any_fail:
	sys.exit(1)
else:
	print("Renewal OK!")
