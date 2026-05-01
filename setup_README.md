**TrashWatch**

Setup Guide for Claude in VS Code

Real-time trash detection using YOLOv8 + Supabase + Streamlit

**What You Are Building**

A live trash detection web app that:

- Detects trash objects (bottles, cups, bags, food waste, etc.) in real-time via laptop webcam or mobile camera

- Draws green bounding boxes with labels and confidence scores on the video feed

- Plays an alert sound whenever trash is detected

- Saves a snapshot image to Supabase cloud storage

- Logs every detection (label, confidence, timestamp, camera source) to a Supabase database

- Shows a live dashboard with charts, detection history, and downloadable logs

- Deploys to Streamlit Cloud so you can access it from any browser

**Files Provided**

|                             |                                                                      |
|-----------------------------|----------------------------------------------------------------------|
| **File**                    | **Purpose**                                                          |
| **app.py**                  | Main Streamlit application --- all detection, UI, and database logic |
| **requirements.txt**        | Python packages to install                                           |
| **supabase_setup.sql**      | SQL to run once in Supabase to create the database table             |
| **.streamlit/secrets.toml** | Template for your Supabase credentials (fill this in)                |
| **.gitignore**              | Prevents secrets from being pushed to GitHub                         |

**Prerequisites**

**Install on your machine**

- Python 3.9 or higher --- download from python.org

- pip (comes with Python)

- VS Code --- download from code.visualstudio.com

- Git --- download from git-scm.com

**Accounts to create (all free)**

- Supabase --- supabase.com (free tier, no credit card)

- GitHub --- github.com (to deploy to Streamlit Cloud)

- Streamlit Cloud --- share.streamlit.io (free, sign in with GitHub)

**Optional --- for mobile camera**

- Android phone with IP Webcam app (free on Play Store)

**Step 1 --- Set Up the Project Folder**

1.  Open VS Code

