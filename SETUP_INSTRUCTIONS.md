# ✅ TrashWatch Project Setup Complete!

## 📁 Project Structure

Your TrashWatch project has been successfully set up with the following structure:

```
trashwatch/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── supabase_setup.sql          # Database setup script
├── setup_README.md             # Full setup guide
├── .gitignore                  # Git ignore rules
├── .streamlit/
│   └── secrets.toml            # Supabase credentials (FILL THIS IN)
└── .venv/                      # Python virtual environment (already created)
```

## ✅ What's Been Done

- ✅ Created `app.py` - Full-featured Streamlit web application
- ✅ Created `requirements.txt` - All Python dependencies listed
- ✅ Created `supabase_setup.sql` - Database schema for detections
- ✅ Created `.streamlit/secrets.toml` - Template for Supabase credentials
- ✅ Created `.gitignore` - Prevents secrets from being committed
- ✅ Created Python virtual environment (.venv)
- ✅ Installed all dependencies:
  - streamlit==1.28.1
  - ultralytics==8.0.195 (YOLOv8)
  - opencv-python==4.8.1.78
  - supabase==2.0.3
  - numpy==1.24.3
  - pillow==10.0.1
  - plotly==5.17.0
  - pandas==2.1.1
  - python-dotenv==1.0.0

## 🎯 Next Steps

