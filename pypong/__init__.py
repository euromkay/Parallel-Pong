import math, random, entity, time, threading, sys
# from PIL import Image

PADDLE_INIT_TYPE = 4

BALL_TYPE = 6

PADDLE_TYPE = 5

SOUND_TYPE = 2

P_TOP = 2
P_DIREC = 3
P_TIME = 4

WALL_HIT = 0
PADDLE_HIT = 1
WIN = 2

def line_line_intersect(x1, y1, x2, y2, x3, y3, x4, y4):
    # Taken from http://paulbourke.net/geometry/lineline2d/
    # Denominator for ua and ub are the same, so store this calculation
    d = float((y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1))
    # n_a and n_b are calculated as seperate values for readability
    n_a = float((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3))
    n_b = float((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3))
    # Make sure there is not a division by zero - this also indicates that
    # the lines are parallel.  
    # If n_a and n_b were both equal to zero the lines would be on top of each 
    # other (coincidental).  This check is not done because it is not 
    # necessary for this implementation (the parallel check accounts for this).
    if d == 0:
        return False
    # Calculate the intermediate fractional point that the lines potentially intersect.
    ua = n_a / d
    ub = n_b / d
    # The fractional point will be between 0 and 1 inclusive if the lines
    # intersect.  If the fractional calculation is larger than 1 or smaller
    # than 0 the lines would need to be longer to intersect.
    if ua >= 0. and ua <= 1. and ub >= 0. and ub <= 1.:
        return [x1 + (ua * (x2 - x1)), y1 + (ua * (y2 - y1))]
    return False
    
