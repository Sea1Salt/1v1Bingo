import pygame
import random
import sys

pygame.init()

# CONFIG
SIZE = 5
CELL_SIZE = 50
MARGIN = 20
GAP = 50
SCREEN_WIDTH = SIZE*CELL_SIZE*2 + MARGIN*4 + GAP + 200
SCREEN_HEIGHT = SIZE*CELL_SIZE + MARGIN*2 + 250
WHITE = (255,255,255)
BLACK = (0,0,0)
RED = (255,0,0)
BLUE = (0,0,255)
GREEN = (0,255,0)
ORANGE = (255,165,0)
YELLOW = (255,255,0)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
font = pygame.font.SysFont(None, 40)
big_font = pygame.font.SysFont(None, 80)
small_font = pygame.font.SysFont(None, 30)
clock = pygame.time.Clock()
pygame.display.set_caption("🔥 1v1 BINGO 🔥")

# -------------------
# CLASSES
# -------------------
class Cell:
    def __init__(self, number, rect, type="normal"):
        self.number = number
        self.marked = False
        self.rect = rect
        self.type = type
        self.blocked = False

    def draw(self, surface):
        color = (200,200,200)
        if self.blocked:
            color = (150,150,150)
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)
        text = str(self.number) if not self.blocked else "BLOCK"
        text_surface = small_font.render(text, True, BLACK)
        surface.blit(text_surface, text_surface.get_rect(center=self.rect.center))
        if self.marked:
            pygame.draw.circle(surface, RED, self.rect.center, CELL_SIZE//3, 5)

class Board:
    def __init__(self, size, position):
        self.size = size
        self.position = position
        self.cells = []
        self.generate_cells()

    def generate_cells(self):
        numbers = random.sample(range(1, 51), self.size*self.size)
        block_indices = random.sample(range(self.size*self.size), 3)
        self.cells = []
        x0, y0 = self.position
        for i in range(self.size):
            row = []
            for j in range(self.size):
                idx = i*self.size + j
                cell_type = "block" if idx in block_indices else "normal"
                rect = pygame.Rect(x0 + j*CELL_SIZE, y0 + i*CELL_SIZE, CELL_SIZE, CELL_SIZE)
                row.append(Cell(numbers[idx], rect, cell_type))
            self.cells.append(row)

    def draw(self, surface):
        for row in self.cells:
            for cell in row:
                cell.draw(surface)

    def mark_number(self, num):
        for row in self.cells:
            for cell in row:
                if cell.number == num and not cell.blocked:
                    cell.marked = True
                    return cell
        return None

    def check_bingo(self):
        for row in self.cells:
            if all(cell.marked and not cell.blocked for cell in row):
                return True
        for c in range(self.size):
            if all(self.cells[r][c].marked and not self.cells[r][c].blocked for r in range(self.size)):
                return True
        if all(self.cells[i][i].marked and not self.cells[i][i].blocked for i in range(self.size)):
            return True
        if all(self.cells[i][self.size-1-i].marked and not self.cells[i][self.size-1-i].blocked for i in range(self.size)):
            return True
        return False

# -------------------
# MAIN GAME CLASS
# -------------------
class BingoGame:
    def __init__(self):
        self.player_board = Board(SIZE, (MARGIN, 100))
        self.bot_board = Board(SIZE, (SIZE*CELL_SIZE + MARGIN*2 + GAP, 100))
        self.called_numbers = []
        self.all_numbers = list(range(1,51))
        random.shuffle(self.all_numbers)
        self.current_number = None
        self.winner = None
        self.player_lives = 3
        self.bot_lives = 3
        self.block_message = None
        self.block_timer = 0
        self.choose_block = False
        self.fire_message = None
        self.fire_timer = 0
        self.heal_message = None
        self.heal_timer = 0
        self.game_over = False

        # Assign skills ensuring no duplicates between player and bot
        player_numbers = [cell.number for row in self.player_board.cells for cell in row if not cell.blocked]
        bot_numbers = [cell.number for row in self.bot_board.cells for cell in row if not cell.blocked]
        used_numbers = set()
        
        self.player_skills = random.sample(player_numbers, 3)
        used_numbers.update(self.player_skills)
        self.player_heal = random.sample([n for n in player_numbers if n not in used_numbers], 1)
        used_numbers.update(self.player_heal)
        self.player_block = random.sample([n for n in player_numbers if n not in used_numbers], 1)
        used_numbers.update(self.player_block)
        self.player_late = random.sample([n for n in player_numbers if n not in used_numbers], 1)
        used_numbers.update(self.player_late)

        # Bot skills unique and non-overlapping
        used_numbers_bot = set()
        self.bot_skills = random.sample([n for n in bot_numbers if n not in used_numbers], 3)
        used_numbers_bot.update(self.bot_skills)
        self.bot_heal = random.sample([n for n in bot_numbers if n not in used_numbers and n not in used_numbers_bot], 1)
        used_numbers_bot.update(self.bot_heal)
        self.bot_block = random.sample([n for n in bot_numbers if n not in used_numbers and n not in used_numbers_bot], 1)
        used_numbers_bot.update(self.bot_block)
        self.bot_late = random.sample([n for n in bot_numbers if n not in used_numbers and n not in used_numbers_bot], 1)
        used_numbers_bot.update(self.bot_late)

    # -------------------
    # ACTIONS
    # -------------------
    def next_number(self):
        if self.all_numbers:
            self.current_number = self.all_numbers.pop(0)
            self.called_numbers.append(self.current_number)
            bot_cell = self.bot_board.mark_number(self.current_number)
            if bot_cell:
                if bot_cell.number in self.bot_skills:
                    self.trigger_fire("player")
                if bot_cell.number in self.bot_heal:
                    self.trigger_heal("bot")
                if bot_cell.number in self.bot_block:
                    bot_cell.marked = True
                if bot_cell.number in self.bot_late:
                    self.trigger_late("bot")
            # Check bingo
            self.check_game_over()

    def player_mark(self,pos):
        if self.choose_block:
            for row in self.bot_board.cells:
                for cell in row:
                    if cell.rect.collidepoint(pos) and not cell.blocked:
                        cell.blocked = True
                        self.choose_block=False
                        self.block_message=f"Player Blocked {cell.number}"
                        self.block_timer=pygame.time.get_ticks()
            return

        for row in self.player_board.cells:
            for cell in row:
                if cell.rect.collidepoint(pos) and not cell.blocked and cell.number in self.called_numbers:
                    cell.marked=True
                    if cell.number in self.player_skills:
                        self.trigger_fire("bot")
                    if cell.number in self.player_heal:
                        self.trigger_heal("player")
                    if cell.number in self.player_block:
                        self.choose_block=True
                        self.block_message="Choose Bot Cell to Block!"
                        self.block_timer=pygame.time.get_ticks()
                    if cell.number in self.player_late:
                        self.trigger_late("player")
                    self.check_game_over()

    def trigger_fire(self,target):
        if target=="bot":
            self.bot_lives=max(0,self.bot_lives-1)
        else:
            self.player_lives=max(0,self.player_lives-1)
        self.fire_message=f"🔥 FIRE {target.upper()}!"
        self.fire_timer=pygame.time.get_ticks()

    def trigger_heal(self,target):
        if target=="player":
            self.player_lives=min(3,self.player_lives+1)
        else:
            self.bot_lives=min(3,self.bot_lives+1)
        self.heal_message=f"❤️ HEAL {target.upper()}!"
        self.heal_timer=pygame.time.get_ticks()

    def trigger_late(self,target):
        self.block_message=f"⚡ LATE {target.upper()}!"
        self.block_timer=pygame.time.get_ticks()

    def check_game_over(self):
        if self.player_lives==0:
            self.winner="Bot"
            self.game_over=True
        elif self.bot_lives==0:
            self.winner="Player"
            self.game_over=True
        elif self.player_board.check_bingo():
            self.winner="Player"
            self.game_over=True
        elif self.bot_board.check_bingo():
            self.winner="Bot"
            self.game_over=True

    # -------------------
    # DRAWING
    # -------------------
    def draw_hearts(self,surface,lives,position):
        x,y=position
        for i in range(lives):
            pygame.draw.polygon(surface,RED,[(x+i*30,y+10),(x+10+i*30,y),(x+20+i*30,y+10),(x+10+i*30,y+20)])

    def draw(self,surface):
        surface.fill(WHITE)
        player_text=font.render("Player",True,BLACK)
        surface.blit(player_text,player_text.get_rect(center=(MARGIN+SIZE*CELL_SIZE//2,60)))
        bot_text=font.render("Bot",True,BLACK)
        surface.blit(bot_text,bot_text.get_rect(center=(SIZE*CELL_SIZE+MARGIN*2+GAP+SIZE*CELL_SIZE//2,60)))
        self.player_board.draw(surface)
        self.bot_board.draw(surface)
        self.draw_hearts(surface,self.player_lives,(MARGIN,100+SIZE*CELL_SIZE+10))
        self.draw_hearts(surface,self.bot_lives,(SIZE*CELL_SIZE+MARGIN*2+GAP,100+SIZE*CELL_SIZE+10))
        if self.current_number:
            text=font.render(f"Lucky Number: {self.current_number}",True,BLUE)
            surface.blit(text,text.get_rect(center=(SCREEN_WIDTH//2,40)))
        now=pygame.time.get_ticks()
        for msg, timer, color in [(self.block_message,self.block_timer,ORANGE),(self.fire_message,self.fire_timer,RED),(self.heal_message,self.heal_timer,GREEN)]:
            if msg and now-timer<3000:
                msg_text=font.render(msg,True,color)
                surface.blit(msg_text,msg_text.get_rect(center=(SCREEN_WIDTH//2,100 if color==ORANGE else 140 if color==RED else 180)))
        if self.winner:
            win_text=big_font.render(f"{self.winner} Wins!",True,YELLOW)
            surface.blit(win_text,win_text.get_rect(center=(SCREEN_WIDTH//2,SCREEN_HEIGHT//2)))
        y_offset=50
        x_offset=SCREEN_WIDTH-180
        for num in self.called_numbers[-15:]:
            num_text=small_font.render(str(num),True,BLACK)
            surface.blit(num_text,(x_offset,y_offset))
            y_offset+=25
        p_skill_text=small_font.render(f"P Skills: {self.player_skills+self.player_heal+self.player_block+self.player_late}",True,BLUE)
        b_skill_text=small_font.render(f"B Skills: {self.bot_skills+self.bot_heal+self.bot_block+self.bot_late}",True,RED)
        surface.blit(p_skill_text,(MARGIN,SCREEN_HEIGHT-80))
        surface.blit(b_skill_text,(SIZE*CELL_SIZE+MARGIN*2+GAP,SCREEN_HEIGHT-80))

    def restart(self):
        self.__init__()

# -------------------
# MAIN LOOP
# -------------------
game=BingoGame()
running=True

while running:
    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            running=False
        if event.type==pygame.KEYDOWN:
            if event.key==pygame.K_SPACE:
                game.next_number()
        if event.type==pygame.MOUSEBUTTONDOWN:
            game.player_mark(event.pos)
            restart_rect=pygame.Rect(SCREEN_WIDTH-150,SCREEN_HEIGHT-50,120,40)
            if restart_rect.collidepoint(event.pos):
                game.restart()
        if event.type==pygame.VIDEORESIZE:
            SCREEN_WIDTH,SCREEN_HEIGHT=event.w,event.h
            screen=pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT),pygame.RESIZABLE)

    game.draw(screen)
    restart_rect=pygame.Rect(SCREEN_WIDTH-150,SCREEN_HEIGHT-50,120,40)
    pygame.draw.rect(screen,(0,120,255),restart_rect)
    restart_text=small_font.render("Restart",True,WHITE)
    screen.blit(restart_text,restart_text.get_rect(center=restart_rect.center))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
