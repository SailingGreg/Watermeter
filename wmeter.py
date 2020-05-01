#
# Smart water meter
# The program queries thamestides.org to check the tidal hieghts
# and if the tide is likely to lead to flooding it monitors and
# records the water height within the undercroft.
# it then emails a summary out to the nominated email
#

import time
import board
import busio
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import requests
#import http.client  # redundant as using requests
from lxml import html
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from emailcreds import * # account and password for email

#FLOODTIDE = 7.0
FLOODTIDE = 6.1
TWOHOURS = 2 * 60 * 60
loop = 1 # every second for now
# loop = 60 # 60 seconds normally

# load tides for 'today'

# flag slots for monitoring

def removeNonAscii(s): return "".join(i for i in s if (ord(i)<128 and ord(i)>31))

#
# email results file to defined recipent
def sendRaces(heights):
    #
    #g_mail_recipent = 'integ@ranelaghsc.co.uk'
    g_mail_recipent = 'greg.brougham@gmail.com'
    #g_mail_recipent = 'racing@ranelaghsc.co.uk'
    fromaddr = 'ranelaghscapp@gmail.com'
    subject = "Club water height information"
    raceday = datetime.now().strftime("%d %b %Y")
    #raceday = datetime.datetime.now().strftime("%d %b %Y")

    # Credentials - injected via emailcreds.py

    # convert the text to mime
    msg = MIMEText(heights)

    msg['To'] = g_mail_recipent # from the conf file
    msg['From'] = fromaddr
    msg['Subject'] = subject

    # The actual mail send
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(eusername, epassword)
    #server.sendmail(fromaddr, toaddr, message)
    server.send_message(msg)
    server.close()
# end of sendRaces()


#tidelist = []
tideurl = "http://thamestides.org.uk/dailytides2.php?statcode=PUT&startdate="

# get the tides for the given date
def getTides(tdate):
    # build the url and get the entry

    dt = datetime.fromisoformat(tdate)
    sdate = str(int(dt.replace(tzinfo=timezone.utc).timestamp()))
    #print(sdate)

    tidelist = [] # truncate
    dayurl = tideurl + sdate

    # need try/exception added
    try:
        page = requests.get(dayurl) # get the day entry
    except Exception as e: # we just note and return blank list
        print ("Error on dayurl")
        return tidelist

    if (page.status_code != 200):
        print ("Error on dayurl")
        return tidelist

    tree = html.fromstring(page.content)

    """
    items = []
    #print (len(items))
    if (len(items) == 0): # then initialise
        for j in range(4, 4 + 5): # should be 4 - 8
            column = []
            for i in range(1,6):
                column.append("")
            items.append(column)
    # now initialised
    #print (len(items))
    """

    entry = ["", "", "", "", ""] # array of 5 items
    # now parse the table into the array - note doesn't error
    for row in range (4, 4 + 5):
        for col in range(1,6):
            # returns list
            item = tree.xpath('//table[@class="first"]//tr['
                        + str(row) + ']//td[' + str(col) + ']//text()')
            if (len(item) > 0):
                #items[row-4][col-1] = item[0]
                #items[row-4][col-1] = removeNonAscii(item[0])
                entry[col-1] = removeNonAscii(item[0])
            else:
                #items[row-4][col-1] = ""
                entry[col-1] = ""
            #print ("items ", str(row), str(col), items[row-4][col-1])

        # for
        tide = {'type': str(entry[0]), 'time': entry[1], 'height': entry[2]}
        tidelist.append(tide)
    # for

    return tidelist
# end getTides()


# initialise

print ("Initialising I2C/ADC")
# Create the I2C bus - appears to default to address of 48
i2c = busio.I2C(board.SCL, board.SDA)

# Create the ADC object using the I2C bus
ads = ADS.ADS1015(i2c)

# Create single-ended input on channel 0
chan = AnalogIn(ads, ADS.P0)

# Create differential input between channel 0 and 1
#chan = AnalogIn(ads, ADS.P0, ADS.P1)

print("{:>5}\t{:>5}".format('raw', 'v'))

floods = [] # truncate
ydate = "1970-01-01" # base of timestamp
while True:

    # this is an infinite loop
    # we check the time and if another day check the tide situation

    fdate = datetime.now()
    tsecs = datetime.timestamp(fdate)
    #print (tsecs, fdate, type(fdate))
    tdate = fdate.strftime("%Y-%m-%d")

    # if another day then get the tides
    if (ydate != tdate):
        # send the previous days summary

        ydate = tdate
        print ("ydate ", ydate)
        tides = getTides(tdate) # "YYYY-MM-DD"
        for tide in tides:
            theight = tide['height']

            # if flood tide add to floods
            if (len(theight) > 1 and float(theight) >= FLOODTIDE):
                #print ("Flood ", theight)
                fdate = tdate + " " + tide['time']
                dobj = datetime.strptime(fdate, '%Y-%m-%d %I:%M')
                fsecs = datetime.timestamp(dobj)
                print ("> ", dobj, fsecs)

                # add check if the flood is in the future!
                # if (fsecs > tsecs):
                flood = {'date': tdate, 'time': tide['time'], \
					'secs': fsecs, 'height': theight}
                floods.append(flood)

        # now trim - that is remove anything older than now minus 2 hours
        """
        while (len (floods) > 0 and floods[0]['secs'] < (tsecs - TWOHOURS)):
            print ("deleting ", floods[0])
            floods.pop(0)
        """
    # end tides

    # check water heights
    # value is 20.5 per mm and offset 12560 at around 3.5cm on the etape
    depth = (chan.value - 12560)/20.5
    if (depth > 0): # then log
        print("{:>5}\t{:>5.3f} {:>5.6f}".format(chan.value, chan.voltage, depth))
        # write to reporting file
        # we need to log the time/height to support reporting
    """
    rs = requests.get(windurl, allow_redirects=True)
    open('./tmp/daywind-copy.png', 'wb').write(rs.content)
    """


    # are we within two hours of a high tide?
    loop = 0
    for flood in floods:
        if (flood['secs'] >= (tsecs - TWOHOURS) and \
				 flood['secs'] <= (tsecs + TWOHOURS)):
            loop = 1 # delay 5 minutes
        else:
            loop = 3 # delay 1 hour
        if (loop == 1): # within two hours of tide so short delay
           break

    time.sleep(loop)
#   end of while true
