import os

def check_password(p):
    # Hardcoded password - Security Issue
    secret = "supersecret"
    if p == secret:
        return True
    return False

def run_command(cmd):
    # Eval - Security Issue
    eval(cmd)

class MyClass:
    def foo(self):
        # Missing docstring - Doc Issue
        x = 5
        if x = 5: # Bug Issue (assignment in condition)
            print("Five")
        
    def bad_style(self):
    	print("Tab indentation") # Style Issue
