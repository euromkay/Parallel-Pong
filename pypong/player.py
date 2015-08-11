import random
import pong_sound, entity
import threading, time

class BasicAIPlayer(object):
    def __init__(self, paddle):
        self.bias = random.random() - 0.5
        self.hit_count = 0
        self.paddle = paddle
        self.game = None

        self.start = threading.Thread(target = self.calculate).start

        if paddle.index == entity.PADDLE_LEFT:
            self.name = 'left'
        else:
            self.name = 'right'

    def calculate(self):
        game = self.game
        while game.hit == None:
            continue

        paddleObj = self.paddle

        if paddleObj.index == entity.PADDLE_RIGHT:
            headingMyWay = self.isPositive
        else:
            headingMyWay = self.isNegative


        height = paddleObj.rec.height
        velocity = paddleObj.velocity
        section_length = height/len(paddleObj.bounce_table)

        paddle = paddleObj.rec

        stop = paddleObj.stop
        up = paddleObj.moveUp
        down = paddleObj.moveDown


        lastAction = stop

        while game.running:
            if not headingMyWay(game.ball.velocity_vec[0]):
                if lastAction == stop:
                    continue
                lastAction = stop
                stop()
                continue

            bally = game.hit['bally']
            delta = (paddle.centery + self.bias * height) - bally
            
            if abs(delta) < section_length and paddle.top < bally and paddle.bottom > bally:
                if lastAction != stop:
                    stop()
                    lastAction = stop

            elif delta < 0:
                down()
                time.sleep(abs(delta)/velocity)
                stop()
            elif delta > 0:
                up()
                time.sleep(abs(delta)/velocity)
                stop()
            else:
                if lastAction != stop:
                    stop()
                    lastAction = stop


        print 'aiPlayer ' + str(self.name) + ' control thread stopped\n'



    def isPositive(self, vel):
        return vel > 0

    def isNegative(self, vel):
        return vel < 0

    def hit(self):
        self.hit_count += 1
        if self.hit_count > 2:
            self.bias = random.random() # Recalculate our bias, this game is going on forever
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

