# Gamification Branch — Merge Summary

> **Branch:** `gamification` → `main`  
> **Commits:** 2 (`65861bb`, `c095205`)  
> **Files changed:** 14 (4 new, 10 modified)  
> **Diff:** +4,257 / −150 lines

---

## New Files

### 1. `templates/fall_blutdruck.html` (468 lines)
**Interactive Case Study — "Blood Pressure Measurement with Frau Schmidt"**
- Full voice-driven patient case study with Prof. Wagner avatar
- 7-step clinical checklist (identify patient → document values)
- Real-time step detection: user speech is analyzed for completed nursing steps
- Uses **OpenAI Whisper** (via `/api/stt`) for speech-to-text — no WebSpeech fallback
- Uses **edge-tts** (via `/api/tts-proxy`) for text-to-speech output
- TalkingHead 1.7 avatar with lip-sync
- Progress sidebar with checklist, vocabulary helper, and timer
- XP rewards on step completion and case finish
- Persists attempts via `CaseStudyAttempt` model

### 2. `templates/learning.html` (364 lines)
**Learning Hub Page — Flashcards + Library + Quiz**
- Module selector dropdown (auto-selects random module if none chosen)
- **Flashcards** section: AI-generated Leitner-box spaced repetition cards, flip animation, "Got it" / "Review again" buttons with XP tracking
- **Library** section: AI-generated topic cards with category labels, simple/technical language toggle, and "Deepen with Prof. Wagner →" button linking to KI-Lehrer
- Section tabs: Karteikarten / Bibliothek / Quiz

### 3. `templates/gamification.html` (182 lines)
**Gamification Dashboard — XP, Leaderboard, Friends, Missions**
- Daily XP goal progress bar
- Streak tracker (consecutive days)
- Top-20 student leaderboard sorted by XP
- Friends list with add-by-email functionality
- Friend missions (cooperative XP challenges)
- Weekly lotto winners display

### 4. `templates/kip_dashboard.html` (108 lines)
**KIP Teacher Analytics Dashboard**
- Total students, active students (last 7 days), total quiz attempts, average score
- 14-day daily activity chart
- Student progress table (name, level, XP, attempts, last active)
- Course enrollment stats
- Topic mastery breakdown (6 nursing topics with percentage bars)
- AI-generated recommendation for weakest topic

---

## Modified Files

### `app.py` (+513 lines)
**New Routes:**
| Route | Method | Description |
|-------|--------|-------------|
| `/learn` | GET | Learning hub page |
| `/api/flashcards/<module_id>` | GET | Generate/retrieve flashcards for a module |
| `/api/flashcards/<card_id>/review` | POST | Submit flashcard review (Leitner box update + XP) |
| `/api/library/<module_id>` | GET | Generate library summary for a module |
| `/api/library/ask` | POST | Ask AI about library card content |
| `/api/library-cards/<module_id>` | GET | Generate structured topic cards (simple + technical) |
| `/gamification` | GET | Gamification dashboard |
| `/api/friends/add` | POST | Add friend by email |
| `/api/missions/create` | POST | Create a cooperative friend mission |
| `/api/daily-goal` | POST | Update student's daily XP target |
| `/api/lotto/draw` | POST | Trigger the weekly lottery draw |
| `/fall/blutdruck` | GET | Case study page |
| `/api/fall/blutdruck/turn` | POST | Process one conversation turn in case study |
| `/kip` | GET | Teacher KIP analytics dashboard |

**Modified Routes:**
- `student_dashboard`: Added stats computation (streak, rank, XP, quizzes count)
- `api_quiz_submit`: Awards XP on quiz completion (+10 per correct, +20 bonus for ≥80%) and updates `DailyGoal`
- `ai_professor_api`: Now passes `build_student_context(user)` for personalized AI responses
- `ki_lehrer_api`: Now passes `build_student_context(user)` to system prompt
- `api_stt` (`/api/stt`): Now uses **OpenAI Whisper** (`whisper-1`) as the primary speech-to-text engine (reads `OPENAI_API_KEY` from env); existing providers remain as fallback

### `models.py` (+126 lines)
**New Models:**
| Model | Purpose |
|-------|---------|
| `Flashcard` | Stores AI-generated flashcard front/back per module |
| `FlashcardProgress` | Per-student Leitner box state (box 0–4, next review date) |
| `DailyGoal` | Daily XP target and earned XP per student |
| `FriendMission` | Cooperative challenges between two students |
| `LottoWinner` | Weekly lottery winners |
| `CaseStudyAttempt` | Tracks case study progress (steps completed, XP, duration) |
| `friendship` | Self-referential many-to-many table for friend relationships |

