import pygame

pygame.mixer.preinit(frequency=22050, size=-16, channels=2, buffersize=2048)
pygame.mixer.init()
def paddle_hit(window):
    collision_song = 'home/pi/collision_song.mp3'
    pygame.mixer.music.load(collision_song)
    pygame.mixer.music.play()

def wall_hit(window):
    wall_song = 'home/pi/wall_song.mp3'
    pygame.mixer.music.load(wall_song)
    pygame.mixer.music.play()

def won_sound(window):
    point_song = 'home/pi/point_song.mp3'
    pygame.mixer.music.load(point_song)
    pygame.mixer.music.play()
