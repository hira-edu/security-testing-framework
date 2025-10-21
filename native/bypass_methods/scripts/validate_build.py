#!/usr/bin/env python3
"""
Build System Validation Script for UndownUnlock

This script validates the build system configuration and checks for common issues
that could cause build failures or inconsistencies.
"""

import os
import sys
import subprocess
import json
import platform
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class BuildValidator:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.errors = []
        self.warnings = []
        self.success_count = 0
        
    def log_error(self, message: str):
        """Log an error message."""
        self.errors.append(f"❌ ERROR: {message}")
        print(f"❌ ERROR: {message}")
        
    def log_warning(self, message: str):
        """Log a warning message."""
        self.warnings.append(f"⚠️  WARNING: {message}")
        print(f"⚠️  WARNING: {message}")
        
    def log_success(self, message: str):
        """Log a success message."""
        self.success_count += 1
        print(f"✅ SUCCESS: {message}")
        
    def check_cmake_files(self) -> bool:
        """Check CMake configuration files for issues."""
        print("\n=== Checking CMake Configuration ===")
        
        # Check main CMakeLists.txt
        main_cmake = self.project_root / "CMakeLists.txt"
        if not main_cmake.exists():
            self.log_error("Main CMakeLists.txt not found")
            return False
            
        self.log_success("Main CMakeLists.txt found")
        
        # Check tests CMakeLists.txt
        tests_cmake = self.project_root / "tests" / "CMakeLists.txt"
        if not tests_cmake.exists():
            self.log_error("tests/CMakeLists.txt not found")
            return False
            
        self.log_success("tests/CMakeLists.txt found")
        
        # Check for project() declaration in tests CMakeLists.txt
        with open(tests_cmake, 'r') as f:
            content = f.read()
            if 'project(' not in content:
                self.log_error("Missing project() declaration in tests/CMakeLists.txt")
                return False
                
        self.log_success("Project declaration found in tests/CMakeLists.txt")
        
        return True
        
    def check_source_files(self) -> bool:
        """Check that source files referenced in CMake exist."""
        print("\n=== Checking Source Files ===")
        
        # Read main CMakeLists.txt to extract source files
        main_cmake = self.project_root / "CMakeLists.txt"
        with open(main_cmake, 'r') as f:
            content = f.read()
            
        # Extract source file lists
        source_patterns = [
            r'set\(DLL_HOOKS_SOURCES\s*([^)]+)\)',
            r'set\(TEST_CLIENT_SOURCES\s*([^)]+)\)'
        ]
        
        import re
        for pattern in source_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                # Extract individual file paths
                files = re.findall(r'src/[^\s)]+', match)
                for file_path in files:
                    full_path = self.project_root / file_path
                    if not full_path.exists():
                        self.log_error(f"Source file not found: {file_path}")
                        return False
                    else:
                        self.log_success(f"Source file found: {file_path}")
                        
        return True
        
    def check_dependencies(self) -> bool:
        """Check dependency configuration."""
        print("\n=== Checking Dependencies ===")
        
        # Check Python requirements files
        requirements_files = [
            "python/requirements/requirements.txt",
            "python/requirements/requirements_accessibility.txt"
        ]
        
        for req_file in requirements_files:
            req_path = self.project_root / req_file
            if not req_path.exists():
                self.log_warning(f"Requirements file not found: {req_file}")
            else:
                self.log_success(f"Requirements file found: {req_file}")
                
        # Check for duplicate FetchContent declarations
        main_cmake = self.project_root / "CMakeLists.txt"
        tests_cmake = self.project_root / "tests" / "CMakeLists.txt"
        
        with open(main_cmake, 'r') as f:
            main_content = f.read()
            
        with open(tests_cmake, 'r') as f:
            tests_content = f.read()
            
        # Check for duplicate googletest declarations
        if 'FetchContent_Declare' in main_content and 'FetchContent_Declare' in tests_content:
            self.log_warning("Duplicate FetchContent declarations detected")
            
        return True
        
    def check_build_environment(self) -> bool:
        """Check build environment requirements."""
        print("\n=== Checking Build Environment ===")
        
        # Check CMake version
        try:
            result = subprocess.run(['cmake', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                self.log_success(f"CMake found: {version_line}")
            else:
                self.log_error("CMake not found or not working")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.log_error("CMake not found in PATH")
            return False
            
        # Check platform
        system = platform.system()
        if system == "Windows":
            self.log_success("Running on Windows (supported platform)")
        else:
            self.log_warning(f"Running on {system} (may have compatibility issues)")
            
        # Check Visual Studio (Windows only)
        if system == "Windows":
            try:
                result = subprocess.run(['where', 'cl'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    self.log_success("Visual Studio compiler found")
                else:
                    self.log_warning("Visual Studio compiler not found")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                self.log_warning("Visual Studio compiler not found")
                
        return True
        
    def check_directory_structure(self) -> bool:
        """Check that required directories exist."""
        print("\n=== Checking Directory Structure ===")
        
        required_dirs = [
            "src",
            "include", 
            "tests",
            "python",
            "docs",
            "scripts"
        ]
        
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                self.log_error(f"Required directory not found: {dir_name}")
                return False
            else:
                self.log_success(f"Directory found: {dir_name}")
                
        return True
        
    def check_visual_studio_project(self) -> bool:
        """Check Visual Studio project files."""
        print("\n=== Checking Visual Studio Project ===")
        
        vs_project = self.project_root / "DLLHooks" / "DLLHooks.vcxproj"
        if not vs_project.exists():
            self.log_warning("Visual Studio project file not found")
        else:
            self.log_success("Visual Studio project file found")
            
        return True
        
    def run_validation(self) -> bool:
        """Run all validation checks."""
        print("🔍 UndownUnlock Build System Validation")
        print("=" * 50)
        
        checks = [
            self.check_directory_structure,
            self.check_cmake_files,
            self.check_source_files,
            self.check_dependencies,
            self.check_build_environment,
            self.check_visual_studio_project
        ]
        
        all_passed = True
        for check in checks:
            if not check():
                all_passed = False
                
        # Print summary
        print("\n" + "=" * 50)
        print("📊 VALIDATION SUMMARY")
        print("=" * 50)
        print(f"✅ Successful checks: {self.success_count}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print(f"❌ Errors: {len(self.errors)}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  {warning}")
                
        if self.errors:
            print("\n❌ ERRORS:")
            for error in self.errors:
                print(f"  {error}")
                
        if all_passed:
            print("\n🎉 All validation checks passed!")
        else:
            print("\n💥 Validation failed. Please fix the errors above.")
            
        return all_passed
        
    def generate_report(self, output_file: str = "build_validation_report.json"):
        """Generate a JSON report of the validation results."""
        report = {
            "timestamp": str(Path().cwd()),
            "project_root": str(self.project_root),
            "platform": platform.system(),
            "success_count": self.success_count,
            "warnings": self.warnings,
            "errors": self.errors,
            "overall_success": len(self.errors) == 0
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\n📄 Report saved to: {output_file}")

def main():
    """Main function."""
    validator = BuildValidator()
    success = validator.run_validation()
    
    # Generate report
    validator.generate_report()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 