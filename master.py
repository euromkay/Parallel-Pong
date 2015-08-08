import pypong, socket, struct, select, time, pygame
import cPickle as Pickle
from pypong.player import BasicAIPlayer, Player
from functools import partial
import pongdisplay

player_left = None # set the players as global so the control thread has access
player_right = None # simplest way to do it

running = True
def setup(ip, port, display, mini_display, client_num, scale = 1):
    global player_left, player_right
    rect = pygame.image.load( 'assets/paddle.png' ).get_rect()
    configuration = {
        'screen_size': display,
        'individual_screen_size': mini_display,
        'paddle_image': 'assets/paddle.png',
        'paddle_left_position': 10, #x position
        'paddle_right_position': (display[0] - 10) - rect.w, #this is the x position of the paddle
        'paddle_velocity': 12.,
        'paddle_bounds': (0, display[1]),  
        #'line_image': 'assets/dividing-line.png',
        'ball_image': 'assets/ball.png',
        'ball_velocity': 80.*scale,
        'ball_velocity_max': 130.*scale,
        'bounce_multiplier': 1.105,
    }

    #make a socket, and connect to a already running server socket
    # read some file with the ip addresses and put them in the variables ip addersses
    # hard coded for now
    
    connections = []
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((ip, port))
    server_socket.listen(client_num)

    connections.append(server_socket)

    while len(connections) != client_num + 1:
        findnewConnections(connections, server_socket)        

    # Prepare game
    player_left  = BasicAIPlayer()#None, 'up', 'down')
    #player_left  = Player(None, 'up', 'down')
    player_right = BasicAIPlayer()#None, 'up', 'down')
    #player_right = Player(None, 'up', 'down')

    pygame.display.init()
    pygame.display.set_mode((200,200))




    game = pypong.Game(player_left, player_right, configuration, partial(sendConnection, connections = connections, server_socket = server_socket), ctrls)
    pygame.display.quit()

    server_socket.close()
    print 'server closed'

def sendConnection(info, connections, server_socket):
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


def findnewConnections(connections, server_socket):
    read_sockets, write_sockets, error_sockets = select.select(connections,[],[], 0.)

    for sock in read_sockets:
        if sock == server_socket:
            sockfd, addr = server_socket.accept()
            connections.append(sockfd)



def ctrls(game):
    global player_left, player_right       

    while game.running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False
                print 'close detected'
                return

            if event.type == pygame.KEYDOWN:
                player_left.input_state = None
                player_right.input_state = None
                
                if event.key == pygame.K_r:
                    player_right.input_state = 'up'
                if event.key == pygame.K_f:
                    player_right.input_state = 'down'

                if event.key == pygame.K_UP:
                    player_left.input_state = 'up'
                if event.key == pygame.K_DOWN:
                    player_left.input_state = 'down'
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_p:
                    print game.ball.rect.x, game.ball.rect.y
                    print game.ball.velocity_vec[0], game.ball.velocity_vec[1]  

            if event.type == pygame.KEYUP:
                player_left.input_state = None
                player_right.input_state = None

    

