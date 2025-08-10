#!/usr/bin/env python3
"""Step-by-step import test"""

print("1. Starting import test...")

try:
    print("2. Importing chess...")
    import chess
    print("   ✅ chess imported")
    
    print("3. Importing SlowMateEngine...")
    from slowmate.engine import SlowMateEngine
    print("   ✅ SlowMateEngine imported")
    
    print("4. Importing intelligence module...")
    import slowmate.intelligence
    print("   ✅ intelligence module imported")
    
    print("5. Getting MoveIntelligence class...")
    MoveIntelligence = getattr(slowmate.intelligence, 'MoveIntelligence')
    print("   ✅ MoveIntelligence class found")
    
    print("6. Getting IntelligentSlowMateEngine class...")
    IntelligentSlowMateEngine = getattr(slowmate.intelligence, 'IntelligentSlowMateEngine')
    print("   ✅ IntelligentSlowMateEngine class found")
    
    print("7. Creating SlowMateEngine instance...")
    base_engine = SlowMateEngine()
    print("   ✅ SlowMateEngine created")
    
    print("8. Creating MoveIntelligence instance...")
    intelligence = MoveIntelligence(base_engine)
    print("   ✅ MoveIntelligence created")
    
    print("9. Creating IntelligentSlowMateEngine instance...")
    engine = IntelligentSlowMateEngine()
    print("   ✅ IntelligentSlowMateEngine created")
    
    print("ALL IMPORTS SUCCESSFUL!")
    
except Exception as e:
    print(f"❌ ERROR at step: {e}")
    import traceback
    traceback.print_exc()
