"""
Enhanced UCI Interface with Comprehensive Search Output
Version: 1.0.0-BETA
"""

import time
import chess
from typing import Optional, Dict, Any, List

class EnhancedUCIInterface:
    """Enhanced UCI interface with full protocol support and rich debugging output."""
    
    def __init__(self, engine):
        """Initialize the UCI interface."""
        self.engine = engine
        self.debug_mode = False
        self.is_thinking = False
        self.nodes_searched = 0
        self.current_depth = 0
        self.current_score = 0
        self.search_start_time = 0
        self.current_pv = []
        
    def _format_score(self, score: int) -> tuple[str, str]:
        """Format evaluation score according to UCI protocol."""
        if abs(score) >= 29000:  # Mate score threshold
            # Calculate mate score:
            # - A mate in N should return "score mate N"
            # - Being mated in N should return "score mate -N"
            # Formula: sign * ceiling((30000 - abs(score))/2)
            mate_in = -((30000 - abs(score) + 1) // 2)  # Add 1 to handle mate in 1
            if score > 0:
                mate_in = -mate_in
            score_type = "mate"
            score_value = str(mate_in)
        else:
            score_type = "cp"
            score_value = str(score)
        return score_type, score_value
        
    def _handle_search_info(self, info: Dict[str, Any]):
        """Handle real-time search information."""
        info_parts = ["info"]
        
        if "depth" in info:
            info_parts.extend(["depth", str(info["depth"])])
            self.current_depth = info["depth"]
        
        if "score" in info:
            score = info["score"]
            score_type, score_value = self._format_score(score)
            info_parts.extend(["score", score_type, score_value])
            self.current_score = score
        
        if "time" in info:
            info_parts.extend(["time", str(info["time"])])
            
        if "nodes" in info:
            info_parts.extend(["nodes", str(info["nodes"])])
            self.nodes_searched = info["nodes"]
            
            # Calculate nodes per second
            elapsed = max(1, (time.time() - self.search_start_time) * 1000)
            nps = int(self.nodes_searched * 1000 / elapsed)
            info_parts.extend(["nps", str(nps)])
        
        if "pv" in info and info["pv"]:
            pv_moves = [move.uci() for move in info["pv"]]
            info_parts.extend(["pv"] + pv_moves)
            self.current_pv = pv_moves
            
        if self.debug_mode and "string" in info:
            info_parts.extend(["string", info["string"]])
            
        print(" ".join(info_parts), flush=True)
        
    def send_search_info(self, depth: int, score: int, pv: List[chess.Move],
                        nodes: int = 0, time_ms: float = 0, debug_info: Optional[str] = None):
        """Send search information in UCI format."""
        info = {
            "depth": depth,
            "score": score,
            "pv": pv,
            "nodes": nodes,
            "time": int(time_ms)
        }
        if debug_info and self.debug_mode:
            info["string"] = debug_info
            
        self._handle_search_info(info)
        
    def send_bestmove(self, move: Optional[chess.Move], ponder: Optional[chess.Move] = None):
        """Send best move found in UCI format."""
        if move:
            output = f"bestmove {move.uci()}"
            if ponder:
                output += f" ponder {ponder.uci()}"
        else:
            output = "bestmove (none)"
            
        print(output, flush=True)
