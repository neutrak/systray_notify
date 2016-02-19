#!/usr/bin/python2.7

#this is a simple notifier which runs in the system tray
#it uses pygtk and periodically polls an event file to get input

import pygtk
pygtk.require('2.0')
import gtk
import os
import sys
import select
import time
import datetime

#icon_path='test_files' #debug
#icon_path=os.path.join(os.getenv('HOME'),'.local','share','systray_notify')
icon_path=os.path.join('imgs')
idle_icon='notify_idle.png'
evnt_icon='notify_checkmark.png'

#event-type specific notification icons
email_icon='notify_email.png'
ping_icon='notify_ping.png'
pm_icon='notify_pm.png'
red_icon='notify_red.png'
green_icon='notify_green.png'
blue_icon='notify_blue.png'
yellow_icon='notify_yellow.png'

#a list of event definitions
#this consists of tuples of the following form
#(evnt_type, evnt_icon, evnt_nice)
#where nice is inverse priority (like *nix nice values)
#unknown events have a nice value of 1000 and use the evnt_icon file
evnt_defs=[
	('email',email_icon,1),
	('ping',ping_icon,2),
	('pm',pm_icon,2),
	('passing',green_icon,6),
	('aborted',yellow_icon,5),
	('failing',red_icon,4),
	]

class systray_evnt:
	def __init__(self,evnt_type,evnt_txt):
		self.evnt_type=evnt_type
		self.evnt_txt=evnt_txt

#this is a class because callbacks can't take window as a parameter and this wraps globals
#it really shouldn't be a class but there ya go; w/e
class systray_notify:
	#read events from the given file and return them
	#this is actually a self-contained side-effect free function
	#and so doesn't really need to be in this class, but is for clarity
	def read_events(self,evnt_file):
		try:
			fp=open(evnt_file,'r')
			fcontent=fp.read()
			fp.close()
		except(IOError):
			return []
		
		#read events; each line corresponds to one event of the following format:
		#evnt_type :evnt_txt
		#comments are lines starting with #
		evnt_ar=[]
		for line in fcontent.split("\n"):
			#don't count on comments or blank lines being around
			#this file gets re-written!
			if(line.startswith('#') or line==''):
				continue
			delimiter=' :'
			delimiter_idx=line.find(delimiter)
			#skip badly-formatted lines
			if(delimiter_idx<0):
				continue
			
			event_desc=systray_evnt(line[0:delimiter_idx],line[delimiter_idx+len(delimiter):])
			evnt_ar.append(event_desc)
		
		#we have all the events from the file so return 'em!
		return evnt_ar
	
	#write events to the given file
	#no return
	#like read events, this is self contained and doesn't need to be in this class
	def write_events(self,evnt_file,evnts):
		try:
			fp=open(evnt_file,'w')
			for evnt in evnts:
				fp.write(evnt.evnt_type+' :'+evnt.evnt_txt+"\n")
			fp.close()
		except(IOError):
			pass

	#delete callback
	def delete_event(self,widget,data=None):
		return True
	
	#destroy callback
	def destroy(self,widget,data=None):
