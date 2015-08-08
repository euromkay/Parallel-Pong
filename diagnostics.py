import cProfile
from multiprocessing import Process
import pong, pongdisplay, master

totalwidth = 900
totalheight = 600
big_display = (totalwidth, totalheight)

def run():
	master.setup(ip, port, big_display, big_display)

ip = '0.0.0.0'
port = 5000

w = 0
h = 1
cols = 1
rows = 1



width = totalwidth/cols
left = width * h
right = left + width

height = totalheight/rows
top = height * w
bot = top + height

total_display = pong.toBounds(0, totalwidth, 0, totalheight)
section = pong.toBounds(left, right ,top, bot)
start = (0,0)
Process(target = pongdisplay.setup, args = [ip, port, section, total_display, start]).start()

cProfile.run('run()')

