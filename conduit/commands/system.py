from conduit.commands.path import CONFIG_DIR
import os

file = os.path.join(CONFIG_DIR,"system.prompt")

def run(args):
    prompt = ""
    print("Input your prompt: (exit for exiting)")
    try:
        while True:
            line = input("")
            if line == "exit":
                break

            prompt = line + "\n"
            
        if os.path.exists(file):
            if input("this will override the previous prompt.\n Confirm (Y|n):") == "Y":
                pass
            else:
                print("Cancelled by user!")
                return

    except KeyboardInterrupt:
        print("Exited!")
        return
    
    open(file, "w").write(prompt)
