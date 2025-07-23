#!/usr/bin/env python3
"""
Comprehensive Project Cleanup Script
Created: June 18, 2025

This script performs a thorough cleanup of the Credit Card Fraud Detection project:
1. Removes redundant files from root directory
2. Cleans up unused imports
3. Archives old log files
4. Removes temporary files
5. Consolidates duplicate scripts
6. Updates documentation
"""

import os
import sys
import shutil
import glob
import datetime
from pathlib import Path
from typing import List, Dict, Set
import json
import argparse

class ProjectCleaner:
    def __init__(self, project_root: str, dry_run: bool = True):
        self.project_root = Path(project_root)
        self.dry_run = dry_run
        self.backup_dir = self.project_root / "cleanup_backup" / datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.cleanup_log = []
        
    def log_action(self, action: str, target: str, status: str = "SUCCESS"):
        """Log cleanup actions"""
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": action,
            "target": target,
            "status": status,
            "dry_run": self.dry_run
        }
        self.cleanup_log.append(entry)
        print(f"[{'DRY RUN' if self.dry_run else 'LIVE'}] {action}: {target} - {status}")
    
    def create_backup(self, file_path: Path):
        """Create backup of file before deletion"""
        if not self.dry_run:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            backup_path = self.backup_dir / file_path.name
            shutil.copy2(file_path, backup_path)
            self.log_action("BACKUP", str(file_path))
    
    def remove_redundant_root_files(self):
        """Remove redundant files from root directory"""
        print("\n=== Cleaning Root Directory ===")
        
        # Files that should be moved to appropriate directories
        files_to_move = {
            "check_model.bat": "scripts/utility/",
            "check_model_files.py": "scripts/utility/",
            "clean_files.bat": "scripts/utility/",
            "clean_files.py": "scripts/utility/",
            "clean_redundant_files_enhanced.ps1": "scripts/utility/",
            "configure_ollama_api.ps1": "scripts/utility/",
            "configure_ollama_api.py": "scripts/utility/",
            "debug_llm_service.py": "scripts/debug/",
            "diagnose_system.py": "scripts/utility/",
            "remove_redundant_folders.ps1": "scripts/utility/",
            "run_all_scripts.ps1": "scripts/powershell/",
            "run_tests.ps1": "scripts/powershell/",
            "run_tests.py": "tests/",
            "run_ui_fixed.ps1": "scripts/powershell/",
            "simple_check.py": "scripts/utility/",
            "start_api.ps1": "scripts/powershell/",
            "start_system.ps1": "scripts/powershell/",
            "start_ui.ps1": "scripts/powershell/",
            "stop_system.ps1": "scripts/powershell/",
            "test_llm_fallback_order.py": "tests/",
            "test_llm_implementations.py": "tests/",
            "test_metrics_endpoint.py": "tests/",
            "test_ollama_api.ps1": "tests/",
            "test_ollama_api.py": "tests/",
            "test_transaction_endpoints.py": "tests/",
            "launch_system.ps1": "scripts/powershell/",
        }
        
        # Files that can be safely removed (duplicates or obsolete)
        files_to_remove = [
            "merged_readme.md",  # Duplicate of README.md
            "metrics_response.json",  # Temporary test file
            "cleanup_summary.md",  # Superseded by cleanup_final_report.md
        ]
        
        # Move files to appropriate directories
        for filename, target_dir in files_to_move.items():
            source_path = self.project_root / filename
            if source_path.exists():
                target_path = self.project_root / target_dir
                target_path.mkdir(parents=True, exist_ok=True)
                
                if not self.dry_run:
                    shutil.move(str(source_path), str(target_path / filename))
                self.log_action("MOVE", f"{filename} -> {target_dir}")
        
        # Remove obsolete files
        for filename in files_to_remove:
            file_path = self.project_root / filename
            if file_path.exists():
                self.create_backup(file_path)
                if not self.dry_run:
                    file_path.unlink()
                self.log_action("REMOVE", filename)
    
    def clean_unused_imports(self):
        """Remove unused imports from Python files"""
        print("\n=== Cleaning Unused Imports ===")
        
        # Check for unused pdb imports in production code
        app_dir = self.project_root / "app"
        for py_file in app_dir.rglob("*.py"):
            if py_file.name == "__pycache__":
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if pdb is imported but not used
                if "import pdb" in content and "pdb.set_trace()" not in content:
                    lines = content.split('\n')
                    new_lines = []
                    for line in lines:
                        if line.strip() == "import pdb" or line.strip().startswith("import pdb"):
                            self.log_action("REMOVE_IMPORT", f"pdb from {py_file.name}")
                            continue
                        new_lines.append(line)
                    
                    if not self.dry_run:
                        with open(py_file, 'w', encoding='utf-8') as f:
                            f.write('\n'.join(new_lines))
                            
            except Exception as e:
                self.log_action("ERROR", f"Processing {py_file}: {e}", "FAILED")
    
    def archive_old_logs(self):
        """Archive old log files"""
        print("\n=== Archiving Old Logs ===")
        
        logs_dir = self.project_root / "logs"
        if not logs_dir.exists():
            return
        
        # Archive logs older than 7 days
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=7)
        archive_dir = logs_dir / "archive"
        
        for log_file in logs_dir.glob("*.json"):
            if log_file.name == "archive":
                continue
                
            # Parse date from filename
            try:
                file_date = datetime.datetime.strptime(log_file.stem, "%Y-%m-%d")
                if file_date < cutoff_date:
                    if not self.dry_run:
                        archive_dir.mkdir(exist_ok=True)
                        shutil.move(str(log_file), str(archive_dir / log_file.name))
                    self.log_action("ARCHIVE", f"Log file {log_file.name}")
            except ValueError:
                continue
    
    def remove_cache_files(self):
        """Remove Python cache files"""
        print("\n=== Removing Cache Files ===")
        
        # Remove __pycache__ directories
        for cache_dir in self.project_root.rglob("__pycache__"):
            if not self.dry_run:
                shutil.rmtree(cache_dir)
            self.log_action("REMOVE", f"Cache directory {cache_dir}")
        
        # Remove .pyc files
        for pyc_file in self.project_root.rglob("*.pyc"):
            if not self.dry_run:
                pyc_file.unlink()
            self.log_action("REMOVE", f"Cache file {pyc_file}")
    
    def consolidate_documentation(self):
        """Consolidate and update documentation"""
        print("\n=== Consolidating Documentation ===")
        
        # Update cleanup report with current cleanup
        cleanup_report = self.project_root / "cleanup_final_report.md"
        if cleanup_report.exists():
            with open(cleanup_report, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Add new cleanup entry
            new_entry = f"""
## Comprehensive Cleanup (June 18, 2025)

- **Final Root Directory Cleanup**: Moved all remaining utility and test scripts to appropriate directories
- **Removed Unused Imports**: Cleaned up unused pdb imports from production code
- **Log Archival**: Archived old log files to maintain clean logs directory
- **Cache Cleanup**: Removed all Python cache files and directories
- **Documentation Consolidation**: Updated and consolidated project documentation

### Files Processed: {len(self.cleanup_log)} actions taken

"""
            
            if not self.dry_run:
                with open(cleanup_report, 'w', encoding='utf-8') as f:
                    f.write(content + new_entry)
            self.log_action("UPDATE", "cleanup_final_report.md")
    
    def update_gitignore(self):
        """Update .gitignore with comprehensive exclusions"""
        print("\n=== Updating .gitignore ===")
        
        gitignore_path = self.project_root / ".gitignore"
        additional_entries = [
            "# Cleanup and backup files",
            "cleanup_backup/",
            "*.bak",
            "*.tmp",
            "",
            "# Test output files",
            "metrics_response.json",
            "debug_*.txt",
            "",
            "# Log archives",
            "logs/archive/",
            "",
            "# Python cache (comprehensive)",
            "__pycache__/",
            "*.py[cod]",
            "*$py.class",
            "*.so",
            "",
            "# IDEs and editors",
            ".vscode/",
            ".idea/",
            "*.swp",
            "*.swo",
            "*~",
        ]
        
        if gitignore_path.exists():
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
            
            # Add new entries if they don't exist
            new_entries = []
            for entry in additional_entries:
                if entry not in existing_content:
                    new_entries.append(entry)
            
            if new_entries and not self.dry_run:
                with open(gitignore_path, 'a', encoding='utf-8') as f:
                    f.write('\n' + '\n'.join(new_entries))
                self.log_action("UPDATE", ".gitignore")
    
    def generate_cleanup_report(self):
        """Generate final cleanup report"""
        print("\n=== Generating Cleanup Report ===")
        
        report_path = self.project_root / f"cleanup_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report_data = {
            "cleanup_date": datetime.datetime.now().isoformat(),
            "dry_run": self.dry_run,
            "total_actions": len(self.cleanup_log),
            "actions": self.cleanup_log,
            "summary": {
                "files_moved": len([a for a in self.cleanup_log if a["action"] == "MOVE"]),
                "files_removed": len([a for a in self.cleanup_log if a["action"] == "REMOVE"]),
                "files_archived": len([a for a in self.cleanup_log if a["action"] == "ARCHIVE"]),
                "imports_cleaned": len([a for a in self.cleanup_log if a["action"] == "REMOVE_IMPORT"]),
                "cache_cleaned": len([a for a in self.cleanup_log if "cache" in a["target"].lower()]),
            }
        }
        
        if not self.dry_run:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2)
        
        self.log_action("CREATE", f"Cleanup report: {report_path.name}")
        
        # Print summary
        print(f"\n=== Cleanup Summary ===")
        print(f"Total actions: {report_data['total_actions']}")
        print(f"Files moved: {report_data['summary']['files_moved']}")
        print(f"Files removed: {report_data['summary']['files_removed']}")
        print(f"Files archived: {report_data['summary']['files_archived']}")
        print(f"Imports cleaned: {report_data['summary']['imports_cleaned']}")
        print(f"Cache files cleaned: {report_data['summary']['cache_cleaned']}")
        
        if self.dry_run:
            print("\n** DRY RUN COMPLETE - No actual changes made **")
        else:
            print(f"\n** CLEANUP COMPLETE - Backup created at: {self.backup_dir} **")
    
    def run_cleanup(self):
        """Run the complete cleanup process"""
        print(f"Starting comprehensive cleanup of: {self.project_root}")
        print(f"Dry run mode: {self.dry_run}")
        
        try:
            self.remove_redundant_root_files()
            self.clean_unused_imports()
            self.archive_old_logs()
            self.remove_cache_files()
            self.consolidate_documentation()
            self.update_gitignore()
            self.generate_cleanup_report()
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
            return False
        
        return True

def main():
    parser = argparse.ArgumentParser(description="Comprehensive Project Cleanup")
    parser.add_argument("--live", action="store_true", help="Execute cleanup (default is dry run)")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    
    args = parser.parse_args()
    
    project_root = os.path.abspath(args.project_root)
    dry_run = not args.live
    
    cleaner = ProjectCleaner(project_root, dry_run)
    success = cleaner.run_cleanup()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
