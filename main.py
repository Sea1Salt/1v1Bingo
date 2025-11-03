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
SCREEN_HEIGHT = SIZE*CELL_SIZE + MARGIN*2 + 200
WHITE = (255,255,255)
BLACK = (0,0,0)
RED = (255,0,0)
BLUE = (0,0,255)
GREEN = (0,255,0)
ORANGE = (255,165,0)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
font = pygame.font.SysFont(None, 40)
big_font = pygame.font.SysFont(None, 80)
small_font = pygame.font.SysFont(None, 30)
clock = pygame.time.Clock()
pygame.display.set_caption("🔥 1v1 BINGO 🔥")

# -------------------
# CLASS
# -------------------
class Cell:
    def __init__(self, number, rect, type="normal"):
        self.number = number
        self.marked = False
        self.rect = rect
        self.type = type   # normal / block
        self.blocked = False

    def draw(self, surface):
        if self.blocked:
            color = (100, 100, 100)
            text_color = WHITE
            text = "B"
        else:
            color = (200, 200, 200)
            text_color = BLACK
            text = str(self.number)

        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)

        text_surface = small_font.render(text, True, text_color)
        surface.blit(text_surface, text_surface.get_rect(center=self.rect.center))

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
        block_indices = random.sample(range(self.size*self.size), 3)  # 3 ช่อง block
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

