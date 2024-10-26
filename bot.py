import disnake, time
from disnake.ext import commands
from logic import DB_Manager
from config import *
from function import update_game_info, wait_for_second_square, wait_for_first_square
from piece_move_checker import *

intents = disnake.Intents().all()
bot = commands.Bot(command_prefix='.', intents=intents)

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

# Запуск бота
if __name__ == '__main__':
    manager = DB_Manager(DATABASE)
    bot.run(TOKEN)
