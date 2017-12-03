#! /usr/local/bin/python3

'''
title: 		link-scrape-tweet

author: 	infinite chill / 2017

about:
			an automated bot tool that scrapes a google drive spreadsheet, and periodically makes a tweet upon 
			selected interval. currently hardcoded to handle a video link spreadsheet but could easily be adjusted.

you must recieve credentials from twitter to psot tweets
https://apps.twitter.com/

you must recieve credentials in the form of a client-secret.json file form goolge to scrape a gdrive spreadsheet
https://console.developers.google.com/apis/credentials?pli=1

'''

import sys,csv, json, smtplib, random, time, datetime, signal, getpass, gspread, re, tweepy
from oauth2client.service_account import ServiceAccountCredentials
from urllib.request import urlopen
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email(subject,message,to_email,my_address,my_password,my_server,my_port):
    # set up the SMTP server
    smtp_server = smtplib.SMTP(my_server, my_port)
    smtp_server.ehlo()
    smtp_server.starttls()
    smtp_server.ehlo()
    smtp_server.login(my_address, my_password)
    # create a message
    mymsg = MIMEMultipart()       
    # setup the parameters of the message
    mymsg['From']=my_address
    mymsg['To']=to_email
    mymsg['Subject']=subject
    # attach the message body
    mymsg.attach(MIMEText(message, 'plain'))
    # send the message from the server
    smtp_server.send_message(mymsg)
    del mymsg
    # end the SMTP session and shut-down connection
    smtp_server.quit()

# wrapper class for congig settings... fill in these values...
class ConfigSettings(object):
	# you must fill in these values below to verify your twitter account
	def __init__(self):
		# please fill these in.
		self.EMAIL_SERVER=""
		self.EMAIL_ADDRESS=""
		self.EMAIL_PASSWORD=""
		self.EMAIL_PORT=""
		self.SEND_TO_EMAIL=""
		self.GOOGLE_DRIVE_SPREADSHEET=""
		self.GOOGLE_DRIVE_MODE=""
		self.CONSUMER_KEY=""
		self.CONSUMER_SECRET=""
		self.ACCESS_KEY=""
		self.ACCESS_SECRET=""
		self.CSV_FILE=""
		self.TWEET_HEAD=""
		self.TWEET_TAIL=""
		self.LOG_DIR=""
		self.LOG_FILE=""
		self.SEND_NOTIF_ON_SUCCESS=""
		self.TIME_INTERVAL=""
	def	set_EMAIL_SERVER(self, new_value):
		self.EMAIL_SERVER= new_value
	def set_EMAIL_ADDRESS(self, new_value):
		self.EMAIL_ADDRESS=new_value
	def set_EMAIL_PASSWORD(self, new_value):
		self.EMAIL_PASSWORD=new_value	
	def set_EMAIL_PORT(self, new_value):
		self.EMAIL_PORT=int(new_value)	
	def set_SEND_TO_EMAIL(self, new_value):
		self.SEND_TO_EMAIL=new_value
	def set_GOOGLE_DRIVE_SPREADSHEET(self, new_value):
		self.GOOGLE_DRIVE_SPREADSHEET=new_value
	def set_GOOGLE_DRIVE_MODE(self, new_value):
		self.GOOGLE_DRIVE_MODE=new_value
	def set_CONSUMER_KEY(self, new_value):
		self.CONSUMER_KEY = new_value
	def set_CONSUMER_SECRET(self, new_value):
		self.CONSUMER_SECRET = new_value
	def set_ACCESS_KEY(self, new_value):
		self.ACCESS_KEY = new_value
	def set_ACCESS_SECRET(self, new_value):
		self.ACCESS_SECRET = new_value
	def set_CSV_FILE(self, new_value):
		self.CSV_FILE=new_value
	def set_TWEET_HEAD(self, new_value):
		self.TWEET_HEAD=new_value
	def set_TWEET_TAIL(self, new_value):
		self.TWEET_TAIL=new_value
	def set_LOG_DIR(self, new_value):
		self.LOG_DIR=new_value
	def set_LOG_FILE(self, new_value):
		self.LOG_FILE=new_value
	def set_SEND_NOTIF_ON_SUCCESS(self, new_value):
		self.SEND_NOTIF_ON_SUCCESS=new_value
	def set_TIME_INTERVAL(self, new_value):
		self.TIME_INTERVAL=new_value