### Step 1: Set Up Supabase (FREE)
1. Go to [supabase.com](https://supabase.com) and sign up
2. Click "New Project" and create a project called "trashwatch"
3. Set a database password and choose a region close to you
4. Wait 2-3 minutes for it to be ready

### Step 2: Create Database Table
1. In Supabase dashboard, click **SQL Editor** on the left
2. Click **New query**
3. Open `supabase_setup.sql` and copy ALL its contents
4. Paste into the SQL editor and click **Run**
5. You should see: "Setup complete!"

### Step 3: Create Storage Bucket
1. In Supabase, click **Storage** on the left sidebar
2. Click **New bucket**
3. Name it exactly: `snapshots`
4. Check **Public bucket**
5. Click **Create bucket**

### Step 4: Get Your API Credentials
1. Go to **Project Settings** (gear icon) → **API**
2. Copy the **Project URL** (looks like `https://xxxx.supabase.co`)
3. Copy the **anon public key** (long string starting with `eyJ...`)

### Step 5: Fill in Your Secrets
1. Open `.streamlit/secrets.toml` in VS Code
2. Replace the placeholder values:
   ```toml
   SUPABASE_URL = "https://YOUR_PROJECT_ID.supabase.co"
   SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   ```
   **⚠️ IMPORTANT: Do NOT share or commit this file. It's already in .gitignore!**

### Step 6: Run the App Locally
1. Open terminal in VS Code (Ctrl + `)
2. Make sure you're in the project folder:
   ```bash
   cd /home/abrarbutt/Anti-Littering-System-Computer-Vision
   ```
3. Activate virtual environment (should be auto-activated):
   ```bash
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
4. Run the app:
   ```bash
   streamlit run app.py
   ```
5. Your browser will open to `http://localhost:8501`

### Step 7: Test the Detection
1. Select **"Laptop webcam"** in the sidebar
2. Go to the **🎥 LIVE DETECTION** tab
3. Click **▶️ START DETECTION**
4. Hold a bottle, cup, or plastic bag in front of your camera
5. You should see:
   - Green bounding boxes around detected objects
   - Alert sound (if enabled)
   - Detection logged in the **📋 HISTORY** tab

## 🎮 Features

### 🎥 Live Detection Tab
- Real-time trash detection from laptop or mobile camera
- Adjustable confidence threshold
- Green bounding boxes with labels
- Detection statistics

### 📋 History Tab
- View all detections in a table
- Download detection history as CSV
- Linked to Supabase database

### ℹ️ About Tab
- Project information
- Troubleshooting guide
- Tech stack details

## 🔧 Camera Options

### Laptop Webcam (Easy - Recommended for Testing)
1. Simply select "Laptop webcam" in sidebar
2. Click START DETECTION
3. Hold trash items in front of camera

### Mobile Phone Camera (Advanced)
1. Install [**IP Webcam**](https://play.google.com/store/apps/details?id=com.pas.webcam) from Play Store
2. Open the app and tap **Start server**
3. Note the IP address shown (e.g., `http://192.168.1.5:8080`)
4. In TrashWatch sidebar, select "Mobile IP Webcam"
5. Enter: `http://192.168.1.5:8080/shot.jpg`
6. Make sure phone and laptop are on **same Wi-Fi network**
7. Click START DETECTION

## 🐛 Troubleshooting

### "Cannot open webcam"
- Close other apps using camera (Teams, Zoom, browser)
- Check Windows Settings → Privacy → Camera permissions
- Try restarting the app

### "Supabase not connecting"
- Double-check credentials in `.streamlit/secrets.toml`
- Make sure there are no extra spaces or quotes
- Verify you copied the **anon key**, not the **service_role key**

### "Nothing is being detected"
- Lower the **Confidence Threshold** slider (try 0.30)
- Ensure good lighting on the object
- Hold the object steady for 1-2 seconds
- Get closer to the camera

### "YOLOv8 download fails"
- Check your internet connection
- The model (6MB) will download automatically on first run
- If stuck, you can manually cancel and restart

### "Port already in use"
```bash
streamlit run app.py --server.port 8502
```

### "ModuleNotFoundError"
```bash
# Make sure venv is active (you see (.venv) in prompt)
source .venv/bin/activate

# Reinstall packages
pip install -r requirements.txt
```

## 📤 Deploy to Streamlit Cloud (Optional)

1. Push to GitHub:
   ```bash
   git add .
   git commit -m "TrashWatch app"
   git push -u origin main
   ```

2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New app** → Select your repo and `app.py`
4. Go to **Advanced settings** → **Secrets** and paste your credentials
5. Deploy!

Your app will be live at `https://your-username-trashwatch.streamlit.app`

## 📊 Detectable Objects

YOLOv8 can detect:
- Bottles, cups, cans
- Food waste, containers
- Plastic bags, wrappers
- Food items on plates
- And much more!

## ⚙️ Customization

### Change Detection Classes
Edit `app.py` and modify the model or add class filtering

### Adjust Alert Sound
Edit the `play_alert_sound()` function in `app.py`

### Change Video Resolution
Look for `cv2.resize(frame, (640, 480))` in `app.py`

### Disable Snapshots
Uncheck **📸 Save Snapshots to Supabase** in the sidebar

## 📚 Files Reference

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit web app with all features |
| `requirements.txt` | Python package dependencies |
| `supabase_setup.sql` | Database table creation |
| `.streamlit/secrets.toml` | Supabase API credentials |
| `.gitignore` | Prevents secrets from being committed |
| `.venv/` | Python virtual environment |

## 🎓 Learning Resources

- [Streamlit Docs](https://docs.streamlit.io)
- [YOLOv8 Docs](https://docs.ultralytics.com)
- [Supabase Docs](https://supabase.com/docs)
- [OpenCV Docs](https://opencv.org)

## 💡 Tips

- ✅ Always activate `.venv` before running commands
- ✅ Keep `.streamlit/secrets.toml` in .gitignore (already done)
- ✅ Test on laptop webcam first before trying mobile
- ✅ Use lower confidence threshold for more detections
- ✅ Good lighting = better detection accuracy
- ✅ Run YOLOv8 once to cache the model (takes 1-2 minutes first time)

## 🚀 Ready to Go!

Your TrashWatch project is ready to run! Follow the steps above and you'll have a working trash detection system in minutes.

**Questions?** Check the troubleshooting section or read `setup_README.md` for more details.

---

**TrashWatch © 2024** | Built with YOLOv8 + Streamlit + Supabase
