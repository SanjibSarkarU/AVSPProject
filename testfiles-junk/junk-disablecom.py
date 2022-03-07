

import subprocess
# Fetches the list of all usb devices:
result = subprocess.run(['devcon', 'hwids', '=usb'],  capture_output=True, text=True)

print(result)