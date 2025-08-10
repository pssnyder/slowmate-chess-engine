"""SlowMate Chess Engine - UCI Protocol Module."""

import chess
import time
import threading
import sys


class UCIProtocol:
    """Basic UCI protocol implementation with flushed output."""

    def __init__(self, engine):
        self.engine = engine
        self.debug = False
        self.name = "SlowMate"
        self.author = "Pat Snyder"
        self.searching = False
        self.stop_requested = False
    # Rely on explicit flush instead of stdout reconfigure for portability
        self._out("info string init complete")

    def _out(self, text: str) -> None:
        print(text, flush=True)

    def process_command(self, command: str) -> None:
        tokens = command.split()
        if not tokens:
            return
        handlers = {
            "uci": self._handle_uci,
            "debug": self._handle_debug,
            "isready": self._handle_isready,
            "setoption": self._handle_setoption,
            "ucinewgame": self._handle_ucinewgame,
            "position": self._handle_position,
            "go": self._handle_go,
            "stop": self._handle_stop,
            "quit": self._handle_quit,
        }
        h = handlers.get(tokens[0])
        if h:
            h(tokens[1:])

    def _handle_uci(self, args):
        self._out(f"id name {self.name}")
        self._out(f"id author {self.author}")
        self._out("option name Hash type spin default 64 min 1 max 1024")
        self._out("option name Debug type check default false")
        self._out("uciok")

    def _handle_debug(self, args):
        self.debug = bool(args and args[0] == "on")

    def _handle_isready(self, args):
        self._out("readyok")

    def _handle_setoption(self, args):
        if len(args) >= 4 and args[0] == "name" and args[2] == "value":
            if args[1] == "Debug":
                self.debug = (args[3].lower() == "true")

    def _handle_ucinewgame(self, args):
        self.engine.new_game()

    def _handle_position(self, args):
        if not args:
            return
        if args[0] == "startpos":
            self.engine.set_position("startpos")
            move_index = 1
        elif args[0] == "fen" and len(args) >= 7:
            fen = " ".join(args[1:7])
            self.engine.set_position(fen)
            move_index = 7
        else:
            return
        if len(args) > move_index and args[move_index] == "moves":
            for mv in args[move_index + 1:]:
                self.engine.make_move(chess.Move.from_uci(mv))

    def _handle_go(self, args):
        search_time = 1000
        i = 0
        while i < len(args):
            if args[i] == "movetime" and i + 1 < len(args):
                search_time = int(args[i + 1])
                break
            elif args[i] == "wtime" and self.engine.board.board.turn and i + 1 < len(args):
                search_time = int(args[i + 1]) // 30
                break
            elif args[i] == "btime" and not self.engine.board.board.turn and i + 1 < len(args):
                search_time = int(args[i + 1]) // 30
                break
            i += 1
        self.searching = True
        self.stop_requested = False
        threading.Thread(target=self._search_and_respond, args=(search_time,), daemon=True).start()

    def _handle_stop(self, args):
        if self.searching:
            self.stop_requested = True

    def _handle_quit(self, args):
        self.stop_requested = True

    def _search_and_respond(self, search_time: int) -> None:
        try:
            start = time.time()
            best_move = None
            try:
                # Pass milliseconds directly; engine converts internally
                best_move = self.engine.search(time_limit_ms=search_time)
            except Exception as e:
                if self.debug:
                    self._out(f"info string search error {e}")
            elapsed_ms = int((time.time() - start) * 1000)
            if self.debug:
                self._out(f"info string time {elapsed_ms}ms")
            if best_move and not self.stop_requested:
                self._out(f"bestmove {best_move.uci()}")
            else:
                legal = self.engine.move_generator.get_ordered_moves()
                if legal:
                    self._out(f"bestmove {legal[0].uci()}")
                else:
                    self._out("bestmove 0000")
        finally:
            self.searching = False
            self.stop_requested = False
