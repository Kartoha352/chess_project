from config import DATABASE
import random, sqlite3, json, pprint 

statuses = ['В поиске игры', 'В игре', 'Не в игре']

class DB_Manager:
    def __init__(self, database):
        self.database = database
        
    def create_tables(self):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''CREATE TABLE games (
                            game_id INTEGER PRIMARY KEY,
                            board TEXT,
                            turn INTEGER,
                            moves_history TEXT
                        )''')
            conn.execute('''CREATE TABLE players (
                            player_id INTEGER PRIMARY KEY,
                            game_id INTEGER,
                            color TEXT,
                            is_check INTEGER,
                            charge_count INTEGER,
                            charge_status INTEGER,
                            king_super_move INTEGER
                        )''')
            conn.execute('''CREATE TABLE status (
                            status_id INTEGER PRIMARY KEY,
                            status_name TEXT
                        )''') 
            conn.execute('''CREATE TABLE users (
                            user_id INTEGER PRIMARY KEY,
                            status_id INTEGER
                        )''')
            conn.commit()

    def __execute(self, sql, data=tuple(), return_lastrowid=False):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute(sql, data)
            conn.commit()
            if return_lastrowid:
                return cur.lastrowid
    
    def __select_data(self, sql, data = tuple()):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute(sql, data)
            return cur.fetchall()

    def default_insert(self):
        for status in statuses: 
            sql = 'INSERT INTO status (status_name) values(?)'
            self.__execute(sql, (status, ))

    def search_player(self, user_id):
        sql = '''SELECT user_id
                FROM users
                JOIN status ON users.status_id = status.status_id
                WHERE status.status_id = 1 AND user_id != ?
                LIMIT 1'''
        result = self.__select_data(sql, (user_id,))
        
        if result:
            return result[0][0]
        else:
            return None
        
    def get_msg_id(self, game_id):
        sql = '''SELECT game_id
                FROM games
                WHERE game_id = ?'''
        return self.__select_data(sql, (game_id,))[0][0]
    
    def get_game_id(self, user_id):
        sql = '''SELECT game_id
                FROM players
                WHERE player_id = ?'''
        return self.__select_data(sql, (user_id,))[0][0]
    
    def get_king_place(self, game_id, color):
        sql = '''SELECT board
                FROM games
                WHERE game_id = ?'''
        result = self.__select_data(sql, (game_id,))[0][0]
        board = json.loads(result)

        king = None

        for row in board:
            if "K_" + color in row:
                king = (board.index(row), row.index("K_" + color))
        
        return king

    def get_player(self, user_id):
        sql = '''SELECT *
                FROM players
                WHERE player_id = ?'''
        result = self.__select_data(sql, (user_id,))[0]
        return result
    
    def add_move_to_history(self, game_id, turn_player, start_row, start_col, end_row, end_col):
        game_info = self.get_game_info(game_id)
        moves_history = json.loads(game_info[3])

        color = self.get_player_color(turn_player.id)
        if moves_history["W"] == {}:
            move_number = 1
        else:
            move_number = int(max(list(moves_history["W"].keys())))
            if self.get_player_color(turn_player.id) == "W":
                move_number += 1


        #{номер хода}. {цвет}: {ход} на {ход}
        letters = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
        numbers = ['1', '2', '3', '4', '5', '6', '7', '8']

        start_square = list(letters.keys())[start_col] + numbers[start_row]
        end_square = list(letters.keys())[end_col] + numbers[end_row]
        new_move = [start_square, end_square]

        moves_history[color][move_number] = new_move

        moves_history_json = json.dumps(moves_history)

        sql = """UPDATE games 
                SET moves_history = ?
                WHERE game_id = ?"""
        self.__execute(sql, (moves_history_json, game_id, ))

    def get_moves_history(self, game_id) -> dict: 
        sql = """SELECT moves_history 
                 FROM GAMES
                 WHERE game_id = ?"""
        moves_history = self.__select_data(sql, (game_id,))[0][0]
        moves_history = json.loads(moves_history)
        pprint.pprint(moves_history)
        if len(moves_history["W"]) > 0:
            limited_white_moves = dict(list(moves_history["W"].items())[-10:])
            limited_black_moves = dict(list(moves_history["B"].items())[-10:])

            return limited_white_moves, limited_black_moves
        else:
            return False, False

    def get_players(self, game_id):
        sql = '''SELECT *
                FROM players
                WHERE game_id = ?'''
        result = self.__select_data(sql, (game_id,))
        return result
    
    def get_game_info(self, game_id):
        sql = '''SELECT *
                FROM games
                WHERE game_id = ?'''
        return self.__select_data(sql, (game_id,))[0]
    
    def get_player_color(self, player_id):
        sql = '''SELECT color
                FROM players
                WHERE player_id = ?'''
        return self.__select_data(sql, (player_id,))[0][0]
    
    def edit_player(self, user_id, action, value = 3):
        if action == "add":
            sql = """INSERT INTO users 
                     (user_id, status_id) 
                     values(?, ?)"""
            self.__execute(sql, (user_id, 3,))
        elif action == "delete":
            sql = """DELETE FROM users
                     WHERE user_id = ?"""
            self.__execute(sql, (user_id,))
        elif action == "check":
            sql = """UPDATE players 
                    SET is_check = ?
                    WHERE player_id = ?"""
            self.__execute(sql, (value, user_id,))
        elif action == "charge_count":
            if value == 1: #добавить
                sql = """UPDATE players 
                        SET charge_count = charge_count + 1
                        WHERE player_id = ?"""
                self.__execute(sql, (user_id,))
            else: #сбросить, то есть активирован суперход
                sql = """UPDATE players 
                        SET charge_count = 0
                        WHERE player_id = ?"""
                self.__execute(sql, (user_id,))

                sql = """UPDATE players 
                        SET charge_status = 1
                        WHERE player_id = ?"""
                self.__execute(sql, (user_id,))
        elif action == "charge_status":
            sql = """UPDATE players 
                    SET charge_status = 0
                    WHERE player_id = ?"""
            self.__execute(sql, (user_id,))
        elif action == "king_super_move":
            if value < 0:
                sql = """UPDATE players 
                        SET king_super_move = king_super_move - 1
                        WHERE player_id = ?"""
                self.__execute(sql, (user_id,))
            else:
                sql = """UPDATE players 
                        SET king_super_move = ?
                        WHERE player_id = ?"""
                self.__execute(sql, (value, user_id,))
        else:
            sql = """SELECT user_id
                     FROM users
                     WHERE user_id = ?"""
            result = self.__select_data(sql, (user_id, ))
            if not(result):
                sql = """INSERT INTO users 
                        (user_id, status_id) 
                        values(?, ?)"""
                self.__execute(sql, (user_id, 3,))
            sql = """UPDATE users 
                    SET status_id = ?
                    WHERE user_id = ?"""
            self.__execute(sql, (value, user_id,))

    def if_not_in_game(self, user_id):
        sql = """SELECT users.status_id
                 FROM users
                 JOIN status ON users.status_id = status.status_id
                 WHERE user_id == ?"""
        result = self.__select_data(sql, (user_id, ))
        if result:
            if result[0][0] == 2:#2 - В игре
                return False
        return True
        
    def end_game(self, game_id):
        sql = """SELECT player_id
                 FROM players
                 WHERE game_id = ?"""
        players = self.__select_data(sql, (game_id,))

        sql = """DELETE FROM players
                 WHERE game_id = ?"""
        self.__execute(sql, (game_id,))

        sql = """DELETE FROM games
                 WHERE game_id = ?"""
        self.__execute(sql, (game_id,))
        
        for id in players: 
            self.edit_player(id[0], "edit", 3)


    def start_game(self, player1_id, player2_id):
        #Добавление в тиблицу games
        players = [player1_id, player2_id]
        random.shuffle(players)

        colors = ["W", "B"]
        
        # K — Король (King)
        # Q — Ферзь (Queen)
        # R — Ладья (Rook)
        # B — Слон (Bishop)
        # N — Конь (Knight)
        # P — Пешка (Pawn)

        board = [
            ['R_W', 'N_W', 'B_W', 'Q_W', ' ', 'B_W', 'N_W', 'R_W'],
            ['P_W', 'P_W', 'P_W', 'P_W', 'P_W', 'P_W', 'P_W', 'P_W'],
            [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
            [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
            [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
            [' ', 'K_B', 'K_W', ' ', ' ', ' ', ' ', ' '],
            ['P_B', 'P_B', 'P_B', 'P_B', 'P_B', 'P_B', 'P_B', 'P_B'],
            ['R_B', 'N_B', 'B_B', 'Q_B', ' ', 'B_B', 'N_B', 'R_B']
        ]
        board_json = json.dumps(board)

        moves_history = {"B": {}, "W": {}}
        moves_history_json = json.dumps(moves_history)

        sql = """INSERT INTO games (board, turn, moves_history) VALUES (?, ?, ?)"""
        game_id = self.__execute(sql, (board_json, players[0], moves_history_json), True)
        
        #Добавление в таблицу players
        for player, color in zip(players, colors):
            sql = """INSERT INTO players (player_id, game_id, color, is_check, charge_count, charge_status, king_super_move) VALUES (?, ?, ?, ?, ?, ?, ?)"""
            self.__execute(sql, (player, game_id, color, 0, 0, 0, 0))

            #Изменение статуса пользователя в таблицу users
            self.edit_player(player, "edit", 2)

        return game_id
    
    def board_edit(self, game_id, old_square:list[int,int], new_square:list[int,int], square = " "):
        sql = """SELECT board 
                 FROM games
                 WHERE game_id = ?"""
        board = self.__select_data(sql, (game_id, ))[0][0]
        board = json.loads(board)

        piece = board[old_square[0]][old_square[1]]

        board[old_square[0]][old_square[1]] = square
        board[new_square[0]][new_square[1]] = piece

        board_json = json.dumps(board)

        sql = """UPDATE games 
                SET board = ?
                WHERE game_id = ?"""
        self.__execute(sql, (board_json, game_id, ))

    def switch_turn(self, game_id):
        players = self.get_players(game_id)
        turn = self.get_game_info(game_id)[2]

        for player in players:
            if player[0] != turn:
                new_turn = player[0]
                break 

        sql = """UPDATE games 
                SET turn = ?
                WHERE game_id = ?"""
        self.__execute(sql, (new_turn, game_id, ))

    def get_opponent_player(self, game_id, player_id):
        players = self.get_players(game_id)

        for player in players:
            if player[0] != player_id:
                opponent_player = player[0]
                break

        return opponent_player

if __name__ == '__main__':
    manager = DB_Manager(DATABASE)
    manager.create_tables()
    manager.default_insert()
#    manager.insert_project([(1, "Бот-портфолио", "https://github.com/Kartoha352/M3L3/", 2)])
    # manager.add_column_into_table("projects", "project_image", "url")