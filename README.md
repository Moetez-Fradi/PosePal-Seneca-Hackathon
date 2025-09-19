# 🏋️ Posepal – Your AI-Powered Personal Coach  

**Posepal** is an AI fitness coach and Movement Analyzer that uses **computer vision** and **real-time feedback** to guide your workouts, track your form, and keep you motivated, all inside your browser.  

## Why Posepal Stands Out

**Fast and Lightweight**: Fast real-time data processing, seperated on both client and server-side for optimization.

**Innovation**: Blends computer vision + LLMs + local TTS with different personas for a fully interactive coach, not just a tracker and a bot.

**Impact**: Helps beginners avoid injuries and makes fitness accessible to everyone with instant, personalized feedback.

**Execution**: Working prototype with real-time tracking, feedback voices, dashboard, and persistent storage.

**Future Potential**: Can scale into personalized training plans, gamified fitness, and even rehab/physiotherapy support.
---

## Tech Stack
- **Backend:** Python + Fastapi
- **Computer Vision:** Mediapipe + OpenCV  
- **Frontend:** Vanilla JS + HTML5 + Tailwind CSS
- **Database:** MongoDB
- **Authentication:** JWT + FastAPI cookies  
- **Voice Feedback:** Local TTS (Piper)
- **LLM Model** Llama 3 8B (light and fast)

---

## Team Members
-  **Moetez** – Fullstack lead, AI & Computer Vision
-  **Ghassen** – Backend developer, UI/UX & dashboard design 
-  **Amin** – TTS integration & LLM orchestration
-  **Myriam** - Our cute motivator and vibecoder

---

## Key Features
-  **Real-time Pose Tracking**: Squats, Push-ups, Rest detection with Mediapipe (extensible to other exercises)  
-  **Persona-based Voice Feedback**: Choose your coach: *Default*, *Goggins*, or *Barbie*.  
-  **Smart Workout Flow**: Switch between exercises and logs rest durations with **smart gestures**.
-  **Instant Motivation & Advice**: Get immediate, persona-tailored feedback after each set.
-  **Workout Dashboard**: See history, reps, sets, personas, and improvements.
-  **Auth System**: Signup, login, JWT-protected routes.  
-  **Workout Storage**: MongoDB keeps your performance history safe.

---
## Bonus Category Target: AI + HealthTech Innovation  

Posepal leverages **AI-powered coaching** to bring **safe, accessible, and personalized fitness** to everyone:  

-  **Beginners**: Get instant, corrective feedback that prevents injuries and builds confidence.  
-  **Busy Intermediates**: Track workouts in real time, anywhere, without needing a gym or trainer.  
-  **Accessibility & Inclusivity**: Persona-based coaching styles adapt to different personalities, fitness levels, and moods.  

This bridges the gap between **professional coaching** and **at-home fitness**, making workouts **safer, smarter, and more motivating**.  


---

## 🛠️ Setup & Run  

### 1. Clone repo
```bash
git clone https://github.com/Moetez-Fradi/PosePal-Seneca-Hackathon.git
cd PosePal-Seneca-Hackathon
```

### 2. Backend Setup

```bash
python -m venv venv
source venv/bin/activate # for windows: source venv/Scripts/activate 
pip install -r requirements.txt
cp .env.exemple .env # add your api key and database url...
uvicorn app.api.main:app --reload --workers 1
```

### 3. Frontend Setup
in a seperate terminal:

```bash
cd app/frontend
python -m http.server 5500
```

Then acess *http://localhost:5500* from your browser

## TTS with Piper

Posepa maps these voices to personas:

- 🎤 default -> LibriTTS

- 💪 goggins -> Joe

- 💖 barbie -> Amy

## 🧠 LLM Feedback

Posepal uses Llama 3 8B Instruct via OpenRouter to generate smart, persona-aware coaching feedback after every set.

**The LLM sees your actual exercise data:**

- Exercise type (squat, push-up, rest, etc.)

- Reps completed

- Duration of the set

- Mistakes detected by computer vision (e.g. knees in, shallow depth, elbows flaring)

Based on this context and your chosen persona, it generates concise **feedback** (1–3 sentences):

- Motivation: Persona-styled encouragement (e.g. “Stay hard!” for Goggins, “You’re glowing!” for Barbie).

- Actionable Cue: One key form correction drawn from detected mistakes.

- Target for Next Set: A simple improvement goal (more reps, cleaner tempo, deeper form).

=> This makes Posepal’s coaching dynamic, personalized, and realistic — it feels like you’re working with a real trainer, not just an app.

## Dashboarding

**Track:**

- Exercises completed

- Sets & reps

- Personas used

- Rest durations

Visual insights help track progress and improvement trends, keeping you aware.

### Future Plans

- Training Plans by Persona – **Difficulty adapts** to your chosen persona (Goggins = intense, Barbie = light & fun, Default = balanced).

- Mobile-first UI – PWA support for workouts on-the-go.

- Gamification – Streaks, badges, and progress milestones.

- Expanded CV Models – Add plank, lunges, burpees, etc.




## Video demo link

[https://drive.google.com/file/d/1hYEzX9RnhdUIdgJpi4nmu2S1jBEnz5Bv/view?usp=sharing](https://drive.google.com/file/d/1RxgJ147TGHJYz_tmzIX2XdI2h_Wj6Y54/view?usp=sharing)





