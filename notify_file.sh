#!/bin/bash

notify_on() {
	#initial timestamp is epoch, until a timestamp is known
	last_ts=0
	input_file="$1"
	output_file="$2"
	protocol="$3"
	while [ 1 ]
	do
#		echo "reformatting ${input_file}, last_ts=${last_ts}..."
		
		#check every line of the input file for new data
		if [ "$protocol" == "curl" ]
		then
			IFS=$'\n' input_lines=( $(curl -L "$input_file") )
		else
#			IFS=$'\n' input_lines=( $(cat "$input_file" | egrep -v '^$') )
			IFS=$'\n' input_lines=( $(cat "$input_file") )
		fi
		
		for line in ${input_lines[@]}
		do
#			write_line="$(echo "$line" | ./notify_reformat.py $last_ts)"
			write_line="$(echo "$line" | ./systray_notify.py reformat $last_ts)"
			#if this data was more recent than our last check
			if [ "$write_line" != '' ]
			then
				echo "$write_line"
				#output to the notification file provided
				echo "$write_line" >> "$2"
				
				#update the timestamp so that lines before that are not read again
#				new_ts=$(echo "$line" | ./notify_reformat.py $last_ts --ts | tail -n 1)
				new_ts=$(echo "$line" | ./systray_notify.py reformat $last_ts --ts | tail -n 1)
				if [ "$new_ts" -ge "$last_ts" ]
				then
					last_ts=$(($new_ts+1))
				fi
			fi
		done
#		sleep 5
		sleep 20
	done
	
	unset IFS
}

#local machine configuration
#notify_on 'http://192.168.1.4/pings.txt' "${HOME}/.local/share/systray_notify/events.txt" "curl"
notify_on "$1" "$2" "$3"

