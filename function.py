from PIL import Image, ImageDraw, ImageFont
from disnake.ext import commands
from logic import DB_Manager
from config import *
import json, io, disnake, asyncio, time, pprint
from piece_move_checker import *
from super_moves import *

manager = DB_Manager(DATABASE)

letters = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
numbers = ['1', '2', '3', '4', '5', '6', '7', '8']
checks = {"P": get_pawn_moves,
        "B": get_bishop_moves,
        "R": get_rook_moves,
        "N": get_knight_moves,
        "K": get_king_moves,
        "Q": get_queen_moves}

super_checks = {"P": get_pawn_super_moves,
        "B": get_bishop_super_moves,
        "R": "rook",
        "N": get_knight_super_moves,
        "K": "king",
        "Q": "queen"}

#функция для изменения сообщения с инфой об игре.
async def update_game_info(ctx: commands.Context | disnake.InteractionMessage, game_id, bot: commands.Bot, action="edit", selected_row=None, selected_col=None):
    from bot import Super_charge, Moves_history
    
    # Получение информации о текущем состоянии игры и игроков
    game_info = manager.get_game_info(game_id)
    board = json.loads(game_info[1])
    turn_player = ctx.guild.get_member(game_info[2])
    players = manager.get_players(game_id)

    # Настройка доски в зависимости от цвета игрока
    color = manager.get_player_color(turn_player.id)
    if color == "B":
        col_labels, row_labels = black_board()
    else:
        if selected_row != None:
            col_labels, row_labels, board, selected_row, selected_col = white_board(board, selected_row, selected_col)
        else:
            col_labels, row_labels, board  = white_board(board)

    # Создание изображения доски
    board_img_byte = create_board(col_labels, row_labels, board, (selected_row, selected_col))
    board_img = disnake.File(board_img_byte, filename='chess_board.png')
    ctx.message.attachments.clear()
    
    # Определение содержания и представления сообщения в зависимости от действия
    if action == "end":
        second_player = next(ctx.guild.get_member(player[0]) for player in players if player[0] != turn_player.id)
        content = f"{turn_player.mention}, {second_player.mention}\nПобедил – {turn_player.mention}"
        await ctx.message.edit(content=content, file=board_img, view=None)

    elif action == "on_timeout":
        second_player = next(ctx.guild.get_member(player[0]) for player in players if player[0] != turn_player.id)
        content = f"{turn_player.mention}, {second_player.mention}\nАвтоматическая победа – {turn_player.mention}"
        await ctx.message.edit(content=content, file=board_img, view=None)

    elif action == "send":
        view = disnake.ui.View(timeout=None)
        view.add_item(Super_charge(turn_player))
        view.add_item(Moves_history(turn_player, game_id))
        await ctx.response.edit_message(content=turn_player.mention + "\nХод противника: —", file=board_img, view=view)
        await wait_for_first_square(bot, turn_player, ctx)
    else:
        view = disnake.ui.View(timeout=None)
        is_first_selection = selected_col is None
        view.add_item(Super_charge(turn_player, is_first_selection))
        view.add_item(Moves_history(turn_player, game_id))
        last_move_white, last_move_black = manager.get_moves_history(game_id)
        content = turn_player.mention
        msg_last_move = ctx.message.content.split("\n")
        if last_move_white:
            if color == "B":
                move_number = int(list(last_move_white.keys())[-1])
                last_move = last_move_white.get(str(move_number))
            else:
                move_number = int(list(last_move_black.keys())[-1])
                last_move = last_move_black.get(str(move_number))
            if msg_last_move != f"{last_move[0]} -> {last_move[1]}":
                content += "\n" + f"Ход противника: {last_move[0]} -> {last_move[1]}"
            else:
                content += msg_last_move
        await ctx.message.edit(content=content, file=board_img, view=view)

        # Запуск ожидания первого выбора клетки, если это начальная отправка
        if is_first_selection:
            await wait_for_first_square(bot, turn_player, ctx)



def black_board():
    # Метки столбцов
    col_labels = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    # Метки строк
    row_labels = ['1', '2', '3', '4', '5', '6', '7', '8']

    return col_labels, row_labels

