# This program uses a thermal printer to print out various information from
# the internet or the "fortune" program

from Adafruit_MCP230xx import *
import RPi.GPIO as GPIO
import time, subprocess, re, textwrap, urllib, urllib2, os, Image, ImageDraw, unicodedata, datetime
from xml.dom.minidom import parseString
from bs4 import BeautifulSoup, NavigableString
from threading import Thread

printerLibrary = __import__('printer')
p = printerLibrary.ThermalPrinter(serialport="/dev/ttyAMA0")

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)


BTN_0 = 18
BTN_1 = 23
BTN_2 = 24
BTN_3 = 25
BTN_4 = 17
BTN_5 = 27

# Enable the pullup resistors on the buttons

GPIO.setup(BTN_0, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BTN_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BTN_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BTN_3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BTN_4, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BTN_5, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Use busnum = 1 for new Raspberry Pi's (512MB with mounting holes)
mcp = Adafruit_MCP230XX(busnum = 1, address = 0x20, num_gpios = 16)
 
# Set pins 0, 1 and 2 to output (you can set pins 0..15 this way)
mcp.config(0, mcp.OUTPUT)
mcp.config(1, mcp.OUTPUT)
mcp.config(2, mcp.OUTPUT)
mcp.config(3, mcp.OUTPUT)
mcp.config(4, mcp.OUTPUT)
mcp.config(5, mcp.OUTPUT)

def print_weather(zipcode):
    if zipcode!="":
        file = urllib2.urlopen('http://weather.yahooapis.com/forecastrss?p='+zipcode)
        data = file.read()
        file.close()
        dom = parseString(data)
        conditionTag = dom.getElementsByTagName('yweather:condition')
        currentImageCode = conditionTag[0].attributes['code'].value
        imageFilename = "weather_imgs/"+currentImageCode+".gif"
        urllib.urlretrieve("http://l.yimg.com/a/i/us/we/52/"+currentImageCode+".gif", imageFilename)
        im = Image.open(imageFilename)
        transparency = im.info['transparency']
        os.remove(imageFilename)
        imageFilename = imageFilename.replace('.gif', '.png')
        im.save(imageFilename, transparency=transparency)
        data = list(im.getdata())
        w, h = im.size
        #p.print_bitmap(data, w, h)
        currentText = conditionTag[0].attributes['text'].value
        currentTemp = conditionTag[0].attributes['temp'].value
        print "Now: " + currentText+" "+currentTemp+" F\n"
        p.inverse_on()
        p.bold_on()
        p.print_text("Now:")
        p.inverse_off()
        p.print_text(" "+currentText+" "+currentTemp)
        p.print_text(chr(0xF8))
        p.print_text("F\n")
        p.bold_off()
        
        forecastTag = dom.getElementsByTagName('yweather:forecast')
        todayDay = forecastTag[0].attributes['day'].value
        todayText = forecastTag[0].attributes['text'].value
        todayHigh = forecastTag[0].attributes['high'].value
        todayLow = forecastTag[0].attributes['low'].value
        print todayDay + ": " + todayText
        print "High: " + todayHigh + " F   Low: " + todayLow + " F"
        
        p.inverse_on()
        p.bold_on()
        p.print_text(todayDay + ":")
        p.inverse_off()
        p.print_text(" "+ todayText+"\n")
        p.print_text("    High: " + todayHigh)
        p.print_text(chr(0xF8))
        p.print_text("F   Low: " + todayLow)
        p.print_text(chr(0xF8))
        p.print_text("F\n")
        
        tomorrowDay = forecastTag[1].attributes['day'].value
        tomorrowText = forecastTag[1].attributes['text'].value
        tomorrowHigh = forecastTag[1].attributes['high'].value
        tomorrowLow = forecastTag[1].attributes['low'].value
        print tomorrowDay + ": " + tomorrowText
        print "High: " + tomorrowHigh + " F   Low: " + tomorrowLow + " F"
        
        p.inverse_on()
        p.bold_on()
        p.print_text(tomorrowDay + ":")
        p.inverse_off()
        p.print_text(" "+ tomorrowText+"\n")
        p.print_text("    High: " + tomorrowHigh)
        p.print_text(chr(0xF8))
        p.print_text("F   Low: " + tomorrowLow)
        p.print_text(chr(0xF8))
        p.print_text("F\n")
        
        p.linefeed()
        p.linefeed()
        p.linefeed()
        time.sleep(2)
        
    else:
        print "No zip code entered"
        
def insert(original, new, pos):
    #Inserts new inside original at pos.
    return original[:pos] + new + original[pos:]
        
def print_word_of_day():
    # Print word of the day
    url = "http://www.merriam-webster.com/word/index.xml"
    response = urllib2.urlopen(urllib2.Request(url))
    the_page = response.read() 
    dom = parseString(the_page)
    #retrieve the first xml tag (<tag>data</tag>) that the parser finds with name tagName:
    summaryTag = dom.getElementsByTagName('itunes:summary')[1].toxml()
    #strip off the tag (<tag>data</tag>  --->   data):
    summaryData=summaryTag.replace('<itunes:summary>','').replace('</itunes:summary>','').replace('&quot;','"').replace('\n\n','\n').replace('\n','',1).replace("Merriam-Webster's Word of the Day", "Word of the Day")
    summaryData = summaryData[:summaryData.index('\n', (summaryData.index('Examples:')+15))]
    
    formattedData = unicodedata.normalize('NFKD', summaryData).encode('ascii','ignore')
    print formattedData
    
    p.inverse_on()
    p.bold_on()
    p.print_text(word_wrap(formattedData[0:formattedData.index(":")], 32))
    p.inverse_off()
    p.bold_off()
    
    restofText = formattedData[formattedData.index(":"):]
    restofFormatted = word_wrap(insert(restofText,"\n",restofText.index('\\')), 32)
    
    p.bold_on()
    p.underline_on()
    p.print_text(restofFormatted[:restofFormatted.index('\\')])
    p.bold_off()
    p.underline_off()
    p.print_text(restofFormatted[restofFormatted.index('\\'):])
    
    p.linefeed()
    p.linefeed()
    p.linefeed()
    p.linefeed()
    
def print_verse_of_day():
    file = urllib2.urlopen('http://feeds.feedburner.com/hl-devos-votd?format=xml')
    data = file.read()
    file.close()
    dom = parseString(data)
    
    titleTag = dom.getElementsByTagName('title')[1].toxml()
    titleTag = titleTag.replace('<title>', '').replace('</title>','')
    titleTag = titleTag[titleTag.find('- ')+2:]
    print titleTag
    
    descTag = dom.getElementsByTagName('description')[1].toxml()
    descTag = descTag.replace('<description>', '')
    descTag = descTag[0:descTag.find('&amp;')]
    descTag = descTag.replace('&quot;', '"')
    print descTag
    
    p.inverse_on()
    p.bold_on()
    p.print_text('Verse of the Day:\n')
    p.inverse_off()
    p.underline_on()
    p.print_text(titleTag)
    p.bold_off()
    p.underline_off()
    
    p.linefeed()
    
    p.print_text(word_wrap(descTag, 32))
    
    p.linefeed()
    p.linefeed()
    p.linefeed()
    p.linefeed()
    
def print_today_in_history():
    file = urllib2.urlopen('http://www.factmonster.com/dayinhistory')
    html_doc = file.read()
    file.close()
    
    html_doc = html_doc[html_doc.find('<td class="bodybg"'):html_doc.find('<div class="feeds"')]
    
    soup = BeautifulSoup(html_doc)
    
    count = 0
    
    titles = soup.find_all('h3')
    events = soup.find_all('p', recursive=True)
    
    p.underline_on()
    
    now = datetime.datetime.now()
    p.print_text('Today in History: '+ now.strftime('%B %d') + '\n')
    print 'Today in History: ' + now.strftime('%B %d')
    p.underline_off()
    
    for title in titles:
        title = ''.join(title)
        print title
        print strip_tags(str(events[count]))
        
        p.inverse_on()
        p.bold_on()
        p.print_text(title+'\n')
        p.inverse_off()
        p.bold_off()
        punctuation = { 0x2018:0x27, 0x2019:0x27, 0x201C:0x22, 0x201D:0x22 }
        eventText = unicode(events[count]).translate(punctuation).encode('ascii', 'ignore')
        p.print_text(word_wrap(str(strip_tags(eventText)), 32))
        p.bold_off()
        
        p.linefeed()
        
        count += 1
    
    p.linefeed()
    p.linefeed()
    p.linefeed()
        
def strip_tags(html):
    soup = BeautifulSoup(html)

    invalid_tags = ['b', 'i', 'u', 'a', 'html', 'body', 'p']
    for tag in invalid_tags:
        for match in soup.findAll(tag):
            match.replaceWithChildren()
    return soup
        

def word_wrap(string, width=80, ind1=0, ind2=0, prefix=''):
    """ word wrapping function.
        string: the string to wrap
        width: the column number to wrap at
        prefix: prefix each line with this string (goes before any indentation)
        ind1: number of characters to indent the first line
        ind2: number of characters to indent the rest of the lines
    """
    string = prefix + ind1 * " " + string
    newstring = ""
    while len(string) > width:
        # find position of nearest whitespace char to the left of "width"
        marker = width - 1
        while not string[marker].isspace():
            marker = marker - 1

        # remove line from original string and add it to the new string
        newline = string[0:marker] + "\n"
        newstring = newstring + newline
        string = prefix + ind2 * " " + string[marker + 1:]

    return newstring + string

currentLED = 0
NUM_LEDS = 5
lastLED = NUM_LEDS

for x in range(0, NUM_LEDS+1):
    mcp.output(x, 0)
    
shouldBlink = False
shouldBlink2 = False

def blinkLED(led):
    global shouldBlink
    while shouldBlink==True:
        mcp.output(led, 1)
        time.sleep(.3)
        mcp.output(led, 0)
        time.sleep(.3)
        
def blinkLED2(led):
    global shouldBlink2
    while shouldBlink2==True:
        mcp.output(led, 1)
        time.sleep(.7)
        mcp.output(led, 0)
        time.sleep(.7)
        
def bottom_btn_menu():
    global shouldBlink
    global shouldBlink2
    while True:
        if GPIO.input(BTN_5) == False:
            time.sleep(1)
            if GPIO.input(BTN_5) == False:
                shouldBlink2 = False
                time.sleep(3)
                subprocess.call(['sudo', 'shutdown', '-h', 'now'])
                raise KeyboardInterrupt
            else:
                shouldBlink2 = False
                time.sleep(.5)
                return
        elif GPIO.input(BTN_0) == False:
            mcp.output(lastLED, 0)
            shouldBlink = True
            thread = Thread(target = blinkLED, args = (0, ))
            thread.start()
            text = subprocess.check_output(["/usr/games/fortune", "-s", "science"])
            #text = text.replace('A:', '\nA:')
            #text = text.replace('--', '\n\n--')
            text = ' '.join(text.split())
            text_formatted = word_wrap(text, 32)
            print text_formatted
            p.print_text(text_formatted)
            p.linefeed()
            p.linefeed()
            p.linefeed()
            p.linefeed()
            
            time.sleep(3)
            shouldBlink = False
            
        elif GPIO.input(BTN_1) == False:
            mcp.output(lastLED, 0)
            shouldBlink = True
            thread = Thread(target = blinkLED, args = (1, ))
            thread.start()
            text = subprocess.check_output(["/usr/games/fortune", "-s", "humorists"])
            text = text.replace('A:', '\nA:')
            #text = text.replace('--', '\n\n--')
            text = ' '.join(text.split())
            text_formatted = word_wrap(text, 32)
            print text_formatted
            p.print_text(text_formatted)
            p.linefeed()
            p.linefeed()
            p.linefeed()
            p.linefeed()
            
            time.sleep(3)
            shouldBlink = False
            
        elif GPIO.input(BTN_2) == False:
            mcp.output(lastLED, 0)
            shouldBlink = True
            thread = Thread(target = blinkLED, args = (2, ))
            thread.start()
            text = subprocess.check_output(["/usr/games/fortune", "-s", "computers"])
            text = text.replace('A:', '\nA:')
            #text = text.replace('--', '\n\n--')
            text = ' '.join(text.split())
            text_formatted = word_wrap(text, 32)
            print text_formatted
            p.print_text(text_formatted)
            p.linefeed()
            p.linefeed()
            p.linefeed()
            p.linefeed()
            
            time.sleep(3)
            shouldBlink = False
            
        elif GPIO.input(BTN_3) == False:
            mcp.output(lastLED, 0)
            shouldBlink = True
            thread = Thread(target = blinkLED, args = (3, ))
            thread.start()
            text = subprocess.check_output(["/usr/games/fortune", "news"])
            text = text.replace('A:', '\nA:')
            #text = text.replace('--', '\n\n--')
            text = ' '.join(text.split())
            text_formatted = word_wrap(text, 32)
            print text_formatted
            p.print_text(text_formatted)
            p.linefeed()
            p.linefeed()
            p.linefeed()
            p.linefeed()
            
            time.sleep(3)
            shouldBlink = False
            
        elif GPIO.input(BTN_4) == False:
            mcp.output(lastLED, 0)
            shouldBlink = True
            thread = Thread(target = blinkLED, args = (4, ))
            thread.start()
            text = subprocess.check_output(["/usr/games/fortune", "politics"])
            text = text.replace('A:', '\nA:')
            #text = text.replace('--', '\n\n--')
            text = ' '.join(text.split())
            text_formatted = word_wrap(text, 32)
            print text_formatted
            p.print_text(text_formatted)
            p.linefeed()
            p.linefeed()
            p.linefeed()
            p.linefeed()
            
            time.sleep(3)
            shouldBlink = False
            

start = time.time()
while (True): 
    try:
        if GPIO.input(BTN_0) == False:
            mcp.output(lastLED, 0)
            shouldBlink = True
            thread = Thread(target = blinkLED, args = (0, ))
            thread.start()
            print_weather('11530')
            time.sleep(3)
            shouldBlink = False
            time.sleep(.5)
        elif GPIO.input(BTN_1) == False:
            mcp.output(lastLED, 0)
            shouldBlink = True
            thread = Thread(target = blinkLED, args = (1, ))
            thread.start()
            print_word_of_day()
            time.sleep(8)
            shouldBlink = False
            time.sleep(.5)
        elif GPIO.input(BTN_2) == False:
            mcp.output(lastLED, 0)
            shouldBlink = True
            thread = Thread(target = blinkLED, args = (2, ))
            thread.start()
            print_verse_of_day()
            time.sleep(6)
            shouldBlink = False
            time.sleep(.5)
        elif GPIO.input(BTN_3) == False:
            mcp.output(lastLED, 0)
            shouldBlink = True
            thread = Thread(target = blinkLED, args = (3, ))
            thread.start()
            subprocess.call(['python', '/home/webide/repositories/my-pi-projects/printer_of_knowledge/sudoku-gfx.py'])
            time.sleep(1)
            p2 = printerLibrary.ThermalPrinter(serialport="/dev/ttyAMA0")
            shouldBlink = False
            time.sleep(.5)
        elif GPIO.input(BTN_4) == False:
            mcp.output(lastLED, 0)
            shouldBlink = True
            thread = Thread(target = blinkLED, args = (4, ))
            thread.start()
            print_today_in_history()
            time.sleep(18)
            shouldBlink = False
            time.sleep(.5)
        elif GPIO.input(BTN_5) == False:
            mcp.output(lastLED, 0)
            shouldBlink2 = True
            thread = Thread(target = blinkLED2, args = (5, ))
            thread.start()
            time.sleep(2)
            bottom_btn_menu()
        else:
            if time.time() - start > 1:
                start = time.time()
                mcp.output(currentLED, 1)
                mcp.output(lastLED, 0)
                lastLED = currentLED
                currentLED += 1
                if currentLED==6: 
                    currentLED = 0
    except KeyboardInterrupt:
        for x in range(0, NUM_LEDS+1):
            mcp.output(x, 1)
        exit()