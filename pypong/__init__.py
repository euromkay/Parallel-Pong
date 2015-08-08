import math, random, entity, time, threading, sys
# from PIL import Image

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
    def __init__(self, player_left, player_right, config, send, ctrls):
        self.player_left = player_left
        self.player_right = player_right

        self.config = config

        self.paddle_left  = entity.Paddle(config['paddle_velocity'], config['paddle_image'], config['paddle_bounds'])
        self.paddle_right = entity.Paddle(config['paddle_velocity'], config['paddle_image'], config['paddle_bounds'])

        self.paddle_left.rect.topleft  = (self.config['paddle_left_position'],  (self.config['screen_size'][1]-self.paddle_left.rect.height)/2)
        self.paddle_right.rect.topleft = (self.config['paddle_right_position'], (self.config['screen_size'][1]-self.paddle_left.rect.height)/2)

        self.ball = entity.Ball( self.config['ball_velocity'], config['ball_image'] )
        
        
        bounds = entity.Rect(0, 0, config['screen_size'][0], config['screen_size'][1])
        self.bounds = bounds

        self.send = send
        self.reset_game(random.random() < 0.5)
        
        self.running = True
        threading.Thread(target = ctrls, args = [self]).start()
        self.time = time.time()

        self.send(self.getInfoPacket())

        ball = self.ball.rect  #refers to ball's rectangle
        velocity = self.ball.velocity_vec #refers to ball's velocity vector
        while self.running:
            hit = self.nextEvent()
            
            while(time.time() < hit['time']):
                if not self.running:
                    return
                #paddle_left.update()
                #paddle_right.update()
                continue

            ball.hit_flag = hit['type']
            if hit['type'] == entity.WALL:
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
                    paddle = self.paddle_left.rect
                    paddle_obj = self.paddle_left

                    playerSide = self.player_left
                    playerNotSide = self.player_right
                else:
                    paddle = self.paddle_right.rect
                    paddle_obj = self.paddle_right

                    playerSide = self.player_right
                    playerNotSide = self.player_left
                    direc = -1.0

                # its a paddle hit
                if within(paddle.top, hit['bally'], paddle.bottom) or within(paddle.top, hit['bally'] + paddle.height, paddle.bottom):
                    ball.x = hit['ballx']
                    ball.y = hit['bally']
                    

                    #velocity = self.paddle_right.calculate_bounce(min(1,max(0,(ball.rect.centery - self.paddle_right.rect.y)/float(self.paddle_right.rect.height))))
                    #ball.velocity = min(self.config['ball_velocity_max'], ball.velocity * self.config['ball_velocity_bounce_multiplier'])
                    #ball.velocity_vec[0] = -velocity[0] * ball.velocity
                    #ball.velocity_vec[1] = velocity[1] * ball.velocity

                    new_velocity = paddle_obj.calculate_bounce(min(1,max(0,(ball.centery - paddle.y)/float(paddle.height))))
                    self.ball.velocity = min(config['ball_velocity_max'], self.ball.velocity * config['bounce_multiplier'])
                    velocity[0] = new_velocity[0] * self.ball.velocity * direc
                    velocity[1] = new_velocity[1] * self.ball.velocity

                    playerSide.hit()

                else: #miss
                    #print 'missed ball'
                    playerSide.lost()
                    playerNotSide.won()

                    time.sleep(2)
                    hit['time'] = time.time()
                    self.reset_game(playerSide == self.player_left)
                    ball.hit_flag = entity.NONE


            self.time = hit['time']
            self.send(self.getInfoPacket())


    def nextEvent(self):
        ball = self.ball.rect
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
            paddle_hit_time += ( (ball.left - self.paddle_left.rect.right) / abs(velocity[0]) )
        else:
            paddle_hit_time += ( (self.paddle_right.rect.left - ball.right) / velocity[0] )

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
                x = self.paddle_left.rect.right
            else:
                typ = entity.PADDLE_RIGHT
                x = self.paddle_right.rect.left - ball.width
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



    

    def getInfoPacket(self):
        print 'sending : ' + str((self.ball.rect.x, self.ball.rect.y))
        if self.ball.rect.x < 0: 
            print 'too far to the left'
            sys.exit()
        if self.ball.rect.y < 0 :
            print 'too far to the top'
            sys.exit()
        if self.ball.rect.bottom > self.bounds.bottom:
            print 'too far to the bottom'
            print str(self.ball.rect.bottom) + ' is greater than ' + str(self.bounds.bottom)
            sys.exit()
        if self.ball.rect.right > self.bounds.right:
            print 'too far to the right'
            sys.exit()

        ball = self.ball
        info = [ball.rect.x, ball.rect.y] #0, 1
        info.extend((ball.velocity_vec[0], ball.velocity_vec[1])) #2, 3
        info.append(self.time) #4
        info.extend(( self.paddle_left.getY(), self.paddle_right.getY() )) # 5, 6
        info.append(ball.hit_flag) # 7
        return info
        
    def reset_game(self, serveLeft=True):

        ball = self.ball

        y = self.config['screen_size'][1] - ball.rect.height
        ball.rect.centerx = self.config['screen_size'][0]/2.0
        ball.rect.centery = self.config['screen_size'][1]/2.0
        ball.velocity = self.config['ball_velocity']
        a = random.random() * math.pi / 2. - math.pi / 4.
        ball.velocity_vec[0] = ball.velocity * math.cos(a)
        ball.velocity_vec[1] = ball.velocity * math.sin(a)
        if random.random() < 0.5:
            ball.velocity_vec[1] *= -1
        if serveLeft:
            ball.velocity_vec[0] *= -1


        


    def update(self):
        ball = self.ball
        self.time = time.time()
        ball.update()
        self.player_left.update(self.paddle_left, self) # update the rects here
        self.player_right.update(self.paddle_right, self)

        # Paddle collision check. Could probably just do a line-line intersect 
        # but I think I prefer having the pixel-pefect result of a rect-rect 
        # intersect test as well.
        if ball.rect.x < self.bounds.centerx:
            # Left side bullet-through-paper check on ball and paddle
            if ball.velocity_vec[0] < 0:
                intersect_point = line_line_intersect(
                    self.paddle_left.rect.right, self.paddle_left.rect.top,
                    self.paddle_left.rect.right, self.paddle_left.rect.bottom,
                    ball.position_x-ball.rect.width/2, ball.position_y+\
                    ball.rect.height/2, ball.position_x-ball.rect.width/2, \
                    ball.position_y+ball.rect.height/2
                )
                if intersect_point:
                    ball.position_y = intersect_point[1]-ball.rect.height/2
                if intersect_point or (self.paddle_left.rect.colliderect(ball.rect)): #and ball.rect.right > self.paddle_left.rect.right):
                    ball.position_x = self.paddle_left.rect.right
                    velocity = self.paddle_left.calculate_bounce(min(1,max(0,(ball.rect.centery - self.paddle_left.rect.y)/float(self.paddle_left.rect.height))))
                    ball.velocity = min(self.config['ball_velocity_max'], ball.velocity * self.config['ball_velocity_bounce_multiplier'])
                    ball.velocity_vec[0] = velocity[0] * ball.velocity
                    ball.velocity_vec[1] = velocity[1] * ball.velocity

                    self.player_left.hit()
                    ball.hit_flag = entity.PADDLE
        else:
            # Right side bullet-through-paper check on ball and paddle.
            if ball.velocity_vec[0] > 0:
                intersect_point = line_line_intersect(
                    self.paddle_right.rect.left, self.paddle_right.rect.top,
                    self.paddle_right.rect.left, self.paddle_right.rect.bottom,
                    ball.position_x-ball.rect.width/2, ball.position_y+ball.rect.height/2,
                    ball.position_x-ball.rect.width/2, ball.position_y+ball.rect.height/2
                )
                if intersect_point:
                    ball.position_y = intersect_point[1]-ball.rect.height/2
                if intersect_point or (self.paddle_right.rect.colliderect(ball.rect)): #and ball.rect.x < self.paddle_right.rect.x):
                    ball.position_x = self.paddle_right.rect.x - ball.rect.width
                    velocity = self.paddle_right.calculate_bounce(min(1,max(0,(ball.rect.centery - self.paddle_right.rect.y)/float(self.paddle_right.rect.height))))
                    ball.velocity = min(self.config['ball_velocity_max'], ball.velocity * self.config['ball_velocity_bounce_multiplier'])
                    ball.velocity_vec[0] = -velocity[0] * ball.velocity
                    ball.velocity_vec[1] = velocity[1] * ball.velocity
                    self.player_right.hit()
        # Bounds collision check
        if ball.rect.y < self.bounds.top:
            ball.position_y = float(self.bounds.top)
            ball.velocity_vec[1] = -ball.velocity_vec[1]
            ball.hit_flag = entity.WALL
        elif ball.rect.y > self.bounds.bottom:
            ball.position_y = float(self.bounds.bottom)
            ball.velocity_vec[1] = -ball.velocity_vec[1]
            ball.hit_flag = entity.WALL
        # Check the ball is still in play
        if ball.rect.x < self.bounds.x:
            self.player_left.lost()
            self.player_right.won()
            self.reset_game(False)
        if ball.rect.x > self.bounds.right:
            self.player_left.won()
            self.player_right.lost()
            self.reset_game(True)

        return ball.hit_flag != entity.NONE

def within(x, a, y):
    return x < a and a < y