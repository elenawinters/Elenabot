import threading, subprocess, ast
from color import trace


class patch():  # most of this tech is taken from my Stitch project, and will probably be expanded upon here
    def __init__(self):
        [run(self) for run in util.hack_the_planet()]

    def check_for_package_updates():
        def in_thread():
            log.warn(f'{trace.warn}Checking for updates. This may take a minute.')
            pipreqs = subprocess.check_output([sys.executable, '-m', 'pip', 'list', '-o', '--format=json'])
            pipreqs = ast.literal_eval(pipreqs.decode("utf-8"))

            with open("requirements.txt", "r") as req_file:
                reqs = [re.split('<|=|>|~|!', line.strip())[0] for line in req_file]

            upd = [x for x in pipreqs for y in reqs if x['name'].lower() == y.lower()]
            log.warn(f"Found updates for '{len(upd)}' module(s).")
            [log.warn(f"{trace.warn}{x['name'].capitalize()} v{x['latest_version']} is available (v{x['version']} installed).") for x in upd]

        threading.Thread(target=in_thread, daemon=True, name='Updates').start()