# -------------------
# MAIN GAME CLASS
# -------------------
class BingoGame:
    def __init__(self):
        self.player_board = Board(SIZE, (MARGIN, 100))
        self.bot_board = Board(SIZE, (SIZE*CELL_SIZE + MARGIN*2 + GAP, 100))
        self.called_numbers = []
        self.all_numbers = list(range(1, SIZE*SIZE*2))
        random.shuffle(self.all_numbers)
        self.current_number = None
        self.winner = None
        self.player_lives = 3
        self.bot_lives = 3
        self.block_message = None
        self.block_timer = 0
        self.fire_message = None
        self.fire_timer = 0
        self.late_message = None
        self.late_timer = 0
        self.heal_message = None
        self.heal_timer = 0

        # NEW: remove mark message/timer
        self.remove_message = None
        self.remove_timer = 0

        self.game_over = False

        self.player_late = 0
        self.bot_late = 0

        # Skill Numbers
        self.player_skills = random.sample(range(1, SIZE*SIZE*2), 5)
        self.bot_skills = random.sample(
            [n for n in range(1, SIZE*SIZE*2) if n not in self.player_skills], 5
        )

        # Late numbers
        self.late_up_numbers = random.sample(self.all_numbers, 3)
        self.late_down_numbers = random.sample(
            [n for n in self.all_numbers if n not in self.late_up_numbers], 3
        )

        # Heal numbers
        self.heal_numbers = random.sample(
            [n for n in self.all_numbers if n not in self.late_up_numbers+self.late_down_numbers],
            5
        )

        # Remove Mark numbers (new skill) - ensure no overlap with existing skills
        used = set(self.player_skills + self.bot_skills + self.late_up_numbers + self.late_down_numbers + self.heal_numbers)
        pool_for_remove = [n for n in range(1, SIZE*SIZE*2) if n not in used]
        # if pool is smaller than 5, reduce accordingly (defensive)
        remove_count = min(5, len(pool_for_remove))
        self.remove_mark_numbers = random.sample(pool_for_remove, remove_count)

        # Block selection
        self.block_selecting = False
        self.block_target_board = None

        # Remove-selecting (player chooses which marked bot cell to unmark)
        self.remove_selecting = False
        self.remove_target_board = None
        self.remove_trigger_number = None  # store which remove-mark number triggered selection

    # -------------------
    # ACTIONS
    # -------------------
    def next_number(self):
        if self.all_numbers:
            self.current_number = self.all_numbers.pop(0)
            self.called_numbers.append(self.current_number)

            # Bot marks number
            bot_cell = self.bot_board.mark_number(self.current_number)
            if bot_cell:
                # Late Check
                self.check_late_numbers(self.current_number, "bot")
                # Block
                if bot_cell.type == "block":
                    self.trigger_block(self.player_board)
                # Fire
                if self.current_number in self.bot_skills:
                    self.trigger_fire("player")
                # Heal
                if self.current_number in self.heal_numbers:
                    self.trigger_heal("bot")
                # Remove Mark (bot case) -> random remove on player
                if self.current_number in self.remove_mark_numbers:
                    self.trigger_remove_mark("bot", self.current_number)

            if self.bot_board.check_bingo() and not self.winner:
                self.winner = "Bot Wins!"

    def player_mark(self, pos):
        # If we are in remove-selecting mode (player must choose a marked bot cell to unmark)
        if self.remove_selecting and self.remove_target_board == self.bot_board:
            for row in self.bot_board.cells:
                for cell in row:
                    if cell.rect.collidepoint(pos) and cell.marked and not cell.blocked:
                        # Unmark that bot cell
                        cell.marked = False
                        # Message
                        self.remove_message = f"Removed mark {cell.number} from Bot!"
                        self.remove_timer = pygame.time.get_ticks()
                        # Return the trigger number back into pool so it can be drawn again later
                        if self.remove_trigger_number is not None:
                            self.all_numbers.append(self.remove_trigger_number)
                            random.shuffle(self.all_numbers)
                        # Reset selecting state
                        self.remove_selecting = False
                        self.remove_target_board = None
                        self.remove_trigger_number = None
                        return
            # If clicked not a valid marked cell, ignore (stay in remove-selecting until valid click)
            return

        # If we are in block-selecting mode as before
        if self.block_selecting and self.block_target_board == self.bot_board:
            for row in self.bot_board.cells:
                for cell in row:
                    if cell.rect.collidepoint(pos) and not cell.blocked:
                        cell.blocked = True
                        cell.marked = False
                        self.block_message = f"BLOCKED {cell.number}"
                        self.block_timer = pygame.time.get_ticks()
                        self.block_selecting = False
                        self.block_target_board = None
                        return
            return  # clicked elsewhere during block selecting -> ignore

        # Normal player marking flow
        for row in self.player_board.cells:
            for cell in row:
                if cell.rect.collidepoint(pos) and not cell.blocked:
                    if self.called_numbers and cell.number in self.called_numbers:
                        cell.marked = True
                        self.check_late_numbers(cell.number, "player")
                        if cell.type == "block":
                            # block-select mode for player to choose bot cell to block
                            self.block_selecting = True
                            self.block_target_board = self.bot_board
                            self.block_message = "CHOOSE TO BLOCK"
                            self.block_timer = pygame.time.get_ticks()
                        if cell.number in self.player_skills:
                            self.trigger_fire("bot")
                        if cell.number in self.heal_numbers:
                            self.trigger_heal("player")
                        # New: if the player marked a remove-mark number -> enter remove-selecting mode
                        if cell.number in self.remove_mark_numbers:
                            # Player may choose one marked cell on bot_board to unmark
                            self.remove_selecting = True
                            self.remove_target_board = self.bot_board
                            self.remove_trigger_number = cell.number
                            self.remove_message = "REMOVE MARK! Choose Bot's marked cell"
                            self.remove_timer = pygame.time.get_ticks()
                        if self.player_board.check_bingo() and not self.winner:
                            self.winner = "Player Wins!"

    def trigger_block(self, board):
        candidates = [cell for row in board.cells for cell in row if not cell.blocked]
        if candidates:
            blocked_cell = random.choice(candidates)
            blocked_cell.blocked = True
            blocked_cell.marked = False
            self.block_message = f"BLOCKED {blocked_cell.number}"
            self.block_timer = pygame.time.get_ticks()

    def trigger_fire(self, target):
        if target == "bot":
            if self.bot_lives > 0:
                self.bot_lives -= 1
        else:
            if self.player_lives > 0:
                self.player_lives -= 1
        self.fire_message = f"🔥 FIRE to {target.upper()}!"
        self.fire_timer = pygame.time.get_ticks()

    def trigger_heal(self, target):
        if target == "player":
            self.player_lives = min(3, self.player_lives+1)
        else:
            self.bot_lives = min(3, self.bot_lives+1)
        self.heal_message = f"💚 HEAL {target.upper()}!"
        self.heal_timer = pygame.time.get_ticks()

    def trigger_late_up(self, board_name):
        if board_name == "player":
            self.player_late += 1
            self.late_message = "PLAYER LATE UP!"
        elif board_name == "bot":
            self.bot_late += 1
            self.late_message = "BOT LATE UP!"
        self.late_timer = pygame.time.get_ticks()

    def trigger_late_down(self, board_name):
        if board_name == "player":
            self.bot_late = max(0, self.bot_late-1)
            self.late_message = "BOT LATE DOWN!"
        elif board_name == "bot":
            self.player_late = max(0, self.player_late-1)
            self.late_message = "PLAYER LATE DOWN!"
        self.late_timer = pygame.time.get_ticks()

    def trigger_remove_mark(self, board_name, number_used):
        """
        If player used remove-mark: set selecting mode for player to choose a marked bot cell to remove.
        If bot used remove-mark: randomly remove one marked player cell.
        After use, put the remove-mark number back into pool (all_numbers) so it can be drawn again later.
        """
        if board_name == "player":
            # Player will choose which bot marked cell to remove (handled in player_mark)
            self.remove_selecting = True
            self.remove_target_board = self.bot_board
            self.remove_trigger_number = number_used
            self.remove_message = "REMOVE MARK! Choose Bot's marked cell"
            self.remove_timer = pygame.time.get_ticks()
        else:
            # Bot removes one random marked cell from player_board (if any)
            player_marked_cells = [cell for row in self.player_board.cells for cell in row if cell.marked and not cell.blocked]
            if player_marked_cells:
                removed = random.choice(player_marked_cells)
                removed.marked = False
                self.remove_message = f"BOT removed Player mark {removed.number}!"
            else:
                self.remove_message = "BOT tried Remove Mark but Player had no marks!"
            self.remove_timer = pygame.time.get_ticks()
            # Return the number back into all_numbers so it can be drawn again
            self.all_numbers.append(number_used)
            random.shuffle(self.all_numbers)

    def check_late_numbers(self, number, board_name):
        if number in self.late_up_numbers:
            self.trigger_late_up(board_name)
        elif number in self.late_down_numbers:
            self.trigger_late_down(board_name)

    # -------------------
    # DRAWING
    # -------------------
    def draw_hearts(self, surface, lives, position):
        x, y = position
        for i in range(lives):
            pygame.draw.polygon(surface, RED, [
                (x+i*30, y+10), (x+10+i*30, y), (x+20+i*30, y+10), (x+10+i*30, y+20)
            ])

    def draw(self, surface):
        surface.fill(WHITE)

        # Titles
        player_text = font.render("Player", True, BLACK)
        surface.blit(player_text, player_text.get_rect(center=(MARGIN + SIZE*CELL_SIZE//2, 60)))
        bot_text = font.render("Bot", True, BLACK)
        surface.blit(bot_text, bot_text.get_rect(center=(SIZE*CELL_SIZE + MARGIN*2 + GAP + SIZE*CELL_SIZE//2, 60)))

        # Boards
        self.player_board.draw(surface)
        self.bot_board.draw(surface)

        # Hearts
        self.draw_hearts(surface, self.player_lives, (MARGIN, 100 + SIZE*CELL_SIZE + 10))
        self.draw_hearts(surface, self.bot_lives, (SIZE*CELL_SIZE + MARGIN*2 + GAP, 100 + SIZE*CELL_SIZE + 10))

        # Lucky Number
        if self.current_number:
            offset = 5 * (pygame.time.get_ticks()//400 % 2)
            text = font.render(f"Lucky Number: {self.current_number}", True, BLUE)
            player_right = MARGIN + SIZE*CELL_SIZE
            bot_left = SIZE*CELL_SIZE + MARGIN*2 + GAP
            x_center = (player_right + bot_left) // 2
            surface.blit(text, text.get_rect(center=(x_center, 40 + offset)))

        # Messages
        now = pygame.time.get_ticks()
        if self.block_message and now - self.block_timer < 3000:
            msg_text = font.render(self.block_message, True, RED)
            surface.blit(msg_text, msg_text.get_rect(center=(SCREEN_WIDTH//2, 100)))
        else:
            if not self.block_selecting:
                self.block_message = None

        if self.fire_message and now - self.fire_timer < 3000:
            fire_text = font.render(self.fire_message, True, ORANGE)
            surface.blit(fire_text, fire_text.get_rect(center=(SCREEN_WIDTH//2, 140)))
        else:
            self.fire_message = None

        if self.late_message and now - self.late_timer < 3000:
            color = BLUE if "UP" in self.late_message else RED
            late_text = font.render(self.late_message, True, color)
            surface.blit(late_text, late_text.get_rect(center=(SCREEN_WIDTH//2, 180)))
        else:
            self.late_message = None

        if self.heal_message and now - self.heal_timer < 3000:
            heal_text = font.render(self.heal_message, True, GREEN)
            surface.blit(heal_text, heal_text.get_rect(center=(SCREEN_WIDTH//2, 220)))
        else:
            self.heal_message = None

        # Remove mark message
        if self.remove_message and now - self.remove_timer < 3000:
            remove_text = font.render(self.remove_message, True, (128, 0, 128))  # purple text
            surface.blit(remove_text, remove_text.get_rect(center=(SCREEN_WIDTH//2, 260)))
        else:
            # if we were in remove-selecting but timer expired, cancel selecting mode
            if not self.remove_selecting:
                self.remove_message = None

        # Winner
        if self.winner:
            win_text = big_font.render(self.winner, True, GREEN)
            surface.blit(win_text, win_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)))

        # Called numbers
        y_offset = 50
        x_offset = SCREEN_WIDTH - 180
        for num in self.called_numbers[-15:]:
            num_text = small_font.render(str(num), True, BLACK)
            surface.blit(num_text, (x_offset, y_offset))
            y_offset += 25

        # Skills (kept as before)
        p_skill_text = small_font.render(f"Player Skill: {self.player_skills}", True, BLUE)
        b_skill_text = small_font.render(f"Bot Skill: {self.bot_skills}", True, RED)
        surface.blit(p_skill_text, (MARGIN, SCREEN_HEIGHT - 80))
        surface.blit(b_skill_text, (SIZE*CELL_SIZE + MARGIN*2 + GAP, SCREEN_HEIGHT - 80))

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
            restart_rect = pygame.Rect(SCREEN_WIDTH-150, SCREEN_HEIGHT-50, 120, 40)
            if restart_rect.collidepoint(event.pos):
                game.restart()

        if event.type == pygame.VIDEORESIZE:
            SCREEN_WIDTH, SCREEN_HEIGHT = event.w, event.h
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)

    game.draw(screen)

    # Restart Button
    restart_rect = pygame.Rect(SCREEN_WIDTH-150, SCREEN_HEIGHT-50, 120, 40)
    pygame.draw.rect(screen, (0,120,255), restart_rect)
    restart_text = small_font.render("Restart", True, WHITE)
    screen.blit(restart_text, restart_text.get_rect(center=restart_rect.center))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
