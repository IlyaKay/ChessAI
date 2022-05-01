from board import ChessBoard, BoardControls
from player import Player, AiPlayer, PlayerOptions
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QMessageBox
import os


'''
Options class scores default parameters used during execution.
Turn limit is represented in seconds and can be altered using the GUI.
'''
class Options:
    DEFAULT_TURN_LIMIT_S = 10
    DEFAULT_AI_EXE_PATH = 'Contemptitan.exe'


'''
This class handles the main window containing the chessboard and player options
'''
class Window(QWidget):

    def __init__(self, exe_path, turn_limit_s, thread):

        super().__init__()

        self.board = ChessBoard(self)

        if os.path.isfile(exe_path):
            self.player_b = AiPlayer(exe_path, turn_limit_s, Player.BLACK, thread, self.board)
            self.player_w = AiPlayer(exe_path, turn_limit_s, Player.WHITE, thread, self.board)
        else:
            self.player_b = Player(Player.BLACK, thread, self.board)
            self.player_w = Player(Player.WHITE, thread, self.board)

        player_options_b = PlayerOptions(self.player_b, self)
        board_controls = BoardControls(self.board)
        player_options_w = PlayerOptions(self.player_w, self)

        v_layout = QVBoxLayout()
        v_layout.addStretch()
        v_layout.addWidget(player_options_b)
        v_layout.addStretch()
        v_layout.addWidget(board_controls)
        v_layout.addStretch()
        v_layout.addWidget(player_options_w)
        v_layout.addStretch()

        h_layout = QHBoxLayout()
        h_layout.addWidget(self.board)
        h_layout.addLayout(v_layout)
        h_layout.addSpacing(50)

        self.setLayout(h_layout)

'''
Main execution
'''
if __name__ == '__main__':

    from PyQt5.QtCore import QThread
    from PyQt5.QtWidgets import QApplication
    from argparse import ArgumentParser

    ### engine debug
    # import logging
    # logging.basicConfig(level=logging.DEBUG)

    # os.chdir(r"C:\Users\Ilya\PycharmProjects\ChessAI\Darky_05e")
    # DEFAULT_AI_EXE_PATH = 'Darky_05e_UCI.exe'
    parser = ArgumentParser()
    parser.add_argument('ai_exe_path', nargs='?', type=str, default=Options.DEFAULT_AI_EXE_PATH,
                        help='Engine exe needs to accept 2 args <fen> <time limit (s)> and use UCI format.')
    args = parser.parse_args()

    q_app = QApplication([])

    if not os.path.isfile(args.ai_exe_path):
        warning = QMessageBox()
        warning.setWindowTitle("Warning")
        warning.setText("AI exe path '{0}' not found. Associated controls will be disabled.".format(args.ai_exe_path))
        warning.exec()

    thread = QThread()
    wnd = Window(args.ai_exe_path, Options.DEFAULT_TURN_LIMIT_S, thread)

    q_app.aboutToQuit.connect(thread.quit)
    thread.start()

    wnd.show()
    q_app.exec()
    thread.wait()
