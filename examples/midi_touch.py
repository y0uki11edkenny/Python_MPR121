'''
    Federico Ramos 13/August/2013

    Before running, install timidity (sudo apt-get install timidity) and run:

    timidity -iA &

    midi base example by: Jeff Kinne
    capacitive hat base code by: Tony DiCola

    interesting links:
	https://ccrma.stanford.edu/~craig/articles/linuxmidi/alsa-1.0/alsarawmidiout.c
	http://zacvineyard.com/blog/2013/11/building-a-christmas-music-light-show-with-a-raspberry-pi
	https://en.wikipedia.org/wiki/Guitar_tunings
	http://www.electronics.dit.ie/staff/tscarff/Music_technology/midi/midi_note_numbers_for_octaves.htm
	http://www.skoogmusic.com/manual/manual1.1/Skoog-Window/navigation/MIDI-Tab/index
'''

import pygame
import pygame.midi
from time import sleep
import time
import Adafruit_MPR121.MPR121 as MPR121

notes=[28,29,31,33,35,36,38,40,41,43,45,47,48,50]

def setup_capacitive_hat():
	# Create MPR121 instance.
	cap = MPR121.MPR121()

	# Initialize communication with MPR121 using default I2C bus of device, and 
	# default I2C address (0x5A).  On BeagleBone Black will default to I2C bus 0.
	if not cap.begin():
    		print 'Error initializing MPR121.  Check your wiring!'
    		sys.exit(1)

	# Alternatively, specify a custom I2C address such as 0x5B (ADDR tied to 3.3V),
	# 0x5C (ADDR tied to SDA), or 0x5D (ADDR tied to SCL).
	#cap.begin(address=0x5B)

	# Also you can specify an optional I2C bus with the bus keyword parameter.
	#cap.begin(bus=1)

	#Stop the chip to set a new threshold value 0x00 -> ECR
	cap._i2c_retry(cap._device.write8,0x5E,0x00)

	#I found this threshold works well with medium fruits (like peaches)
	#Change this for your needs
	cap.set_thresholds(50, 10)

	#I will check if the register are written correctly (debug purposes)
	#tth=cap._i2c_retry(cap._device.readU8,0x41);
	#rth=cap._i2c_retry(cap._device.readU8,0x42);
	#print "Touch TH:" + str(tth) + "Release TH: " +str(rth)

	#Start again the ic
	cap._i2c_retry(cap._device.write8,0x5E,0x8F)

	return cap

def midiExample():
    # Things to consider when using pygame.midi:
    #
    # 1) Initialize the midi module with a to pygame.midi.init().
    # 2) Create a midi.Output instance for the desired output device port.
    # 3) Select instruments with set_instrument() method calls.
    # 4) Play notes with note_on() and note_off() method calls.
    # 5) Call pygame.midi.Quit() when finished. Though the midi module tries
    #    to ensure that midi is properly shut down, it is best to do it
    #    explicitly. A try/finally statement is the safest way to do this.
    #

    #Not all instruments will work :(, I only tested this
    GRAND_PIANO = 0
    CHURCH_ORGAN = 19
    GUITAR=25
    DRUMB=115
    SAX=65
    VIOLA=42
    TROMBONE=58
    
    instrument_array=[GRAND_PIANO,CHURCH_ORGAN,GUITAR,DRUMB,SAX,VIOLA,TROMBONE]
    current_instrument=0
    
    #Init the pygame system
    pygame.init()	

    #Init the pygame midi system
    pygame.midi.init()

    
    #Setup the output number 2, this is the timidity interface (check the beginning of the file)
    midi_out = pygame.midi.Output(2, 0)

    #Setup the HAT
    cap=setup_capacitive_hat();

    #shift example to the tones (this line have no effect)
    octave=0
    notes_offset=[x+12*octave for x in notes]

    #Here goes the body of the program (loop)
    try:
        midi_out.set_instrument(instrument_array[current_instrument])

	# Main loop to print a message every time a pin is touched.
	print 'Press Ctrl-C to quit.'
	last_touched = cap.touched()	

	while True:
    		current_touched = cap.touched()
    		# Check each pin's last and current state to see if it was pressed or released.
    		for i in range(12):
        		# Each pin is represented by a bit in the touched value.  A value of 1
        		# means the pin is being touched, and 0 means it is not being touched.
        		pin_bit = 1 << i
        		# First check if transitioned from not touched to touched.
        		if current_touched & pin_bit and not last_touched & pin_bit:
            			print '{0} touched!'.format(i)
				#Here we will trigger the MIDI tones
				if i == 11:
					print "Changing instrument"
					current_instrument+=1
					current_instrument=current_instrument%len(instrument_array)
					midi_out.set_instrument(instrument_array[current_instrument])
				elif i== 10:
					#Increment the tones
					print "Octave increased, actual: "+str(octave)
					octave+=1
					if octave>8:
						octave=8

					#We need shut down all the notes before change
                                        #to avoid "hang" notes
					for i in notes_offset:
                                                midi_out.note_off(i,127)

					notes_offset=[x+12*octave for x in notes]
				elif i==9:
					#Do nothing, se need reserve this case for the 
					#Decrement event
					print ""
				else:				
					midi_out.note_on(notes_offset[i],127)
				
        		# Next check if transitioned from touched to not touched.
        		if not current_touched & pin_bit and last_touched & pin_bit:
            			print '{0} released!'.format(i)

				if i== 9:
                                        #Decrement the tones
                                        print "Octave decremented, actual: "+str(octave)
                                        octave-=1
                                        if octave<0:
                                                octave=0

					#We need shut down all the notes before change
					#to avoid "hang" notes
					for i in notes_offset:
						midi_out.note_off(i,127)

                                        notes_offset=[x+12*octave for x in notes]
				else:
				#Here we will stop the midi tones
					midi_out.note_off(notes_offset[i],127)
    			# Update last state and wait a short period before repeating.
    		last_touched = current_touched
    		time.sleep(0.1)

	

    finally:
        del midi_out
        pygame.midi.quit()

midiExample()
