from logic import DB_Manager
from config import *
from piece_move_checker import *

manager = DB_Manager(DATABASE)

checks = {"P": get_pawn_moves,
        "B": get_bishop_moves,
        "R": get_rook_moves,
        "N": get_knight_moves,
        "K": get_king_moves,
        "Q": get_queen_moves}


async def rook_super_move(player, game_id, color, board, turn_player, start_row, start_col, bot, ctx):
    from function import update_game_info
    king = manager.get_king_place(game_id, color)
    manager.board_edit(game_id, [start_row, start_col], [king[0], king[1]], board[king[0]][king[1]])

    #новые возможнные ходы и король противника
    moves_check = checks[board[start_row][start_col][0]]
    new_moves = moves_check(turn_player.id, board, king[0], king[1])
    opponent_color = "B" if color == "W" else "W"
    opponent_king = manager.get_king_place(game_id, opponent_color)
    if player[4] < 10:
        manager.edit_player(turn_player.id, "charge_count", 1)

    #Проверка на шах противнику
    if opponent_king in new_moves:
        opponent_player = manager.get_opponent_player(game_id, turn_player.id)
        manager.edit_player(opponent_player, "check", 1)
        manager.switch_turn(game_id)
        await ctx.send(f"{turn_player.mention}, Вы сделали шах противнику", delete_after=5.0)
        await update_game_info(ctx, game_id, bot)
        return "check"
        
    #изменение доски
    manager.switch_turn(game_id)
    await ctx.send("da", delete_after=5.0)
    await update_game_info(ctx, game_id, bot)
    return True

async def queen_super_move(player, game_id, color, board, turn_player, start_row, start_col, bot, ctx, end_row, end_col):
    from function import update_game_info
    #новые возможнные ходы и король противника
    moves_check = checks[board[start_row][start_col][0]]
    new_moves = moves_check(turn_player.id, board, end_row, end_col)
    opponent_color = "B" if color == "W" else "W"
    opponent_king = manager.get_king_place(game_id, opponent_color)
    if player[4] < 10:
        manager.edit_player(turn_player.id, "charge_count", 1)

    #Проверка на шах противнику
    if opponent_king in new_moves:
        opponent_player = manager.get_opponent_player(game_id, turn_player.id)
        manager.edit_player(opponent_player, "check", 1)
        manager.board_edit(game_id,[start_row, start_col], [end_row, end_col])
        await ctx.send(f"{turn_player.mention}, Вы сделали шах противнику", delete_after=5.0)
        await update_game_info(ctx, game_id, bot, "edit", None, "queen")
        return "check"

    #Проверка на победу(сьесть короля)
    if opponent_king == (end_row, end_col):
        await ctx.send(f"Победил {turn_player.mention}!", delete_after=5.0)
        manager.board_edit(game_id,[start_row, start_col], [end_row, end_col])
        await update_game_info(ctx, game_id, bot, "end")
        manager.end_game(game_id)
        return "end"
        
    #изменение доски
    manager.board_edit(game_id,[start_row, start_col], [end_row, end_col])
    await ctx.send("da", delete_after=5.0)
    await update_game_info(ctx, game_id, bot, "edit", None, "queen")
    return True