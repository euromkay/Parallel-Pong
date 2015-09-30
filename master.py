import pypong, socket, struct, select, time, pygame, threading
import cPickle as Pickle
from pypong.player import BasicAIPlayer, Player
from functools import partial
import pongdisplay
import pypong.entity as entity
import pypong

player_left = None # set the players as global so the control thread has access
player_right = None # simplest way to do it

running = True


server_socket = None

def setup(ip, port, display, mini_display, client_num, scale = 1):
    global player_left, player_right, server_socket
    rect = pygame.image.load( 'assets/paddle.png' ).get_rect()
    config = {
        'screen_size': display,
        'individual_screen_size': mini_display,
        'paddle_image': 'assets/paddle.png',
        'paddle_left_position': 10, #x position
        'paddle_right_position': (display[0] - 10) - rect.w, #this is the x position of the paddle
        'paddle_velocity': 120. * scale,
        'paddle_bounds': (0, display[1]),  
        #'line_image': 'assets/dividing-line.png',
        'ball_image': 'assets/ball.png',
        'ball_velocity': 80. * scale,
        'ball_velocity_max': 130. * scale,
        'bounce_multiplier': 1.105,
    }

    x = display[0]/mini_display[0]
    y = display[1]/mini_display[1]
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((ip, port))
    server_socket.listen(client_num)

    connections = []
    connections.append(server_socket)
    ports = []

    while len(connections) != client_num + 1:
        findnewConnections(connections, server_socket, x, y, ports)  
    connections.remove(server_socket)      

    paddle_left  = entity.Paddle(config['paddle_velocity'], config['paddle_image'], config['paddle_bounds'], entity.PADDLE_LEFT)
    paddle_right = entity.Paddle(config['paddle_velocity'], config['paddle_image'], config['paddle_bounds'], entity.PADDLE_RIGHT)

    ai = False
    # Prepare game
    if(ai):
        player_right = BasicAIPlayer(paddle_right)#None, 'up', 'down')
        player_left  = BasicAIPlayer(paddle_left)#None, 'up', 'down')
    else:
        player_left  = Player(paddle_left)
        player_right = Player(paddle_right)


    pygame.display.init()
    pygame.display.set_mode((200,200))

    game = pypong.Game(player_left, player_right, config, sendHandler, ports)

    #threading.Thread(target = sendConnection, args = [game, connections, server_socket]).start()

    game.start(ctrls)
    pygame.display.quit()

    for sock in connections:
        sock.close()

    server_socket.close()
    print 'server closed'


def findnewConnections(connections, server_socket, _x, _y, ports):
    read_sockets, write_sockets, error_sockets = select.select(connections,[],[], 0.)

    for sock in read_sockets:
        if sock == server_socket:
            sockfd, addr = server_socket.accept()
            val = int(sockfd.recv(2))
            x = val % _x
            y = val / _x
            connections.append(sockfd)
            print (x,y)
            ports.append((sockfd, (x, y)))
    #print len(ports)




def sendHandler(info, connections):
    sendInfo(info, connections)
    return

ball = None
paddleLeft = None
paddleRight = None
paddleInfo = None

ball_lock  = threading.Lock()
right_lock = threading.Lock()
left_lock  = threading.Lock()

lock = threading.Lock()
def sendInfo(info, connections):
    lock.acquire()
    if info == None:
        return
    coordinates = ''
    for x in info:
        coordinates += str(x) + "*"
    #coordinates = coordinates[:-1]#Pickle.dumps(, Pickle.HIGHEST_PROTOCOL)# + pongdisplay.SOCKET_DEL
    #print coordinates
    # loop over clients and send the coordinates
    for sock in connections:
        if sock is not server_socket:
            sock.send(coordinates)
            sock.recv(16)
    lock.release()

def ctrls(game):
    global player_left, player_right       

    while game.running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False
                break

            if event.type == pygame.KEYDOWN:
                
                if event.key == pygame.K_r:
                    player_right.paddle.moveUp()
                if event.key == pygame.K_f:
                    player_right.paddle.moveDown()

                if event.key == 264 or event.key == pygame.K_UP:
                    player_left.paddle.moveUp()
                if event.key == 258 or event.key == pygame.K_DOWN:
                    player_left.paddle.moveDown()

                if event.key == pygame.K_ESCAPE:
                    game.running = False

                if event.key == pygame.K_p:
                    print game.ball.rec.x, game.ball.rec.y
                    print game.ball.velocity_vec[0], game.ball.velocity_vec[1] 

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_r or event.key == pygame.K_f:
                    player_right.paddle.stop()
                if event.key == pygame.K_UP or event.key == pygame.K_DOWN or event.key == 264 or event.key == 258:
                    player_left.paddle.stop()

    print 'controls finished: 1\n'
    
