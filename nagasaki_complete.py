#!/usr/bin/env python3
"""
SlowMate v0.3.03 - NAGASAKI Protocol Complete Backup

Final backup before systematic reversion to v0.1.0 baseline and 
incremental feature restoration process.
"""

import os
import shutil
import json
from datetime import datetime

def create_complete_backup():
    """Create comprehensive backup of current state."""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = f"../BACKUP_COMPLETE_NAGASAKI_{timestamp}"
    
    print(f"🗂️  Creating complete backup: {backup_dir}")
    
    # Create backup directory
    os.makedirs(backup_dir, exist_ok=True)
    
    # Items to backup
    backup_items = [
        'slowmate/',           # Core engine code
        'builds/',             # Build history and configurations
        'testing/',            # Test scripts and results
        'docs/',              # Documentation
        'games/',             # Game PGNs and analysis
        'data/',              # Opening/endgame data
        'analysis/',          # Analysis utilities
        '*.py',               # Root level Python scripts
        '*.bat',              # Batch files
        '*.md',               # Markdown files
        '*.txt',              # Text files
        'requirements.txt',    # Dependencies
    ]
    
    # Copy items to backup
    for item in backup_items:
        if '*' in item:
            # Handle wildcards
            import glob
            for file in glob.glob(item):
                if os.path.isfile(file):
                    shutil.copy2(file, backup_dir)
        else:
            src = item
            dst = os.path.join(backup_dir, item)
            if os.path.exists(src):
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)
    
    # Create backup manifest
    manifest = {
        "backup_timestamp": timestamp,
        "version": "v0.3.03_NAGASAKI",
        "purpose": "Complete state preservation before systematic reversion",
        "restoration_target": "v0.1.0_BETA baseline",
        "next_version": "v0.4.0_REVERSION_START",
        "problems_documented": [
            "Massive evaluation scores (+M500/8, -2500cp)",
            "UCI debug options not visible in Arena", 
            "Performance regression vs v0.1.0",
            "False mate scores in normal positions",
            "Build inconsistencies"
        ],
        "features_preserved": 30,
        "restoration_phases": 4
    }
    
    with open(os.path.join(backup_dir, 'BACKUP_MANIFEST.json'), 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"✅ Complete backup created: {backup_dir}")
    return backup_dir

def identify_baseline_version():
    """Identify the stable baseline version for restoration."""
    
    print("🔍 Analyzing version history for stable baseline...")
    
    # Check available versions
    version_analysis = {
        "v0.1.0": {
            "status": "TOURNAMENT_WINNER", 
            "evidence": "first_tournament_victory.pgn shows 1-0 win",
            "features": "Basic intelligence, material evaluation, checkmate detection",
            "problems": "None documented",
            "recommendation": "BASELINE CANDIDATE"
        },
        "v0.2.x": {
            "status": "FEATURE_ADDITIONS",
            "evidence": "Added depth search and advanced features", 
            "features": "Depth search, enhanced tactics, endgame knowledge",
            "problems": "Unknown - needs analysis",
            "recommendation": "ANALYZE_PERFORMANCE"
        },
        "v0.3.x": {
            "status": "BROKEN",
            "evidence": "Massive evaluation scores, tournament losses",
            "features": "All v0.2.x plus emergency fixes",
            "problems": "Multiple critical bugs, performance regression", 
            "recommendation": "ABANDON_AND_REVERT"
        }
    }
    
    print("📊 Version Analysis:")
    for version, data in version_analysis.items():
        print(f"  {version}: {data['status']} - {data['recommendation']}")
    
    baseline = "v0.1.0"
    print(f"🎯 Selected baseline: {baseline}")
    return baseline, version_analysis

