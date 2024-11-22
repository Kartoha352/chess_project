import disnake, time, pprint
from disnake.ext import commands
from logic import DB_Manager
from config import *
from function import update_game_info, wait_for_second_square, wait_for_first_square
from piece_move_checker import *

intents = disnake.Intents().all()
bot = commands.Bot(command_prefix='.', intents=intents, help_command=None)

checks = {"P": get_pawn_moves,
        "B": get_bishop_moves,
        "R": get_rook_moves,
        "N": get_knight_moves,
        "K": get_king_moves,
        "Q": get_queen_moves}

#View
class Confirm_view(disnake.ui.View):
    def __init__(self, author:disnake.User, user:disnake.User, msg:disnake.Message = None):
        self.author = author
        self.user = user
        self.msg = msg
        super().__init__(timeout=30)
        
    @disnake.ui.button(label="Согласиться", style=disnake.ButtonStyle.gray, custom_id = "confirm")
    async def confirm(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if inter.author.id == self.user.id:
            self.stop()
            manager.edit_player(self.user.id, "status", 2)
            manager.edit_player(self.author.id, "status", 2)
            game_id = manager.start_game(self.author.id, self.user.id)

            await update_game_info(inter, game_id, bot, "send")

    async def on_timeout(self):
        await self.msg.edit(f"Время вышло. Пользователь {self.user.mention} не успел ответить.", view=None)

class Confirm_super_charge_view(disnake.ui.View):
    def __init__(self, user:disnake.User, ctx:commands.Context, start_row, start_col, board, opponent_player, start_time, game_id, bot):
        self.user = user
        self.ctx = ctx
        self.start_row = start_row
        self.start_col = start_col
        self.board = board
        self.opponent_player = opponent_player
        self.game_id = game_id
        self.start_time = start_time
        self.bot = bot
        super().__init__(timeout=None)
        
    @disnake.ui.button(label="Выбрать", style=disnake.ButtonStyle.green, custom_id = "select")
    async def select(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if inter.author.id == self.user.id:
            await update_game_info(self.ctx, self.game_id, self.bot, "edit", self.start_row, self.start_col)
            await inter.response.send_message("Выбор сделан. Теперь выберите клетку куда хотите походить.", delete_after=5.0)
            await inter.message.delete()
            await wait_for_second_square(self.bot, self.user, self.ctx, self.start_row, self.start_col, self.board, self.opponent_player)

    @disnake.ui.button(label="Выбрать другую", style=disnake.ButtonStyle.blurple, custom_id = "select_other")
    async def select_other(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if inter.author.id == self.user.id:
            elapsed_time = time.time() - self.start_time 
            remaining_time = 1.0 if (60 - elapsed_time) < 0 else 60 - elapsed_time
            await inter.response.send_message(f"Выберите другую клетку.\nУ вас осталось {round(remaining_time,1)} сек.", delete_after=5.0)
            await inter.message.delete()
            await wait_for_first_square(self.bot, self.user, self.ctx, self.start_time)

class Moves_history(disnake.ui.Button):
    def __init__(self, turn_player, game_id):
        self.game_id = game_id
        self.turn_player = turn_player
        super().__init__(label="История",
                style=disnake.ButtonStyle.blurple,
                custom_id = "moves_history")

    async def callback(self, inter: disnake.MessageInteraction):
        limited_white_moves, limited_black_moves = manager.get_moves_history(self.game_id)
        if limited_white_moves:
            turn_player = await inter.guild.fetch_member(self.turn_player.id)
            turn_player_color = manager.get_player_color(turn_player.id)
            opponent_player = await inter.guild.fetch_member(manager.get_opponent_player(self.game_id, turn_player.id))

            min_moves = int(list(limited_white_moves.keys())[0])
            max_moves = int(list(limited_white_moves.keys())[-1])

            print(limited_white_moves)
            print(limited_black_moves)

            print(min_moves)
            print(max_moves)

            history_lines = []
            for move_number in range(min_moves, max_moves + 1):
                white_move = limited_white_moves.get(str(move_number), "—")
                black_move = limited_black_moves.get(str(move_number), "—")
                history_lines.insert(0, f"**{move_number}.** `W`: {white_move[0] + ' -> ' + white_move[1] if white_move != '—' else white_move} | `B`: {black_move[0] + ' -> ' + black_move[1] if black_move != '—' else black_move}")

            history_text = "\n".join(history_lines)

            if turn_player_color == "W":
                name = f"Белые (`W`) — {turn_player.mention}\n"
                name+= f"Чёрные (`B`) — {opponent_player.mention}"
            else:
                name = f"Белые (`W`) — {opponent_player.mention}\n"
                name += f"Чёрные (`B`) — {turn_player.mention}"

            emb = disnake.Embed(
                title="История ходов",
                description=name+"\n\n"+history_text,
                color = disnake.Colour.from_rgb(48, 49, 54)
            )

            await inter.response.send_message(embed=emb, ephemeral=True)
        else:
            await inter.response.send_message("Ещё никто не походил.", ephemeral=True)

        # moves_history = manager.get_moves_history(self.game_id)
        # if len(moves_history["W"]) > 0:
        #     turn_player = await inter.guild.fetch_member(self.turn_player.id)
        #     turn_player_color = manager.get_player_color(turn_player.id)
        #     opponent_player = await inter.guild.fetch_member(manager.get_opponent_player(self.game_id, turn_player.id))

        #     emb = disnake.Embed(title="История ходов", color = disnake.Colour.from_rgb(48, 49, 54))
        #     if turn_player_color == "W":
        #         name_W = f"W - {turn_player.name}"
        #         name_B = f"B - {opponent_player.name}"
        #     else:
        #         name_W = f"W - {opponent_player.name}"
        #         name_B = f"B - {turn_player.name}"

        #     value_W = ""
        #     for move_num in moves_history["W"]:
        #         value_W += f"`{move_num}.` {moves_history['W'][move_num]}\n"

        #     value_B = ""
        #     if len(moves_history["B"]) > 0:
        #         for move_num in moves_history["B"]:
        #             value_B += f"`{move_num}.`{moves_history['B'][move_num]}\n"
        #     else:
        #         value_B = "Пусто"

        #     emb.add_field(name_W,value_W)
        #     emb.add_field(name_B,value_B)

        #     await inter.response.send_message(embed=emb, ephemeral=True)
        # else:
        #     await inter.response.send_message("Ещё никто не походил.", ephemeral=True)

class Super_charge(disnake.ui.Button):
    def __init__(self, user:disnake.User, disabled = False):
        player = manager.get_player(user.id) #id, game_id, color, check, charge_count, charge_status
        self.user = user
        if disabled == False:
            if player[4] == 10:
                super().__init__(label=f"Суперход 10/10",
                                style=disnake.ButtonStyle.green,
                                disabled=False,
                                custom_id = "super_charge")
            else:
                super().__init__(label=f"Суперход {player[4]}/10",
                                style=disnake.ButtonStyle.gray,
                                disabled=True,
                                custom_id = "super_charge")
        else:
            super().__init__(label=f"Суперход {player[4]}/10",
                            style=disnake.ButtonStyle.gray,
                            disabled=disabled,
                            custom_id = "super_charge")

    async def callback(self, inter: disnake.MessageInteraction):
        if inter.author == self.user:
            manager.edit_player(inter.author.id, "charge_count", 0)
            view = disnake.ui.View(timeout=None)
            view.add_item(Super_charge(inter.author))
            await inter.response.send_message("Вы активировали супер-ход.\nВыберите клетку если это нужно, если это не требуется для выполнения условий супер-хода фигуры который вы выбрали то, можете просто написать что угодно.", ephemeral=True)
            await inter.message.edit(view=view)
        else:
            await inter.response.send_message("Вы не можете использовать эту кнопку", ephemeral=True)

#Commands
@bot.command(name = "start")
async def start(ctx:commands.Context, user:disnake.User = None):
    if user != None:
        if user != ctx.author:
            if manager.if_not_in_game(ctx.author.id):
                if manager.if_not_in_game(user.id):
                    result = manager.edit_player(ctx.author.id, "status", 1)
                    if result == False:
                        manager.edit_player(ctx.author.id, "add")
                        manager.edit_player(ctx.author.id, "status", 1)
                    view = Confirm_view(ctx.author, user)
                    msg = await ctx.send(content=f"{user.mention}, пользователь {ctx.author.mention} хочет пригласить вас в игру в шахматы. У вас есть 30 секунд чтобы согласиться.", view=view)
                    view.msg = msg
                else:
                    await ctx.reply("Пользователь которого вы выбрали уже находиться в игре.")
            else:
                await ctx.reply("Вы уже находитесь в игре.")
        else:
            await ctx.reply("Вы не можете играть сами с собой, увы :(.")
    else:
        await ctx.reply("Вы не выбрали пользователя.")

@bot.command(name = "super_moves")
async def start(ctx:commands.Context):
    await ctx.send("""# Супер-Ходы

- **Пешка: «Призрачная атака»**  
  Пешка может ходить до трех клеток вперед, даже перепрыгивая через другие фигуры. Если на конечной клетке находится фигура противника, пешка ее съест.

- **Конь: «Прямой удар»**  
  Конь может двигаться не только буквой "Г", но и буквой "I", что позволяет ему перемещаться вертикально или горизонтально на три клетки.

- **Слон: «Фазовый сдвиг»**  
  Слон может перемещаться по диагонали на любое расстояние, игнорируя препятствия.

- **Ладья: «Рокировка хаоса»**  
  Ладья может поменяться местами с королем в любой момент.

- **Королева: «Командирский ход»**  
  После своего хода королева может дать "приказ" другой фигуре, предоставив ей возможность сделать дополнительный ход/
                         
- **Король: «Крепость»**
  Король может на два хода сделать все клетки вокруг себя неприступными, ни одна фигура не может атаковать фигуры под защитой короля в это время.""")
    

@bot.command(name = "help")
async def start(ctx:commands.Context):
    await ctx.send("""
Запустить игру можно с помощью команды `.start <user>`. После этого вы можете начать игру.
-# **Время на ответ - 30сек**.
Во время игры вы должны будете выбирать клетку куда идти и писать их чат.
-# **Время на выбор клетки - 60сек**, если вы не успели написать то победа автоматически перейдёт к противнику.
                   
Посмотреть доступные супер-ходы вы можете через команду `.super_moves`.
Информация о обновлениях и о версия по команде `.check_log`
""")
    
@bot.command(name = "check_log")
async def start(ctx:commands.Context):
    await ctx.send("""
# v1.0 - Бот был создан
## v1.1
- Был добавлен супер-ход для короля.
- Были добавлены команды `.help`, `.super_move`, `.check_log`.
## v1.2
- Была добавлена возможность просматривать историю ходов.
- Так же теперь написано какой ход сделал противник чтобы проще было ориентироваться.""")

# Запуск бота
if __name__ == '__main__':
    manager = DB_Manager(DATABASE)
    bot.run(TOKEN)