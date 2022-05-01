from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, Qt
from PyQt5.QtWidgets import QWidget, QCheckBox, QDoubleSpinBox, QVBoxLayout
import chess.engine


'''
An object of this class represents a player in a chess game
Required signals, slots, etc are defined and stored here
'''
class Player(QObject):

    WHITE = 'w'
    BLACK = 'b'

    DecidedMove = pyqtSignal(str)

    def __init__(self, colour, thread=None, board=None):

        super().__init__()

        # set member vars
        self.colour = colour

        # maybe move to thread
        if thread:
            self.moveToThread(thread)

        # connect signals/slots
        if board:
            self.DecidedMove.connect(board.ApplyMove)
            board.ReadyForNextMove.connect(self.TakeTurn)

    '''
    Check the fen to see if it's my turn
    '''
    def IsMyMove(self, fen):
        return " {0} ".format(self.colour) in fen

    @pyqtSlot(str)
    def TakeTurn(self, fen):
        return
        # If self.IsMyMove, emit DecidedMove(uci) and return uci


'''
Class containing the engine
'''
class AiPlayer(Player):

    '''
    Initialise with the path to the exe and seconds limit per turn
    '''
    def __init__(self, exe_path, turn_limit_s, colour, thread=None, board=None):

        super().__init__(colour, thread, board)

        # set member vars
        self.exe_path = exe_path
        self.engine = chess.engine.SimpleEngine.popen_uci(self.exe_path)
        self.turn_limit_s = turn_limit_s
        self.enabled = board is None  # enabled by default if no board
        self.last_fen = board.fen() if board else None

    '''
    Check to temporarily disable the engine if not playing
    '''
    def IsMyMove(self, fen):
        return super().IsMyMove(fen) and self.enabled

    '''
    Open a process to get the next move from the engine
    Emit DecidedMove(uci) and return uci
    '''
    @pyqtSlot(str)
    def TakeTurn(self, fen):
        self.last_fen = fen
        if self.IsMyMove(fen):
            board = chess.Board(fen)
            result = self.engine.play(board, chess.engine.Limit(time=self.turn_limit_s),
                                      options={'Analysis Contempt': 'Both', 'Contempt': "100"})
            uci = str(result.move)
            self.DecidedMove.emit(uci)
            return uci

    '''
    Set the turn limit for the player
    '''
    @pyqtSlot(float)
    def SetTurnLimit(self, turn_limit_s):
        self.turn_limit_s = turn_limit_s

    '''
    Overload SetEnabled for QCheckBox
    '''
    @pyqtSlot(int)
    def SetCheckSate(self, check_state):
        self.SetEnabled(check_state == Qt.Checked)

    '''
    Set the enabled state
    '''
    @pyqtSlot(bool)
    def SetEnabled(self, enabled):
        self.enabled = enabled
        self.TakeTurn(self.last_fen)

'''
Display player options on GUI
'''
class PlayerOptions(QWidget):

    def __init__(self, player, parent=None):

        super().__init__(parent)

        # create box to enable/disable engine
        colour = {Player.WHITE: "White", Player.BLACK: "Black"}[player.colour]
        ai_enabled = QCheckBox("{0} Engine".format(colour), self)
        turn_limit_s = QDoubleSpinBox(self)

        v_layout = QVBoxLayout()
        v_layout.addWidget(ai_enabled)
        v_layout.addWidget(turn_limit_s)

        self.setLayout(v_layout)

        # connect signals/slots or disable option if engine unavailable
        if isinstance(player, AiPlayer):
            ai_enabled.stateChanged.connect(player.SetCheckSate)
            turn_limit_s.setValue(player.turn_limit_s)
            turn_limit_s.valueChanged.connect(player.SetTurnLimit)
        else:
            ai_enabled.setEnabled(False)
            turn_limit_s.setEnabled(False)


'''
Player class testing
'''
if __name__ == "__main__":

    import chess
    import sys

    exe_path = 'stockfish_12_x64_avx2.exe'

    # ----------------------
    # Synchronous
    # ----------------------
    board = chess.Board()
    player_b = AiPlayer(exe_path, .1, Player.BLACK)
    player_w = AiPlayer(exe_path, .1, Player.WHITE)
    player = player_w

    while not board.is_game_over():
        uci = player.TakeTurn(board.fen())

        print(uci)
        sys.stdout.flush()

        board.push(chess.Move.from_uci(uci))

        if player == player_w:
            player = player_b
        else:
            player = player_w

    print(board.fen())
    sys.stdout.flush()

    # ----------------------
    # Asynchronous
    # ----------------------
    from PyQt5.QtCore import QThread
    from PyQt5.QtWidgets import QApplication


    class ChessBoard(QObject, chess.Board):
        """
         BRIEF  A helper class for the signal/slot testing
      """
        ReadyForNextMove = pyqtSignal(str)
        GameOver = pyqtSignal()

        def __init__(self):
            """
            BRIEF  Construct the base classes
         """
            super().__init__()

        @pyqtSlot(str)
        def ApplyMove(self, uci):
            """
            BRIEF  Apply a move to the board
         """
            print(uci)

            move = chess.Move.from_uci(uci)
            if move in self.legal_moves:
                self.push(move)

                if not self.is_game_over():
                    self.ReadyForNextMove.emit(self.fen())
                else:
                    print(self.fen())
                    self.GameOver.emit()

            sys.stdout.flush()


    q_app = QApplication([])
    thread = QThread()
    board = ChessBoard()
    player_b = AiPlayer(exe_path, .1, Player.BLACK, thread, board)
    player_w = AiPlayer(exe_path, .1, Player.WHITE, thread, board)

    player_options_b = PlayerOptions(player_b)
    player_options_b.setGeometry(300, 300, 200, 100)

    player_options_w = PlayerOptions(player_w)
    player_options_w.setGeometry(300, 600, 200, 100)

    board.GameOver.connect(q_app.exit)
    q_app.aboutToQuit.connect(thread.quit)
    thread.start()

    player_options_b.show()
    player_options_w.show()

    q_app.exec()
    thread.wait()