class Game(object):
    hit = None
    
    def __init__(self, player_left, player_right, config, send, connections):
        self.player_left = player_left
        self.player_right = player_right

        player_left.game = self
        player_right.game = self

        self.config = config

        player_left.paddle.send  = self.sendPaddlePacket
        player_right.paddle.send = self.sendPaddlePacket

        player_left.paddle.rec.topleft  = (self.config['paddle_left_position'],  (self.config['screen_size'][1]-player_left.paddle.rec.height)/2)
        player_right.paddle.rec.topleft = (self.config['paddle_right_position'], (self.config['screen_size'][1]-player_right.paddle.rec.height)/2)

        self.ball = entity.Ball( self.config['ball_velocity'], config['ball_image'] )
        
        self.setupConnections(connections)

        self.bounds = entity.Rect(0, 0, config['screen_size'][0], config['screen_size'][1])

        paddle = player_left.paddle
        self.send = send
        self.send([PADDLE_INIT_TYPE, paddle.velocity, paddle.bounds[0], paddle.bounds[1]], self.allPorts)
        self.reset_game(player_left.paddle, player_right.paddle, self.bounds, random.random() < 0.5)
        self.running = False

    def setupConnections(self, connections):
        self.allPorts = []
        self.leftPorts = []
        self.rightPorts = []
        max_x = -1
        for port, (x, y) in connections:
            print (x,y)
            if x > max_x:
                max_x = x
                self.rightPorts = []

            if x == 0:
                self.leftPorts.append(port)
            elif x == max_x:
                self.rightPorts.append(port)

            self.allPorts.append(port)
        print len(self.rightPorts)
        print len(self.leftPorts)


    def start(self, ctrls):
        self.running = True
        self.time = time.time()
        self.sendBallPacket()
        self.sendPaddles()

        threading.Thread(target = ctrls, args = [self]).start()

        ball = self.ball.rec  #refers to ball's rectangle
        velocity = self.ball.velocity_vec #refers to ball's velocity vector
        within = entity.within
        bounds = self.bounds

        player_left  = self.player_left
        player_right = self.player_right
        paddle_left  = player_left.paddle
        paddle_right = player_right.paddle
        player_left.start()
        player_right.start()


        while self.running:
            self.hit = self.nextEvent(paddle_left, paddle_right)
            hit = self.hit
            

            while(time.time() < hit['time']):
                if not self.running:
                    break

            if not self.running:
                continue

            ball.hit_flag = hit['type']
            if hit['type'] == entity.WALL:
                self.sendSound(WALL_HIT)
                ball.x = hit['ballx']
                ball.y = hit['bally']
                velocity[1] *= -1



            else:
                paddle = None
                paddle_obj = None
                playerSide = None
                playerNotSide = None
                direc = 1.0
                if hit['type'] == entity.PADDLE_LEFT:
                    paddle = paddle_left.rec
                    paddle_obj = paddle_left

                    playerSide = self.player_left
                    playerNotSide = self.player_right
                else:
                    paddle = paddle_right.rec
                    paddle_obj = paddle_right

                    playerSide = self.player_right
                    playerNotSide = self.player_left
                    direc = -1.0
                paddle_obj.update(paddle_obj.direction)

                # its a paddle hit
                if within(paddle.top, hit['bally'], paddle.bottom) or within(paddle.top, hit['bally'] + paddle.height, paddle.bottom):
                    self.sendSound(PADDLE_HIT)
                    ball.x = hit['ballx']
                    ball.y = hit['bally']

                    new_velocity = paddle_obj.calculate_bounce(min(1,max(0,(ball.centery - paddle.y)/float(paddle.height))))
                    self.ball.velocity = min(self.config['ball_velocity_max'], self.ball.velocity * self.config['bounce_multiplier'])
                    velocity[0] = new_velocity[0] * self.ball.velocity * direc
                    velocity[1] = new_velocity[1] * self.ball.velocity

                    playerSide.hit() #really for purposes of the robot so it can hit
                else: #miss
                    self.sendSound(WIN)
                    print 'missed ball'
                    playerSide.lost()
                    playerNotSide.won()

                    time.sleep(2)
                    hit['time'] = time.time()
                    self.reset_game(paddle_left, paddle_right, self.bounds, playerSide == self.player_left)


            self.time = hit['time']
            self.sendBallPacket()

        print 'game ended'

    def sendSound(self, sound):
        self.send([SOUND_TYPE, sound], self.allPorts)

    def nextEvent(self, paddle_left, paddle_right):
        ball = self.ball.rec
        bounds = self.bounds
        velocity = self.ball.velocity_vec

        headingLeft = velocity[0] < 0.0
        headingUp   = velocity[1] < 0.0
        paddle_hit_time = self.time
        wall_hit_time = self.time

        #DIVIDE BY 0 ERROR
        if velocity[0] == 0.0:
            paddle_hit_time = float('inf')
        elif headingLeft: 
            paddle_hit_time += ( (ball.left - paddle_left.rec.right) / abs(velocity[0]) )
        else:
            paddle_hit_time += ( (paddle_right.rec.left - ball.right) / velocity[0] )

        if velocity[1] == 0.0:
            wall_hit_time = float('inf')
        elif headingUp:
            wall_hit_time += (bounds.top - ball.top) / velocity[1]
        else:
            wall_hit_time += (bounds.bottom - ball.bottom) / velocity[1]


        t = 0.0
        y = 0.0
        x = 0.0
        typ = 0
        if paddle_hit_time < wall_hit_time:
            t = paddle_hit_time
            if headingLeft:
                typ = entity.PADDLE_LEFT
                x = paddle_left.rec.right
            else:
                typ = entity.PADDLE_RIGHT
                x = paddle_right.rec.left - ball.width
            y = ball.y + (t - self.time) * self.ball.velocity_vec[1]
        else:
            typ = entity.WALL
            t = wall_hit_time
            if headingUp:
                y = bounds.top
            else:
                y = bounds.bottom - ball.height
            x = ball.x + (t - self.time) * self.ball.velocity_vec[0]
        
        if x == ball.x and y == ball.y:
            self.running = False
            return dict(time = float('inf'))

        return dict(time = t, ballx = x, bally = y, type = typ)

    

    def sendBallPacket(self):
        if self.ball.rec.x < 0: 
            print 'too far to the left'
            sys.exit()
        if self.ball.rec.y < 0 :
            print 'too far to the top'
            sys.exit()
        if self.ball.rec.bottom > self.bounds.bottom:
            print 'too far to the bottom'
            sys.exit()
        if self.ball.rec.right > self.bounds.right:
            print 'too far to the right'
            sys.exit()

        ball = self.ball
        info = [BALL_TYPE, ball.rec.x, ball.rec.y] #0, 1
        info.extend((ball.velocity_vec[0], ball.velocity_vec[1])) #2, 3
        info.append(self.time) #4
        self.send(info, self.allPorts)

    def sendPaddlePacket(self, paddle, byPass = False):
        info = [PADDLE_TYPE]
        info.append(paddle.index)
        info.append(paddle.rec.top)
        info.append(paddle.direction)
        info.append(paddle.time)
        ports = []
        if(paddle.index == entity.PADDLE_LEFT):
            ports = self.leftPorts
        else:
            ports = self.rightPorts
        self.send(info, ports)


    def reset_game(self, paddle_left, paddle_right, bounds, serveLeft=True):
        ball = self.ball

        y = self.config['screen_size'][1] - ball.rec.height
        ball.rec.centerx = self.config['screen_size'][0]/2.0
        ball.rec.centery = self.config['screen_size'][1]/2.0
        ball.velocity = self.config['ball_velocity']
        a = random.random() * math.pi / 2. - math.pi / 4.
        ball.velocity_vec[0] = ball.velocity * math.cos(a)
        ball.velocity_vec[1] = ball.velocity * math.sin(a)
        if random.random() < 0.5:
            ball.velocity_vec[1] *= -1
        if serveLeft:
            ball.velocity_vec[0] *= -1

        paddle_left.direction  = 0
        paddle_right.direction = 0

        paddle_left.rec.centery  = bounds.centery
        paddle_right.rec.centery = bounds.centery

        paddle_left.time  = time.time()
        paddle_right.time = time.time()
        self.sendPaddles(byPass = True)

    def sendPaddles(self, byPass = False):
        self.sendPaddlePacket(self.player_right.paddle, byPass)
        self.sendPaddlePacket(self.player_left.paddle, byPass)


def within(x, a, y):
    return x < a and a < y