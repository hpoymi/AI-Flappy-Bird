import random
import sys
import pygame
import pygame_widgets
from pygame_widgets.slider import Slider
from pygame.locals import *
import numpy
import matplotlib.pyplot as plt

SW = 280  # Szerokość okna
SH = 511  # Wysokość okna
TIMEMS = 50  # Czas w milisekundach

BASEY = SH * 0.8  # Bazowa pozycja Y
IMAGES = {}  # Słownik przechowujący obrazy
pygame.font.init()  # Inicjalizacja czcionki
WINDOW = pygame.display.set_mode((SW, SH))  # Utworzenie okna gry
Font = pygame.font.SysFont("comicsans", 30)  # Utworzenie czcionki
BIRD = 'imgs/bird1.png'  # Ścieżka do obrazu ptaka
BG = 'imgs/bg.png'  # Ścieżka do obrazu tła
PIPE = 'imgs/pipe.png'  # Ścieżka do obrazu rury
Q = numpy.zeros((7, 21, 2), dtype=float)  # Inicjalizacja tablicy Q
FPS = 32  # Liczba klatek na sekundę

slider = Slider(WINDOW, 40, SH-50, 200, 12, min=50, max=1000, step=1, initial=0, colour='white')  # Inicjalizacja suwaka

def static():
    """
    Funkcja odpowiedzialna za wyświetlanie statycznego ekranu startowego.
    """
    birdxpos = int(SW/5)  # Pozycja X ptaka
    birdypos = int((SH - IMAGES['bird'].get_height())/2)  # Pozycja Y ptaka
    basex = 0  # Pozycja X podłoża

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):
                return

        WINDOW.blit(IMAGES['background'], (0, 0))
        WINDOW.blit(IMAGES['bird'], (birdxpos, birdypos))
        WINDOW.blit(IMAGES['base'], (basex, BASEY))
        text1 = Font.render("WE LOVE PWR", 1, (255, 255, 255))
        WINDOW.blit(text1, (SW/8.5, SH/5))

        pygame.display.update()
        FPSCLOCK.tick(FPS)

def game_start(generation,x,y):
	"""
	Funkcja odpowiedzialna za rozpoczęcie gry.
    Przyjmuje argumenty:
    - generation: aktualna generacja
    - x: lista przechowująca wartości osi X do wykresu
    - y: lista przechowująca wartości osi Y do wykresu
	"""
	score = 0
	birdxpos = int(SW/5)
	birdypos = int(SH/2)
	basex1 = 0
	basex2 = SW

	bgx1=0
	bgx2 = IMAGES['background'].get_width()

	newPipe1 = get_new_pipe()
	newPipe2 = get_new_pipe()

	up_pipes = [
	{'x':SW +200,'y': newPipe1[0]['y']},
	{'x':SW +500 ,'y': newPipe2[0]['y']}
	]

	bttm_pipes = [
	{'x':SW+200,'y':newPipe1[1]['y']},
	{'x':SW +500 ,'y': newPipe2[1]['y']}
	]

	pipeVelx = -4

	birdyvel = -9
	birdymaxvel = 10
	birdyvelmin = -8
	birdyacc = 1

	playerFlapAccv = -8
	playerFlapped =False
	
	while(True):
		
		x_prev,y_prev = convert(birdxpos,birdypos,bttm_pipes)
		jump = ai_play(x_prev,y_prev)
		events = pygame.event.get()
		for event in events:
			if event.type == QUIT:
				#plt.scatter(x,y)
				plt.bar(x,y)
				plt.xlabel("GENERATION")
				plt.ylabel("SCORE")
				plt.title("Ptaki: AI Projekt")
				plt.show()
				pygame.quit()

				sys.exit()


		if jump:
			if birdypos>0:
				birdyvel = playerFlapAccv
				playerFlapped = True

		
		playerMidPos= birdxpos + IMAGES['bird'].get_width()/2
		for pipe in up_pipes:
			pipeMidPos = pipe ['x'] +IMAGES['pipe'][0].get_width()/2
			if pipeMidPos <= playerMidPos < pipeMidPos +4 :
				score += 1


		if birdyvel < birdymaxvel and not playerFlapped:
			birdyvel += birdyacc


		if playerFlapped:
			playerFlapped = False

		playerHeight = IMAGES['bird'].get_height()

		birdypos = birdypos + min (birdyvel, BASEY - birdypos -playerHeight)

		for upperPipe,lowerPipe in zip(up_pipes,bttm_pipes):
			upperPipe['x'] += pipeVelx
			lowerPipe['x'] += pipeVelx

		if (0<up_pipes[0]['x']<5):
			newPipe = get_new_pipe()
			up_pipes.append(newPipe[0])
			bttm_pipes.append(newPipe[1])

		if(up_pipes[0]['x'] < -IMAGES['pipe'][0].get_width() ):
			up_pipes.pop(0)
			bttm_pipes.pop(0)
		basex1-=4
		basex2-=4
		if(basex1 <= -IMAGES['base'].get_width()):
			basex1 = basex2
			basex2 = basex1 + IMAGES['base'].get_width()

		bgx1-=2
		bgx2-=2
		if(bgx1 <= -IMAGES['background'].get_width()):
			bgx1 = bgx2
			bgx2 = bgx1 + IMAGES['background'].get_width()
		crashTest = Collision(birdxpos,birdypos,up_pipes,bttm_pipes)
		x_new,y_new = convert(birdxpos,birdypos,bttm_pipes)
		if crashTest:
			reward = -1000
			Q_update(x_prev,y_prev,jump,reward,x_new,y_new)
			return score

		reward = 15

		Q_update(x_prev,y_prev,jump,reward,x_new,y_new)

		WINDOW.blit(IMAGES['background'],(bgx1,0))
		WINDOW.blit(IMAGES['background'],(bgx2,0))
		for upperPipe,lowerPipe in zip(up_pipes,bttm_pipes):
			WINDOW.blit(IMAGES['pipe'][0],(upperPipe['x'],upperPipe['y']))
			WINDOW.blit(IMAGES['pipe'][1],(lowerPipe['x'],lowerPipe['y']))
		WINDOW.blit(IMAGES['base'],(basex1,BASEY))
		WINDOW.blit(IMAGES['base'],(basex2,BASEY))
		text1 = Font.render("Score: "+ str(score),1,(255,255,255))
		text2 = Font.render("Generation: "+ str(generation),1,(255,255,255))
		#WINDOW.blit(text1,(SW - 10 -text1.get_width(),10))
		WINDOW.blit(text1, (5,35))
		WINDOW.blit(text2,(5,0))
		WINDOW.blit(IMAGES['bird'],(birdxpos,birdypos))
		pygame_widgets.update(events)
		pygame.display.update()
		TIMEMS = slider.getValue()
		FPSCLOCK.tick(TIMEMS)

