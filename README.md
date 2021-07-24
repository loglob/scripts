# xssh
A script that initiaties a ssh session with X11 and Pulseaudio forwarding

## Setup
Obviously, both client and server need to have X and pulseaudio installed.

### on Server
The server needs to have the `pax11publish` utility installed (usually supplied by the `pulseaudio-utils` package)

### on Client
The client needs to configure its pulseaudio server to accept remote connection.

To do this, use `paprefs` to `Enable network access to local sound device` and enable `Don't require Authentication`

Make sure to restart pulseaudio after this.

#### Troubleshooting
If the options in `paprefs` are greyed out, it's probably due to version discrepancies between paprefs and pulseaudio.

To fix it, run `strace paprefs 2>&1 | grep /lib/pulse` and check the pulseaudio version numbers.

Then, check `/usr/lib/pulse*`.
If the versions doesn't match, simply create a symlink in `/usr/lib` from paprefs' version to the actually installed version.

## Usage
Simply run `xssh host` to connect to the host as with ssh.

Alternatively, use `xssh` to connect to the last used host.
(This information is stored in `~/.config/xssh-host` and updated on running the regular command)