#		gtk.main_quit()
		self.done=True
	
	def display_about(self,widget,data=None):
		abt_dsp=gtk.AboutDialog()
		abt_dsp.set_destroy_with_parent(False)
		abt_dsp.set_name('Systray Notify')
		abt_dsp.set_version('0.1')
		abt_dsp.set_authors([''])
		abt_dsp.run()
		abt_dsp.destroy()
	
	#acknowledge an event; data gives index
	def ack_evnt(self,widget,data=None):
		if(data!=None):
			idx=int(data)
			
			#this event has been acknowledged, so remove it from the event list
			new_evnts=[]
			for n in xrange(0,len(self.evnts)):
				if(n!=idx):
					new_evnts.append(self.evnts[n])
			self.evnts=new_evnts
		#destroy the event menu if it exists
		if(self.evnt_menu!=None):
			self.evnt_menu.popdown()
			self.evnt_menu.destroy()
			self.evnt_menu=None
		
		#rewrite the event file
		self.write_events(self.evnt_file,self.evnts)
		self.set_ackmenu()
	
	#acknowledge an event from a submenu item
	#just a little wrapper
	def ack_evnt_from_btn(self,widget,evnt,data=None):
		self.sts_ico.menu.popdown()
		return self.ack_evnt(widget,data)
	
	def set_ackmenu(self):
		#destroy the event menu if it exists
		if(self.evnt_menu!=None):
			self.evnt_menu.popdown()
			self.evnt_menu.destroy()
			self.evnt_menu=None
		
		#create a menu which allows the user to acknowledge events
		self.evnt_menu=gtk.Menu()
		for n in xrange(0,len(self.evnts)):
			evnt=self.evnts[n]
			evnt_item=gtk.MenuItem(evnt.evnt_type+' : '+evnt.evnt_txt)
			#pass the index of this event through to the ack_evnt callback
			#so it knows what event got acknowledged
			evnt_item.connect('activate',self.ack_evnt,n)
			
			#for some reason activate doesn't get called during submenu clicks
			#this is a workaround
			evnt_item.connect('button-press-event',self.ack_evnt_from_btn,n)

			self.evnt_menu.append(evnt_item)
		self.evnt_menu.show_all()
		
		self.ack_item.set_submenu(self.evnt_menu)
	
	#icon clicked/activated callback (left click)
	def activate(self,widget,data=None):
		#destroy the event menu if it exists
		if(self.evnt_menu!=None):
			self.evnt_menu.popdown()
			self.evnt_menu.destroy()
			self.evnt_menu=None
		
		#clear the menu in case it was previously visible
		self.sts_ico.menu.popdown()
		
		#clear any blinking state; we have the user's attention at this time
		self.sts_ico.set_blinking(False)
		
		#create a menu which allows the user to acknowledge events
		self.set_ackmenu()
		
		#TODO: fix arrow placement so it doesn't cover up menu items!
		#can we just make the menu always be large enough that it's not a problem?
		
		#windows
		if(os.name=='nt'):
			self.evnt_menu.popup(None,None,None,1,int(time.time()))
		#*nix
		else:
			self.evnt_menu.popup(None,None,gtk.status_icon_position_menu,1,int(time.time()))

		
#		widget.stop_emission('activate')
	
	#popup menu (right click) callback
	def popup_menu(self,status,button,time):
		#destroy the event menu if it exists
		if(self.evnt_menu!=None):
			self.evnt_menu.popdown()
			self.evnt_menu.destroy()
			self.evnt_menu=None
		
		#clear the menu in case it was previously visible
		self.sts_ico.menu.popdown()
		
		#clear any blinking state; we have the user's attention at this time
		self.sts_ico.set_blinking(False)
		
		self.sts_ico.menu.popup(None,None,None,button,time)
		self.set_ackmenu()
	
	#constructor
	#poll_delay is waiting time between file polls, in seconds (default 5 seconds)
	def __init__(self,evnt_file='systray_events.txt',blnk_on_evnt=False,poll_delay=5.0):
		#configure local settings
		self.evnt_file=evnt_file
		self.blnk_on_evnt=blnk_on_evnt
		self.poll_delay=poll_delay
		
		#force a poll on the first loop
		self.last_poll=0
		self.icon_name=''
		
		#create status icon in system tray
		sts_ico=gtk.StatusIcon()
		#initially the status icon is idle
		sts_ico.set_from_file(os.path.join(icon_path,idle_icon))
		sts_ico.set_title('Systray Notify')
		sts_ico.set_tooltip('Systray Notify')
		sts_ico.set_visible(True)
		
		#create a menu accesible from the status icon
		sts_ico.menu=gtk.Menu()
		
		#acknowledgement menu item
		self.ack_item=gtk.MenuItem('ACK')
		self.ack_item.set_submenu(None)
		sts_ico.menu.append(self.ack_item)
		
		#about menu item
		about_item=gtk.MenuItem('About')
		about_item.connect('activate',self.display_about)
		sts_ico.menu.append(about_item)
		
		#exit menu item
		exit_item=gtk.MenuItem('Exit')
		exit_item.connect('activate',self.destroy)
		sts_ico.menu.append(exit_item)
		
		#show all menu items on display
		sts_ico.menu.show_all()
		
		#bind status icon events to menu display
		sts_ico.connect('activate',self.activate)
		sts_ico.connect('popup-menu',self.popup_menu)
		
		#store the status icon in the class variables for later reference
		self.sts_ico=sts_ico
		
		#we're not quite dead yet!
		self.done=False
		
		#a list of all events which are yet to be acknowledged
		self.evnts=[]
		self.evnt_menu=None
	
	def main(self):