2.  Open Terminal inside VS Code: press Ctrl + \` (backtick) or go to Terminal \> New Terminal

3.  Create a new folder and navigate into it:

> mkdir trashwatch
>
> cd trashwatch

4.  Copy all provided files into this folder so the structure looks like this:

> trashwatch/
>
> app.py
>
> requirements.txt
>
> supabase_setup.sql
>
> .gitignore
>
> .streamlit/
>
> secrets.toml

**Step 2 --- Install Python Packages**

5.  In the VS Code terminal, create a virtual environment:

> python -m venv .venv

6.  Activate it:

**On Windows:** .venv\Scripts\activate

**On Mac/Linux:** source .venv/bin/activate

7.  Install all dependencies:

> pip install -r requirements.txt

This will also download the YOLOv8n model automatically on first run. It is about 6MB.

> Note: The first time you run detection, ultralytics will download yolov8n.pt automatically. You do not need to download it manually.

**Step 3 --- Set Up Supabase**

**Create a project**

8.  Go to supabase.com and sign up

9.  Click New Project, give it a name like trashwatch, set a database password, choose a region close to you

10. Wait about 2 minutes for the project to be ready

**Run the database setup SQL**

11. In your Supabase dashboard, click SQL Editor in the left sidebar

12. Click New query

13. Open the file supabase_setup.sql from your project folder, copy all its contents

14. Paste into the SQL editor and click Run

15. You should see: Setup complete!

**Create the snapshots storage bucket**

16. In Supabase, click Storage in the left sidebar

17. Click New bucket

18. Name it exactly: snapshots

19. Check the box Public bucket

20. Click Create bucket

**Copy your API credentials**

21. Go to Project Settings (gear icon) \> API

22. Copy the Project URL (looks like https://xxxx.supabase.co)

23. Copy the anon public key (long string starting with eyJ\...)

24. Open .streamlit/secrets.toml in VS Code and fill in:

> SUPABASE_URL = \"https://YOUR_PROJECT_ID.supabase.co\"
>
> SUPABASE_KEY = \"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\...\"
>
> Important: Do NOT share or commit this file. It is already in .gitignore so it will not be pushed to GitHub.

**Step 4 --- Run Locally**

25. Make sure your virtual environment is activated (you should see (.venv) in the terminal prompt)

26. Run the app:

> streamlit run app.py

27. Your browser should open automatically to http://localhost:8501

28. If not, open your browser and go to http://localhost:8501

**Test the detection**

29. In the sidebar, make sure Laptop webcam is selected

30. Go to the LIVE DETECTION tab

31. Click START DETECTION

32. Hold a plastic bottle or cup in front of your laptop camera

33. You should see a green bounding box, hear a beep, and see the detection logged in the HISTORY tab

**Step 5 --- Deploy to Streamlit Cloud**

**Push to GitHub**

34. Create a new repository on github.com (click + \> New repository)

35. Name it trashwatch, set it to Public, do NOT add README or .gitignore (you already have one)

36. Back in VS Code terminal, initialize git and push:

> git init
>
> git add .
>
> git commit -m \"Initial commit\"
>
> git branch -M main
>
> git remote add origin https://github.com/YOUR_USERNAME/trashwatch.git
>
> git push -u origin main

**Deploy on Streamlit Cloud**

37. Go to share.streamlit.io and sign in with your GitHub account

38. Click New app

39. Select your trashwatch repository

40. Set Main file path to: app.py

41. Click Advanced settings \> Secrets

42. Paste your secrets in TOML format:

> \[general\]
>
> SUPABASE_URL = \"https://YOUR_PROJECT_ID.supabase.co\"
>
> SUPABASE_KEY = \"eyJ\...\"

43. Click Deploy --- your app will be live in about 1 minute at a URL like https://your-app.streamlit.app

**Step 6 --- Connect Mobile Camera (Optional)**

44. Install IP Webcam from the Google Play Store on your Android phone

45. Open the app, scroll down and tap Start server

46. The app will show an IP address like http://192.168.1.5:8080

47. Make sure your phone and laptop are on the same Wi-Fi network

48. In the TrashWatch sidebar, select Mobile IP Webcam

49. Enter the URL with /shot.jpg at the end, for example: http://192.168.1.5:8080/shot.jpg

50. Click START DETECTION --- the app will grab frames from your phone camera

> The phone camera is especially useful for pointing at outdoor areas, bins, or areas where your laptop cannot easily reach.

**Troubleshooting**

**Camera not opening**

- Make sure no other app (Teams, Zoom, browser) is using the webcam

- Try closing and reopening the app

- On Windows, check camera permissions in Settings \> Privacy \> Camera

**Supabase not connecting**

- Double-check the URL and key in .streamlit/secrets.toml --- no extra spaces or quotes

- Make sure you copied the anon key, not the service_role key

- The table must exist --- re-run supabase_setup.sql if unsure

**Nothing being detected**

- Lower the Confidence threshold slider in the sidebar (try 0.20)

- Make sure the object is well-lit and clearly visible

- The model detects: bottles, cups, bowls, bags, food items, and more

- Hold the object steady for 1-2 seconds

**YOLOv8 download fails**

- Make sure you have an internet connection when running the first time

- The model file (yolov8n.pt) downloads once and is cached locally

- If download fails, manually download from github.com/ultralytics/assets and place yolov8n.pt in the project folder

**Port already in use**

> streamlit run app.py \--server.port 8502

**ModuleNotFoundError**

Make sure your virtual environment is active (you see (.venv) in the prompt), then run:

> pip install -r requirements.txt

**Quick Reference**

|                               |                                                  |
|-------------------------------|--------------------------------------------------|
| **Action**                    | **Command / Location**                           |
| **Start app locally**         | streamlit run app.py                             |
| **Stop app**                  | Ctrl + C in terminal                             |
| **Activate venv (Windows)**   | .venv\Scripts\activate                           |
| **Activate venv (Mac/Linux)** | source .venv/bin/activate                        |
| **Update packages**           | pip install -r requirements.txt \--upgrade       |
| **View logs (Supabase)**      | Supabase Dashboard \> Table Editor \> detections |
| **View snapshots**            | Supabase Dashboard \> Storage \> snapshots       |
| **Streamlit Cloud dashboard** | share.streamlit.io                               |

TrashWatch --- Built with YOLOv8 + Streamlit + Supabase
