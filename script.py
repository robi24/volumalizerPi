import time
import RPi.GPIO as GPIO
import pyaudio
import numpy as np
import signal
import sys

# main config
CHARACTER = '*'
CHARACTER_L = '>'
CHARACTER_R = '<'
CHARACTER_SPACE = ' '
SHOW_CONSOLE = False
SKIP_EVERY = 5

# set GPIO
LCD_RS = 12
LCD_E  = 6
LCD_DATA4 = 26
LCD_DATA5 = 19
LCD_DATA6 = 16
LCD_DATA7 = 20
LCD_WIDTH = 16
LCD_LINE_1 = 0x80
LCD_LINE_2 = 0xC0
LCD_CHR = GPIO.HIGH
LCD_CMD = GPIO.LOW
E_PULSE = 0.0005
E_DELAY = 0.0005

def lcd_send_byte(bits, mode):
	GPIO.output(LCD_RS, mode)
	GPIO.output(LCD_DATA4, GPIO.LOW)
	GPIO.output(LCD_DATA5, GPIO.LOW)
	GPIO.output(LCD_DATA6, GPIO.LOW)
	GPIO.output(LCD_DATA7, GPIO.LOW)
	if bits & 0x10 == 0x10:
	  GPIO.output(LCD_DATA4, GPIO.HIGH)
	if bits & 0x20 == 0x20:
	  GPIO.output(LCD_DATA5, GPIO.HIGH)
	if bits & 0x40 == 0x40:
	  GPIO.output(LCD_DATA6, GPIO.HIGH)
	if bits & 0x80 == 0x80:
	  GPIO.output(LCD_DATA7, GPIO.HIGH)
	time.sleep(E_DELAY)    
	GPIO.output(LCD_E, GPIO.HIGH)  
	time.sleep(E_PULSE)
	GPIO.output(LCD_E, GPIO.LOW)  
	time.sleep(E_DELAY)      
	GPIO.output(LCD_DATA4, GPIO.LOW)
	GPIO.output(LCD_DATA5, GPIO.LOW)
	GPIO.output(LCD_DATA6, GPIO.LOW)
	GPIO.output(LCD_DATA7, GPIO.LOW)
	if bits&0x01==0x01:
	  GPIO.output(LCD_DATA4, GPIO.HIGH)
	if bits&0x02==0x02:
	  GPIO.output(LCD_DATA5, GPIO.HIGH)
	if bits&0x04==0x04:
	  GPIO.output(LCD_DATA6, GPIO.HIGH)
	if bits&0x08==0x08:
	  GPIO.output(LCD_DATA7, GPIO.HIGH)
	time.sleep(E_DELAY)    
	GPIO.output(LCD_E, GPIO.HIGH)  
	time.sleep(E_PULSE)
	GPIO.output(LCD_E, GPIO.LOW)  
	time.sleep(E_DELAY)  

def display_init():
	lcd_send_byte(0x33, LCD_CMD)
	lcd_send_byte(0x32, LCD_CMD)
	lcd_send_byte(0x28, LCD_CMD)
	lcd_send_byte(0x0C, LCD_CMD)  
	lcd_send_byte(0x06, LCD_CMD)
	lcd_send_byte(0x01, LCD_CMD)  

def lcd_message(message):
	message = message.ljust(LCD_WIDTH," ")  
	for i in range(LCD_WIDTH):
	  lcd_send_byte(ord(message[i]),LCD_CHR)
	
def signal_handler(sig, frame):
        print("\nThanks for using!")
        display_init()
        sys.exit(0)
	
def show_welcome_screen():
	lcd_send_byte(LCD_LINE_1, LCD_CMD)
	lcd_message("volumalizer")
	lcd_send_byte(LCD_LINE_2, LCD_CMD)
	lcd_message("Pi")

def animate_vertical(peakL, peakR, bars):
	lString = CHARACTER * int(peakL*bars) + CHARACTER_SPACE * int(bars-peakL*bars)
	rString = CHARACTER * int(peakR*bars) + CHARACTER_SPACE * int(bars-peakR*bars)
	lcd_send_byte(LCD_LINE_1, LCD_CMD)
	lcd_message(lString)
	lcd_send_byte(LCD_LINE_2, LCD_CMD)
	lcd_message(rString)
	if (SHOW_CONSOLE):
		print("L=[%s]\tR=[%s]"%(lString, rString))
	
def animate_horizontal(peakL, peakR, bars):
	lInt = int(peakL*bars)
	rInt = int(peakR*bars)
	middle = 16 - (lInt + rInt)
	displayString = CHARACTER_L * lInt + CHARACTER_SPACE * middle + CHARACTER_R * rInt
	lcd_send_byte(LCD_LINE_1, LCD_CMD)
	lcd_message(displayString)
	lcd_send_byte(LCD_LINE_2, LCD_CMD)
	lcd_message(displayString)
	if (SHOW_CONSOLE): 
		print("L=[%s]=R"%(displayString))

if __name__ == '__main__':
	# GPIO init
	GPIO.setmode(GPIO.BCM)
	GPIO.setwarnings(False)
	GPIO.setup(LCD_E, GPIO.OUT)
	GPIO.setup(LCD_RS, GPIO.OUT)
	GPIO.setup(LCD_DATA4, GPIO.OUT)
	GPIO.setup(LCD_DATA5, GPIO.OUT)
	GPIO.setup(LCD_DATA6, GPIO.OUT)
	GPIO.setup(LCD_DATA7, GPIO.OUT)
	
	# display init
	signal.signal(signal.SIGINT, signal_handler)
	display_init()
	show_welcome_screen()
	time.sleep(2)
	
	# start Pyaudio stream
	maxValue = 2**16
	p=pyaudio.PyAudio()
	stream=p.open(format=pyaudio.paInt16,channels=2,rate=44100,
				  input=True, frames_per_buffer=1024)
				  
	# main loop
	skip = 0
	while True:
		data = np.fromstring(stream.read(1024),dtype=np.int16)
		dataL = data[0::2]
		dataR = data[1::2]
		peakL = np.abs(np.max(dataL)-np.min(dataL))/maxValue
		peakR = np.abs(np.max(dataR)-np.min(dataR))/maxValue
		if(skip == SKIP_EVERY):
			#animate_horizontal(peakL, peakR, 15)
			animate_vertical(peakL, peakR, 20)
			skip = 0
		else: skip = skip +1
	
	lcd_message("Thanks!")
	GPIO.cleanup()