#		gtk.main()
		
		self.done=False
		while(not self.done):
			while(gtk.events_pending()):
				gtk.main_iteration()
			#change icon based on what unacknowledged events exist
			if(len(self.evnts)>0):
				#use nice values to set icon based on the highest-priority event
				high_pri_idx=0
				low_nice=1000
				for n in xrange(0,len(self.evnts)):
					evnt_type=(self.evnts[n].evnt_type).lower()
					for evnt_def in evnt_defs:
						if(evnt_type==evnt_def[0]):
							#this event has higher priority than any event yet seen
							#note that <= instead of < causes more recent events to be used
							#in the event of a priority tie
							if(evnt_def[2]<=low_nice):
								high_pri_idx=n
								low_nice=evnt_def[2]
				
				evnt_type=(self.evnts[high_pri_idx].evnt_type).lower()
				
				#change the icon to a different one based on the event
				for evnt_def in evnt_defs:
					if(evnt_type==evnt_def[0]):
						if(self.icon_name!=(evnt_def[1])):
							self.sts_ico.set_from_file(os.path.join(icon_path,evnt_def[1]))
							self.icon_name=evnt_def[1]
						break
				else:
					#use a generic icon for unknown events
					if(self.icon_name!=evnt_icon):
						self.sts_ico.set_from_file(os.path.join(icon_path,evnt_icon))
						self.icon_name=evnt_icon
				
				#regardless of event type set icon blinking
				if(self.blnk_on_evnt):
					self.sts_ico.set_blinking(True)
				
				#TODO: balloon dialog when an event first comes in?
				#probably not necessary...
				
			#when no events exist, set to idle
			elif(self.icon_name!=idle_icon):
				self.sts_ico.set_from_file(os.path.join(icon_path,idle_icon))
				self.icon_name=idle_icon
			#give the cpu a 50ms break
			time.sleep(0.05)
			
			#if the polling time is up, then read from the file
			if((time.time()-self.last_poll)>=self.poll_delay):
				self.evnts=self.read_events(self.evnt_file)
				#if all events have been acknowledged then stop blinking
				if(len(self.evnts)==0):
					self.sts_ico.set_blinking(False)
				self.last_poll=time.time()
			


#converts a string defining a month into a number defining that month
def month_str_to_intstr(m_str):
	months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
	for m_idx in xrange(0,len(months)):
		if(m_str.startswith(months[m_idx])):
			month_number=m_idx+1
			if(month_number<10):
				return '0'+str(month_number)
			return str(month_number)
	return m_str

#return a simple notification for a given maildir email file
def parse_maildir_file(fname):
	fp=open(fname)
	fcontent=fp.read()
	fp.close()
	
	#all the header fields we want out of this file
	date_line=''
	from_line=''
	to_line=''
	subject_line=''
	
	#message content
	content=''
	
	#read each line, starting with the email header
	header_done=False
	for line in fcontent.split('\n'):
		line=line.rstrip("\r")
		if((line=='') and (not header_done)):
			header_done=True
		elif(not header_done):
			#read date lines; we want to know when this was sent
			if(line.startswith('Date: ')):
				date_line=line[len('Date: '):]
			#read from lines; we want to know who sent this
			elif(line.startswith('From: ')):
				from_line=line[len('From: '):]
			#read to lines; we want to know the intended recipient
			elif(line.startswith('To: ')):
				to_line=line[len('To: '):]
			#read subject lines; we want to know what this is about
			elif(line.startswith('Subject: ')):
				subject_line=line[len('Subject: '):]
		else:
			content+=line+"\n"
	
	#reformat the date line for brevity
	
	#e.g. starting date: Sun, 07 Feb 2016 21:46:01 -0600
	date_fields={}
	for field in ['day_of_wk','day_of_mn','month','year','clock','timezone']:
		space_idx=date_line.find(' ')
		date_fields[field]=date_line[0:space_idx]
		date_line=date_line[space_idx+1:]
	date_line=date_fields['year']+'-'+month_str_to_intstr(date_fields['month'])+'-'+date_fields['day_of_mn']
	
	#return the nicely-formatted result :)
	return 'EMAIL :('+date_line+') '+from_line+': '+subject_line

