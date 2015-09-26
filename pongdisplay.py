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

    ball_length = entity.Ball.LENGTH

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
    tile.drawing = True
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
        ball_rightEdge = ball_leftEdge + ball_length

        ball_topEdge = ball_init_y + (ball_vel_y*(curr_time- prev_time))
        ball_botEdge = ball_topEdge + ball_length


        inWidth = entity.within(leftEdge, ball_leftEdge, rightEdge) or entity.within(leftEdge, ball_rightEdge, rightEdge)
        inHeight = entity.within(topEdge, ball_topEdge, botEdge) or entity.within(topEdge, ball_botEdge, botEdge)

        if ( inWidth and inHeight):
            ballrect.x = ball_leftEdge - leftEdge# offset the bounds
            ballrect.y = ball_topEdge - topEdge
            draw( ball, ballrect )


        if isEdge:  
            paddleTopEdge = tile.paddle_top + (tile.paddle_direc * (curr_time - tile.paddle_time) * tile.paddle_vel)
            paddleBotEdge = paddleTopEdge + entity.Paddle.HEIGHT

            #paddle trying to go too high up
            if paddleTopEdge < tile.paddle_min:
                paddleTopEdge     = tile.paddle_min
                paddleBotEdge     = paddleTopEdge + entity.Paddle.HEIGHT
                tile.paddle_direc = 0
                tile.paddle_top   = tile.paddle_min

            
            #paddle trying to go too low
            elif tile.paddle_max < paddleTopEdge:
                paddleTopEdge = tile.paddle_max
                paddleBotEdge = paddleTopEdge + entity.Paddle.HEIGHT
                tile.paddle_direc = 0
                tile.paddle_top = tile.paddle_max

            if entity.within(topEdge, paddleBotEdge, botEdge) or entity.within(topEdge, paddleTopEdge, botEdge):
                paddle_rect.y = paddleTopEdge - topEdge
                draw( tile.paddle, paddle_rect )

        pygame.display.flip()

        #if(tile.data[4] == entity.PADDLE_RIGHT or tile.data[4] == entity.PADDLE_LEFT):
            #sound.paddle_hit(tile.mixer)
        #elif(tile.data[4] == entity.WALL):
            #sound.wall_hit(tile.mixer)
    tile.drawing = False


def read_pong_settings(left_edge, right_edge, bot_edge, top_edge, tile):
    tile.leftEdge = left_edge
    tile.rightEdge = right_edge
    tile.botEdge = bot_edge
    tile.topEdge = top_edge

def setup(ip, port, display, total_display, coords = None):
    mode = pygame.FULLSCREEN
    if coords != None:
        os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % coords
        mode = pygame.NOFRAME
    pygame.init()
    tile = Tile()
    tile.screen = pygame.display.mode_ok( (display['right'] - display['left'], display['bot'] - display['top']), mode, 0)

    tile.ball = pygame.image.load( 'assets/ball.png' )
    
    tile.ball = pygame.transform.smoothscale(tile.ball, (entity.Ball.LENGTH, entity.Ball.LENGTH))

    read_pong_settings(display['left'], display['right'], display['bot'], display['top'], tile)
    pygame.mouse.set_visible(False)
    pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=2048)
    pygame.mixer.init()

    tile.mixer = pygame.mixer


    if ( display['right'] == total_display['right'] ):
        tile.isEdge = True #will signal to update paddle as well
        tile.paddle_index = entity.PADDLE_RIGHT

    if( display['left'] == total_display['left'] ):
        tile.isEdge = True #will signal to update paddle as well
        tile.paddle_index = entity.PADDLE_LEFT

    if (tile.isEdge):
        tile.paddle = pygame.image.load( 'assets/paddle.png' )
        tile.paddle = pygame.transform.smoothscale(tile.paddle, (entity.Paddle.WIDTH, entity.Paddle.HEIGHT))
        paddle_rect = tile.paddle.get_rect()

    tile.screen.fill((0,0,240))
    pygame.display.flip()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try :
        time.sleep(3)
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
            while(tile.drawing):
                continue
            
            tile.screen.fill((149,0,0)) #red
            pygame.display.flip()
            time.sleep(3)
            pygame.display.quit()
            pygame.quit()

            print 'display is closing'
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
                tile.ball_time   = float(segments[TIME])
                #print 'initial ball time ' + str(tile.ball_time) 
            elif data_type == pypong.PADDLE_TYPE:
                if tile.isEdge and int(segments[1]) == tile.paddle_index:
                    tile.paddle_top   = float(segments[pypong.P_TOP])
                    tile.paddle_direc = float(segments[pypong.P_DIREC])
                    tile.paddle_time  = float(segments[pypong.P_TIME])
                    #print tile.paddle_direc
            elif data_type == pypong.PADDLE_INIT_TYPE:
                tile.paddle_vel = float(segments[1])
                tile.paddle_min = float(segments[2])
                tile.paddle_max = float(segments[3])
                #print 'tile start info: ' + str((tile.paddle_vel, tile.paddle_min, tile.paddle_max))
            elif data_type == pypong.SOUND_TYPE:
                sound_type = int(segments[1])
                if sound_type == pypong.WALL_HIT:
                    sound.wall_hit(tile.mixer)
                elif sound_type == pypong.PADDLE_HIT:
                    sound.paddle_hit(tile.mixer)
                else:#if sound_type == pypong.WIN:
                    sound.won_sound(tile.mixer)
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
    sounds = []
        
        
