import pypong, socket, struct, threading, select, time, pygame
from pypong.player import BasicAIPlayer, Player

player_left = None # set the players as global so the control thread has access
player_right = None # simplest way to do it

running = True
def setup(ip, port, display, mini_display):
    global player_left, player_right
    rect = pygame.image.load( 'assets/paddle.png' ).get_rect()
    configuration = {
        'screen_size': display,
        'individual_screen_size': mini_display,
        'paddle_image': 'assets/paddle.png',
        'paddle_left_position': 10,
        'paddle_right_position': display[0] - rect.w,
        'paddle_velocity': 120.,
        'paddle_bounds': (1, display[1] - 1),  
        'line_image': 'assets/dividing-line.png',
        'ball_image': 'assets/ball.png',
        'ball_velocity': 80.,
        'ball_velocity_bounce_multiplier': 1.105,
        'ball_velocity_max': 130.,
    }

    #make a socket, and connect to a already running server socket
    # read some file with the ip addresses and put them in the variables ip addersses
    # hard coded for now
    
    connections = []
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((ip, port))
    server_socket.listen(15)

    connections.append(server_socket)

    # Prepare game
    #player_left  = BasicAIPlayer()#None, 'up', 'down')
    player_left  = Player(None, 'up', 'down')
    #player_right = BasicAIPlayer()#None, 'up', 'down')
    player_right = Player(None, 'up', 'down')

    pygame.init()
    pygame.display.set_mode((200,200))
    game = pypong.Game(player_left, player_right, configuration)



    threading.Thread(target = ctrls, args = [game]).start()


    # Main game loop
    while game.running:
        findnewConnections(connections, server_socket)
        game.update()

        coordinates = struct.pack('iiii', game.ball.position_vec[0], game.ball.position_vec[1], game.paddle_left.rect.y, game.paddle_right.rect.y )
        # loop over clients and send the coordinates
        for sock in connections:
            if sock is not server_socket:
                sock.send(coordinates)

        # wait for them to send stuff back to avoid a race condition.
        #for x in range( 0,len( clisocket ) ):
            #clisocket[x].recv( 16 )
        
    pygame.display.quit()
    pygame.quit()

    print 'server is closing'
    server_socket.close()
    print 'server closed'

def findnewConnections(connections, server_socket):
    read_sockets, write_sockets, error_sockets = select.select(connections,[],[], 0.)

    for sock in read_sockets:
        if sock == server_socket:
            sockfd, addr = server_socket.accept()
            connections.append(sockfd)



def ctrls(game):
    global player_left, player_right       

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False
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

            if event.type == pygame.KEYUP:
                player_left.input_state = None
                player_right.input_state = None

    