def create_restoration_roadmap():
    """Create detailed roadmap for systematic restoration."""
    
    roadmap = {
        "mission": "Systematic restoration from v0.1.0 to tournament-ready v0.5.0_BETA",
        "baseline": "v0.1.0_BETA",
        "target": "v0.5.0_BETA",
        
        "phase_0_preparation": {
            "version": "v0.4.0_RESTORATION_BASE",
            "goal": "Restore and verify v0.1.0 baseline",
            "tasks": [
                "Extract v0.1.0 source code",
                "Verify it builds correctly",
                "Test basic functionality",
                "Confirm tournament performance",
                "Document exact feature set"
            ],
            "success_criteria": [
                "Engine builds without errors",
                "Passes basic move generation tests", 
                "Shows reasonable evaluation scores",
                "Can win games against weaker opponents"
            ]
        },
        
        "phase_1_infrastructure": {
            "version": "v0.4.01",
            "goal": "Add essential development infrastructure",
            "features_to_add": [
                "UCI options framework",
                "Debug toggles system",
                "Evaluation logging",
                "Build configuration system"
            ],
            "validation": "Must not affect game performance"
        },
        
        "phase_2_evaluation_fixes": {
            "version": "v0.4.02", 
            "goal": "Fix evaluation scaling and mate detection",
            "features_to_add": [
                "Proper evaluation scaling (-10.00 to +10.00 range)",
                "Correct mate score handling",
                "Evaluation component separation",
                "UCI info output fixes"
            ],
            "validation": "Tournament test vs v0.4.01, must show improvement"
        },
        
        "phase_3_tactical_intelligence": {
            "version": "v0.4.03",
            "goal": "Add proven tactical features incrementally",
            "features_to_add": [
                "Enhanced material evaluation",
                "King safety improvements", 
                "Basic threat detection",
                "Capture evaluation"
            ],
            "validation": "Each feature tested individually, removed if harmful"
        },
        
        "phase_4_search_depth": {
            "version": "v0.4.04", 
            "goal": "Add depth search if beneficial",
            "features_to_add": [
                "Limited depth search (2-3 ply max)",
                "Critical position recognition",
                "Search optimization"
            ],
            "validation": "Must significantly improve performance, or remove"
        },
        
        "phase_5_advanced_features": {
            "version": "v0.4.05+",
            "goal": "Add advanced features only if they improve performance",
            "features_to_consider": [
                "Advanced tactical patterns (pins, forks)",
                "Endgame knowledge", 
                "Opening principles",
                "Piece coordination"
            ],
            "approach": "Add one at a time, validate each, remove if harmful"
        },
        
        "phase_6_stabilization": {
            "version": "v0.5.0_BETA",
            "goal": "Create stable, tournament-ready version",
            "requirements": [
                "Consistently beats v0.1.0 baseline",
                "Clean UCI interface with working debug options",
                "Evaluation scores in reasonable range",
                "No critical bugs or regressions",
                "Professional tournament appearance"
            ]
        }
    }
    
    return roadmap

def main():
    """Execute complete NAGASAKI protocol."""
    
    print("=" * 60)
    print("SLOWMATE v0.3.03 - NAGASAKI PROTOCOL")
    print("Complete Backup and Restoration Planning")
    print("=" * 60)
    
    # Step 1: Complete backup
    backup_dir = create_complete_backup()
    
    # Step 2: Identify baseline
    baseline, analysis = identify_baseline_version()
    
    # Step 3: Create restoration roadmap
    roadmap = create_restoration_roadmap()
    
    # Step 4: Save restoration plan
    restoration_plan = {
        "backup_location": backup_dir,
        "baseline_version": baseline,
        "version_analysis": analysis,
        "restoration_roadmap": roadmap,
        "next_steps": [
            "Review and approve restoration plan",
            "Begin Phase 0: Restore v0.1.0 baseline", 
            "Execute incremental restoration phases",
            "Validate each phase before proceeding"
        ]
    }
    
    with open('NAGASAKI_RESTORATION_PLAN.json', 'w', encoding='utf-8') as f:
        json.dump(restoration_plan, f, indent=2, ensure_ascii=False)
    
    # Create human-readable summary
    summary = f"""# NAGASAKI Protocol - Complete Restoration Plan

## Mission Accomplished
- ✅ Complete backup created: {backup_dir}
- ✅ Feature enumeration completed (30 features documented)
- ✅ Problems identified and analyzed (5 critical issues)
- ✅ Restoration roadmap created (6 phases planned)

## Baseline Selection
**Selected**: {baseline}
**Reason**: Tournament-winning version with documented victory

## Next Actions
1. **Review Plan**: Confirm restoration approach
2. **Phase 0**: Restore {baseline} baseline and verify functionality
3. **Incremental Restoration**: Execute phases v0.4.01 → v0.5.0_BETA
4. **Validation**: Tournament test each phase before proceeding

## Success Metrics
- Engine consistently beats v0.1.0 baseline
- Evaluation scores stay reasonable (-10.00 to +10.00)
- UCI interface works properly with debug options
- Tournament-ready reliability and performance

## Files Created
- `NAGASAKI_RESTORATION_PLAN.json` - Complete plan data
- `SLOWMATE_V0303_FEATURE_ENUMERATION.md` - Feature documentation
- `SLOWMATE_V0303_COMPLETE_ENUMERATION.json` - Structured feature data

🚀 **Ready to begin systematic restoration!**
"""
    
    with open('NAGASAKI_SUMMARY.md', 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print("\n🎯 MISSION ACCOMPLISHED!")
    print(f"📦 Backup: {backup_dir}")
    print(f"📋 Plan: NAGASAKI_RESTORATION_PLAN.json")
    print(f"📄 Summary: NAGASAKI_SUMMARY.md")
    print(f"🎯 Baseline: {baseline}")
    print("\n🚀 Ready to begin Phase 0: Baseline Restoration!")
    
    return True

if __name__ == "__main__":
    main()
