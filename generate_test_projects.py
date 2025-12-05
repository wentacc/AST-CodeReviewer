import os
import glob
import re

DATA_DIR = "./data/python-commits/merged"
OUTPUT_DIR = "./generated_projects"
MAX_FILES = 50

def is_python_code(content):
    """
    Heuristic to check if content is Python code.
    """
    # Check for common Python keywords
    if re.search(r'^\s*(import|from)\s+\w+', content, re.MULTILINE):
        return True
    if re.search(r'^\s*def\s+\w+\(', content, re.MULTILINE):
        return True
    if re.search(r'^\s*class\s+\w+', content, re.MULTILINE):
        return True
        
    # Check for C# indicators to exclude
    if re.search(r'^\s*using\s+System', content, re.MULTILINE):
        return False
    if re.search(r'^\s*namespace\s+\w+', content, re.MULTILINE):
        return False
        
    return False

def generate_projects():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    context_files = glob.glob(os.path.join(DATA_DIR, "*-context.txt"))
    count = 0
    
    print(f"Scanning {len(context_files)} files...")
    
    for file_path in context_files:
        if count >= MAX_FILES:
            break
            
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                
            if is_python_code(content):
                # Double check it's not C# (IronPython case)
                if "using System" in content or "namespace " in content:
                    continue
                    
                filename = f"sample_{count + 1}.py"
                output_path = os.path.join(OUTPUT_DIR, filename)
                
                with open(output_path, "w") as f:
                    f.write(content)
                    
                print(f"Generated: {filename} from {os.path.basename(file_path)}")
                count += 1
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            
    print(f"Done. Generated {count} Python files in {OUTPUT_DIR}")

if __name__ == "__main__":
    generate_projects()
