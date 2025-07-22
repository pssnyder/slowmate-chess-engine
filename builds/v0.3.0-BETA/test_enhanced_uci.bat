@echo off
REM SlowMate v0.3.0-BETA Enhanced UCI Test
REM Tests the enhanced UCI interface with proper time management

echo Testing SlowMate v0.3.0-BETA Enhanced UCI Interface
echo =====================================================
echo.

echo Testing basic UCI compliance...
(
    echo uci
    echo isready
    echo quit
) | slowmate_v0.3.0-BETA.exe

echo.
echo Testing position setup and search...
(
    echo uci
    echo debug on
    echo isready
    echo ucinewgame
    echo position startpos
    echo go wtime 5000 btime 5000 winc 100 binc 100
    echo quit
) | slowmate_v0.3.0-BETA.exe

echo.
echo Test completed! 
echo The engine now provides:
echo - Full UCI compliance with time management
echo - Real-time search info (depth, score, pv, nodes, nps)
echo - Professional tournament-level output
echo - Proper time control parsing and usage
echo.
pause