def white_board(board, selected_row=None, selected_col=None):
    # Переворачиваем строки и столбцы на доске
    reversed_board = [row[::-1] for row in board[::-1]]

    # Перевернутая нумерация строк (1-8 становится 8-1)
    row_labels = ['8', '7', '6', '5', '4', '3', '2', '1']
    
    # Перевернутая нумерация столбцов (a-h становится h-a)
    col_labels = ['h', 'g', 'f', 'e', 'd', 'c', 'b', 'a']

    if selected_row != None:
        reversed_selected_row = 7 - selected_row
        reversed_selected_col = 7 - selected_col

        return col_labels, row_labels, reversed_board, reversed_selected_row, reversed_selected_col
    else:
        return col_labels, row_labels, reversed_board
    
async def wait_for_message(bot, turn, channel, timeout:float):
    def check(m):
        return (
            len(m.content) == 2 and 
            m.content[0] in letters and m.content[1] in numbers and 
            m.author == turn and m.channel == channel
        )
    try:
        msg = await bot.wait_for("message", check=check, timeout=timeout)
        return msg
    except asyncio.TimeoutError:
        return None

async def out_of_time(bot, turn_player, ctx, opponent_player):
    game_id = manager.get_game_id(turn_player.id)
    manager.switch_turn(game_id)
    await ctx.send(f"Время вышло. Победа автоматически переходит к <@{opponent_player}>.", delete_after=5.0)
    await update_game_info(ctx, game_id, bot, "on_timeout")
    manager.end_game(game_id)

async def wait_for_first_square(bot, turn_player, ctx:commands.Context, start_time=None):
    player = manager.get_player(turn_player.id) #id, game_id, color, check, charge_count, charge_status - 0, 1, 2, 3, 4, 5
    game_id, color, king, opponent_player = player[1], player[2], manager.get_king_place(player[1], player[2]), manager.get_opponent_player(player[1], turn_player.id)
    start_time = start_time or time.time()

    while True:
        remaining_time = 60 - (time.time() - start_time)
        
        if remaining_time <= 0: #время вышло
            await out_of_time(bot, turn_player, ctx, opponent_player)
            break
        
        msg = await wait_for_message(bot, turn_player, ctx.channel, remaining_time)
        if msg:
            await msg.delete()
            start_row = int(msg.content[1]) - 1
            start_col = letters[msg.content[0]]

            #Если шах, то ходить можно только королём
            if player[3] == 1 and (start_row, start_col) != king:
                await ctx.send(f"{turn_player.mention}, У вас шах, вы можете ходить только королём", delete_after=5.0)
                continue
            
            board = json.loads(manager.get_game_info(game_id)[1])
            if board[start_row][start_col][-1] != color:
                await ctx.send(f"{turn_player.mention}, Вы указали неправильную клетку.", delete_after=5.0)
                continue

            moves_check = checks[board[start_row][start_col][0]]
            moves = moves_check(turn_player.id, board, start_row, start_col)
            super_moves = []
            
            if player[4] == 10 or player[5] == 1:#супер-ход МОЖНО активировать ИЛИ он УЖЕ АКТИВИРОВАН
                moves_check = super_checks[board[start_row][start_col][0]]
                super_moves = moves_check(turn_player.id, board, start_row, start_col) if callable(moves_check) else range(2)

            if len(moves) > 0:
                await ctx.send(f"{turn_player.mention}, Вы выбрали фигуру. Теперь выберите куда хотите пойти.", delete_after=5.0)
                await update_game_info(ctx, game_id, bot, "edit", start_row, start_col)
                await wait_for_second_square(bot, turn_player, ctx, start_row, start_col, board, opponent_player)
                break
            elif len(super_moves) > 0:
                from bot import Confirm_super_charge_view
                await ctx.send(f"{turn_player.mention}, Вы выбрали фигуру, но чтобы походить этой фигурой вы будете **обязаны** использовать супер-ход. Вы согласны?", view=Confirm_super_charge_view(turn_player, ctx, start_row, start_col, board, opponent_player, start_time, game_id, bot), delete_after=remaining_time)
                break
            else:
                await ctx.send(f"{turn_player.mention}, Вы указали неправильную клетку.", delete_after=5.0)
        else:
            await out_of_time(bot, turn_player, ctx, opponent_player)
            break

