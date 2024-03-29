# Scripts
A collection of scripts

## vm-exec
Executes a preconfigured program on a windows VM using VirtualBox.
Uses a shared folder to pass file arguments and copy changes back out.

### Setup
Set up a Windows VM using VirtualBox and install some program you want to use.
Configure a user without login password and set up a auto-mounted shared folder (called the DMZ in the script).
Make sure to specify a guest-side mount point.

Edit the variables in `vm-exec`to correspond to the virtual machine and the windows program.

The Windows guest also needs to configured to allow passwordless shell logons:
Go into `Local Security Policy` Settings, under `Accounts` and set `Limit local account use...` to `Disabled`-

### Usage
Executing the script with a file as argument forwards the file to the virtual machine and propagates any changes back.

The VM is started and stopped automatically when the wrapped program is started or stops.

Host-side edits to the file are not forwarded to the virtual machine.

## xssh
A script that initiaties a ssh session with X11 and Pulseaudio forwarding

### Setup
Obviously, both client and server need to have X and pulseaudio installed.

#### on Server
The server needs to have the `pax11publish` utility installed (usually supplied by the `pulseaudio-utils` package)

#### on Client
The client needs to configure its pulseaudio server to accept remote connection.

To do this, use `paprefs` to `Enable network access to local sound device` and enable `Don't require Authentication`

Make sure to restart pulseaudio after this.

##### Troubleshooting
If the options in `paprefs` are greyed out, it's probably due to version discrepancies between paprefs and pulseaudio.

To fix it, run `strace paprefs 2>&1 | grep /lib/pulse` and check the pulseaudio version numbers.

Then, check `/usr/lib/pulse*`.
If the versions doesn't match, simply create a symlink in `/usr/lib` from paprefs' version to the actually installed version.

### Usage
Simply run `xssh host` to connect to the host as with ssh.

Alternatively, use `xssh` to connect to the last used host.
(This information is stored in `~/.config/xssh-host` and updated on running the regular command)

## fail2ban-ips, ips-whois, whois-ipset
Scripts to build an ipset from fail2ban logs or other IPs.
Example combined usage:
```sh
	sudo ./fail2ban-ips | ./ips-whois > whois-data
	sudo whois-ipset whois-data IPSetHere "black listed domains here" "white listed domains here"
```

### fail2ban-ips
Exports every offender IP detected by fail2ban

### ips-whois
Uses whois records to find the subnets in a list of IPs.
Then use abuse/email records to identify the providers of those subnets.

### whois-ipset
Use the whois information from `ips-whois` to interactively build an IPset containing offending subnets.
Uses the identified providers for filtering the sets.

## sound-webm
Adds the sound to a webm or image created for the [4chan external sound](https://sleazyfork.org/en/scripts/31045-4chan-external-sounds) userscript.

## find-dupes
Finds all duplicate files (by MD5) in the current directory tree.

# Dotfiles
A collection of my config files

## .Xmodmap
Custom key maps to type ʋ,Ʋ, ə and ɾ for IPA.
Move to `~` to enable on boot.

## uca.xml
Custom actions for Thunar
- Open a terminal emulator
- Play audio using mpv (forces it to show GUI) 
- Open VS code
- Convert a .webp image to a .png or .jpg with image magick
- run a script with bash
- shortcut for the `sound-webm` script

To install, move to `~/.config/Thunar/uca.xml`.
Note that that file probably already exists & you probably want to merge the XML by hand.

