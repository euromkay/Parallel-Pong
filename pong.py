from multiprocessing import Process
import master
import pongdisplay
import sys, platform

totalwidth = 900
totalheight = 600

def toBounds(left, right, top, bot):
	disp = {}
	disp['left'] = left
	disp['right'] = right
	disp['bot'] = bot
	disp['top'] = top
	return disp

def disp(ip, port, section, start):
	total_display = toBounds(0, totalwidth, 0, totalheight)
	return Process(target = pongdisplay.setup, args= [ip, port, section, total_display, start])


local = (len(sys.argv) == 3)

if local:

	ip = "0.0.0.0"
	port = 5000

	rows  = int(sys.argv[1])
	cols  = int(sys.argv[2])
	scale = 1
	i = 0
	t = None
	for w in reversed(range(rows)):
		for h in range(cols):
			width = totalwidth/cols
			left = width * h
			right = left + width

			height = totalheight/rows
			top = height * w
			bot = top + height

			t = disp(ip, port, toBounds(left, right ,top, bot), (left,top) )
			i += 1
			t.start()

	
	big_display = (totalwidth, totalheight)
	mini_display = totalwidth/cols, totalheight/rows

	master_thread = Process(target = master.setup, args = [ip, port, big_display, mini_display, i, scale])
	master_thread.start()

else:
	TOTAL_WIDTH = 1920 * 5
	TOTAL_HEIGHT = 1200 * 3
	mini_display = 1920, 1200
	scal = 1
	COLS = 5
	ROWS = 3
	name = platform.node()
	ip = "10.0.0.10"
	port = 5000
	if name == 'master':
		master.setup(ip, port, (TOTAL_WIDTH, TOTAL_HEIGHT), mini_display, 15, scale = 5)
	else:
		xcoord = int(name[5])
		ycoord = int(name[7])

		width = TOTAL_WIDTH/COLS
		left = width * xcoord
		right = left + width

		height = TOTAL_HEIGHT/ROWS
		top = height * ycoord
		bot = top + height

		bounds = toBounds(left, right, top, bot)
		total_display = toBounds(0, TOTAL_WIDTH, 0, TOTAL_HEIGHT)
		pongdisplay.setup(ip, port, bounds, total_display, None)