def Collision(birdxpos,birdypos,up_pipes,bttm_pipes):
	if (birdypos >= BASEY - IMAGES['bird'].get_height() or birdypos < 0):
		return True
	for pipe in up_pipes:
		pipeHeight = IMAGES['pipe'][0].get_height()
		if(birdypos < pipeHeight + pipe['y'] and abs(birdxpos - pipe['x']) < IMAGES['pipe'][0].get_width()):
			return True

	for pipe in bttm_pipes:
		if (birdypos + IMAGES['bird'].get_height() > pipe['y'] and abs(birdxpos - pipe['x']) < IMAGES['pipe'][0].get_width()):
			return True
	return False


def get_new_pipe():

	pipeHeight = IMAGES['pipe'][1].get_height()
	gap = int(SH/4)
	y2 = int(gap + random.randrange(0,int(SH - IMAGES['base'].get_height() - 1.2*gap)))
	pipex = int(SW+300 )
	y1 = int(pipeHeight -y2 +gap)

	pipe = [
	{'x':pipex,'y':-y1},
	{'x':pipex,'y':y2}
	]
	return pipe

def ai_play(x,y):
	max=0
	jump = False

	if(Q[x][y][1]>Q[x][y][0]):
		max = Q[x][y][1]
		jump =True

	return jump

def convert(birdxpos,birdypos,bttm_pipes):
	x = min(280, bttm_pipes[0]['x'])
	y = bttm_pipes[0]['y']-birdypos
	if(y<0):
		y=abs(y)+408
	return int(x/40-1),int(y/40)


def Q_update(x_prev,y_prev,jump,reward,x_new,y_new):
	LEARNING_RATE = 0.6
	if jump:
		Q[x_prev][y_prev][1] = (1-LEARNING_RATE) * Q[x_prev][y_prev][1] + LEARNING_RATE*(reward+ max(Q[x_new][y_new][0],Q[x_new][y_new][1]))
	else :
		Q[x_prev][y_prev][0] = (1-LEARNING_RATE) * Q[x_prev][y_prev][0] + LEARNING_RATE*(reward+ max(Q[x_new][y_new][0],Q[x_new][y_new][1]))



if __name__=="__main__":

	pygame.init()
	FPSCLOCK = pygame.time.Clock()
	pygame.display.set_caption("Ptaki AI")

	IMAGES['base'] = pygame.image.load('imgs/base.png').convert_alpha()
	IMAGES['pipe'] = ( pygame.transform.rotate(pygame.image.load(PIPE).convert_alpha(),180) , pygame.image.load(PIPE).convert_alpha())
	IMAGES['background']= pygame.image.load(BG).convert()
	IMAGES['bird'] = pygame.image.load(BIRD).convert_alpha()
	generation = 1
	static()
	x=[]
	y=[]
	max_score = 0
	while(True):
		score = game_start(generation,x,y)
		if (score==-1):
			break
		x.append(generation)
		y.append(score)
		generation+=1

		if score > max_score:
			max_score = score
			print(f'Generation: {generation}, Max score: {max_score}')
