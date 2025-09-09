#!/usr/bin/env python3
"""
Strict Template & Design System Validator
ZERO TOLERANCE enforcement of template and CSS standards

This script BLOCKS any violations and provides detailed error reports.
"""

import os
import re
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class ViolationLevel(Enum):
    CRITICAL = "CRITICAL"  # Blocks everything
    ERROR = "ERROR"        # Must fix to proceed
    WARNING = "WARNING"    # Should fix

@dataclass
class Violation:
    level: ViolationLevel
    file: str
    line: Optional[int]
    message: str
    pattern: str
    suggestion: str

class StrictValidator:
    """Ultra-strict validator with zero tolerance for violations"""
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path).resolve()
        self.violations: List[Violation] = []
        self.setup_forbidden_patterns()
        
    def setup_forbidden_patterns(self):
        """Define all forbidden CSS and HTML patterns"""
        self.css_forbidden = [
            # Inline styles
            (r'style\s*=\s*["\'][^"\']*["\']', "Inline styles are forbidden", "Use CSS classes instead"),
            
            # Hex colors
            (r'#[0-9a-fA-F]{3,6}', "Hex colors forbidden", "Use var(--color-name) instead"),
            
            # RGB/RGBA colors
            (r'rgba?\s*\([^)]+\)', "RGB/RGBA colors forbidden", "Use CSS variables instead"),
            
            # HSL colors
            (r'hsla?\s*\([^)]+\)', "HSL colors forbidden", "Use CSS variables instead"),
            
            # Direct pixel values
            (r'[^-]\d+px', "Direct pixel values forbidden", "Use var(--space-X) instead"),
            
            # Important flags
            (r'!important', "!important flags forbidden", "Fix CSS specificity instead"),
            
            # Custom CSS variables
            (r'--[a-zA-Z][a-zA-Z0-9-]*\s*:', "Custom CSS variables forbidden", "Use design-system variables only"),
            
            # External fonts
            (r'@import[^;]*fonts\.googleapis\.com', "External fonts forbidden", "Use var(--font-sans) or var(--font-mono)"),
            (r'@font-face', "Custom fonts forbidden", "Use system fonts only"),
            
            # Specific color names
            (r'\b(red|blue|green|yellow|orange|purple|black|white|gray|grey)\b', "Color names forbidden", "Use CSS variables"),
            
            # Bootstrap/External CSS
            (r'bootstrap|tailwind|bulma|foundation', "External CSS frameworks forbidden", "Use components.css only"),
        ]
        
        self.html_forbidden = [
            # Wrong CSS import order
            (r'components\.css.*design-system\.css', "Wrong CSS import order", "design-system.css must come first"),
            
            # Missing CSS imports
            (r'<link[^>]*design-system\.css[^>]*>', "Missing design-system.css", "Add required CSS imports"),
            
            # External CSS
            (r'<link[^>]*(?:bootstrap|tailwind|cdn\.)', "External CSS forbidden", "Remove external stylesheets"),
        ]
        
        self.protected_files = [
            "shared/design-system.css",
            "shared/components.css",
            ".claude/agents/*.md",
            "clone-template.sh",
            "service-manager.sh"
        ]

    def validate_project(self) -> bool:
        """Run complete project validation"""
        print("🔍 STRICT VALIDATION STARTING")
        print("=" * 50)
        
        # Step 1: Location validation
        if not self.validate_location():
            return False
            
        # Step 2: Structure validation
        if not self.validate_structure():
            return False
            
        # Step 3: CSS validation
        if not self.validate_css_files():
            return False
            
        # Step 4: HTML validation
        if not self.validate_html_files():
            return False
            
        # Step 5: Protected files validation
        if not self.validate_protected_files():
            return False
            
        # Report results
        return self.report_results()

    def validate_location(self) -> bool:
        """Validate project is in correct location"""
        github_path = "/Documents/GitHub/"
        if github_path not in str(self.project_path):
            self.add_violation(
                ViolationLevel.CRITICAL,
                str(self.project_path),
                None,
                f"Project MUST be in GitHub directory",
                "Location validation",
                f"Move project to path containing {github_path}"
            )
            return False
        return True

    def validate_structure(self) -> bool:
        """Validate required project structure"""
        required_dirs = ["backend", "frontend", "shared", "docs"]
        required_files = [
            "start.sh",
            "backend/api.py",
            "backend/storage.py", 
            "frontend/index.html",
            "shared/design-system.css",
            "shared/components.css",
            ".env.example"
        ]
        
        valid = True
        
        for dir_name in required_dirs:
            dir_path = self.project_path / dir_name
            if not dir_path.exists():
                self.add_violation(
                    ViolationLevel.CRITICAL,
                    str(dir_path),
                    None,
                    f"Required directory missing: {dir_name}",
                    "Structure validation",
                    f"Create directory: {dir_name}"
                )
                valid = False
                
        for file_name in required_files:
            file_path = self.project_path / file_name
            if not file_path.exists():
                self.add_violation(
                    ViolationLevel.CRITICAL,
                    str(file_path),
                    None,
                    f"Required file missing: {file_name}",
                    "Structure validation",
                    f"Create file: {file_name}"
                )
                valid = False
                
        return valid

    def validate_css_files(self) -> bool:
        """Validate all CSS files for forbidden patterns"""
        css_files = list(self.project_path.glob("**/*.css"))
        valid = True
        
        for css_file in css_files:
            if not self.validate_css_content(css_file):
                valid = False
                
        return valid

    def validate_css_content(self, file_path: Path) -> bool:
        """Validate individual CSS file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
            valid = True
            
            for line_num, line in enumerate(lines, 1):
                for pattern, message, suggestion in self.css_forbidden:
                    if re.search(pattern, line, re.IGNORECASE):
                        self.add_violation(
                            ViolationLevel.CRITICAL,
                            str(file_path),
                            line_num,
                            message,
                            pattern,
                            suggestion
                        )
                        valid = False
                        
        except Exception as e:
            self.add_violation(
                ViolationLevel.ERROR,
                str(file_path),
                None,
                f"Could not read CSS file: {e}",
                "File access",
                "Fix file permissions or encoding"
            )
            return False
            
        return valid

    def validate_html_files(self) -> bool:
        """Validate all HTML files"""
        html_files = list(self.project_path.glob("**/*.html"))
        valid = True
        
        for html_file in html_files:
            if not self.validate_html_content(html_file):
                valid = False
                
        return valid

    def validate_html_content(self, file_path: Path) -> bool:
        """Validate individual HTML file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            valid = True
            
            # Check CSS import order
            css_imports = re.findall(r'<link[^>]*\.css[^>]*>', content)
            if len(css_imports) >= 2:
                design_system_pos = -1
                components_pos = -1
                
                for i, import_tag in enumerate(css_imports):
                    if 'design-system.css' in import_tag:
                        design_system_pos = i
                    elif 'components.css' in import_tag:
                        components_pos = i
                        
                if design_system_pos > components_pos and components_pos != -1:
                    self.add_violation(
                        ViolationLevel.CRITICAL,
                        str(file_path),
                        None,
                        "Wrong CSS import order - design-system.css must come before components.css",
                        "CSS import order",
                        "Reorder CSS imports: design-system.css, then components.css"
                    )
                    valid = False
            
            # Check for inline styles
            if 'style="' in content or "style='" in content:
                self.add_violation(
                    ViolationLevel.CRITICAL,
                    str(file_path),
                    None,
                    "Inline styles detected",
                    "style attribute",
                    "Remove all inline styles, use CSS classes instead"
                )
                valid = False
                
            # Check for external CSS frameworks
            forbidden_frameworks = ['bootstrap', 'tailwind', 'bulma', 'foundation']
            for framework in forbidden_frameworks:
                if framework in content.lower():
                    self.add_violation(
                        ViolationLevel.CRITICAL,
                        str(file_path),
                        None,
                        f"External CSS framework detected: {framework}",
                        f"{framework} framework",
                        "Remove external frameworks, use components.css only"
                    )
                    valid = False
                    
        except Exception as e:
            self.add_violation(
                ViolationLevel.ERROR,
                str(file_path),
                None,
                f"Could not read HTML file: {e}",
                "File access",
                "Fix file permissions or encoding"
            )
            return False
            
        return valid

    def validate_protected_files(self) -> bool:
        """Check if any protected files have been modified"""
        valid = True
        
        # Check if git exists
        if not (self.project_path / '.git').exists():
            return valid
            
        try:
            # Check git status for protected file modifications
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                modified_files = result.stdout.strip().split('\n')
                for file_line in modified_files:
                    if file_line.strip():
                        file_path = file_line[3:]  # Remove git status prefix
                        if any(file_path.startswith(protected) for protected in self.protected_files):
                            self.add_violation(
                                ViolationLevel.CRITICAL,
                                file_path,
                                None,
                                f"Protected file has been modified: {file_path}",
                                "Protected file modification",
                                f"Revert changes to {file_path}"
                            )
                            valid = False
                            
        except Exception as e:
            # Git not available or other error - skip protected file check
            pass
            
        return valid

    def add_violation(self, level: ViolationLevel, file: str, line: Optional[int], 
                     message: str, pattern: str, suggestion: str):
        """Add a violation to the list"""
        self.violations.append(Violation(level, file, line, message, pattern, suggestion))

    def report_results(self) -> bool:
        """Generate detailed violation report"""
        print("\n" + "=" * 50)
        print("STRICT VALIDATION RESULTS")
        print("=" * 50)
        
        if not self.violations:
            print("🎉 PROJECT IS FULLY COMPLIANT!")
            print("✅ All validation checks passed")
            return True
            
        # Group violations by level
        critical = [v for v in self.violations if v.level == ViolationLevel.CRITICAL]
        errors = [v for v in self.violations if v.level == ViolationLevel.ERROR]
        warnings = [v for v in self.violations if v.level == ViolationLevel.WARNING]
        
        # Report critical violations
        if critical:
            print(f"\n🚨 CRITICAL VIOLATIONS ({len(critical)}) - BLOCKS ALL DEVELOPMENT:")
            for v in critical:
                print(f"  ❌ {v.file}{f':{v.line}' if v.line else ''}")
                print(f"     {v.message}")
                print(f"     Fix: {v.suggestion}")
                print()
                
        # Report errors
        if errors:
            print(f"\n❌ ERRORS ({len(errors)}):")
            for v in errors:
                print(f"  ❌ {v.file}{f':{v.line}' if v.line else ''}")
                print(f"     {v.message}")
                print(f"     Fix: {v.suggestion}")
                print()
                
        # Report warnings
        if warnings:
            print(f"\n⚠️  WARNINGS ({len(warnings)}):")
            for v in warnings:
                print(f"  ⚠️  {v.file}{f':{v.line}' if v.line else ''}")
                print(f"     {v.message}")
                print(f"     Fix: {v.suggestion}")
                print()
        
        # Final verdict
        print("=" * 50)
        if critical or errors:
            print("❌ VALIDATION FAILED")
            print("Project is NOT compliant and is BLOCKED")
            print("Fix all CRITICAL and ERROR violations to proceed")
            return False
        else:
            print("✅ VALIDATION PASSED (with warnings)")
            print("Project is compliant but has warnings")
            return True

    def save_report(self, output_file: str = "validation-report.json"):
        """Save detailed JSON report"""
        report = {
            "project_path": str(self.project_path),
            "total_violations": len(self.violations),
            "critical_count": len([v for v in self.violations if v.level == ViolationLevel.CRITICAL]),
            "error_count": len([v for v in self.violations if v.level == ViolationLevel.ERROR]),
            "warning_count": len([v for v in self.violations if v.level == ViolationLevel.WARNING]),
            "violations": [
                {
                    "level": v.level.value,
                    "file": v.file,
                    "line": v.line,
                    "message": v.message,
                    "pattern": v.pattern,
                    "suggestion": v.suggestion
                }
                for v in self.violations
            ]
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"📄 Detailed report saved to: {output_file}")

def main():
    """Main validation entry point"""
    project_path = sys.argv[1] if len(sys.argv) > 1 else "."
    
    validator = StrictValidator(project_path)
    
    print("🔒 STRICT TEMPLATE & CSS VALIDATOR")
    print("🚨 ZERO TOLERANCE ENFORCEMENT")
    print()
    
    is_valid = validator.validate_project()
    
    # Save detailed report
    validator.save_report()
    
    # Exit with appropriate code
    if is_valid:
        print("\n✅ VALIDATION SUCCESSFUL")
        sys.exit(0)
    else:
        print("\n❌ VALIDATION FAILED - DEVELOPMENT BLOCKED")
        sys.exit(1)

if __name__ == "__main__":
    main()