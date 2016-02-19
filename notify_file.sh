#!/bin/bash

#this checks for new emails in a maildir directory
#note this does not FETCH mail, it just checks if what's been downloaded is new
#1st argument: mail directory (maildir)
#2nd argument: minimum timestamp to be considered "new"
check_new_emails(){
	output_file="$1"
	email_path="$2"
#	last_ts=0
	#not knowing when we last checked, start from now
	last_ts="$(date +%s)"
	
	while [ 1 ]
	do
		new_ts=$last_ts
		#for each email folder
		for dir in "${email_path}"/*
		do
			#for each individual email
			for f in $(ls "${dir}")
			do
				#check when this email was sent/received
				file_date="$(date --date="$(fgrep "Date: " "${dir}/$f" | sed 's/^Date: //g')" +%s)"
				
				#if this was a new email, then display it
				if [ $file_date -ge $last_ts ]
				then
					./systray_notify.py email "${dir}/$f" >> $1
					
					if [ $file_date -gt $new_ts ]
					then
						new_ts=$(($file_date+1))
					fi
				fi
			done
		done
		last_ts=$new_ts
	done
}

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
if [ "$1" == "email" ]
then
	#1st argument: output file
	#2nd argument: mail directory (maildir)
	check_new_emails "$2" "$3"
elif [ "$1" == "watch" ]
then
	#1st argument: input file
	#2nd argument: output file
	#3rd argument: network input? (curl)
	#notify_on 'http://192.168.1.4/pings.txt' "${HOME}/.local/share/systray_notify/events.txt" "curl"
	notify_on "$2" "$3" "$4"
else
	echo "Usage: $0 <email> <output file> <mail directory>"
	echo "Usage: $0 <watch> <input file> <output file> <curl|local>"
fi

