import pygame
import random
import sys

pygame.init()

# CONFIG
SIZE = 5
CELL_SIZE = 60
MARGIN = 20
GAP = 50
SCREEN_WIDTH = SIZE*CELL_SIZE*2 + MARGIN*4 + GAP + 200
SCREEN_HEIGHT = SIZE*CELL_SIZE + MARGIN*2 + 150
WHITE = (255,255,255)
BLACK = (0,0,0)
RED = (255,0,0)
BLUE = (0,0,255)
GREEN = (0,255,0)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
font = pygame.font.SysFont(None, 40)
big_font = pygame.font.SysFont(None, 80)
small_font = pygame.font.SysFont(None, 30)
clock = pygame.time.Clock()

# -------------------
# CLASS
# -------------------
class Cell:
    def __init__(self, number, rect):
        self.number = number
        self.marked = False
        self.rect = rect

    def draw(self, surface):
        pygame.draw.rect(surface, (200,200,200), self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)
        num_text = font.render(str(self.number), True, BLACK)
        surface.blit(num_text, num_text.get_rect(center=self.rect.center))
        if self.marked:
            pygame.draw.circle(surface, RED, self.rect.center, CELL_SIZE//3, 5)

class Board:
    def __init__(self, size, position):
        self.size = size
        self.position = position  # (x, y)
        self.cells = []
        self.generate_cells()

    def generate_cells(self):
        numbers = random.sample(range(1, self.size*self.size*2), self.size*self.size)
        self.cells = []
        x0, y0 = self.position
        for i in range(self.size):
            row = []
            for j in range(self.size):
                rect = pygame.Rect(x0 + j*CELL_SIZE, y0 + i*CELL_SIZE, CELL_SIZE, CELL_SIZE)
                row.append(Cell(numbers[i*self.size + j], rect))
            self.cells.append(row)

    def draw(self, surface):
        for row in self.cells:
            for cell in row:
                cell.draw(surface)

    def mark_number(self, num):
        for row in self.cells:
            for cell in row:
                if cell.number == num:
                    cell.marked = True

    def check_bingo(self):
        # rows
        for row in self.cells:
            if all(cell.marked for cell in row):
                return True
        # cols
        for c in range(self.size):
            if all(self.cells[r][c].marked for r in range(self.size)):
                return True
        # diagonals
        if all(self.cells[i][i].marked for i in range(self.size)):
            return True
        if all(self.cells[i][self.size-1-i].marked for i in range(self.size)):
            return True
        return False

class BingoGame:
    def __init__(self):
        self.player_board = Board(SIZE, (MARGIN, 100))
        self.bot_board = Board(SIZE, (SIZE*CELL_SIZE + MARGIN*2 + GAP, 100))
        self.called_numbers = []
        self.all_numbers = list(range(1, SIZE*SIZE*2))
        random.shuffle(self.all_numbers)
        self.current_number = None
        self.winner = None

    def next_number(self):
        if self.all_numbers:
            self.current_number = self.all_numbers.pop(0)
            self.called_numbers.append(self.current_number)
            self.bot_board.mark_number(self.current_number)
            if self.bot_board.check_bingo() and not self.winner:
                self.winner = "Bot ชนะ!"

    def player_mark(self, pos):
        for i,row in enumerate(self.player_board.cells):
            for j,cell in enumerate(row):
                if cell.rect.collidepoint(pos):
                    if cell.number == self.current_number:
                        cell.marked = True
                        if self.player_board.check_bingo() and not self.winner:
                            self.winner = "Player ชนะ!"

    def draw(self, surface):
        surface.fill(WHITE)
        # ชื่อ
        player_text = font.render("Player", True, BLACK)
        surface.blit(player_text, player_text.get_rect(center=(MARGIN + SIZE*CELL_SIZE//2, 60)))
        bot_text = font.render("Bot", True, BLACK)
        surface.blit(bot_text, bot_text.get_rect(center=(SIZE*CELL_SIZE + MARGIN*2 + GAP + SIZE*CELL_SIZE//2, 60)))

        # board
        self.player_board.draw(surface)
        self.bot_board.draw(surface)

        # เลขสุ่ม
        if self.current_number:
            offset = 5 * (pygame.time.get_ticks()//400 % 2)
            text = font.render(f"lucky number: {self.current_number}", True, BLUE)
            # x_center = ตรงกลางระหว่างสองบอร์ด
            player_right = MARGIN + SIZE*CELL_SIZE
            bot_left = SIZE*CELL_SIZE + MARGIN*2 + GAP
            x_center = (player_right + bot_left) // 2
            surface.blit(text, text.get_rect(center=(x_center, 40 + offset)))

        # Victory
        if self.winner:
            win_text = big_font.render(self.winner, True, GREEN)
            win_rect = win_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            surface.blit(win_text, win_rect)

        # แสดงเลขที่สุ่มไปแล้ว
        y_offset = 50
        x_offset = SCREEN_WIDTH - 180
        for num in self.called_numbers[-15:]:
            num_text = small_font.render(str(num), True, BLACK)
            surface.blit(num_text, (x_offset, y_offset))
            y_offset += 25

    def restart(self):
        self.__init__()

# -------------------
# MAIN LOOP
# -------------------
game = BingoGame()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                game.next_number()

        if event.type == pygame.MOUSEBUTTONDOWN:
            game.player_mark(event.pos)
            # Restart button
            restart_rect = pygame.Rect(SCREEN_WIDTH-150, SCREEN_HEIGHT-50, 120, 40)
            if restart_rect.collidepoint(event.pos):
                game.restart()

    game.draw(screen)

    # ปุ่ม Restart
    restart_rect = pygame.Rect(SCREEN_WIDTH-150, SCREEN_HEIGHT-50, 120, 40)
    pygame.draw.rect(screen, (0,120,255), restart_rect)
    restart_text = small_font.render("Restart", True, WHITE)
    screen.blit(restart_text, restart_text.get_rect(center=restart_rect.center))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