**Modified Models:**
- `User`: Added `xp` column (Integer, default 0) and `friends` relationship
- Added `index=True` to several foreign key columns for performance
- Added `UniqueConstraint` on `Enrollment(student_id, course_id)`

### `services.py` (+405 lines)
**New Functions:**
| Function | Description |
|----------|-------------|
| `build_student_context(user)` | Creates a profile string (name, level, country, language, speciality) for AI prompts |
| `generate_flashcards(module, level, num)` | AI-generates Leitner flashcards via Gemini |
| `generate_library_summary(module, level, ctx)` | AI-generates simplified library reading card |
| `generate_library_cards(module, level, ctx)` | AI-generates structured topic cards with `simple` + `technical` language variants |
| `FALL_BLUTDRUCK` | Case study data dictionary: patient info, 7 steps with keywords, vocabulary |
| `build_fall_blutdruck_prompt(...)` | Builds the system prompt for Prof. Wagner during the case study |
| `detect_fall_steps(case, text, done)` | Keyword-based detection of completed nursing steps from user speech |
| `_seed_demo_students()` | Seeds 10 demo students with realistic XP for leaderboard |

**Modified Functions:**
- `get_ai_professor_response`: New `student_context` parameter appended to system instruction
- `build_ki_lehrer_system_prompt`: New `student_context` parameter appended to prompt
- `init_db`: Extended migrations list (adds `xp` column, creates indexes), calls `_seed_demo_students()`

### `templates/base.html` (+5 lines)
- Student nav: Added links to **Fallstudie**, **Lernen**, **Erfolge** (gamification)
- Teacher nav: Added link to **KIP** dashboard

### `templates/dashboard_student.html` (major redesign)
- Replaced simple welcome card with **Mission des Tages** hero banner (links to case study)
- Added **4-stat grid**: Streak, Rank, XP, Quizzes
- Added **Quick Actions** grid: Case Study, Flashcards, KI-Lehrer
- Added **chip row** for level/speciality info
- Kept enrolled courses and recommended courses sections

### `templates/index.html` (+66 lines)
- Redesigned landing page hero section
- Updated feature showcase and CTA buttons

### `templates/quiz.html` (+20 lines)
- Added XP display and progress bar improvements

### `templates/register.html` (+79 lines)
- Enhanced registration form layout/styling

### `static/styles.css` (+1,897 lines)
**New CSS sections:**
- Stat Grid (4-up dashboard widgets)
- Pill Chips (level badges)
- Learning Hub (module bar, card grid, section tabs)
- Flashcard Card (flip animation, Leitner box indicator)
- Library Cards (topic cards, language toggle, deepen button)
- Gamification (leaderboard, friends, missions, lotto, activity chart)
- Case Study (avatar, chat, sidebar, patient card, checklist, vocab, input bar, finish overlay)
- Quick-action grid (dashboard cards)
- KIP Insights (teacher analytics dashboard)

### `requirements.txt` (+2 lines)
```
edge-tts>=7.0.0    # Text-to-speech for Prof. Wagner avatar
openai>=1.0.0       # Whisper STT for voice input
```

---

## Database Migrations (automatic)
The `init_db()` function handles these migrations automatically on startup:
- `ALTER TABLE user ADD COLUMN xp INTEGER DEFAULT 0`
- New tables: `flashcard`, `flashcard_progress`, `daily_goal`, `friend_mission`, `lotto_winner`, `case_study_attempt`, `friendship`
- New indexes on frequently queried foreign keys
- Unique constraints on enrollment, daily goals, lotto positions

> **Note:** Existing data in `main` will not be affected. New tables are created via `db.create_all()` and column additions use safe `ALTER TABLE` with try/catch fallback.

---

## Required Environment Variables
| Variable | Purpose | Required? |
|----------|---------|-----------|
| `GEMINI_API_KEY` | Existing — AI content generation (Gemini) | Yes (unchanged) |
| `OPENAI_API_KEY` | **New** — OpenAI Whisper speech-to-text for the case study | Yes, for `/fall/blutdruck` voice input |

> Without `OPENAI_API_KEY`, the case study page still loads, but speech input will fall back / fail. Add it to your `.env` before testing.

---

## How to Test After Merge
```bash
pip install -r requirements.txt   # installs edge-tts + openai
# Make sure OPENAI_API_KEY is set in your .env (new requirement)
python app.py                     # auto-runs migrations
```
Then visit:
- `http://localhost:5000/student` → New dashboard with mission + stats
- `http://localhost:5000/fall/blutdruck` → Voice case study
- `http://localhost:5000/learn` → Flashcards + Library
- `http://localhost:5000/gamification` → XP / Leaderboard
- `http://localhost:5000/kip` → Teacher analytics (login as `lehrer@carelearn.de`)