#this re-formats a message from
#"(host #chan) timestamp PING: <user> message content"
#or was it...
#"(host #chan) PING: timestamp <user> message content"
#to
#"PING :timestamp <user> message content"
#for handling by systray_notify
def ping_reformat(in_str,pretty_timefrmt=True):
	#we can't parse nothing
	#garbage in, garbage out
	if(in_str==''):
		return 0,''
	
	#get the event type by use of a delimiter
	idx=in_str.find(': ')
	msg_type=''
	strt_idx=idx
	while(in_str[strt_idx]!=' ' and strt_idx>0):
		strt_idx-=1
	
	if(strt_idx>0):
		strt_idx+=1

	evnt_type=in_str[strt_idx:idx]
	evnt_txt=in_str[idx+len(': '):]
	
	#parse out the timestamp, too, for reference
	timestamp=0
	if(len(evnt_txt)>0):
		timestamp_end_idx=evnt_txt.find(' ')
		#if there was no space then the entire message is the timestamp
		if(timestamp_end_idx<0):
			timestamp_end_idx=len(evnt_txt)-1
		
		#get the timestamp as a numeric value
		try:
			timestamp=int(evnt_txt[0:timestamp_end_idx])
		except(ValueError):
			try:
				timestamp=int(float(evnt_txt[0:timestamp_end_idx]))
			except(ValueError):
				timestamp=0
		
		if(pretty_timefrmt):
			#prettily format the timestamp for output
			pretty_time=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(timestamp))
			evnt_txt=pretty_time+' '+evnt_txt[timestamp_end_idx:]
	
	out_str=evnt_type+' :'+evnt_txt
	
	#return a tuple with the timestamp and the evnt_type :evnt_txt string
	return timestamp,out_str

if(__name__=='__main__'):
	evnt_file=os.path.join('files','systray_events.txt') #debug
#	evnt_file=os.path.join(os.getenv('HOME'),'.local','share','systray_notify','events.txt')
	
	#command-line utilities and options
	if(len(sys.argv)>1):
		#reformat an email from maildir to systray_notify event format
		if(sys.argv[1]=='email'):
			if(len(sys.argv)>2):
				notification=parse_maildir_file(sys.argv[2])
				print(notification)
			else:
				print('Usage: '+sys.argv[0]+' email <email file>')
			sys.exit(0)
		#reformat a ping log into a systray_notify event format
		elif(sys.argv[1]=='reformat'):
			import sys
			#if an argument was provided it is the minimum timestamp to alert on
			min_time=0
			if(len(sys.argv)>2):
				try:
					min_time=int(sys.argv[2])
				except(ValueError):
					min_time=0
			timestamp,output=ping_reformat(raw_input())
			#messages prior to the minimum timestamp are ignored
			if(timestamp>=min_time):
				print(output)
			if(len(sys.argv)>3 and sys.argv[3]=='--ts'):
				print(timestamp)
			sys.exit(0)
		elif(sys.argv[1]=='--help'):
			print('Tools:')
			print('  '+sys.argv[0]+' email <email file>')
			print('  '+sys.argv[0]+' reformat')
			print('    (reads ping-format messages from stdin; you can pipe to it)')
			print('Run:')
			print('  '+sys.argv[0])
			print('  '+sys.argv[0]+' --file <event file>')
			sys.exit(0)
		#accept requests for nonstandard event files
		elif(sys.argv[1]=='--file'):
			if(len(sys.argv)>2):
				evnt_file=sys.argv[2]
			else:
				print('Warn: Using default event file, because no file was given')
	notifier=systray_notify(evnt_file=evnt_file)
	notifier.main()


