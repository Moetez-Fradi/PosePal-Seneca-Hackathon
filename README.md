# 🏋️ Posepa – Your AI-Powered Personal Coach  

**Posepa** is an AI fitness coach that uses **computer vision (Mediapipe)** and **real-time feedback** to guide your workouts, track your form, and keep you motivated — all inside your browser.  

🎥 **[Demo Video → Coming Soon]()**  

---

## 🚀 Tech Stack
- **Backend:** FastAPI ⚡ + Python 🐍  
- **Computer Vision:** Mediapipe + OpenCV 🎥  
- **Frontend:** Vanilla JS + HTML5 + Tailwind-style design  
- **Database:** MongoDB 🍃  
- **Authentication:** JWT + FastAPI cookies  
- **Voice Feedback:** Local TTS (Piper) 🎙️  

---

## 👥 Team Members
- 🧑 **Alice** – Fullstack, project lead, backend architecture  
- 👩 **Bob** – Frontend UI/UX & dashboard designer  
- 🧑 **Charlie** – Computer Vision & pose estimation guru  
- 👩 **Dana** – AI feedback & persona voice integration  

*(adapt with your real names/roles)*  

---

## ✨ Key Features
- 🧍 **Real-time Pose Tracking** – Squats, Push-ups, Rest detection with Mediapipe.  
- 🎙️ **Persona-based Voice Feedback** – Choose your coach: *Default*, *Goggins*, or *Barbie*.  
- ⏱️ **Smart Rest Timer** – Auto-switches between exercises and logs rest durations.  
- 📊 **Workout Dashboard** – See history, reps, sets, personas, and improvements.  
- 🔐 **Auth System** – Signup, login, JWT-protected routes.  
- 💾 **Workout Storage** – MongoDB keeps your performance history safe.  

---

## 🎯 Bonus Category Target
- **AI + HealthTech Innovation**  
Posepa helps beginners exercise safely with instant feedback — lowering injury risks and making fitness accessible anywhere.  

---

## 🛠️ Setup & Run  

### 1. Clone repo
```bash
git clone https://github.com/<your-org>/posepa.git
cd posepa
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```