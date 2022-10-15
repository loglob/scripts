#!/bin/env bash
# sound-webm.sh: Adds sound to webms for the 4chan sound userscript
# Accepts a list of vidoes or images as input.
# Checks their filename for a tag like [sound=SOME_URL] that points to an audio file.
# Downloads that audio and muxes it into the input video.
# The output is a webm with the same filename, or including a +sound suffix if the input is already a webm.

function proc
{
	sound=$(grep -P -o "(?<=\[sound=).*(?=\])" <<< $1)
	if [ $? == 1 ]
	then
		echo "Not processing '$1' since it lacks a sound tag" 
		return
	fi

	url=$(urlencode -d <<< "$sound")
	tmp=$(mktemp)
	if ! wget "$url" -O $tmp -q --show-progress
	then
		echo "Failed retrieving audio for '$1' from '$url'"
		return
	fi

	if [[ "$1" == *.webm ]]
	then
		out=${1%.*}"+sound.webm"
	else
		out=${1%.*}".webm"
	fi

	ffmpeg -loglevel error -stats -i "$1" -i $tmp -vcodec libvpx "$out"
	ffreturn=$?
	rm $tmp

	if [ ffreturn == 1 ]
	then
		echo "Failed converting '$1'"
		return
	fi

	echo "$1 -> $out"
}

for a in "$@"
do
	proc "$a"
done