async def wait_for_second_square(bot, turn_player, ctx:commands.Context, start_row, start_col, board, opponent_player):
    player = manager.get_player(turn_player.id) #id, game_id, color, check, charge_count
    game_id, color, timeout = player[1], player[2], 60.0
    start_time = time.time()

    while True:
        remaining_time = timeout - (time.time() - start_time)
        
        if remaining_time <= 0: #время вышло
            await out_of_time(bot, turn_player, ctx, opponent_player)
            break

        msg = await wait_for_message(bot, turn_player, ctx.channel, remaining_time)
        if msg:
            await msg.delete()
            player = manager.get_player(turn_player.id)
            end_row, end_col = int(msg.content[1]) - 1, letters[msg.content[0]]
            moves_check = super_checks[board[start_row][start_col][0]] if player[5] == 1 else checks[board[start_row][start_col][0]]
            if player[5] == 1: 
                manager.edit_player(turn_player.id, "charge_status", 0)
            if player[4] < 10: 
                manager.edit_player(turn_player.id, "charge_count", 1)
            if player[6] != 0:
                manager.edit_player(turn_player.id, "king_super_move", -1)

            if callable(moves_check):#если это является функцией(если суперход не активирован то всегда True, если активирован то иногда может быть False т.к для некоторых суперходов не нужна функция для просчёта ходов)
                moves = moves_check(turn_player.id, board, start_row, start_col)
                if (end_row, end_col) in moves:
                    opponent_color = "B" if color == "W" else "W"
                    if manager.get_player(opponent_player)[6] > 0:
                        if king_super_move_check(opponent_color, board, end_row, end_col):
                            await ctx.send("Сюда нельзя пойти. Король противника защищает эту фигуру.", delete_after=5.0)
                            continue
                        
                    #новые возможнные ходы и король противника
                    moves_check = checks[board[start_row][start_col][0]]
                    new_moves = moves_check(turn_player.id, board, end_row, end_col)
                    opponent_king = manager.get_king_place(game_id, opponent_color)

                    if player[3] == 1:
                        manager.edit_player(turn_player.id, "check", 0)
                
                    manager.add_move_to_history(game_id, turn_player, start_row, start_col, end_row, end_col)

                    #Проверка на шах противнику
                    if opponent_king in new_moves:
                        opponent_player = manager.get_opponent_player(game_id, turn_player.id)
                        manager.edit_player(opponent_player, "check", 1)
                        manager.board_edit(game_id,[start_row, start_col], [end_row, end_col])
                        manager.switch_turn(game_id)
                        await ctx.send(f"{turn_player.mention}, Вы сделали шах противнику", delete_after=5.0)
                        await update_game_info(ctx, game_id, bot)
                        break

                    #Проверка на победу(сьесть короля)
                    if opponent_king == (end_row, end_col):
                        await ctx.send(f"Победил {turn_player.mention}!", delete_after=5.0)
                        manager.board_edit(game_id,[start_row, start_col], [end_row, end_col])
                        await update_game_info(ctx, game_id, bot, "end")
                        manager.end_game(game_id)
                        break
                        
                    #изменение доски
                    manager.board_edit(game_id,[start_row, start_col], [end_row, end_col])
                    manager.switch_turn(game_id)
                    await ctx.send("Вы успешно походили.", delete_after=5.0)
                    await update_game_info(ctx, game_id, bot)
                    break
                else:
                    await ctx.send("Сюда нельзя пойти.", delete_after=5.0)
            else:
                if moves_check == "rook":#менять местами короля и ладью
                    manager.edit_player(turn_player.id, "charge_status", 0)
                    await ctx.send("Вы использовали супер-ход Ладьи.\nВы поменялись местами с королём.", delete_after=5.0)
                    await rook_super_move(player, game_id, color, board, turn_player, start_row, start_col, bot, ctx)
                elif moves_check == "queen":#Даёт доп ход любой фигуре
                    result = await queen_super_move(player, game_id, color, board, turn_player, start_row, start_col, bot, ctx, end_row, end_col)
                    if result != "end":
                        await ctx.send("Вы использовали супер-ход королевы.\nВыберите новую фигуру для хода.", delete_after=5.0)
                        await wait_for_first_square(bot, turn_player, ctx)
                else:#Король. Вокруг себя делает не пробиваемую стену
                    manager.edit_player(turn_player.id, "king_super_move", 2)
                    manager.switch_turn(game_id)
                    manager.add_move_to_history(game_id, turn_player, start_row, start_col, start_row, start_col)
                    await ctx.send("Вы использовали супер-ход короля.\nТеперь вокруг короля будет щит который не даст сьесть фигуры рядом с ним на протяжении 2-ух __ваших__ ходов.", delete_after=5.0)
                    await update_game_info(ctx, game_id, bot)
                break
        else:
            await out_of_time(bot, turn_player, ctx, opponent_player)
            break