# set up globally
mySettings=ConfigSettings()

# wrapper class to exit program gracefully
class exitProgram:
	kill_now = False
	def __init__(self):
		# if sig int or sig term is recieved, set kill now to true
		signal.signal(signal.SIGINT, self.exit_gracefully)
		signal.signal(signal.SIGTERM, self.exit_gracefully)
	def exit_gracefully(self, signum, frame):
		self.kill_now = True

# function that selects a random entry from a two dimensional array and returns both columns
# returns the title, url, and index that it can be found in the list
def getRandomVideo(my_videos):
	index=random.randint(0,len(my_videos)-1)
	title=my_videos[index][0]
	url=my_videos[index][1]
	return title, url, index


# function that prints the contents of a two dimensional array
def showVideoList(videos):
	for video in videos:
		print("title:",video[0],"url:",video[1])
	return


# function that loads the contents of a 2 column csv file into a 2d list
# returns 2d list of videos and descriptions
def loadVideoList(csv_file):
	# open csv
	videos = []
	with open(csv_file) as csvDataFile:
		csvReader = csv.reader(csvDataFile)
		for row in csvReader:
			new_video = []
			for item in row:
				new_video.append(item)
			videos.append(new_video)
	return videos


# function that takes a list of videos with descriptions, selects a random one and updates a twitter status
# returns title of last video tweeted
def make_tweet(my_videos,api,tweet_header,tweet_tags,logfile):
	title, url, index = getRandomVideo(my_videos)
	new_tweet=tweet_header+" "+title+" "+url+" "+tweet_tags
	api.update_status(new_tweet)
	print(get_time_stamp(),"posted random tweet:\t",new_tweet,file=logfile,flush=True)
	#print(get_time_stamp(),"posted random tweet:\t",new_tweet,flush=True)
	return new_tweet


# function that scrapes a google drive spreadsheet for links and builds a 2d list for tweet composition
# returns 2d list of videos and descriptions
def scrape_google_drive(my_spreadsheet):
	# use creds to create a client to interact with the Google Drive API
	scope = ['https://spreadsheets.google.com/feeds']
	creds = ServiceAccountCredentials.from_json_keyfile_name('client-secret.json', scope)
	client = gspread.authorize(creds)
	sheet = client.open(my_spreadsheet).sheet1
	# Extract all of the values
	my_videos=sheet.get_all_values()
	# return results
	return my_videos


# function to return the actual wait time in seconds or exit
def get_wait_time(time_interval):
	if (time_interval == 1):
		return FOUR_HOURS	
	elif (time_interval == 2):
		return ONE_HOUR
	elif (time_interval == 3):
		return FIFTEEN_MINUTES
	elif (time_interval == 4):
		return ONE_MINUTE		
	elif (time_interval == 5):
		logfile.close()
		sys.exit(0)


def get_time_stamp():
	ts = time.time()
	return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')


def isValidEmail(email):
	if len(email) > 7:
		if re.match("(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", email) != None:
			return True
		else:
			return False


def single_quotes(s1):
    return "'{}'".format(s1)


