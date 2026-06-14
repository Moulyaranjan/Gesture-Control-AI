import mss
import os

os.makedirs("screenshots", exist_ok=True)


with mss.mss() as sct:
   sct.shot(output="screenshots/test.png")

print("Done")