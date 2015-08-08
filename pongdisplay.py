import pygame
import sys, os, time
import socket, select, threading
import cPickle as Pickle
import pypong.entity as entity
import pypong.pong_sound as sound


BLACK = 0,0,0
LEFT_PADDLE = 5
RIGHT_PADDLE = 6
BUFFER = 64
SOCKET_DEL = '*ET*'
ELEMENTS_SENT = 8

BALL_X = 0
BALL_Y = 1

BALL_VX = 2
BALL_VY = 3

TIME = 4

#class broadcastServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    #pass
#class requestHandler(posvec):
def screenDraw(tile):
    topEdge = tile.topEdge
    leftEdge = tile.leftEdge
    rightEdge = tile.rightEdge
    botEdge = tile.botEdge

    print leftEdge, rightEdge, topEdge, botEdge

    ballrect   = tile.ball.get_rect()
    draw = tile.screen.blit
    ball = tile.ball
    paddle_rect  = tile.paddle.get_rect()
    isEdge = tile.isEdge


    paddle_index = tile.paddle_index
    if tile.paddle_index == RIGHT_PADDLE:
        paddle_rect.x = rightEdge - (paddle_rect.w + leftEdge)

    while tile.active:

        tile.screen.fill( BLACK )


        ball_init_x = tile.data[BALL_X]
        ball_init_y = tile.data[BALL_Y]
        ball_vel_x = tile.data[BALL_VX]
        ball_vel_y = tile.data[BALL_VY]
        prev_time = tile.data[TIME]

        curr_time = time.time()
        if curr_time > prev_time:
            print '-----------'
            #tile.active = False


        print ball_init_x
        ball_leftEdge = ball_init_x + (ball_vel_x*(curr_time - prev_time))
        ball_rightEdge = ball_leftEdge + 96

        ball_topEdge = ball_init_y + (ball_vel_y*(curr_time - prev_time))
        ball_botEdge = ball_topEdge + 96


        inWidth = within(leftEdge, ball_leftEdge, rightEdge) or within(leftEdge, ball_rightEdge, rightEdge)
        print leftEdge, ball_rightEdge, rightEdge
        inHeight = within(topEdge, ball_topEdge, botEdge) or within(topEdge, ball_botEdge, botEdge)

        print inWidth
        print inHeight 

        if ( inWidth and inHeight):
            ballrect.x = ball_leftEdge - leftEdge# offset the bounds
            ballrect.y = ball_topEdge - topEdge

            draw( ball, ballrect )

        if isEdge:
            paddleTopEdge = tile.data[paddle_index]
            paddleBotEdge = paddleTopEdge + entity.Paddle.LENGTH
            if ( (topEdge < paddleBotEdge and paddleBotEdge < botEdge ) or (botEdge > paddleTopEdge and paddleTopEdge > topEdge)  ):
                paddle_rect.y = paddleTopEdge - topEdge
                draw( tile.paddle, paddle_rect )

        pygame.display.flip()

        if(tile.data[4] == entity.PADDLE_RIGHT or tile.data[4] == entity.PADDLE_LEFT):
            sound.paddle_hit(tile.mixer)
        elif(tile.data[4] == entity.WALL):
            sound.wall_hit(tile.mixer)

        #self.request.send( 'Got it' )
        #try:
          #  posvec=self.request.recv( 16 )
       # except:
          #  print( 'client disconnect' )
    #         pygame.quit()s
    #         sys.exit()
    # pygame.quit()
    # sys.exit()

def read_pong_settings(left_edge, right_edge, bot_edge, top_edge, tile):
    # put in seperate function since it's special. Could have been done easier
    #settings = open( 'Pong Renders/settings.txt', 'r' )
    #line = settings.readline()
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
        tile.paddle_index = RIGHT_PADDLE

    if( display['left'] == total_display['left'] ):
        tile.paddle = pygame.image.load( 'assets/paddle.png' )
        paddle_rect = tile.paddle.get_rect()
        tile.isEdge = True #will signal to update paddle as well
        tile.paddle_index = LEFT_PADDLE

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

    data = ''
    while tile.active:
        #read_sockets, _, _ = select.select([s], [], [], 0)
        #for sock in read_sockets:
        data += s.recv(BUFFER)
        if not data:
            print 'exiting here'
            return
        s.send('gotit')
        # print 'rdbuff is ' + rdbuf
        #split = data.split(SOCKET_DEL) # split at newline, as per our custom protocol
        #if len(split) == 2: # it should be 2 elements big if it got the whole message

        segments = data.split("*")#Pickle.loads(data)
        while len(segments) >= ELEMENTS_SENT + 1:
            #print data

            posvec = []
            for x in segments[:ELEMENTS_SENT]: #all but last element
                posvec.append(float(x))
                
            posvec.append(int(segments[ELEMENTS_SENT - 1]))

            tile.data = posvec

            data = ''
            for seg in segments[ELEMENTS_SENT:]:
                data += seg + '*'
            data = data[:-1]
            segments = data.split("*")



class Tile:
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
    data = [0.0, 0.0, 0.0, 0.0, sys.float_info.max, 0.0, 0.0, 0]
    active = True


    
    
        
        

def within(x, a, y):
    return x < a and a < y