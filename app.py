"""
TrashWatch - Smart Trash Detection
Detects trash only, confirms before saving, stores permanently in Supabase
"""

import streamlit as st
import cv2
import numpy as np
import requests
import os
import time
import datetime
from PIL import Image
from io import BytesIO
import pandas as pd

st.set_page_config(
    page_title="TrashWatch",
    page_icon="🗑️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CUSTOM TRASH MODEL ───────────────────────────────────────────────────────
MODEL_PATH = os.getenv("TRASHWATCH_MODEL", "best.pt")

TRASH_SEVERITY = {
    "plastic_bottle":  ("HIGH",   "#FF4444"),
    "plastic_bag":     ("HIGH",   "#FF4444"),
    "cigarette_butt":  ("HIGH",   "#FF4444"),
    "glass_bottle":    ("HIGH",   "#FF4444"),
    "broken_glass":    ("HIGH",   "#FF4444"),
    "plastic_straw":   ("HIGH",   "#FF4444"),
    "straw":           ("MEDIUM", "#F59E0B"),
    "food_wrapper":    ("MEDIUM", "#F59E0B"),
    "paper_cup":       ("MEDIUM", "#F59E0B"),
    "aluminum_can":    ("MEDIUM", "#F59E0B"),
    "styrofoam":       ("MEDIUM", "#F59E0B"),
    "tetra_pak":       ("MEDIUM", "#F59E0B"),
    "cardboard":       ("LOW",    "#00BB66"),
    "newspaper":       ("LOW",    "#00BB66"),
    "food_waste":      ("LOW",    "#00BB66"),
}

HIGH_SEVERITY_TERMS = ("plastic", "cigarette", "glass", "sharp", "ewaste", "e-waste")
LOW_SEVERITY_TERMS = ("paper", "cardboard", "newspaper", "food_waste", "organic")

def normalize_label(label: str) -> str:
    return str(label).strip().lower().replace(" ", "_").replace("-", "_")

def display_label(label: str) -> str:
    return normalize_label(label).replace("_", " ").title()

def get_severity(label: str) -> tuple[str, str]:
    key = normalize_label(label)
    if key in TRASH_SEVERITY:
        return TRASH_SEVERITY[key]
    if any(term in key for term in HIGH_SEVERITY_TERMS):
        return "HIGH", "#FF4444"
    if any(term in key for term in LOW_SEVERITY_TERMS):
        return "LOW", "#00BB66"
    return "MEDIUM", "#F59E0B"

# ─── SUPABASE HELPERS ─────────────────────────────────────────────────────────
def get_headers():
    key = st.secrets["SUPABASE_KEY"]
    return {
        "Authorization": f"Bearer {key}",
        "apikey": key,
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

def upload_snapshot(image_bytes: bytes, filename: str) -> str | None:
    """Upload image to Supabase storage, return public URL."""
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        upload_url = f"{url}/storage/v1/object/snapshots/{filename}"
        headers = {
            "Authorization": f"Bearer {key}",
            "apikey": key,
            "Content-Type": "image/jpeg",
            "x-upsert": "true"
        }
        r = requests.post(upload_url, headers=headers, data=image_bytes, timeout=10)
        if r.status_code in (200, 201):
            return f"{url}/storage/v1/object/public/snapshots/{filename}"
        return None
    except Exception:
        return None

def save_detection(label: str, trash_type: str, confidence: float,
                   camera_source: str, snapshot_url: str | None,
                   severity: str, notes: str = "") -> bool:
    """Permanently save a confirmed detection to Supabase."""
    try:
        url = st.secrets["SUPABASE_URL"]
        data = {
            "label": label,
            "trash_type": trash_type,
            "confidence": round(float(confidence), 3),
            "camera_source": camera_source,
            "snapshot_url": snapshot_url,
            "severity": severity,
            "notes": notes,
            "detected_at": datetime.datetime.now(datetime.UTC).isoformat(),
        }
        r = requests.post(
            f"{url}/rest/v1/detections",
            headers=get_headers(),
            json=data,
            timeout=10
        )
        return r.status_code in (200, 201)
    except Exception as e:
        st.warning(f"DB save failed: {e}")
        return False

def fetch_all_detections() -> pd.DataFrame:
    """Fetch all permanent detections from Supabase."""
    try:
        url = st.secrets["SUPABASE_URL"]
        r = requests.get(
            f"{url}/rest/v1/detections?order=detected_at.desc&limit=500",
            headers=get_headers(),
            timeout=10
        )
        if r.status_code == 200 and r.json():
            return pd.DataFrame(r.json())
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

# ─── YOLO MODEL ───────────────────────────────────────────────────────────────
@st.cache_resource
def load_model():
    try:
        from ultralytics import YOLO
        import torch
        torch.serialization.add_safe_globals([])
        model = YOLO(MODEL_PATH)
        return model
    except Exception as e:
        st.error(f"Model load failed from {MODEL_PATH!r}: {e}")
        return None

def frame_to_jpg_bytes(frame) -> bytes:
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 88])
    return buf.tobytes()

