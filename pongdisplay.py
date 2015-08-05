import pygame
import sys, os
import socket, select, threading
import cPickle as Pickle
import pypong.entity as entity
import pypong.pong_sound as sound


BLACK = 0,0,0
LEFT_PADDLE = 2
RIGHT_PADDLE = 3
BUFFER = 4096
SOCKET_DEL = '*ET*'

#class broadcastServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    #pass
#class requestHandler(posvec):
def handle(data, tile):

    tile.screen.fill( BLACK )
    
    paddle_index = tile.paddle_index
 
    paddleTopEdge = data[paddle_index]
    paddleBotEdge = paddleTopEdge + entity.PADDLE_LENGTH


    ballRightEdge = data[0] + 96
    ballLeftEdge  = data[1]


    if ( ballRightEdge > tile.left_edge and ballLeftEdge < tile.right_edge ):
        ballrect   = tile.ball.get_rect()
        ballrect.x = data[0] - tile.left_edge # offset the bounds
        ballrect.y = data[1] - tile.top_edge 
        tile.screen.blit( tile.ball, ballrect )

    if tile.isEdge:
        if ( paddleBotEdge > tile.top_edge and paddleTopEdge < tile.bot_edge  ):
            paddle_rect  = tile.paddle.get_rect()
            if paddle_index == RIGHT_PADDLE:
                paddle_rect.x = tile.right_edge - (paddle_rect.w + tile.left_edge)
            paddle_rect.y = data[paddle_index] - tile.top_edge
            tile.screen.blit( tile.paddle, paddle_rect )

    pygame.display.flip()

    if(data[4] == entity.PADDLE):
        sound.paddle_hit(tile.mixer)
    elif(data[4] == entity.WALL):
        sound.wall_hit(tile.mixer)

        #self.request.send( 'Got it' )
        #try:
          #  posvec=self.request.recv( 16 )
       # except:
          #  print( 'client disconnect' )
    #         pygame.quit()
    #         sys.exit()
    # pygame.quit()
    # sys.exit()

def read_pong_settings(left_edge, right_edge, bot_edge, top_edge, tile):
    # put in seperate function since it's special. Could have been done easier
    #settings = open( 'Pong Renders/settings.txt', 'r' )
    #line = settings.readline()
    tile.left_edge = left_edge
    tile.right_edge = right_edge
    tile.bot_edge = bot_edge
    tile.top_edge = top_edge

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
        print 'right_edge_node'
        tile.paddle = pygame.image.load( 'assets/paddle.png' )
        paddle_rect = tile.paddle.get_rect()
        tile.isEdge = True #will signal to update paddle as well
        tile.paddle_index = RIGHT_PADDLE

    if( display['left'] == total_display['left'] ):
        print 'left_edge_node'
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


    data = ''
    while True:
        #read_sockets, _, _ = select.select([s], [], [], 0)
        #for sock in read_sockets:
        data += s.recv(BUFFER)
        s.send('gotit')
        if not data:
            print 'exiting here'
            sys.exit()
        # print 'rdbuff is ' + rdbuf
        #split = data.split(SOCKET_DEL) # split at newline, as per our custom protocol
        #if len(split) == 2: # it should be 2 elements big if it got the whole message

        segments = data.split("-")#Pickle.loads(data)
        while len(segments) >= 7:
            #print data
            posvec = [float(segments[0]), float(segments[1]), float(segments[2]), float(segments[3]), int(segments[4]), int(segments[5])]
            #print posvec
            handle(posvec, tile)

            data = ''
            for seg in segments[6:]:
                data += seg + '-'
            data = data[:-1]
            segments = data.split("-")






class Tile:
    isEdge = False
    ball = None
    screen = None
    bot_edge = 0
    top_edge = 0
    right_edge = 0
    left_edge = 0
    boundsy = (0, 0)
    left_edge_node = ''
    right_edge_node = ''
    paddle_index = 0
    mixer = None


    
    
        
        
