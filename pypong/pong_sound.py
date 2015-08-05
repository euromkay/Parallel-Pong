
def paddle_hit(mixer):
  collision_song = './assets/hit_sound.mp3'
  mixer.music.load(collision_song)
  mixer.music.play()

def wall_hit(mixer):
  wall_song = './assets/bounce-wall.wav'
  mixer.music.load(wall_song)
  mixer.music.play()

def won_sound(mixer):
  point_song = './assets/won_sound.mp3'
  mixer.music.load(point_song)
  mixer.music.play()