def detect_trash_in_frame(frame, model, threshold: float):
    """Run a custom trash YOLO model and return every detection it finds."""
    results = model(frame, conf=threshold, verbose=False)[0]
    annotated = frame.copy()
    trash_found = []

    for box in results.boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        raw_label = model.names[cls_id]
        trash_type = display_label(raw_label)
        severity, color = get_severity(raw_label)
        x1, y1, x2, y2 = map(int, box.xyxy[0])

        # BGR color from hex
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        bgr = (b, g, r)

        cv2.rectangle(annotated, (x1, y1), (x2, y2), bgr, 2)
        tag = f"{trash_type} ({conf:.0%})"
        tw = len(tag) * 8 + 10
        cv2.rectangle(annotated, (x1, y1 - 26), (x1 + tw, y1), bgr, -1)
        cv2.putText(annotated, tag, (x1 + 4, y1 - 7),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

        trash_found.append({
            "label": normalize_label(raw_label),
            "trash_type": trash_type,
            "confidence": conf,
            "severity": severity,
            "bbox": (x1, y1, x2, y2),
        })

    return annotated, trash_found

def play_beep():
    """Silent fallback — use browser alert instead of paplay."""
    pass  # Handled via JS in browser

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🗑️ TrashWatch")
    st.caption("Smart trash detection & logging")
    st.divider()

    cam_source = st.radio("Camera", ["Laptop webcam", "Mobile IP Webcam"])
    ip_url = ""
    if cam_source == "Mobile IP Webcam":
        ip_url = st.text_input("IP Webcam URL", placeholder="http://192.168.x.x:8080/shot.jpg")

    st.divider()
    threshold = st.slider("Detection confidence", 0.15, 0.90, 0.40, 0.05,
                          help="Lower = catches more, higher = fewer false positives")
    cam_index = st.number_input("Webcam index (try 0, 2, 4 if camera fails)", 0, 10, 0, step=2)
    auto_save = st.toggle("Auto-save detections (no confirmation)", value=False)
    save_snapshots = st.toggle("Save snapshot images", value=True)

    st.divider()
    st.caption("Model")
    if os.path.exists(MODEL_PATH):
        st.success(f"Using {MODEL_PATH}")
    else:
        st.warning(f"Add your trained model as {MODEL_PATH}")

    st.divider()
    st.caption("Supabase status")
    try:
        _ = st.secrets["SUPABASE_URL"]
        st.success("Connected ✓")
    except Exception:
        st.error("No credentials in secrets.toml")

# ─── SESSION STATE ─────────────────────────────────────────────────────────────
if "running" not in st.session_state:
    st.session_state.running = False
if "pending" not in st.session_state:
    st.session_state.pending = None   # Detection waiting for confirmation
if "session_count" not in st.session_state:
    st.session_state.session_count = 0
if "last_save_time" not in st.session_state:
    st.session_state.last_save_time = 0

# ─── TABS ─────────────────────────────────────────────────────────────────────
tab_live, tab_db, tab_about = st.tabs(["📹 LIVE DETECTION", "📊 DATABASE", "ℹ️ ABOUT"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — LIVE DETECTION
# ══════════════════════════════════════════════════════════════════════════════
with tab_live:
    col_feed, col_panel = st.columns([3, 1], gap="large")

    with col_panel:
        st.markdown("#### Controls")
        btn_start = st.button("▶ START", use_container_width=True)
        btn_stop  = st.button("■ STOP",  use_container_width=True)
        st.divider()
        st.markdown("#### Session stats")
        stat_box = st.empty()
        st.divider()
        alert_box = st.empty()

    with col_feed:
        feed_ph = st.empty()
        confirm_ph = st.empty()

    if btn_start:
        st.session_state.running = True
        st.session_state.pending = None
        st.session_state.session_count = 0

    if btn_stop:
        st.session_state.running = False
        st.session_state.pending = None

    # ── Confirmation panel (shown when trash is found) ────────────────────
    if st.session_state.pending is not None:
        p = st.session_state.pending
        with confirm_ph.container():
            st.markdown("---")
            st.markdown(f"### 🗑️ Trash detected: **{p['trash_type']}**")

            sev_color = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(p["severity"], "🟡")
            c1, c2, c3 = st.columns(3)
            c1.metric("Type", p["trash_type"])
            c2.metric("Confidence", f"{p['confidence']:.0%}")
            c3.metric("Severity", f"{sev_color} {p['severity']}")

            if p.get("snapshot_bytes"):
                img = Image.open(BytesIO(p["snapshot_bytes"]))
                st.image(img, caption="Captured snapshot", width=400)

            notes = st.text_input("Add notes (optional)", key="notes_input",
                                  placeholder="e.g. found near main gate")

            ca, cb, cc = st.columns(3)
            with ca:
                if st.button("✅ CONFIRM & SAVE", use_container_width=True):
                    snap_url = None
                    if save_snapshots and p.get("snapshot_bytes"):
                        fname = f"trash_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
                        snap_url = upload_snapshot(p["snapshot_bytes"], fname)

                    ok = save_detection(
                        label=p["label"],
                        trash_type=p["trash_type"],
                        confidence=p["confidence"],
                        camera_source=p["camera_source"],
                        snapshot_url=snap_url,
                        severity=p["severity"],
                        notes=notes,
                    )
                    if ok:
                        st.success("✅ Saved to database!")
                        st.session_state.session_count += 1
                        st.session_state.last_save_time = time.time()
                    else:
                        st.error("Save failed — check Supabase connection")
                    st.session_state.pending = None
                    st.rerun()

            with cb:
                if st.button("❌ DISCARD", use_container_width=True):
                    st.session_state.pending = None
                    st.rerun()

            with cc:
                if st.button("⏩ RESUME CAMERA", use_container_width=True):
                    st.session_state.pending = None
                    st.rerun()

    # ── Detection loop ────────────────────────────────────────────────────
    if st.session_state.running and st.session_state.pending is None:
        model = load_model()
        if model is None:
            st.error("Model not loaded.")
            st.session_state.running = False
        else:
            cap = None
            if cam_source == "Laptop webcam":
                cap = cv2.VideoCapture(int(cam_index))
                if not cap.isOpened():
                    st.error(f"Cannot open camera index {cam_index}. Try 0, 2, or 4 in the sidebar.")
                    st.session_state.running = False

            cooldown = 4.0  # seconds between saves
            last_detect_time = 0

            stat_box.metric("Saved this session", st.session_state.session_count)

            for _ in range(60):  # 60 frames per Streamlit rerun cycle
                if not st.session_state.running:
                    break

                # Grab frame
                frame = None
                if cam_source == "Laptop webcam" and cap:
                    ret, frame = cap.read()
                    if not ret:
                        break
                elif cam_source == "Mobile IP Webcam" and ip_url:
                    try:
                        resp = requests.get(ip_url, timeout=3)
                        arr = np.frombuffer(resp.content, dtype=np.uint8)
                        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                    except Exception:
                        st.warning("Mobile camera not reachable")
                        break

                if frame is None:
                    time.sleep(0.1)
                    continue

                frame = cv2.resize(frame, (640, 480))
                annotated, trash_list = detect_trash_in_frame(frame, model, threshold)

                # Display feed
                rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                feed_ph.image(rgb, channels="RGB", width=640)

                now = time.time()
                if trash_list and (now - last_detect_time) > cooldown:
                    last_detect_time = now
                    best = max(trash_list, key=lambda x: x["confidence"])

                    _, buf = cv2.imencode(".jpg", frame)
                    snap_bytes = buf.tobytes()

                    if auto_save:
                        # Save directly without confirmation
                        snap_url = None
                        if save_snapshots:
                            fname = f"trash_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
                            snap_url = upload_snapshot(snap_bytes, fname)
                        save_detection(
                            label=best["label"],
                            trash_type=best["trash_type"],
                            confidence=best["confidence"],
                            camera_source=cam_source,
                            snapshot_url=snap_url,
                            severity=best["severity"],
                        )
                        st.session_state.session_count += 1
                        alert_box.success(f"Auto-saved: {best['trash_type']}")
                    else:
                        # Pause and ask for confirmation
                        st.session_state.pending = {
                            **best,
                            "camera_source": cam_source,
                            "snapshot_bytes": snap_bytes,
                        }
                        if cap:
                            cap.release()
                        st.rerun()

                time.sleep(0.04)

            if cap:
                cap.release()

            if st.session_state.running:
                st.rerun()

    elif not st.session_state.running and st.session_state.pending is None:
        feed_ph.info("Press ▶ START to begin detection with your custom trash model.")
        stat_box.metric("Saved this session", st.session_state.session_count)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — DATABASE
# ══════════════════════════════════════════════════════════════════════════════
with tab_db:
    st.markdown("### 📊 All saved detections")

    col_r, col_d = st.columns([1, 1])
    with col_r:
        refresh = st.button("🔄 Refresh", use_container_width=True)
    with col_d:
        pass

    df = fetch_all_detections()

    if df.empty:
        st.info("No detections saved yet. Use the Live Detection tab to capture and save trash.")
    else:
        # KPIs
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total saved", len(df))
        k2.metric("Unique types", df["trash_type"].nunique() if "trash_type" in df.columns else 0)
        high = len(df[df["severity"] == "HIGH"]) if "severity" in df.columns else 0
        k3.metric("High severity", high)
        today = datetime.date.today().isoformat()
        today_count = len(df[df["detected_at"].str[:10] == today]) if "detected_at" in df.columns else 0
        k4.metric("Today", today_count)

        st.divider()

        # Charts
        try:
            import plotly.express as px
            c1, c2 = st.columns(2)

            with c1:
                st.markdown("**Detections by trash type**")
                vc = df["trash_type"].value_counts().reset_index()
                vc.columns = ["type", "count"]
                fig = px.bar(vc.head(10), x="count", y="type", orientation="h",
                             color_discrete_sequence=["#00BB66"])
                fig.update_layout(height=280, margin=dict(l=0,r=0,t=10,b=0),
                                  paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                  font_color="#aaa", yaxis=dict(gridcolor="rgba(0,0,0,0)"),
                                  xaxis=dict(gridcolor="#222"))
                st.plotly_chart(fig, use_container_width=True)

            with c2:
                st.markdown("**Severity breakdown**")
                sv = df["severity"].value_counts().reset_index()
                sv.columns = ["severity", "count"]
                fig2 = px.pie(sv, names="severity", values="count",
                              color_discrete_sequence=["#FF4444", "#F59E0B", "#00BB66"])
                fig2.update_layout(height=280, margin=dict(l=0,r=0,t=10,b=0),
                                   paper_bgcolor="rgba(0,0,0,0)", font_color="#aaa")
                st.plotly_chart(fig2, use_container_width=True)
        except ImportError:
            pass

        st.divider()
        st.markdown("**Full detection log**")

        # Show snapshot thumbnails if URLs exist
        if "snapshot_url" in df.columns:
            snaps = df[df["snapshot_url"].notna() & (df["snapshot_url"] != "")].head(6)
            if not snaps.empty:
                st.markdown("**Recent snapshots**")
                cols = st.columns(min(6, len(snaps)))
                for i, (_, row) in enumerate(snaps.iterrows()):
                    with cols[i]:
                        try:
                            st.image(row["snapshot_url"], caption=row.get("trash_type","?"), width=120)
                        except Exception:
                            pass

        show_cols = [c for c in ["detected_at","trash_type","label","confidence",
                                  "severity","camera_source","notes"] if c in df.columns]
        st.dataframe(df[show_cols], use_container_width=True, height=360)

        csv = df.to_csv(index=False)
        st.download_button("⬇ Download CSV", csv, "trashwatch_detections.csv",
                           "text/csv", use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — ABOUT
# ══════════════════════════════════════════════════════════════════════════════
with tab_about:
    st.markdown("""
### How it works

1. **Camera captures frames** from your laptop or phone
2. **Your custom YOLOv8 trash model scans each frame**
3. **Every model class is treated as a trash class**, so train it only on real litter categories
4. **When trash is found**, detection pauses and shows you:
   - What object was detected
   - What type of trash it is
   - Confidence score
   - Severity level (High / Medium / Low)
   - A snapshot of the frame
5. **You confirm** — only then is it saved permanently to Supabase
6. **Database tab** shows all saved detections with charts and CSV export

### Trash severity levels

| Level | Examples |
|-------|---------|
| 🔴 HIGH | Plastic bottles, plastic bags, e-waste, sharp waste |
| 🟡 MEDIUM | Cups, food containers, hygiene waste, solid waste |
| 🟢 LOW | Food waste, organic waste, paper/cardboard |

### Supabase table needed

Run this SQL in your Supabase SQL Editor:

```sql
create table if not exists detections (
  id            bigserial primary key,
  label         text,
  trash_type    text,
  confidence    float,
  camera_source text,
  snapshot_url  text,
  severity      text,
  notes         text,
  detected_at   timestamptz default now()
);
create policy "allow all" on detections for all using (true) with check (true);
alter table detections enable row level security;
```
""")





