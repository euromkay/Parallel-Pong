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


class Board(object):
    def __init__(self, x, y, x_total, y_total):
        self.active = True

        self.x = x
        self.y = y
        self.x_total = x_total
        self.y_total = y_total

        self.ball_left = 0.0
        self.ball_top = 0.0
        self.ball_vel_y = 0.0
        self.ball_vel_x = 0.0
        self.ball_time = time.time()

        self.paddle_top = 0.0
        self.paddle_direc = 0.0
        self.paddle_time = self.ball_time
        self.paddle_vel = 0.0
        self.paddle_min = 0.0
        self.paddle_max = 0.0

        if ( x == 0 ):
            self.isEdge = True #will signal to update paddle as well
            self.paddle_index = entity.PADDLE_LEFT

        if( x == x_total - 1):
            self.isEdge = True #will signal to update paddle as well
            self.paddle_index = entity.PADDLE_RIGHT

        self.frame = pygame.FULLSCREEN

        



    def start(self):
        pygame.init()
        pygame.mouse.set_visible(False)

        self.screen = pygame.display.set_mode((self.rightEdge - self.leftEdge, self.botEdge - self.topEdge), self.mode, 0)
        self.screen.fill((0,0, 199)) #blue
        pygame.display.flip()

        pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=2048)
        pygame.mixer.init()
        mixer = pygame.mixer


        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try :
            time.sleep(3)
            s.connect((self.ip, self.port))
        except :
            print 'Unable to connect'
            sys.exit()

        val = str(self.x+3*self.y)
        if len(val) == 0:
            val = '0' + val
        #s.send(val)

        threading.Thread(target = self.screenDraw).start()

        data_type = -1

        data = ''
        while self.active:
            data += s.recv(BUFFER)
            if not data:
                print 'end signal'
                self.active = False
                while(self.drawing):
                    continue
                
                self.screen.fill((149,0,0)) #red
                pygame.display.flip()
                time.sleep(3)
                pygame.display.quit()

                print 'display is closing'
                return
            s.send('gotit')

            segments = data.split("*")
            if len(segments) < 2:  #that means the full type hasn't come in yet
                continue

            data_type = int(segments[0])

            while len(segments) >= data_type + 1:

                if data_type == pypong.BALL_TYPE:
                    self.ball_left   = float(segments[BALL_X])
                    self.ball_top    = float(segments[BALL_Y])
                    self.ball_vel_x  = float(segments[BALL_VX])
                    self.ball_vel_y  = float(segments[BALL_VY])
                    self.ball_time   = float(segments[TIME])
                    #print 'initial ball time ' + str(tile.ball_time) 
                elif data_type == pypong.PADDLE_TYPE:
                    if self.isEdge and int(segments[1]) == self.paddle_index:
                        self.paddle_top   = float(segments[pypong.P_TOP])
                        self.paddle_direc = float(segments[pypong.P_DIREC])
                        self.paddle_time  = float(segments[pypong.P_TIME])
                        #print tile.paddle_direc
                elif data_type == pypong.PADDLE_INIT_TYPE:
                    self.paddle_vel = float(segments[1])
                    self.paddle_min = float(segments[2])
                    self.paddle_max = float(segments[3])
                    #print 'tile start info: ' + str((tile.paddle_vel, tile.paddle_min, tile.paddle_max))
                elif data_type == pypong.SOUND_TYPE:
                    sound_type = int(segments[1])
                    if sound_type == pypong.WALL_HIT:
                        sound.wall_hit(mixer)
                    elif sound_type == pypong.PADDLE_HIT:
                        sound.paddle_hit(mixer)
                    else:#if sound_type == pypong.WIN:
                        sound.won_sound(mixer)
                data = ''
                for seg in segments[data_type:]:
                    data += seg + '*'
                data = data[:-1]
                segments = data.split("*")

                if len(segments) < 2:
                    break

                data_type = int(segments[0])

    def screenDraw(self):
        topEdge = self.topEdge
        leftEdge = self.leftEdge
        rightEdge = self.rightEdge
        botEdge = self.botEdge

        ball_length = entity.Ball.LENGTH

        draw = self.screen.blit
        clear = self.screen.fill
        flip = pygame.display.flip


        ball = pygame.image.load( 'assets/ball.png' )
        ball = pygame.transform.smoothscale(ball, (entity.Ball.LENGTH, entity.Ball.LENGTH))
        ballrect = ball.get_rect()

        isEdge = self.isEdge
        if isEdge:
            paddle = pygame.image.load( 'assets/paddle.png' )
            paddle = pygame.transform.smoothscale(paddle, (entity.Paddle.WIDTH, entity.Paddle.HEIGHT))
            paddle_rect  = paddle.get_rect()

        getTime = time.time

        if self.paddle_index == entity.PADDLE_RIGHT:
            paddle_rect.x = rightEdge - (paddle_rect.w + leftEdge)
        b = True #what is this
        self.drawing = True
        while self.active:
            clear(BLACK)


            ball_init_x = self.ball_left
            ball_init_y = self.ball_top
            ball_vel_x = self.ball_vel_x
            ball_vel_y = self.ball_vel_y
            prev_time = self.ball_time

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
                paddleTopEdge = self.paddle_top + (self.paddle_direc * (curr_time - self.paddle_time) * self.paddle_vel)
                paddleBotEdge = paddleTopEdge + entity.Paddle.HEIGHT

                #paddle trying to go too high up
                if paddleTopEdge < self.paddle_min:
                    paddleTopEdge     = self.paddle_min
                    paddleBotEdge     = paddleTopEdge + entity.Paddle.HEIGHT
                    self.paddle_direc = 0
                    self.paddle_top   = self.paddle_min

                
                #paddle trying to go too low
                elif self.paddle_max < paddleTopEdge:
                    paddleTopEdge     = self.paddle_max
                    paddleBotEdge     = paddleTopEdge + entity.Paddle.HEIGHT
                    self.paddle_direc = 0
                    self.paddle_top   = self.paddle_max

                if entity.within(topEdge, paddleBotEdge, botEdge) or entity.within(topEdge, paddleTopEdge, botEdge):
                    paddle_rect.y = paddleTopEdge - topEdge
                    draw( paddle, paddle_rect )

            flip()

            #if(tile.data[4] == entity.PADDLE_RIGHT or tile.data[4] == entity.PADDLE_LEFT):
                #sound.paddle_hit(tile.mixer)
            #elif(tile.data[4] == entity.WALL):
                #sound.wall_hit(tile.mixer)
        self.drawing = False


    def setIP(self, ip, port):
        self.ip = ip
        self.port = port
            

    def setCoords(self):

        os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (self.leftEdge + 10, self.topEdge + 10)
        self.mode = pygame.NOFRAME

    def setDisplay(self, display):
        width = display[0]
        height = display[1]

        border = 0

        self.topEdge = self.y * (height + border)
        self.botEdge = self.topEdge + height

        self.leftEdge  = self.x * (width + border)
        self.rightEdge = self.leftEdge + width
        