def create_board(col_labels, row_labels, board, selected_cell = None):
    # Размер клетки на доске
    cell_size = 80

    # Размер области для меток (ширина и высота зон для меток)
    label_area_size = 20

    # Загрузка изображений фигур, как в предыдущем коде
    pieces = {
        'K_W': Image.open('pieces/K_W.png'),
        'Q_W': Image.open('pieces/Q_W.png'),
        'R_W': Image.open('pieces/R_W.png'),
        'B_W': Image.open('pieces/B_W.png'),
        'N_W': Image.open('pieces/N_W.png'),
        'P_W': Image.open('pieces/P_W.png'),
        'K_B': Image.open('pieces/K_B.png'),
        'Q_B': Image.open('pieces/Q_B.png'),
        'R_B': Image.open('pieces/R_B.png'),
        'B_B': Image.open('pieces/B_B.png'),
        'N_B': Image.open('pieces/N_B.png'),
        'P_B': Image.open('pieces/P_B.png')
    }

    # Размер доски с метками
    board_size_with_labels = (
        8 * cell_size + label_area_size,  # ширина доски + зона для меток слева
        8 * cell_size + label_area_size   # высота доски + зона для меток сверху
    )

    # Создаем изображение доски с метками
    board_image = Image.new('RGB', board_size_with_labels, 'white')
    draw = ImageDraw.Draw(board_image)

    # Фон для меток
    draw.rectangle(
        [0, 0, board_size_with_labels[0], label_area_size], fill='black'  # Черный фон для верхней строки (буквы)
    )
    draw.rectangle(
        [0, 0, label_area_size, board_size_with_labels[1]], fill='black'  # Черный фон для левой колонки (цифры)
    )

    # Загрузка шрифта (стандартный шрифт или свой)
    # font = ImageFont.load_default()  # Если хотите использовать другой шрифт
    font = ImageFont.truetype('arial.ttf', 20)

    # Рисуем клетки доски
    for row in range(8):
        for col in range(8):
            # Определяем цвет клетки: зеленая, если она выбрана, иначе стандартный цвет доски
            if selected_cell and (row, col) == selected_cell:
                color = 'green'  # Зеленая клетка, если она выбрана
            else:
                color = 'white' if (row + col) % 2 == 0 else 'gray'
            
            draw.rectangle(
                [col * cell_size + label_area_size, row * cell_size + label_area_size,
                 (col + 1) * cell_size + label_area_size, (row + 1) * cell_size + label_area_size],
                fill=color
            )

    # Расставляем фигуры на доске
    for row in range(8):
        for col in range(8):
            piece_code = board[row][col]
            if piece_code != ' ':
                # Получаем соответствующее изображение фигуры
                piece_image = pieces[piece_code]

                # Получаем исходный размер изображения фигуры
                original_width, original_height = piece_image.size

                # Рассчитываем новую ширину с учетом сохранения пропорций
                aspect_ratio = original_width / original_height
                new_width = int(cell_size * aspect_ratio)

                # Изменяем размер фигуры так, чтобы высота была равна cell_size (высота клетки)
                piece_image = piece_image.resize((new_width, cell_size))

                # Рассчитываем позицию для вставки изображения (чтобы оно было центрировано по ширине)
                x_offset = col * cell_size + label_area_size + (cell_size - new_width) // 2

                # Вставляем изображение фигуры на доску
                board_image.paste(piece_image, (x_offset, row * cell_size + label_area_size), piece_image)

    # Рисуем метки столбцов (буквы) — белый текст на черном фоне
    for col in range(8):
        draw.text(
            ((col + 1) * cell_size - label_area_size * 1.5, label_area_size // 4 - 10),  # Центрируем текст по высоте зоны
            col_labels[col], fill='white', font=font
        )

    # Рисуем метки строк (цифры) — белый текст на черном фоне
    for row in range(8):
        draw.text(
            (label_area_size // 4, (row + 1) * cell_size - label_area_size * 1.5),  # Центрируем текст по ширине зоны
            row_labels[row], fill='white', font=font
        )

    # Сохраняем изображение доски с фигурами и метками
    byte_io = io.BytesIO()
    board_image.save(byte_io, 'PNG')
    byte_io.seek(0)

    return byte_io