#!/usr/bin/env python3
"""
JARVIS Project Cleanup Script
Safely removes identified unnecessary files and reorganizes structure
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

class ProjectCleaner:
    """Safe cleanup utility for JARVIS AI project"""
    
    def __init__(self, project_root: str = None, dry_run: bool = True):
        self.project_root = Path(project_root or os.getcwd())
        self.dry_run = dry_run
        self.backup_dir = self.project_root / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.log = []
        self.stats = {
            "files_deleted": 0,
            "dirs_deleted": 0,
            "files_moved": 0,
            "space_freed": 0
        }
        
    def log_action(self, action: str, target: str, status: str = "SUCCESS"):
        """Log cleanup actions"""
        entry = f"[{status}] {action}: {target}"
        self.log.append(entry)
        if not self.dry_run or status == "INFO":
            print(entry)
    
    def calculate_size(self, path: Path) -> int:
        """Calculate size of file or directory in bytes"""
        if path.is_file():
            return path.stat().st_size
        elif path.is_dir():
            total = 0
            for item in path.rglob('*'):
                if item.is_file():
                    total += item.stat().st_size
            return total
        return 0
    
    def backup_file(self, file_path: Path):
        """Backup a file before deletion"""
        if not self.dry_run:
            relative_path = file_path.relative_to(self.project_root)
            backup_path = self.backup_dir / relative_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, backup_path)
            self.log_action("BACKUP", str(relative_path))
    
    def clean_pycache(self) -> Tuple[int, int]:
        """Remove all __pycache__ directories and .pyc files"""
        self.log_action("INFO", "Cleaning Python cache files", "INFO")
        
        pycache_count = 0
        pyc_count = 0
        
        # Find and remove __pycache__ directories
        for pycache_dir in self.project_root.rglob('__pycache__'):
            size = self.calculate_size(pycache_dir)
            if not self.dry_run:
                shutil.rmtree(pycache_dir)
            self.log_action("DELETE_DIR", str(pycache_dir.relative_to(self.project_root)))
            self.stats["dirs_deleted"] += 1
            self.stats["space_freed"] += size
            pycache_count += 1
        
        # Find and remove .pyc files
        for pyc_file in self.project_root.rglob('*.pyc'):
            size = pyc_file.stat().st_size
            if not self.dry_run:
                pyc_file.unlink()
            self.log_action("DELETE_FILE", str(pyc_file.relative_to(self.project_root)))
            self.stats["files_deleted"] += 1
            self.stats["space_freed"] += size
            pyc_count += 1
        
        return pycache_count, pyc_count
    
    def clean_logs_and_temp(self) -> List[str]:
        """Remove temporary files and logs"""
        self.log_action("INFO", "Cleaning temporary files and logs", "INFO")
        
        temp_files = [
            "gpu_stats.log",
            "dxdiag_output.txt",
            "test_screenshot.png"
        ]
        
        cleaned = []
        for temp_file in temp_files:
            file_path = self.project_root / temp_file
            if file_path.exists():
                size = file_path.stat().st_size
                self.backup_file(file_path)  # Backup before deletion
                if not self.dry_run:
                    file_path.unlink()
                self.log_action("DELETE_FILE", temp_file)
                self.stats["files_deleted"] += 1
                self.stats["space_freed"] += size
                cleaned.append(temp_file)
        
        return cleaned
    
    def clean_empty_dirs(self) -> List[str]:
        """Remove empty directories"""
        self.log_action("INFO", "Removing empty directories", "INFO")
        
        empty_dirs = []
        dirs_to_check = ["cache", "logs"]
        
        for dir_name in dirs_to_check:
            # Check root level
            dir_path = self.project_root / dir_name
            if dir_path.exists() and dir_path.is_dir() and not any(dir_path.iterdir()):
                if not self.dry_run:
                    dir_path.rmdir()
                self.log_action("DELETE_DIR", dir_name)
                self.stats["dirs_deleted"] += 1
                empty_dirs.append(str(dir_path))
        
        # Check service cache directories
        for cache_dir in self.project_root.glob("services/*/cache"):
            if cache_dir.is_dir() and not any(cache_dir.iterdir()):
                if not self.dry_run:
                    cache_dir.rmdir()
                self.log_action("DELETE_DIR", str(cache_dir.relative_to(self.project_root)))
                self.stats["dirs_deleted"] += 1
                empty_dirs.append(str(cache_dir))
        
        return empty_dirs
    
    def reorganize_tests(self) -> Dict[str, str]:
        """Move test files from root to proper test directory"""
        self.log_action("INFO", "Reorganizing test files", "INFO")
        
        test_files_at_root = [
            "test_conversation.py",
            "test_conversation_demo.py",
            "test_simple_conversation.py",
            "test_gpu_integration.py",
            "test_gpu_service_direct.py",
            "test_gpu_simple.py",
            "test_personas.py"
        ]
        
        moved = {}
        target_dir = self.project_root / "tests" / "integration"
        
        if not self.dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)
        
        for test_file in test_files_at_root:
            source = self.project_root / test_file
            if source.exists():
                destination = target_dir / test_file
                
                # Check if file already exists in destination
                if destination.exists():
                    self.log_action("SKIP", f"{test_file} (already exists in target)", "WARNING")
                    # Rename the root file to .old for safety
                    if not self.dry_run:
                        old_path = source.with_suffix('.py.old')
                        source.rename(old_path)
                    moved[test_file] = "renamed to .old (duplicate found)"
                else:
                    if not self.dry_run:
                        shutil.move(str(source), str(destination))
                    self.log_action("MOVE", f"{test_file} -> tests/integration/")
                    self.stats["files_moved"] += 1
                    moved[test_file] = str(destination.relative_to(self.project_root))
        
        return moved
    
    def update_gitignore(self):
        """Update .gitignore with proper patterns"""
        self.log_action("INFO", "Updating .gitignore", "INFO")
        
        gitignore_path = self.project_root / ".gitignore"
        
        patterns_to_add = [
            "\n# Python",
            "__pycache__/",
            "*.py[cod]",
            "*$py.class",
            "*.pyc",
            "\n# Logs",
            "*.log",
            "logs/",
            "\n# Cache",
            "cache/",
            ".cache/",
            "\n# Test artifacts",
            "test_screenshot.png",
            "dxdiag_output.txt",
            "\n# IDE",
            ".vscode/",
            ".idea/",
            "*.swp",
            "*.swo",
            "\n# Virtual Environment",
            "venv/",
            "env/",
            ".env",
            "\n# Database",
            "*.sqlite3",
            "*.db",
            "\n# Temporary",
            "*.tmp",
            "*.temp",
            "*.old"
        ]
        
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                current_content = f.read()
        else:
            current_content = ""
        
        patterns_needed = []
        for pattern in patterns_to_add:
            if pattern not in current_content:
                patterns_needed.append(pattern)
        
        if patterns_needed and not self.dry_run:
            with open(gitignore_path, 'a') as f:
                f.write("\n" + "\n".join(patterns_needed))
            self.log_action("UPDATE", ".gitignore with missing patterns")
    
    def generate_report(self) -> str:
        """Generate cleanup report"""
        report = [
            "=" * 60,
            "JARVIS PROJECT CLEANUP REPORT",
            "=" * 60,
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Mode: {'DRY RUN' if self.dry_run else 'ACTUAL CLEANUP'}",
            "",
            "STATISTICS:",
            f"  Files deleted: {self.stats['files_deleted']}",
            f"  Directories deleted: {self.stats['dirs_deleted']}",
            f"  Files moved: {self.stats['files_moved']}",
            f"  Space freed: {self.stats['space_freed'] / 1024 / 1024:.2f} MB",
            "",
            "ACTIONS LOG:",
        ]
        report.extend(self.log)
        
        return "\n".join(report)
    
    def run_cleanup(self):
        """Execute the complete cleanup process"""
        print("=" * 60)
        print(f"JARVIS PROJECT CLEANUP - {'DRY RUN' if self.dry_run else 'ACTUAL'}")
        print("=" * 60)
        
        if not self.dry_run:
            print(f"Creating backup directory: {self.backup_dir}")
            self.backup_dir.mkdir(exist_ok=True)
        
        # Execute cleanup steps
        pycache_count, pyc_count = self.clean_pycache()
        print(f"  Python cache: {pycache_count} __pycache__ dirs, {pyc_count} .pyc files")
        
        temp_cleaned = self.clean_logs_and_temp()
        print(f"  Temporary files: {len(temp_cleaned)} files")
        
        empty_cleaned = self.clean_empty_dirs()
        print(f"  Empty directories: {len(empty_cleaned)} dirs")
        
        tests_moved = self.reorganize_tests()
        print(f"  Test files reorganized: {len(tests_moved)} files")
        
        self.update_gitignore()
        print("  .gitignore updated")
        
        # Generate and save report
        report = self.generate_report()
        
        if not self.dry_run:
            report_path = self.project_root / f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(report_path, 'w') as f:
                f.write(report)
            print(f"\nReport saved to: {report_path}")
        
        print("\n" + "=" * 60)
        print(f"CLEANUP {'SIMULATION' if self.dry_run else 'COMPLETE'}")
        print(f"Space {'would be' if self.dry_run else ''} freed: {self.stats['space_freed'] / 1024 / 1024:.2f} MB")
        print("=" * 60)
        
        return report


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up JARVIS AI project")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually perform cleanup (default is dry run)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt (use with --execute)"
    )
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Project root path (default: current directory)"
    )
    
    args = parser.parse_args()
    
    cleaner = ProjectCleaner(
        project_root=args.path,
        dry_run=not args.execute
    )
    
    if not args.execute:
        print("\n[WARNING] This is a DRY RUN - no files will be modified")
        print("Use --execute flag to perform actual cleanup\n")
    else:
        if not args.force:
            response = input("\n[WARNING] This will modify files. Are you sure? (yes/no): ")
            if response.lower() != 'yes':
                print("Cleanup cancelled.")
                return
        else:
            print("\n[WARNING] Force mode enabled - executing cleanup...")
    
    cleaner.run_cleanup()


if __name__ == "__main__":
    main()