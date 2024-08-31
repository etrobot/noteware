import sys
import traceback

def read_and_execute_app():
    try:
        with open('app_template.py', 'r') as master_file:
            content = master_file.read()

    except Exception as e:
        print(f"Error reading app_master.py: {e}")
        return

    try:
        namespace = {}
        exec(content, namespace)
    except Exception as e:
        print("Error executing app_master.py content:")
        traceback.print_exc()

if __name__ == "__main__":
    read_and_execute_app()
