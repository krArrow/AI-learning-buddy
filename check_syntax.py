#!/usr/bin/env python3
"""
Syntax and import checker for all Python files in the project
"""
import sys
from pathlib import Path
import py_compile
import importlib.util

def check_syntax():
    """Check syntax of all Python files"""
    print("=" * 70)
    print("SYNTAX CHECK - Compiling all Python files")
    print("=" * 70)
    
    src_dir = Path('src')
    py_files = list(src_dir.rglob('*.py'))
    
    print(f"\nFound {len(py_files)} Python files\n")
    
    syntax_errors = []
    
    for py_file in sorted(py_files):
        if '__pycache__' in str(py_file):
            continue
        
        try:
            py_compile.compile(str(py_file), doraise=True)
            print(f"✓ {py_file}")
        except py_compile.PyCompileError as e:
            syntax_errors.append((str(py_file), str(e)))
            print(f"✗ {py_file}: {str(e)[:80]}")
    
    print("\n" + "=" * 70)
    if syntax_errors:
        print(f"SYNTAX ERRORS FOUND: {len(syntax_errors)}")
        for file, error in syntax_errors:
            print(f"\n  {file}:")
            print(f"    {error}")
        return False
    else:
        print("✓ All files have valid syntax!")
        return True

def check_imports():
    """Check if all modules can be imported"""
    print("\n" + "=" * 70)
    print("IMPORT CHECK - Importing all modules")
    print("=" * 70)
    
    src_dir = Path('src')
    py_files = list(src_dir.rglob('*.py'))
    
    print(f"\nChecking {len(py_files)} modules...\n")
    
    import_errors = []
    
    for py_file in sorted(py_files):
        if '__pycache__' in str(py_file):
            continue
        
        if py_file.name == '__init__.py':
            continue
        
        module_path = str(py_file.relative_to('.')).replace('.py', '').replace('\\', '.')
        
        try:
            __import__(module_path)
            print(f"✓ {module_path}")
        except Exception as e:
            import_errors.append((module_path, str(e)))
            print(f"✗ {module_path}: {str(e)[:80]}")
    
    print("\n" + "=" * 70)
    if import_errors:
        print(f"IMPORT ERRORS FOUND: {len(import_errors)}")
        for module, error in import_errors:
            print(f"\n  {module}:")
            print(f"    {error}")
        return False
    else:
        print("✓ All modules can be imported successfully!")
        return True

def main():
    """Run all checks"""
    print("\n")
    syntax_ok = check_syntax()
    import_ok = check_imports()
    
    print("\n" + "=" * 70)
    print("FINAL RESULT")
    print("=" * 70)
    
    if syntax_ok and import_ok:
        print("✓ All checks passed!")
        print("Your project is ready for deployment.")
        return 0
    else:
        print("✗ Some checks failed. Please review the errors above.")
        if not syntax_ok:
            print("  - Fix syntax errors in the files listed above")
        if not import_ok:
            print("  - Fix import errors in the modules listed above")
        return 1

if __name__ == '__main__':
    sys.exit(main())
