import os
import importlib.util
import argparse

from test_specs import test_specifications

def get_src_files(root_dir="src"):
    '''
    Recursively find all .py files in src/ and return relative paths
    
    in : root directory (default: "src")
    out: list of relative paths to source files
    '''
    src_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".py") and filename != "__init__.py":
                rel_path = os.path.relpath(os.path.join(dirpath, filename), root_dir)
                src_files.append(rel_path.replace(".py", "").replace(os.sep, "/"))
    return src_files

def get_test_files(root_dir="tests"):
    '''
    Recursively find all test_*.py files in tests/ and return relative paths
    
    in : root directory (default: "tests")
    out: list of relative paths to test files
    '''
    test_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.startswith("test_") and filename.endswith(".py"):
                rel_path = os.path.relpath(os.path.join(dirpath, filename), root_dir)
                test_files.append(rel_path.replace(".py", "").replace("test_", "").replace(os.sep, "/"))
    return test_files

def validate_function(src_path, function_name, verbose=False):
    '''
    Check if the function exists in the source file
    
    in : source file path, function name to validate, verbose flag (default: False)
    out: boolean indicating if function exists
    '''
    full_src_path = os.path.join("src", f"{src_path}.py")
    if not os.path.exists(full_src_path):
        return False
    
    spec = importlib.util.spec_from_file_location(src_path.replace("/", "."), full_src_path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        exists = hasattr(module, function_name)
        if verbose and not exists:
            print(f"Warning: {function_name} not found in {full_src_path}")
        return exists
    except Exception as e:
        if verbose:
            print(f"Error loading {full_src_path}: {e}")
        return False

def generate_test_file(src_path, specs, force=False, verbose=False):
    '''
    Generate test file for given src path based on specs
    
    in : source file path, test specifications, force flag (default: False), verbose flag (default: False)
    out: None
    '''
    test_dir = os.path.join("tests", os.path.dirname(src_path))
    test_filename = f"test_{os.path.basename(src_path)}.py"
    test_filepath = os.path.join(test_dir, test_filename)

    if os.path.exists(test_filepath) and not force:
        if verbose:
            print(f"Skipping {test_filepath} (already exists)")
        return

    function_name = specs["function_name"]
    if not validate_function(src_path, function_name, verbose):
        print(f"Error: {function_name} not found in src/{src_path}.py, skipping")
        return

    os.makedirs(test_dir, exist_ok=True)

    # Generate test content
    import_path = f"src.{src_path.replace('/', '.')}"
    test_cases = specs["test_cases"]
    content = f"from {import_path} import {function_name}\n\n"
    for i, case in enumerate(test_cases):
        input_args = ", ".join(f"{k}={repr(v)}" for k, v in case['input'].items())
        output = repr(case['output'])
        content += f"def test_case_{i}():\n"
        content += f"    assert {function_name}({input_args}) == {output}\n\n"

    with open(test_filepath, "w") as f:
        f.write(content)
    print(f"{'Regenerated' if force and os.path.exists(test_filepath) else 'Generated'} {test_filepath}")

def clean_orphaned_tests(src_files, verbose=False):
    '''
    Remove test files that no longer have a corresponding source file
    
    in : list of source file paths, verbose flag (default: False)
    out: None
    '''
    test_files = get_test_files()
    for test_path in test_files:
        if test_path not in src_files:
            test_filepath = os.path.join("tests", f"{test_path}.py")
            if os.path.exists(test_filepath):
                os.remove(test_filepath)
                print(f"Removed orphaned test file: {test_filepath}")
            elif verbose:
                print(f"Test file {test_filepath} already removed")

def main():
    '''
    Main function to orchestrate test file generation
    
    in : None (parses command-line arguments)
    out: None
    '''
    parser = argparse.ArgumentParser(description="Generate test files for NeetCode problems")
    parser.add_argument("--force", action="store_true", help="Force regeneration of existing test files")
    parser.add_argument("--verbose", action="store_true", help="Print detailed output")
    args = parser.parse_args()

    src_files = get_src_files()
    if args.verbose:
        print(f"Found source files: {src_files}")

    clean_orphaned_tests(src_files, args.verbose)

    # Generate tests for each source file with specs
    for src_path in src_files:
        if src_path in test_specifications:
            generate_test_file(src_path, test_specifications[src_path], args.force, args.verbose)
        elif args.verbose:
            print(f"No test specs found for src/{src_path}.py")

if __name__ == "__main__":
    main()