# main driver function
def main():
	# check for proper usage. exit if no config file supplied
	if (len(sys.argv)) != 2:
		print("Error: no config file supplied.")
		print("Usage: ./link-tweeter ")
		sys.exit(1)
	try:
		# get settings from config json
		with open(sys.argv[1]) as json_data_file:
			data = json.load(json_data_file)
		smtp_server=data['email_settings']['host']
		email_address=data['email_settings']['email']
		email_password=data['email_settings']['password']
		email_port=data['email_settings']['port']
		send_to_email=data['email_settings']['send-to-email']
		google_spreadsheet=data['google_spreadsheet_settings']['spreadsheet-name']
		google_drive_mode=data['google_spreadsheet_settings']['google-drive-mode']
		consumer_key=data['twitter_settings']['consumer-key']
		consumer_secret=data['twitter_settings']['consumer-secret']
		access_key=data['twitter_settings']['access-key']
		access_secret=data['twitter_settings']['access-secret']
		csv_file=data['other_default_settings']['csv-file']
		tweet_header=data['other_default_settings']['tweet-head']
		tweet_tags=data['other_default_settings']['tweet-tail']
		log_dir=data['other_default_settings']['log-dir']
		log_file=data['other_default_settings']['log-file']
		send_notif_on_success=data['other_default_settings']['send-notif-on-success']
		time_interval=data['other_default_settings']['time-interval']

	# exit if there was an error
	except Exception as e:
		print("Error loading from config file.")
		sys.exit(1)			

	#print()
	#print(get_time_stamp())
	#print("hello, welcome to link-tweeter\n", flush=True)	

	# init config settings object to hold values
	mySettings.set_EMAIL_SERVER(smtp_server)
	mySettings.set_EMAIL_ADDRESS(email_address)
	mySettings.set_EMAIL_PASSWORD(email_password)
	mySettings.set_EMAIL_PORT(email_port)
	mySettings.set_SEND_TO_EMAIL(send_to_email)
	mySettings.set_GOOGLE_DRIVE_SPREADSHEET(google_spreadsheet)
	mySettings.set_GOOGLE_DRIVE_MODE(google_drive_mode)
	mySettings.set_CONSUMER_KEY(consumer_key)
	mySettings.set_CONSUMER_SECRET(consumer_secret)
	mySettings.set_ACCESS_KEY(access_key)
	mySettings.set_ACCESS_SECRET(access_secret)
	mySettings.set_CSV_FILE(csv_file)
	mySettings.set_TWEET_HEAD(tweet_header)
	mySettings.set_TWEET_TAIL(tweet_tags)
	mySettings.set_LOG_DIR(log_dir)
	mySettings.set_LOG_FILE(log_file)
	mySettings.set_SEND_NOTIF_ON_SUCCESS(bool(send_notif_on_success))
	mySettings.set_TIME_INTERVAL(int(time_interval))

	# open logfile
	try:
		logfile = open(mySettings.LOG_FILE, 'a')
	except Exception as e:
		sys.exit(1)

	print(get_time_stamp(),"opened log file", file=logfile, flush=True)
	#print(get_time_stamp(),"opened log file", flush=True)

	# test email
	try:
		subject="link-tweeter notif: started"
		message="link-tweeter was started"
		send_email(subject,message,mySettings.SEND_TO_EMAIL,mySettings.EMAIL_ADDRESS,mySettings.EMAIL_PASSWORD,mySettings.EMAIL_SERVER,mySettings.EMAIL_PORT)
		print(get_time_stamp(),"sent email to:\t",mySettings.SEND_TO_EMAIL,subject,message, file=logfile, flush=True)
		#print(get_time_stamp(),"sent email to:\t",mySettings.SEND_TO_EMAIL,subject,message, flush=True)
	except Exception as e:
		print(get_time_stamp(),"error sending email.", file=logfile, flush=True)
		#print(get_time_stamp(),"error sending email.", flush=True)
		sys.exit(1)

	# authorize twitter
	try:
		# reminder: the secret credentials must be filled in the json config supplied
		auth = tweepy.OAuthHandler(mySettings.CONSUMER_KEY, mySettings.CONSUMER_SECRET)
		auth.set_access_token(mySettings.ACCESS_KEY, mySettings.ACCESS_SECRET)
		api = tweepy.API(auth)

	except Exception as e:
		print(get_time_stamp(),"error authorizing twitter.", file=logfile, flush=True)
		#print(get_time_stamp(),"error authorizing twitter.", flush=True)
		sys.exit(1)

	print(get_time_stamp(),"authorized twitter",file=logfile,flush=True)
	#print(get_time_stamp(),"authorized twitter",flush=True)

	tweet_count=0
	# start infinite loop making tweets every time_interval
	killer = exitProgram()
	print(get_time_stamp(),"began tweeting", file=logfile,flush=True)
	#print(get_time_stamp(),"began tweeting", flush=True)
	while(1):
		# check if we got kill signal
		if (killer.kill_now):
			print(get_time_stamp(),"link-tweeter was killed.",file=logfile,flush=True)
			#print(get_time_stamp(),"link-tweeter was killed.",flush=True)
			subject="link-tweeter notif: killed"
			message="link-tweeter was killed"
			send_email(subject,message,mySettings.SEND_TO_EMAIL,mySettings.EMAIL_ADDRESS,mySettings.EMAIL_PASSWORD,mySettings.EMAIL_SERVER,mySettings.EMAIL_PORT)
			print(get_time_stamp(),"sent email to:\t",mySettings.SEND_TO_EMAIL,subject,message,file=logfile,flush=True)
			#print(get_time_stamp(),"sent email to:\t",mySettings.SEND_TO_EMAIL,subject,message,flush=True)
			break
		#scrape google drive every time we tweet to make sure and get the new ones
		if (mySettings.GOOGLE_DRIVE_MODE == 'True'):
			# try to scrape the goole drive for new links
			try:
				# scrape google drive for 2 column spreadsheet.
				# first column will be information and second column will be a link
				my_videos=scrape_google_drive("liked videos")
			except Exception as e:
				# halted attempting to get videos from google drive
				subject="link-tweeter notif: error"
				message="link-tweeter halted attempting to get links from google drive"
				send_email(subject,message,mySettings.SEND_TO_EMAIL,mySettings.EMAIL_ADDRESS,mySettings.EMAIL_PASSWORD,mySettings.EMAIL_SERVER,mySettings.EMAIL_PORT)
				print(get_time_stamp(),"sent email to:\t",mySettings.SEND_TO_EMAIL,subject,message, file=logfile,flush=True)
				#print(get_time_stamp(),"sent email to:\t",mySettings.SEND_TO_EMAIL,subject,message,flush=True)
				logfile.close()
				sys.exit(1)
			else:
				print(get_time_stamp(),"succesfully scraped google-drive sheet.", file=logfile,flush=True)
				print(get_time_stamp(),"succesfully scraped google-drive sheet.", flush=True)
		else:
			try:
				my_videos=loadVideoList(csv_file)
			except Exception as e:
				# halted attempting to get links from csv file
				subject="link-tweeter notif: error"
				message="link-tweeter halted attempting to get links from csv file"
				send_email(subject,message,mySettings.SEND_TO_EMAIL,mySettings.EMAIL_ADDRESS,mySettings.EMAIL_PASSWORD,mySettings.EMAIL_SERVER,mySettings.EMAIL_PORT)
				print(get_time_stamp(),"sent email to:\t",mySettings.SEND_TO_EMAIL,subject,message, file=logfile, flush=True)
				#print(get_time_stamp(),"sent email to:\t",mySettings.SEND_TO_EMAIL,subject,message, flush=True)
				logfile.close()
				sys.exit(1)
			else:
				print(get_time_stamp(),"succesfully scraped csv file.", file=logfile, flush=True)
				#print(get_time_stamp(),"succesfully scraped csv file.", flush=True)
		
		try:
			last_tweet=make_tweet(my_videos,api,mySettings.TWEET_HEAD,mySettings.TWEET_TAIL,logfile)
			time.sleep(mySettings.TIME_INTERVAL)
		except Exception as e:
			# halted attempting to make a tweet
			subject="link-tweeter notif: error"
			message="link-tweeter halted attempting to make a tweet"
			send_email(subject,message,mySettings.SEND_TO_EMAIL,mySettings.EMAIL_ADDRESS,mySettings.EMAIL_PASSWORD,mySettings.EMAIL_SERVER,mySettings.EMAIL_PORT)
			print(get_time_stamp(),"sent email to:\t",mySettings.SEND_TO_EMAIL,subject,message, file=logfile, flush=True)
			#print(get_time_stamp(),"sent email to:\t",mySettings.SEND_TO_EMAIL,subject,message, flush=True)
			logfile.close()
			sys.exit(1)
		else:
			subject="link-tweeter notif: new post"
			message="link-tweeter tweeted: "+ last_tweet
			if (mySettings.SEND_NOTIF_ON_SUCCESS):
				send_email(subject,message,mySettings.SEND_TO_EMAIL,mySettings.EMAIL_ADDRESS,mySettings.EMAIL_PASSWORD,mySettings.EMAIL_SERVER,mySettings.EMAIL_PORT)
				print(get_time_stamp(),"sent email to:\tå",mySettings.SEND_TO_EMAIL,subject,message, file=logfile, flush=True)
				#print(get_time_stamp(),"sent email to:\t",mySettings.SEND_TO_EMAIL,subject,message, flush=True)
			tweet_count+=1
	
	# recieved a sig int.
	logfile.close()
	sys.exit(0)

if __name__ == "__main__":
	main()
	
else:
	print("link-tweeter.py is being imported into another module")
