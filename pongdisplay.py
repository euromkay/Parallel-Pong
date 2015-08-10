import pygame
import sys, os, time
import socket, select, threading
import cPickle as Pickle
import pypong.entity as entity
import pypong.pong_sound as sound
import pypong


BLACK = 0,0,0
BUFFER = 64


BALL_X = 1
BALL_Y = 2

BALL_VX = 3
BALL_VY = 4
TIME = 5




#class broadcastServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    #pass
#class requestHandler(posvec):
def screenDraw(tile):
    topEdge = tile.topEdge
    leftEdge = tile.leftEdge
    rightEdge = tile.rightEdge
    botEdge = tile.botEdge


    ballrect   = tile.ball.get_rect()
    draw = tile.screen.blit
    ball = tile.ball
    isEdge = tile.isEdge
    if isEdge:
        paddle_rect  = tile.paddle.get_rect()
    getTime = time.time

    if tile.paddle_index == entity.PADDLE_RIGHT:
        paddle_rect.x = rightEdge - (paddle_rect.w + leftEdge)
    b = True
    while tile.active:
        #print tile.paddle_direc

        tile.screen.fill( BLACK )


        ball_init_x = tile.ball_left
        ball_init_y = tile.ball_top
        ball_vel_x = tile.ball_vel_x
        ball_vel_y = tile.ball_vel_y
        prev_time = tile.ball_time

        curr_time = getTime()

        ball_leftEdge  = ball_init_x + (ball_vel_x*(curr_time - prev_time))
        ball_rightEdge = ball_leftEdge + 96

        ball_topEdge = ball_init_y + (ball_vel_y*(curr_time- prev_time))
        ball_botEdge = ball_topEdge + 96


        inWidth = within(leftEdge, ball_leftEdge, rightEdge) or within(leftEdge, ball_rightEdge, rightEdge)
        inHeight = within(topEdge, ball_topEdge, botEdge) or within(topEdge, ball_botEdge, botEdge)

        if ( inWidth and inHeight):
            ballrect.x = ball_leftEdge - leftEdge# offset the bounds
            ballrect.y = ball_topEdge - topEdge
            draw( ball, ballrect )

        if isEdge:  
            paddleTopEdge = tile.paddle_top + (tile.paddle_direc * (curr_time - tile.paddle_time) * tile.paddle_vel)
            paddleBotEdge = paddleTopEdge + entity.Paddle.LENGTH

            #paddle trying to go too high up
            if paddleTopEdge < tile.paddle_min:
                print tile.paddle_top, tile.paddle_direc, paddleTopEdge, tile.paddle_min
                return
                paddleTopEdge     = tile.paddle_min
                paddleBotEdge     = paddleTopEdge + entity.Paddle.LENGTH
                tile.paddle_direc = 0
                tile.paddle_top   = tile.paddle_min
                print 'nto supposed to go here'

            
            #paddle trying to go too low
            elif tile.paddle_max < paddleTopEdge:
                return
                print 'Wtf why you in here'
                paddleTopEdge = tile.paddle_max
                paddleBotEdge = paddleTopEdge + entity.Paddle.LENGTH
                tile.paddle_direc = 0
                tile.paddle_top = tile.paddle_max

            if within(topEdge, paddleBotEdge, botEdge) or within(topEdge, paddleTopEdge, botEdge):
                paddle_rect.y = paddleTopEdge - topEdge
                draw( tile.paddle, paddle_rect )

        pygame.display.flip()

        #if(tile.data[4] == entity.PADDLE_RIGHT or tile.data[4] == entity.PADDLE_LEFT):
            #sound.paddle_hit(tile.mixer)
        #elif(tile.data[4] == entity.WALL):
            #sound.wall_hit(tile.mixer)


def read_pong_settings(left_edge, right_edge, bot_edge, top_edge, tile):
    tile.leftEdge = left_edge
    tile.rightEdge = right_edge
    tile.botEdge = bot_edge
    tile.topEdge = top_edge

def setup(ip, port, display, total_display, coords = None):
    if coords != None:
        os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % coords
    pygame.init()
    tile = Tile()
    tile.screen = pygame.display.set_mode( (display['right'] - display['left'], display['bot'] - display['top']))

    tile.ball = pygame.image.load( 'assets/ball.png' )

    read_pong_settings(display['left'], display['right'], display['bot'], display['top'], tile)
    pygame.mouse.set_visible(False)
    pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=2048)
    pygame.mixer.init()

    tile.mixer = pygame.mixer


    if ( display['right'] == total_display['right'] ):
        tile.paddle = pygame.image.load( 'assets/paddle.png' )
        paddle_rect = tile.paddle.get_rect()
        tile.isEdge = True #will signal to update paddle as well
        tile.paddle_index = entity.PADDLE_RIGHT

    if( display['left'] == total_display['left'] ):
        tile.paddle = pygame.image.load( 'assets/paddle.png' )
        paddle_rect = tile.paddle.get_rect()
        tile.isEdge = True #will signal to update paddle as well
        tile.paddle_index = entity.PADDLE_LEFT

    #else:
     #   print 'nope'
     #   edge_node = False
    pygame.display.flip()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(None)

    try :
        s.connect((ip, port))
    except :
        print 'Unable to connect'
        sys.exit()

    threading.Thread(target = screenDraw, args=[tile]).start()

    data_type = -1

    data = ''
    while tile.active:
        data += s.recv(BUFFER)
        if not data:
            tile.active = False
            print 'exiting here'
            return
        s.send('gotit')

        segments = data.split("*")
        if len(segments) < 2:  #that means the full type hasn't come in yet
            continue

        data_type = int(segments[0])

        while len(segments) >= data_type + 1:

            if data_type == pypong.BALL_TYPE:
                tile.ball_left   = float(segments[BALL_X])
                tile.ball_top    = float(segments[BALL_Y])
                tile.ball_vel_x  = float(segments[BALL_VX])
                tile.ball_vel_y  = float(segments[BALL_VY])
                tile.ball_time = float(segments[TIME])
                #print 'initial ball time ' + str(tile.ball_time) 
            elif data_type == pypong.PADDLE_TYPE:
                if tile.isEdge and int(segments[1]) == tile.paddle_index:
                    tile.paddle_top   = float(segments[pypong.P_TOP])
                    tile.paddle_direc = float(segments[pypong.P_DIREC])
                    tile.paddle_time  = float(segments[pypong.P_TIME])
                    print tile.paddle_direc
            elif data_type == pypong.PADDLE_INIT_TYPE:
                tile.paddle_vel = float(segments[1])
                tile.paddle_min = float(segments[2])
                tile.paddle_max = float(segments[3])
                print 'tile start info: ' + str((tile.paddle_vel, tile.paddle_min, tile.paddle_max))

            data = ''
            for seg in segments[data_type:]:
                data += seg + '*'
            data = data[:-1]
            segments = data.split("*")

            if len(segments) < 2:
                break

            data_type = int(segments[0])




class Tile(object):
    isEdge = False
    ball = None
    screen = None
    botEdge = 0
    topEdge = 0
    rightEdge = 0
    leftEdge = 0
    boundsy = (0, 0)
    left_edge_node = ''
    right_edge_node = ''
    paddle_index = 0
    mixer = None
    active = True
    ball_left = 0.0
    ball_top = 0.0
    ball_vel_y = 0.0
    ball_vel_x = 0.0
    ball_time = time.time()
    paddle_top = 200
    paddle_direc = 0
    paddle_time = time.time()
    paddle_vel = 0.0
    paddle_min = -5000
    paddle_max = sys.float_info.max

        
        

def within(x, a, y):
    return x < a and a < y