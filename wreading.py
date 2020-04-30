#
# test ads feed
#

import time
import board
import busio
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import requests
#import http.client  # redundant as using requests

loop = 1 # every second for now
# loop = 60 # 60 seconds normally



# initialise

# Create the I2C bus - appears to default to address of 48
i2c = busio.I2C(board.SCL, board.SDA)

# Create the ADC object using the I2C bus
ads = ADS.ADS1015(i2c)

# Create single-ended input on channel 0
chan = AnalogIn(ads, ADS.P0)

# Create differential input between channel 0 and 1
#chan = AnalogIn(ads, ADS.P0, ADS.P1)

print("{:>5}\t{:>5}".format('raw', 'v'))

while True:

    # value is 20.5 per mm and offset 12560 at around 3.5cm on the etape
    depth = (chan.value - 12560)/20.5
    print("{:>5}\t{:>5.3f} {:>5.6f}".format(chan.value, chan.voltage, depth))

    time.sleep(loop)
#   end of while true
