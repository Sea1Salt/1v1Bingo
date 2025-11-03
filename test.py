import pygame
import random
import sys

pygame.init()

# ------------------- CONFIG -------------------
SIZE = 5
CELL_SIZE = 50
MARGIN = 20
GAP = 50
SCREEN_WIDTH = SIZE*CELL_SIZE*2 + MARGIN*4 + GAP + 200
SCREEN_HEIGHT = SIZE*CELL_SIZE + MARGIN*2 + 200
WHITE = (255,255,255)
BLACK = (0,0,0)

# Pastel colors
PASTEL_FIRE = (255,179,186)
PASTEL_BLOCK = (255,223,186)
PASTEL_HEAL = (186,255,201)
PASTEL_REMOVE = (186,225,255)
PASTEL_LATEUP = (255,255,186)
PASTEL_LATEDOWN = (215,186,255)
PASTEL_NORMAL = (220,220,220)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
font = pygame.font.SysFont(None, 40)
big_font = pygame.font.SysFont(None, 80)
small_font = pygame.font.SysFont(None, 30)
clock = pygame.time.Clock()
pygame.display.set_caption("🌸 1v1 BINGO 🌸")

# ------------------- CLASSES -------------------
class Cell:
    def __init__(self, number, rect, skill="normal"):
        self.number = number
        self.skill = skill
        self.marked = False
        self.rect = rect
        self.blocked = False

    def draw(self, surface):
        color_map = {
            "fire": PASTEL_FIRE,
            "block": PASTEL_BLOCK,
            "heal": PASTEL_HEAL,
            "remove": PASTEL_REMOVE,
            "lateup": PASTEL_LATEUP,
            "latedown": PASTEL_LATEDOWN,
            "normal": PASTEL_NORMAL
        }
        color = color_map.get(self.skill, PASTEL_NORMAL)
        if self.blocked:
            color = (150,150,150)
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)
        text = "B" if self.blocked else str(self.number)
        text_surface = small_font.render(text, True, BLACK)
        surface.blit(text_surface, text_surface.get_rect(center=self.rect.center))
        if self.marked:
            pygame.draw.circle(surface, (255,100,100), self.rect.center, CELL_SIZE//3, 5)

class Board:
    def __init__(self, size, position, numbers_skills):
        self.size = size
        self.position = position
        self.cells = []
        self.generate_cells(numbers_skills)

    def generate_cells(self, numbers_skills):
        x0, y0 = self.position
        self.cells = []
        for i in range(self.size):
            row = []
            for j in range(self.size):
                idx = i*self.size + j
                number, skill = numbers_skills[idx]
                rect = pygame.Rect(x0 + j*CELL_SIZE, y0 + i*CELL_SIZE, CELL_SIZE, CELL_SIZE)
                row.append(Cell(number, rect, skill))
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
            if all(cell.marked for cell in row):
                return True
        for c in range(self.size):
            if all(self.cells[r][c].marked for r in range(self.size)):
                return True
        if all(self.cells[i][i].marked for i in range(self.size)):
            return True
        if all(self.cells[i][self.size-1-i].marked for i in range(self.size)):
            return True
        return False

# ------------------- GAME -------------------
class BingoGame:
    def __init__(self):
        self.player_board, self.bot_board = self.generate_boards()
        self.called_numbers = []
        self.all_numbers = [cell.number for row in self.player_board.cells for cell in row] + \
                           [cell.number for row in self.bot_board.cells for cell in row]
        random.shuffle(self.all_numbers)
        self.current_number = None
        self.winner = None
        self.player_lives = 3
        self.bot_lives = 3

        self.block_message = None
        self.block_timer = 0
        self.fire_message = None
        self.fire_timer = 0
        self.heal_message = None
        self.heal_timer = 0
        self.remove_message = None
        self.remove_timer = 0

        self.block_selecting = False
        self.block_target_board = None
        self.remove_selecting = False
        self.remove_target_board = None
        self.remove_trigger_number = None

    def generate_boards(self):
        skill_counts = {"fire":5, "block":3, "heal":5, "remove":5, "lateup":2, "latedown":2, "normal":3}
        def generate_numbers_skills(start_num):
            nums = list(range(start_num, start_num+25))
            random.shuffle(nums)
            skills = []
            for skill, count in skill_counts.items():
                skills += [skill]*count
            random.shuffle(skills)
            return list(zip(nums, skills))
        player_ns = generate_numbers_skills(1)
        bot_ns = generate_numbers_skills(26)
        return Board(SIZE, (MARGIN,100), player_ns), Board(SIZE, (SIZE*CELL_SIZE+MARGIN*2+GAP,100), bot_ns)

    def next_number(self):
        if self.all_numbers and not self.winner:
            self.current_number = self.all_numbers.pop(0)
            self.called_numbers.append(self.current_number)
            bot_cell = self.bot_board.mark_number(self.current_number)
            if bot_cell:
                self.activate_skill(bot_cell, "bot")
            if self.bot_board.check_bingo() and not self.winner:
                self.winner = "Bot Wins!"

    def player_mark(self, pos):
        if self.winner: return
        if self.remove_selecting and self.remove_target_board==self.bot_board:
            for row in self.bot_board.cells:
                for cell in row:
                    if cell.rect.collidepoint(pos) and cell.marked and not cell.blocked:
                        cell.marked=False
                        self.remove_message=f"Removed mark {cell.number} from Bot!"
                        self.remove_timer=pygame.time.get_ticks()
                        self.remove_selecting=False
                        self.remove_target_board=None
                        self.remove_trigger_number=None
                        return
        if self.block_selecting and self.block_target_board==self.bot_board:
            for row in self.bot_board.cells:
                for cell in row:
                    if cell.rect.collidepoint(pos) and not cell.blocked:
                        cell.blocked=True
                        cell.marked=False
                        self.block_message=f"BLOCKED {cell.number}"
                        self.block_timer=pygame.time.get_ticks()
                        self.block_selecting=False
                        self.block_target_board=None
                        return
        for row in self.player_board.cells:
            for cell in row:
                if cell.rect.collidepoint(pos) and not cell.blocked:
                    if cell.number in self.called_numbers:
                        cell.marked=True
                        self.activate_skill(cell,"player")
                        if self.player_board.check_bingo() and not self.winner:
                            self.winner="Player Wins!"

    def activate_skill(self, cell, owner):
        opponent = "bot" if owner=="player" else "player"
        if cell.skill=="block":
            if owner=="player":
                self.block_selecting=True
                self.block_target_board=self.bot_board
                self.block_message="CHOOSE TO BLOCK"
                self.block_timer=pygame.time.get_ticks()
            else:
                self.trigger_block(self.player_board)
        elif cell.skill=="fire":
            self.trigger_fire(opponent)
        elif cell.skill=="heal":
            self.trigger_heal(owner)
        elif cell.skill=="remove":
            if owner=="player":
                self.remove_selecting=True
                self.remove_target_board=self.bot_board
                self.remove_trigger_number=cell.number
                self.remove_message="REMOVE MARK! Choose Bot's marked cell"
                self.remove_timer=pygame.time.get_ticks()
            else:
                self.trigger_remove_mark("bot", cell.number)
        elif cell.skill=="lateup":
            self.trigger_lateup(owner)
        elif cell.skill=="latedown":
            self.trigger_latedown(opponent)

    def trigger_block(self, board):
        candidates=[cell for row in board.cells for cell in row if not cell.blocked]
        if candidates:
            c=random.choice(candidates)
            c.blocked=True
            c.marked=False
            self.block_message=f"BLOCKED {c.number}"
            self.block_timer=pygame.time.get_ticks()
    
    def trigger_heal(self, target):
        if target == "player":
            self.player_lives = min(3, self.player_lives + 1)  # สมมติ max 3 หัวใจ
        else:
            self.bot_lives = min(3, self.bot_lives + 1)
        self.heal_message = f"💖 HEAL {target.upper()} +1!"
        self.heal_timer = pygame.time.get_ticks()

    def trigger_fire(self, target):
        if target=="bot":
            self.bot_lives=max(0,self.bot_lives-1)
            if self.bot_lives==0: self.winner="Player Wins!"
        if target=="player":
            self.player_lives=max(0,self.player_lives-1)
            if self.player_lives==0: self.winner="Bot Wins!"
        self.fire_message=f"🔥 FIRE to {target.upper()}!"
        self.fire_timer=pygame.time.get_ticks()

    def trigger_remove_mark(self, board_name, number_used):
        if board_name=="player":
            self.remove_selecting=True
            self.remove_target_board=self.bot_board
            self.remove_trigger_number=number_used
            self.remove_message="REMOVE MARK! Choose Bot's marked cell"
            self.remove_timer=pygame.time.get_ticks()
        else:
            player_marked=[cell for row in self.player_board.cells for cell in row if cell.marked and not cell.blocked]
            if player_marked:
                removed=random.choice(player_marked)
                removed.marked=False
                self.remove_message=f"BOT removed Player mark {removed.number}!"
            else:
                self.remove_message="BOT tried Remove Mark but Player had no marks!"
            self.remove_timer=pygame.time.get_ticks()

    def trigger_lateup(self, target):
        board = self.player_board if target=="player" else self.bot_board
        unmarked=[cell.number for row in board.cells for cell in row if not cell.marked]
        if not unmarked: return
        boost_count=max(1,len(unmarked)//6)
        boost_numbers=random.sample(unmarked,min(boost_count,len(unmarked)))
        self.all_numbers=[n for n in self.all_numbers if n not in boost_numbers]
        random.shuffle(boost_numbers)
        self.all_numbers=boost_numbers+self.all_numbers
        self.heal_message=f"✨ LATE UP {target.upper()}!"
        self.heal_timer=pygame.time.get_ticks()

    def trigger_latedown(self,target):
        board = self.player_board if target=="player" else self.bot_board
        unmarked=[cell.number for row in board.cells for cell in row if not cell.marked]
        if not unmarked: return
        reduce_count=max(1,len(unmarked)//6)
        reduce_numbers=random.sample(unmarked,min(reduce_count,len(unmarked)))
        self.all_numbers=[n for n in self.all_numbers if n not in reduce_numbers]+reduce_numbers
        self.heal_message=f"✨ LATE DOWN {target.upper()}!"
        self.heal_timer=pygame.time.get_ticks()

    def draw_hearts(self,surface,lives,pos):
        x,y=pos
        for i in range(lives):
            pygame.draw.polygon(surface,(255,100,100),[(x+i*30,y+10),(x+10+i*30,y),(x+20+i*30,y+10),(x+10+i*30,y+20)])

    def draw(self,surface):
        surface.fill(WHITE)
        surface.blit(font.render("Player",True,BLACK), font.render("Player",True,BLACK).get_rect(center=(MARGIN+SIZE*CELL_SIZE//2,60)))
        surface.blit(font.render("Bot",True,BLACK), font.render("Bot",True,BLACK).get_rect(center=(SIZE*CELL_SIZE+MARGIN*2+GAP+SIZE*CELL_SIZE//2,60)))
        self.player_board.draw(surface)
        self.bot_board.draw(surface)
        self.draw_hearts(surface,self.player_lives,(MARGIN,100+SIZE*CELL_SIZE+10))
        self.draw_hearts(surface,self.bot_lives,(SIZE*CELL_SIZE+MARGIN*2+GAP,100+SIZE*CELL_SIZE+10))
        if self.current_number:
            text=font.render(f"Lucky Number: {self.current_number}",True,BLACK)
            surface.blit(text,text.get_rect(center=(SCREEN_WIDTH//2,40)))
        now=pygame.time.get_ticks()
        messages=[
            (self.block_message,(255,180,180),self.block_timer),
            (self.fire_message,PASTEL_FIRE,self.fire_timer),
            (self.heal_message,PASTEL_HEAL,self.heal_timer),
            (self.remove_message,PASTEL_REMOVE,self.remove_timer)
        ]
        y_base=100
        for idx,(msg,color,t) in enumerate(messages):
            if msg and now-t<3000:
                text_surf=font.render(msg,True,color)
                surface.blit(text_surf,text_surf.get_rect(center=(SCREEN_WIDTH//2,y_base+idx*40)))
        if self.winner:
            surface.blit(big_font.render(self.winner,True,(0,150,0)), big_font.render(self.winner,True,(0,150,0)).get_rect(center=(SCREEN_WIDTH//2,SCREEN_HEIGHT//2)))
        y_offset=50
        x_offset=SCREEN_WIDTH-180
        for num in self.called_numbers[-15:]:
            surface.blit(small_font.render(str(num),True,BLACK),(x_offset,y_offset))
            y_offset+=25
        restart_rect=pygame.Rect(SCREEN_WIDTH-150,SCREEN_HEIGHT-50,120,40)
        pygame.draw.rect(surface,(186,225,255),restart_rect)
        surface.blit(small_font.render("Restart",True,BLACK), small_font.render("Restart",True,BLACK).get_rect(center=restart_rect.center))
    

    def restart(self):
        self.__init__()

# ------------------- MAIN LOOP -------------------
game=BingoGame()
running=True

while running:
    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            running=False
        if event.type==pygame.KEYDOWN and event.key==pygame.K_SPACE:
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
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
