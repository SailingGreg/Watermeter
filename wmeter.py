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
from lxml import html
from datetime import datetime, timezone
from bs4 import BeautifulSoup

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

    # Credentials (to parameterise and inject)
    username = 'ranelaghscapp@gmail.com'
    password = 'R0nel0ghSC'

    msg = MIMEText(heights)

    msg['Subject'] = subject
    msg['From'] = fromaddr
    msg['To'] = g_mail_recipent # from the conf file


    # The actual mail send
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(username, password)
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
    page = requests.get(dayurl) # get the day entry
    if (page.status_code != 200):
        print ("Error on dayurl")

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

# Create the I2C bus - appears to default to address of 48
i2c = busio.I2C(board.SCL, board.SDA)

# Create the ADC object using the I2C bus
ads = ADS.ADS1015(i2c)

# Create single-ended input on channel 0
chan = AnalogIn(ads, ADS.P0)

# Create differential input between channel 0 and 1
#chan = AnalogIn(ads, ADS.P0, ADS.P1)

print("{:>5}\t{:>5}".format('raw', 'v'))

ydate = "2020-01-01"
while True:

    # this is an infinite loop
    # we check the time and if another day check the tide situation

    fdate = datetime.now()
    tdate = fdate.strftime("%Y-%m-%d")

    if (ydate != tdate):
        ydate = tdate
        print ("ydate ", ydate)
        tides = getTides(tdate) # "YYYY-MM-DD"
    #     checkheights

    # value is 20.5 per mm and offset 12560 at around 3.5cm on the etape
    depth = (chan.value - 12560)/20.5
    print("{:>5}\t{:>5.3f} {:>5.6f}".format(chan.value, chan.voltage, depth))

    # if time window # is it in a time slot that needs to be monitored

    # we need to log the time/height to support reporting
    # print date/time, depth
    # flush?

    time.sleep(loop)
#   end of while true
