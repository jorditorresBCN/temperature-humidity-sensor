#!/usr/bin/python

from time import sleep
from sys import exit
import ConfigParser
import os.path
import datetime
import eeml
import eeml.datastream
import subprocess, os, sys
import RPi.GPIO as GPIO
from interfaces.DHT22 import DHT22
from interfaces.MCP3008 import MCP3008, MCP3208, AQSensor, LightSensor
from interfaces.PiPlate import Adafruit_CharLCDPlate

class DataPoint():
	def __init__(self,value,name,unit,decimalplaces,uploadID,shortName=None):
		self.value = value
		self.name = name
		self.unit = unit
		self.decimals = decimalplaces
		self.uploadID = uploadID
		self.sName = shortName
	def roundedValue(self):
		formatString = '{0:.' + str(self.decimals) + 'f}'
		return formatString.format(self.value)


def mainUpload(stdscr):
	
	        config = ConfigParser.ConfigParser()
                config.read('sensor.cfg')

		LOGGER = config.getboolean("Cosm", "Enabled")
		FREQUENCY = 2 
		NETRESTART = True 
		NETRETRIES = 15 
#
	        GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(22,GPIO.OUT)

                # Get the ADC details from the config			
		SPIMOSI = 23 
		SPIMISO = 24 
		SPICLK = 18 
		SPICS = 25 
		adc = MCP3008.MCP3008(SPIMOSI,SPIMISO,SPICLK,SPICS)

		# DHT22 details 	
		DHTPin = 4  
		dht = DHT22.DHT22(DHTPin)
                

		if LOGGER:
			API_KEY = config.get("Cosm", "APIKEY", 1)
			FEED = config.getint("Cosm", "FEEDID")
			API_URL = '/v2/feeds/{feednum}.xml' .format(feednum=FEED)
		failCount = 0
		currentDisplay = 0
		
		# Continuously append data
		while(True):
			datas = []
		
			dht.get_data()
			d = DataPoint(dht.temp(),"Temperature","C",1,0, "Temp")
			if d.value != False:
				datas.append(d)
				datas.append(DataPoint(dht.humidity(),"Humidity   ","%",1,1,"Humidity"))
#tros posat
                                for dp in datas:
                                        print dp.name + ":\t" + dp.roundedValue() + " " + dp.unit
#
			if stdscr != None:
				a = 0
				for dp in datas:
					if dp.uploadID != -1:
						a+=1
						stdscr.addstr(5 + (a * 2), 3, dp.name + ":\t" + dp.roundedValue() + " " + dp.unit)
						stdscr.clrtoeol()
				stdscr.refresh() 
			if LOGGER:
				#Attempt to submit the data to cosm
				try:
					pac = eeml.datastream.Cosm(API_URL, API_KEY)
					for dp in datas:
						if dp.uploadID!=-1:
							pac.update([eeml.Data(dp.uploadID, dp.roundedValue())])
					pac.put()
					if stdscr == None:
						print "Uploaded data at " + str(datetime.datetime.now())
					GPIO.output(22, True)
					failCount = 0
				except KeyboardInterrupt:
					raise
				except:
					print "Unable to upload data at " + str(datetime.datetime.now()) + ".  Check your connection?"
					if NETRESTART:
						failCount+=1
						if failCount>NETRETRIES:
							subprocess.Popen(["sudo", "/etc/init.d/networking", "restart"])
							failCount=0
	
			sleep(FREQUENCY-1)
			GPIO.output(22, False)
			currentDisplay+=1
			if currentDisplay == 4:
				currentDisplay = 0

mainUpload(None)
