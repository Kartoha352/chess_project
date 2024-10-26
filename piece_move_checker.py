from logic import DB_Manager
from config import *

manager = DB_Manager(DATABASE)

def get_bishop_moves(player_id, board, start_row, start_col):
    moves = []
    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]  # 4 направления для диагоналей

    for dr, dc in directions:
        row, col = start_row, start_col
        while True:
            row += dr
            col += dc

            # Проверка, что слон не выходит за границы доски
            if row < 0 or row >= 8 or col < 0 or col >= 8:
                break

            # Если на клетке нет другой фигуры, добавляем ее в список возможных ходов
            if board[row][col] == " ":  # " " означает пустую клетку
                moves.append((row, col))
            else:
                # Если на клетке стоит фигура, проверим, можно ли ее съесть
                if board[row][col][-1] != board[start_row][start_col][-1]:
                    moves.append((row, col))
                break  # Слон не может перепрыгивать через фигуры

    return moves

def get_rook_moves(player_id, board, start_row, start_col):
    moves = []
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # 4 направления

    for dr, dc in directions:
        row, col = start_row, start_col
        while True:
            row += dr
            col += dc

            # Проверка, что ладья не выходит за границы доски
            if row < 0 or row >= 8 or col < 0 or col >= 8:
                break

            # Если на клетке нет другой фигуры, добавляем ее в список возможных ходов
            if board[row][col] == " ":  # " " означает пустую клетку
                moves.append((row, col))
            else:
                # Если на клетке стоит фигура, проверим, можно ли ее съесть
                if board[row][col][-1] != board[start_row][start_col][-1]:
                    moves.append((row, col))
                break

    return moves

def get_pawn_moves(player_id, board, start_row, start_col):
    moves = []
    
    player_color = manager.get_player_color(player_id)
    
    # Определяем направление движения пешки и начальную строку для удвоенного хода
    if player_color == "W":
        direction = 1  # Пешка белого игрока движется вниз
        start_row_pawn = 1  # Начальная строка для пешек белого игрока
    else:
        direction = -1  # Пешка черного игрока движется вверх
        start_row_pawn = 6  # Начальная строка для пешек черного игрока
    
    # Одно клеточное движение вперед
    row, col = start_row + direction, start_col
    if 0 <= row < 8 and board[row][col] == " ":
        moves.append((row, col))
        
        # Двойное движение вперед с начальной позиции
        if start_row == start_row_pawn:
            row += direction
            if 0 <= row < 8 and board[row][col] == " ":
                moves.append((row, col))

    # Взятие фигур по диагонали
    for diag_col in [start_col - 1, start_col + 1]:
        row = start_row + direction
        if 0 <= row < 8 and 0 <= diag_col < 8:
            if board[row][diag_col] != " " and board[row][diag_col][-1] != board[start_row][start_col][-1]:
                moves.append((row, diag_col))
    
    return moves

def get_knight_moves(player_id, board, start_row, start_col):
    moves = []
    directions = [(-1, 2), (1, 2), (-2, -1), (-2, 1), (-1, -2), (1, -2), (2, -1), (2, 1)]

    for dr, dc in directions:
        row, col = start_row, start_col
        row += dr
        col += dc

        # Проверка, что конь не выходит за границы доски
        if row < 0 or row >= 8 or col < 0 or col >= 8:
            continue

        # Если на клетке нет другой фигуры, добавляем ее в список возможных ходов
        if board[row][col] == " ":  # " " означает пустую клетку
            moves.append((row, col))
        else:
            # Если на клетке стоит фигура, проверим, можно ли ее съесть
            if board[row][col][-1] != board[start_row][start_col][-1]:
                moves.append((row, col))

    return moves

def get_queen_moves(player_id, board, start_row, start_col):
    moves = []
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]  # 8 направлений. По диаагонали и горизонтали/вертикали

    for dr, dc in directions:
        row, col = start_row, start_col
        while True:
            row += dr
            col += dc

            # Проверка, что королева не выходит за границы доски
            if row < 0 or row >= 8 or col < 0 or col >= 8:
                break

            # Если на клетке нет другой фигуры, добавляем ее в список возможных ходов
            if board[row][col] == " ":  # " " означает пустую клетку
                moves.append((row, col))
            else:
                # Если на клетке стоит фигура, проверим, можно ли ее съесть
                if board[row][col][-1] != board[start_row][start_col][-1]:
                    moves.append((row, col))
                break

    return moves

def get_king_moves(player_id, board, start_row, start_col):
    moves = []
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1)]

    for dr, dc in directions:
        row, col = start_row, start_col
        row += dr
        col += dc

        # Проверка, что король не выходит за границы доски
        if row < 0 or row >= 8 or col < 0 or col >= 8:
            continue

        # Если на клетке нет другой фигуры, добавляем ее в список возможных ходов
        if board[row][col] == " ":  # " " означает пустую клетку
            moves.append((row, col))
        else:
            # Если на клетке стоит фигура, проверим, можно ли ее съесть
            if board[row][col][-1] != board[start_row][start_col][-1]:
                moves.append((row, col))

    return moves


#Суперходы
def get_pawn_super_moves(player_id, board, start_row, start_col):
    moves = []

    player_color = manager.get_player_color(player_id)
    
    # Определяем направление движения пешки и начальную строку для удвоенного хода
    if player_color == "W":
        directions = [1, 2, 3]  # Пешка белого игрока движется вниз
    else:
        directions = [-1, -2, -3]  # Пешка черного игрока движется вверх
    
    for dir in directions:
        row, col = start_row + dir, start_col

        # Проверка, что пешка не выходит за границы доски
        if row < 0 or row >= 8:
            break

        # Если на клетке нет другой фигуры, добавляем ее в список возможных ходов
        if board[row][col] == " ":  # " " означает пустую клетку
            moves.append((row, col))
        else:
            # Если на клетке стоит фигура, проверим, можно ли ее съесть
            if board[row][col][-1] != board[start_row][start_col][-1]:
                moves.append((row, col))

    return moves

def get_knight_super_moves(player_id, board, start_row, start_col):
    moves = []
    directions = [(-1, 2), (0, 2), (1, 2), (-2, -1), (-2, 0), (-2, 1), (-1, -2),(0, -2), (1, -2), (2, -1), (2, 0), (2, 1)]

    for dr, dc in directions:
        row, col = start_row, start_col
        row += dr
        col += dc

        # Проверка, что конь не выходит за границы доски
        if row < 0 or row >= 8 or col < 0 or col >= 8:
            continue

        # Если на клетке нет другой фигуры, добавляем ее в список возможных ходов
        if board[row][col] == " ":  # " " означает пустую клетку
            moves.append((row, col))
        else:
            # Если на клетке стоит фигура, проверим, можно ли ее съесть
            if board[row][col][-1] != board[start_row][start_col][-1]:
                moves.append((row, col))

    return moves

def get_bishop_super_moves(player_id, board, start_row, start_col):
    moves = []
    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]  # 4 направления для диагоналей

    for dr, dc in directions:
        row, col = start_row, start_col
        while True:
            row += dr
            col += dc

            # Проверка, что слон не выходит за границы доски
            if row < 0 or row >= 8 or col < 0 or col >= 8:
                break

            # Если на клетке нет другой фигуры, добавляем ее в список возможных ходов
            if board[row][col] == " ":  # " " означает пустую клетку
                moves.append((row, col))
            else:
                # Если на клетке стоит фигура, проверим, можно ли ее съесть
                if board[row][col][-1] != board[start_row][start_col][-1]:
                    moves.append((row, col))

    return moves