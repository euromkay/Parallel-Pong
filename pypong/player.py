import random
import pong_sound

class BasicAIPlayer(object):
    def __init__(self, paddle):
        self.bias = random.random() - 0.5
        self.hit_count = 0
        self.paddle = paddle
        
    def update(self, ball_center, bounds):
        paddle = self.paddle
        # Dead simple AI, waits until the ball is on its side of the screen then moves the paddle to intercept.
        # A bias is used to decide which edge of the paddle is going to be favored.
        #paddle.update()

           #paddle left edge to the left of center   ball left edge
        if (paddle.rec.left < bounds.centerx and ball_center[0] < bounds.centerx) or (paddle.rec.right > bounds.centerx and ball_center[0] > bounds.centerx):
            delta = (paddle.rec.centery + self.bias * paddle.rec.height) - ball_center[1]
            #if abs(delta) > paddle.velocity:
            if delta > 0:
                #print '\t move down'
                return paddle.moveDown()
            #else:
            #print '\t move up'
            return paddle.moveUp()
        #else:
        #print '\t is going to hit the paddle, don\'t move it'
        return paddle.stop()

    def hit(self):
        self.hit_count += 1
        if self.hit_count > 6:
            self.bias = random.random() - 0.5 # Recalculate our bias, this game is going on forever
            self.hit_count = 0
            
    def lost(self):
        # If we lose, randomise the bias again
        self.bias = random.random() - 0.5
        
    def won(self):
        pass
        
class Player(object):
    def __init__(self, paddle):
        self.paddle = paddle
        
    def update(self, paddle, game):
        if self.paddle.update():
            game.send
        #if self.input_state == self.up_key:
        #    paddle.moveUp()
        #elif self.input_state == self.down_key:
        #    paddle.moveDown()
        #else:
        #    paddle.stop()
        #paddle.update()
        return True

    def hit(self):
        pass

    def lost(self):
        pass
        
    def won(self):
        pass

