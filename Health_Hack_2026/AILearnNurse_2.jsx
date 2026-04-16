import { useState, useEffect, useRef } from 'react';
import {
  Home, BookOpen, MessageSquare, Trophy, Upload, GraduationCap,
  Mic, MicOff, Volume2, ChevronRight, ChevronLeft, Check, X,
  Flame, Target, Ticket, Users, TrendingUp, Clock, Sparkles,
  ArrowRight, RotateCw, Brain, Stethoscope, Heart, Shield,
  Pill, AlertCircle, Languages, Library, HelpCircle, Headphones
} from 'lucide-react';

export default function AILearnNurse() {
  const [screen, setScreen] = useState('onboarding');
  const [role, setRole] = useState('student');
  const [user, setUser] = useState({
    firstName: '',
    lastName: '',
    country: '',
    language: '',
    speciality: '',
    level: 'B1'
  });
  const [learningSection, setLearningSection] = useState(null);
  const [profContext, setProfContext] = useState(null);

  // Jump to AI professor with pre-loaded context
  const askProfessor = (context) => {
    setProfContext(context);
    setScreen('learning');
    setLearningSection('professor');
  };

  // Quick skip helper for demo
  const skipToHome = () => {
    setUser({
      firstName: 'Amara',
      lastName: 'Okafor',
      country: 'Nigeria',
      language: 'Igbo',
      speciality: 'Allgemeinpflege',
      level: 'B1'
    });
    setScreen('home');
  };

  return (
    <div style={{ minHeight: '100vh', background: 'var(--ground)', color: 'var(--ink)' }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Geist:wght@300;400;500;600&display=swap');

        :root {
          --ground: #F5EEE2;
          --ground-2: #EDE4D4;
          --paper: #FBF7EF;
          --ink: #2A1F15;
          --ink-2: #5A4B3C;
          --ink-3: #8A7A68;
          --terracotta: #C4523E;
          --terracotta-dark: #9E3E2D;
          --sage: #3D5B42;
          --sage-dark: #2A3F2E;
          --honey: #C88A2E;
          --cream-border: rgba(42, 31, 21, 0.12);
        }

        .font-serif { font-family: 'Fraunces', Georgia, serif; font-feature-settings: "ss01", "ss02"; }
        .font-sans { font-family: 'Geist', -apple-system, sans-serif; }
        body, #root, * { font-family: 'Geist', -apple-system, sans-serif; }
        h1, h2, h3, .display { font-family: 'Fraunces', Georgia, serif; letter-spacing: -0.02em; }

        .paper-card {
          background: var(--paper);
          border: 1px solid var(--cream-border);
          border-radius: 14px;
        }
        .chip {
          display: inline-flex; align-items: center; gap: 6px;
          padding: 4px 10px; border-radius: 999px;
          font-size: 11px; font-weight: 500;
          background: var(--ground-2); color: var(--ink-2);
          border: 1px solid var(--cream-border);
          letter-spacing: 0.02em; text-transform: uppercase;
        }
        .btn-primary {
          background: var(--terracotta); color: #FBF7EF;
          padding: 12px 22px; border-radius: 10px; font-weight: 500;
          display: inline-flex; align-items: center; gap: 8px;
          transition: background 0.15s ease;
          border: none; cursor: pointer; font-size: 14px;
        }
        .btn-primary:hover { background: var(--terracotta-dark); }
        .btn-secondary {
          background: transparent; color: var(--ink);
          padding: 12px 22px; border-radius: 10px; font-weight: 500;
          border: 1px solid var(--cream-border); cursor: pointer; font-size: 14px;
          display: inline-flex; align-items: center; gap: 8px;
        }
        .btn-secondary:hover { background: var(--ground-2); }
        .nav-item {
          display: flex; align-items: center; gap: 12px;
          padding: 10px 14px; border-radius: 10px;
          color: var(--ink-2); cursor: pointer; font-size: 14px;
          transition: all 0.15s;
        }
        .nav-item:hover { background: var(--ground-2); color: var(--ink); }
        .nav-item.active { background: var(--ink); color: var(--paper); }
        .input {
          width: 100%; padding: 12px 14px;
          background: var(--paper); border: 1px solid var(--cream-border);
          border-radius: 10px; font-size: 14px; color: var(--ink);
          outline: none; transition: border-color 0.15s;
        }
        .input:focus { border-color: var(--terracotta); }
        .label { font-size: 12px; color: var(--ink-2); margin-bottom: 6px; display: block; font-weight: 500; letter-spacing: 0.02em; text-transform: uppercase; }
        .section-num {
          font-family: 'Fraunces', serif; font-style: italic;
          color: var(--terracotta); font-size: 13px;
          letter-spacing: 0.05em;
        }
        @keyframes pulse-mic {
          0%, 100% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.08); opacity: 0.85; }
        }
        @keyframes wave {
          0% { height: 20%; }
          50% { height: 100%; }
          100% { height: 20%; }
        }
        .mic-pulse { animation: pulse-mic 1.2s ease-in-out infinite; }
        .wave-bar { animation: wave 0.9s ease-in-out infinite; background: var(--terracotta); border-radius: 2px; width: 4px; }
        @keyframes flip-in {
          from { transform: rotateY(90deg); opacity: 0; }
          to { transform: rotateY(0); opacity: 1; }
        }
        .flip-enter { animation: flip-in 0.35s ease-out; }
        .card-hover { transition: transform 0.2s, box-shadow 0.2s; cursor: pointer; }
        .card-hover:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(42,31,21,0.08); }
      `}</style>

      {screen === 'onboarding' && <Onboarding user={user} setUser={setUser} onNext={() => setScreen('test')} onSkip={skipToHome} />}
      {screen === 'test' && <LanguageTest onComplete={(lvl) => { setUser({ ...user, level: lvl }); setScreen('home'); }} />}
      {screen !== 'onboarding' && screen !== 'test' && (
        <AppShell
          user={user} role={role} setRole={setRole}
          screen={screen} setScreen={setScreen}
          learningSection={learningSection} setLearningSection={setLearningSection}
        >
          {role === 'student' && screen === 'home' && <Dashboard user={user} setScreen={setScreen} />}
          {role === 'student' && screen === 'learning' && !learningSection && (
            <LearningHub setLearningSection={setLearningSection} />
          )}
          {role === 'student' && screen === 'learning' && learningSection === 'flashcards' && (
            <Flashcards onBack={() => setLearningSection(null)} onAskProfessor={askProfessor} />
          )}
          {role === 'student' && screen === 'learning' && learningSection === 'library' && (
            <LibraryView onBack={() => setLearningSection(null)} onAskProfessor={askProfessor} />
          )}
          {role === 'student' && screen === 'learning' && learningSection === 'quiz' && (
            <Quiz onBack={() => setLearningSection(null)} />
          )}
          {role === 'student' && screen === 'learning' && learningSection === 'audio' && (
            <AudioQA onBack={() => setLearningSection(null)} />
          )}
          {role === 'student' && screen === 'learning' && learningSection === 'professor' && (
            <AIProfessor onBack={() => { setLearningSection(null); setProfContext(null); }} user={user} initialContext={profContext} clearContext={() => setProfContext(null)} />
          )}
          {role === 'student' && screen === 'gamification' && <Gamification user={user} />}
          {role === 'student' && screen === 'upload' && <UploadView />}
          {role === 'teacher' && <TeacherDashboard />}
        </AppShell>
      )}
    </div>
  );
}

/* ---------- ONBOARDING ---------- */
function Onboarding({ user, setUser, onNext, onSkip }) {
  return (
    <div style={{ minHeight: '100vh', display: 'grid', gridTemplateColumns: '1fr 1fr' }}>
      <div style={{ padding: '60px 64px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 80 }}>
            <div style={{ width: 32, height: 32, borderRadius: 8, background: 'var(--terracotta)', display: 'grid', placeItems: 'center' }}>
              <Stethoscope size={18} color="#FBF7EF" />
            </div>
            <span className="display" style={{ fontSize: 20, fontWeight: 600 }}>Kurare</span>
          </div>

          <div className="section-num">Schritt 01 — Profil</div>
          <h1 style={{ fontSize: 48, lineHeight: 1.05, margin: '12px 0 16px', fontWeight: 500 }}>
            Willkommen. Lass uns dich <em style={{ color: 'var(--terracotta)' }}>kennenlernen.</em>
          </h1>
          <p style={{ color: 'var(--ink-2)', fontSize: 16, lineHeight: 1.6, maxWidth: 420, marginBottom: 40 }}>
            Wir passen Lerninhalte, Schwierigkeit und Sprache an deinen Hintergrund an. Das dauert zwei Minuten.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, maxWidth: 460 }}>
            <div>
              <label className="label">Vorname</label>
              <input className="input" value={user.firstName} onChange={(e) => setUser({ ...user, firstName: e.target.value })} placeholder="Amara" />
            </div>
            <div>
              <label className="label">Nachname</label>
              <input className="input" value={user.lastName} onChange={(e) => setUser({ ...user, lastName: e.target.value })} placeholder="Okafor" />
            </div>
            <div>
              <label className="label">Herkunftsland</label>
              <input className="input" value={user.country} onChange={(e) => setUser({ ...user, country: e.target.value })} placeholder="Nigeria" />
            </div>
            <div>
              <label className="label">Muttersprache</label>
              <input className="input" value={user.language} onChange={(e) => setUser({ ...user, language: e.target.value })} placeholder="Igbo" />
            </div>
            <div style={{ gridColumn: 'span 2' }}>
              <label className="label">Fachrichtung</label>
              <select className="input" value={user.speciality} onChange={(e) => setUser({ ...user, speciality: e.target.value })}>
                <option value="">Bitte auswählen</option>
                <option>Allgemeinpflege</option>
                <option>Altenpflege</option>
                <option>Kinderkrankenpflege</option>
                <option>Intensivpflege</option>
                <option>Psychiatrische Pflege</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 12, marginTop: 36 }}>
            <button className="btn-primary" onClick={onNext} disabled={!user.firstName}>
              Weiter zum Sprachtest <ArrowRight size={16} />
            </button>
            <button className="btn-secondary" onClick={onSkip}>Demo überspringen</button>
          </div>
        </div>

        <div style={{ color: 'var(--ink-3)', fontSize: 12 }}>
          HealthHack 2026 · Prototyp
        </div>
      </div>

      <div style={{
        background: 'var(--ground-2)', position: 'relative', overflow: 'hidden',
        padding: 60, display: 'flex', alignItems: 'flex-end'
      }}>
        <div style={{
          position: 'absolute', top: 80, right: 80,
          width: 280, height: 280, borderRadius: '50%',
          background: 'var(--terracotta)', opacity: 0.12
        }} />
        <div style={{
          position: 'absolute', top: 200, right: 220,
          width: 180, height: 180, borderRadius: '50%',
          background: 'var(--sage)', opacity: 0.15
        }} />
        <div style={{ position: 'relative', maxWidth: 420 }}>
          <Sparkles size={28} color="var(--terracotta)" style={{ marginBottom: 20 }} />
          <p className="display" style={{ fontSize: 28, lineHeight: 1.25, fontWeight: 400, fontStyle: 'italic', color: 'var(--ink)' }}>
            "Pflege lernt man nicht nur aus Büchern — man lernt sie im Gespräch, am Fall, und an sich selbst."
          </p>
          <div style={{ marginTop: 16, color: 'var(--ink-2)', fontSize: 13 }}>— Prinzip hinter Kurare</div>
        </div>
      </div>
    </div>
  );
}

/* ---------- LANGUAGE TEST ---------- */
function LanguageTest({ onComplete }) {
  const questions = [
    {
      q: 'Der Patient ___ über Schmerzen in der Brust.',
      options: ['klagt', 'spricht', 'sagt', 'ruft'],
      correct: 0
    },
    {
      q: 'Was bedeutet "Vitalzeichen"?',
      options: ['Körpergewicht', 'Grundlegende Körperfunktionen', 'Symptome einer Krankheit', 'Medikamente'],
      correct: 1
    },
    {
      q: 'Welcher Satz ist grammatisch korrekt?',
      options: [
        'Ich habe den Patient gewaschen.',
        'Ich habe dem Patient gewaschen.',
        'Ich habe den Patienten gewaschen.',
        'Ich habe der Patient gewaschen.'
      ],
      correct: 2
    },
    {
      q: '"Subkutan" bedeutet die Verabreichung...',
      options: ['in die Vene', 'in den Muskel', 'unter die Haut', 'auf die Haut'],
      correct: 2
    }
  ];

  const [idx, setIdx] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [selected, setSelected] = useState(null);

  const submit = () => {
    const next = [...answers, selected];
    if (idx < questions.length - 1) {
      setAnswers(next);
      setSelected(null);
      setIdx(idx + 1);
    } else {
      const correct = next.filter((a, i) => a === questions[i].correct).length;
      const level = correct <= 1 ? 'A2' : correct <= 2 ? 'B1' : correct <= 3 ? 'B2' : 'C1';
      onComplete(level);
    }
  };

  const progress = ((idx + 1) / questions.length) * 100;

  return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: 40 }}>
      <div style={{ maxWidth: 640, width: '100%' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <span className="chip"><Languages size={12} /> Sprachniveau</span>
          <span style={{ fontSize: 13, color: 'var(--ink-2)' }}>Frage {idx + 1} von {questions.length}</span>
        </div>

        <div style={{ height: 4, background: 'var(--ground-2)', borderRadius: 2, marginBottom: 40 }}>
          <div style={{ width: `${progress}%`, height: '100%', background: 'var(--terracotta)', borderRadius: 2, transition: 'width 0.3s' }} />
        </div>

        <div className="section-num">Aufgabe {String(idx + 1).padStart(2, '0')}</div>
        <h2 style={{ fontSize: 32, lineHeight: 1.2, fontWeight: 500, margin: '12px 0 32px' }}>
          {questions[idx].q}
        </h2>

        <div style={{ display: 'grid', gap: 10 }}>
          {questions[idx].options.map((opt, i) => (
            <button
              key={i}
              onClick={() => setSelected(i)}
              style={{
                textAlign: 'left', padding: '16px 20px', borderRadius: 10,
                border: selected === i ? '1.5px solid var(--terracotta)' : '1px solid var(--cream-border)',
                background: selected === i ? 'rgba(196, 82, 62, 0.06)' : 'var(--paper)',
                cursor: 'pointer', fontSize: 15, color: 'var(--ink)',
                transition: 'all 0.15s'
              }}
            >
              <span style={{ color: 'var(--ink-3)', marginRight: 12, fontSize: 12 }}>{String.fromCharCode(65 + i)}</span>
              {opt}
            </button>
          ))}
        </div>

        <div style={{ marginTop: 36, display: 'flex', justifyContent: 'flex-end' }}>
          <button className="btn-primary" onClick={submit} disabled={selected === null}>
            {idx === questions.length - 1 ? 'Auswerten' : 'Weiter'} <ArrowRight size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}

/* ---------- APP SHELL (Sidebar) ---------- */
function AppShell({ user, role, setRole, screen, setScreen, learningSection, setLearningSection, children }) {
  const studentNav = [
    { key: 'home', label: 'Home', icon: Home },
    { key: 'learning', label: 'Lernen', icon: BookOpen },
    { key: 'gamification', label: 'Ranking', icon: Trophy },
    { key: 'upload', label: 'Materialien', icon: Upload }
  ];

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '240px 1fr', minHeight: '100vh' }}>
      <aside style={{
        background: 'var(--ground-2)', borderRight: '1px solid var(--cream-border)',
        padding: '28px 16px', display: 'flex', flexDirection: 'column', gap: 24
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '0 10px' }}>
          <div style={{ width: 30, height: 30, borderRadius: 7, background: 'var(--terracotta)', display: 'grid', placeItems: 'center' }}>
            <Stethoscope size={16} color="#FBF7EF" />
          </div>
          <span className="display" style={{ fontSize: 18, fontWeight: 600 }}>Kurare</span>
        </div>

        <div style={{
          padding: '4px', background: 'var(--paper)', borderRadius: 10,
          display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, fontSize: 12, fontWeight: 500
        }}>
          <button onClick={() => { setRole('student'); setScreen('home'); }}
            style={{
              padding: '8px 0', borderRadius: 7, border: 'none', cursor: 'pointer',
              background: role === 'student' ? 'var(--ink)' : 'transparent',
              color: role === 'student' ? 'var(--paper)' : 'var(--ink-2)'
            }}>Schüler:in</button>
          <button onClick={() => setRole('teacher')}
            style={{
              padding: '8px 0', borderRadius: 7, border: 'none', cursor: 'pointer',
              background: role === 'teacher' ? 'var(--ink)' : 'transparent',
              color: role === 'teacher' ? 'var(--paper)' : 'var(--ink-2)'
            }}>Schule</button>
        </div>

        {role === 'student' && (
          <nav style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {studentNav.map(n => {
              const Icon = n.icon;
              const active = screen === n.key;
              return (
                <div key={n.key} className={`nav-item ${active ? 'active' : ''}`}
                  onClick={() => { setScreen(n.key); setLearningSection(null); }}>
                  <Icon size={16} /> {n.label}
                </div>
              );
            })}
          </nav>
        )}

        {role === 'teacher' && (
          <nav style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <div className="nav-item active">
              <TrendingUp size={16} /> Dashboard
            </div>
          </nav>
        )}

        <div style={{ marginTop: 'auto', padding: 12, background: 'var(--paper)', borderRadius: 10, border: '1px solid var(--cream-border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ width: 34, height: 34, borderRadius: '50%', background: 'var(--sage)', color: 'var(--paper)', display: 'grid', placeItems: 'center', fontWeight: 600, fontSize: 13 }}>
              {(user.firstName[0] || 'A') + (user.lastName[0] || '')}
            </div>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontSize: 13, fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {user.firstName} {user.lastName}
              </div>
              <div style={{ fontSize: 11, color: 'var(--ink-3)' }}>{user.speciality} · {user.level}</div>
            </div>
          </div>
        </div>
      </aside>

      <main style={{ padding: '36px 48px', maxWidth: 1180 }}>
        {children}
      </main>
    </div>
  );
}

/* ---------- DASHBOARD ---------- */
function Dashboard({ user, setScreen }) {
  return (
    <div>
      <div className="section-num">Heute, {new Date().toLocaleDateString('de-DE', { weekday: 'long', day: 'numeric', month: 'long' })}</div>
      <h1 style={{ fontSize: 42, fontWeight: 500, margin: '10px 0 40px', lineHeight: 1.1 }}>
        Hallo {user.firstName || 'Amara'}, <em style={{ color: 'var(--terracotta)' }}>bereit zu lernen?</em>
      </h1>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 28 }}>
        <Stat icon={Flame} label="Streak" value="12" unit="Tage" tone="terracotta" />
        <Stat icon={Target} label="Heute" value="3/5" unit="Aufgaben" tone="sage" />
        <Stat icon={Ticket} label="Lotterie" value="Fr" unit="in 2 Tagen" tone="honey" />
        <Stat icon={Trophy} label="Rang" value="#14" unit="von 87" tone="ink" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 14 }}>
        <div className="paper-card" style={{ padding: 28 }}>
          <span className="chip" style={{ background: 'rgba(196, 82, 62, 0.12)', color: 'var(--terracotta-dark)' }}>
            <Sparkles size={11} /> Mission des Tages
          </span>
          <h2 style={{ fontSize: 26, fontWeight: 500, margin: '14px 0 10px' }}>
            Vitalzeichen sicher messen
          </h2>
          <p style={{ color: 'var(--ink-2)', fontSize: 14, lineHeight: 1.6, marginBottom: 24, maxWidth: 520 }}>
            10 Minuten: Karteikarten zu Puls, Blutdruck und Atemfrequenz — dann ein kurzes Gespräch mit der KI-Professorin zur Interpretation auffälliger Werte.
          </p>
          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn-primary" onClick={() => setScreen('learning')}>
              Mission starten <ArrowRight size={15} />
            </button>
            <button className="btn-secondary">Später</button>
          </div>
        </div>

        <div className="paper-card" style={{ padding: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
            <span style={{ fontSize: 13, fontWeight: 500 }}>Wochenfortschritt</span>
            <TrendingUp size={14} color="var(--ink-3)" />
          </div>
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 6, height: 80, marginBottom: 14 }}>
            {[45, 72, 30, 88, 60, 95, 40].map((v, i) => (
              <div key={i} style={{ flex: 1, background: i === 5 ? 'var(--terracotta)' : 'var(--ground-2)', height: `${v}%`, borderRadius: 3 }} />
            ))}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--ink-3)', letterSpacing: '0.05em' }}>
            {['M', 'D', 'M', 'D', 'F', 'S', 'S'].map((d, i) => <span key={i}>{d}</span>)}
          </div>
        </div>
      </div>

      <h3 className="display" style={{ fontSize: 22, fontWeight: 500, margin: '44px 0 16px' }}>Schneller Einstieg</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
        <QuickAction icon={MessageSquare} title="KI-Professorin" subtitle="Gespräch starten" onClick={() => setScreen('learning')} highlight />
        <QuickAction icon={BookOpen} title="Karteikarten" subtitle="15 Min. üben" onClick={() => setScreen('learning')} />
        <QuickAction icon={HelpCircle} title="Quiz" subtitle="Schnell testen" onClick={() => setScreen('learning')} />
      </div>
    </div>
  );
}

function Stat({ icon: Icon, label, value, unit, tone }) {
  const colors = {
    terracotta: 'var(--terracotta)',
    sage: 'var(--sage)',
    honey: 'var(--honey)',
    ink: 'var(--ink)'
  };
  return (
    <div className="paper-card" style={{ padding: 18 }}>
      <Icon size={16} color={colors[tone]} />
      <div style={{ fontSize: 11, color: 'var(--ink-3)', margin: '10px 0 4px', letterSpacing: '0.05em', textTransform: 'uppercase' }}>{label}</div>
      <div className="display" style={{ fontSize: 28, fontWeight: 500, lineHeight: 1 }}>{value}</div>
      <div style={{ fontSize: 12, color: 'var(--ink-2)', marginTop: 4 }}>{unit}</div>
    </div>
  );
}

function QuickAction({ icon: Icon, title, subtitle, onClick, highlight }) {
  return (
    <div className="paper-card card-hover" onClick={onClick} style={{
      padding: 20, display: 'flex', alignItems: 'center', gap: 16,
      background: highlight ? 'var(--ink)' : 'var(--paper)',
      color: highlight ? 'var(--paper)' : 'var(--ink)',
      borderColor: highlight ? 'var(--ink)' : 'var(--cream-border)'
    }}>
      <div style={{ width: 38, height: 38, borderRadius: 9, background: highlight ? 'var(--terracotta)' : 'var(--ground-2)', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
        <Icon size={18} color={highlight ? 'var(--paper)' : 'var(--ink)'} />
      </div>
      <div>
        <div style={{ fontSize: 14, fontWeight: 500 }}>{title}</div>
        <div style={{ fontSize: 12, color: highlight ? 'rgba(251,247,239,0.6)' : 'var(--ink-3)', marginTop: 2 }}>{subtitle}</div>
      </div>
    </div>
  );
}

/* ---------- LEARNING HUB ---------- */
function LearningHub({ setLearningSection }) {
  const modules = [
    { key: 'flashcards', icon: BookOpen, title: 'Karteikarten', desc: 'Fachbegriffe mit Spaced-Repetition lernen', time: '10–15 Min', tone: 'terracotta' },
    { key: 'library', icon: Library, title: 'Bibliothek', desc: 'Themen in einfacher Sprache erklärt', time: 'flexibel', tone: 'sage' },
    { key: 'quiz', icon: HelpCircle, title: 'Quiz', desc: 'Single- und Multiple-Choice zu deinem Niveau', time: '5–10 Min', tone: 'honey' },
    { key: 'audio', icon: Headphones, title: 'Audio-Fragen', desc: 'Hörverständnis mit Fachsituationen', time: '10 Min', tone: 'sage' },
    { key: 'professor', icon: MessageSquare, title: 'KI-Professorin', desc: 'Sprachgespräch zum Thema deiner Wahl', time: 'offen', tone: 'terracotta', highlight: true }
  ];

  return (
    <div>
      <div className="section-num">02 — Lernen</div>
      <h1 style={{ fontSize: 40, fontWeight: 500, margin: '10px 0 12px', lineHeight: 1.1 }}>
        Was möchtest du <em style={{ color: 'var(--terracotta)' }}>heute üben?</em>
      </h1>
      <p style={{ color: 'var(--ink-2)', fontSize: 15, maxWidth: 540, marginBottom: 36 }}>
        Fünf Module, eine Lernreise. Kombiniere sie frei — oder folge deiner heutigen Mission.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 14 }}>
        {modules.map(m => {
          const Icon = m.icon;
          return (
            <div key={m.key} className="paper-card card-hover" onClick={() => setLearningSection(m.key)}
              style={{
                padding: 26,
                background: m.highlight ? 'var(--ink)' : 'var(--paper)',
                color: m.highlight ? 'var(--paper)' : 'var(--ink)',
                borderColor: m.highlight ? 'var(--ink)' : 'var(--cream-border)',
                gridColumn: m.highlight ? 'span 2' : 'span 1'
              }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 18 }}>
                <div style={{
                  width: 44, height: 44, borderRadius: 10, flexShrink: 0,
                  background: m.highlight ? 'var(--terracotta)' : `var(--${m.tone === 'terracotta' ? 'terracotta' : m.tone === 'sage' ? 'sage' : 'honey'})`,
                  display: 'grid', placeItems: 'center'
                }}>
                  <Icon size={20} color="#FBF7EF" />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                    <h3 className="display" style={{ fontSize: 20, fontWeight: 500 }}>{m.title}</h3>
                    {m.highlight && <span className="chip" style={{ background: 'var(--terracotta)', color: '#FBF7EF', border: 'none' }}>Voice</span>}
                  </div>
                  <p style={{ fontSize: 14, color: m.highlight ? 'rgba(251,247,239,0.72)' : 'var(--ink-2)', lineHeight: 1.5, marginBottom: 10 }}>
                    {m.desc}
                  </p>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: m.highlight ? 'rgba(251,247,239,0.5)' : 'var(--ink-3)' }}>
                    <Clock size={11} /> {m.time}
                  </div>
                </div>
                <ChevronRight size={16} color={m.highlight ? 'rgba(251,247,239,0.6)' : 'var(--ink-3)'} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ---------- FLASHCARDS ---------- */
function Flashcards({ onBack, onAskProfessor }) {
  const cards = [
    { front: 'Hypertonie', back: 'Bluthochdruck — chronisch erhöhter arterieller Blutdruck über 140/90 mmHg.' },
    { front: 'Dyspnoe', back: 'Atemnot — subjektives Gefühl erschwerter Atmung.' },
    { front: 'Obstipation', back: 'Verstopfung — erschwerte oder seltene Stuhlentleerung.' },
    { front: 'Tachykardie', back: 'Herzrasen — Ruhepuls über 100 Schläge pro Minute.' },
    { front: 'Exsikkose', back: 'Austrocknung — Flüssigkeitsmangel des Körpers.' }
  ];
  const [idx, setIdx] = useState(0);
  const [flipped, setFlipped] = useState(false);

  const askAboutCard = () => {
    const card = cards[idx];
    onAskProfessor({
      source: 'flashcard',
      topic: card.front,
      content: `Karteikarte — Begriff: "${card.front}". Erklärung: "${card.back}"`,
      suggestedQuestion: `Kannst du mir "${card.front}" mit einem praktischen Pflegebeispiel erklären?`
    });
  };

  return (
    <div>
      <BackButton onBack={onBack} section="Karteikarten" />
      <div style={{ maxWidth: 600, margin: '40px auto 0' }}>
        <div style={{ textAlign: 'center', marginBottom: 18, color: 'var(--ink-3)', fontSize: 13 }}>
          Karte {idx + 1} von {cards.length} — Vitalzeichen & Symptome
        </div>

        <div
          className="paper-card flip-enter"
          key={idx + (flipped ? '-b' : '-f')}
          onClick={() => setFlipped(!flipped)}
          style={{
            minHeight: 280, padding: 44, display: 'grid', placeItems: 'center',
            textAlign: 'center', cursor: 'pointer',
            background: flipped ? 'var(--ink)' : 'var(--paper)',
            color: flipped ? 'var(--paper)' : 'var(--ink)'
          }}
        >
          <div>
            <div style={{ fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', color: flipped ? 'rgba(251,247,239,0.5)' : 'var(--ink-3)', marginBottom: 18 }}>
              {flipped ? 'Erklärung' : 'Begriff'}
            </div>
            <div className="display" style={{ fontSize: flipped ? 22 : 42, fontWeight: flipped ? 400 : 500, lineHeight: 1.3 }}>
              {flipped ? cards[idx].back : cards[idx].front}
            </div>
            {!flipped && <div style={{ marginTop: 28, fontSize: 12, color: 'var(--ink-3)' }}>Tippen zum Umdrehen</div>}
          </div>
        </div>

        {flipped && (
          <>
            <button
              onClick={askAboutCard}
              style={{
                width: '100%', marginTop: 14, padding: '14px 18px',
                background: 'var(--sage)', color: 'var(--paper)',
                border: 'none', borderRadius: 10, cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10,
                fontSize: 14, fontWeight: 500
              }}
            >
              <MessageSquare size={16} /> Frag die Professorin zu "{cards[idx].front}"
            </button>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10, marginTop: 10 }}>
              <button className="btn-secondary" style={{ justifyContent: 'center' }} onClick={() => { setIdx((idx + 1) % cards.length); setFlipped(false); }}>
                Schwer
              </button>
              <button className="btn-secondary" style={{ justifyContent: 'center' }} onClick={() => { setIdx((idx + 1) % cards.length); setFlipped(false); }}>
                Okay
              </button>
              <button className="btn-primary" style={{ justifyContent: 'center' }} onClick={() => { setIdx((idx + 1) % cards.length); setFlipped(false); }}>
                Einfach <Check size={15} />
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/* ---------- QUIZ ---------- */
function Quiz({ onBack }) {
  const questions = [
    {
      q: 'Welche Puls-Frequenz gilt bei einem erwachsenen Patienten in Ruhe als normal?',
      options: ['40–60 pro Minute', '60–100 pro Minute', '100–140 pro Minute', '140–180 pro Minute'],
      correct: 1,
      explain: 'Der Normwert des Ruhepulses beim Erwachsenen liegt zwischen 60 und 100 Schlägen pro Minute.'
    },
    {
      q: 'Welche der folgenden sind klassische Anzeichen einer Dehydratation? (Mehrere möglich)',
      options: ['Stehende Hautfalten', 'Trockene Mundschleimhaut', 'Blutdruckanstieg', 'Dunkler Urin'],
      correct: [0, 1, 3],
      multi: true,
      explain: 'Stehende Hautfalten, trockene Schleimhäute und dunkler, konzentrierter Urin deuten auf einen Flüssigkeitsmangel hin. Der Blutdruck fällt bei Dehydratation eher ab.'
    },
    {
      q: 'Was ist die korrekte Reihenfolge der hygienischen Händedesinfektion?',
      options: [
        'Einreiben, Trocknen, Waschen',
        'Waschen, Einreiben für 30 Sek., Trocknen lassen',
        'Desinfektionsmittel für 30 Sekunden in trockene Hände einreiben',
        'Handschuhe anziehen, dann desinfizieren'
      ],
      correct: 2,
      explain: 'Bei der hygienischen Händedesinfektion werden ca. 3 ml Desinfektionsmittel für 30 Sekunden in trockene Hände einmassiert, bis sie trocken sind.'
    }
  ];

  const [idx, setIdx] = useState(0);
  const [selected, setSelected] = useState([]);
  const [showAnswer, setShowAnswer] = useState(false);
  const [score, setScore] = useState(0);

  const q = questions[idx];
  const isMulti = q.multi;

  const toggle = (i) => {
    if (showAnswer) return;
    if (isMulti) {
      setSelected(selected.includes(i) ? selected.filter(x => x !== i) : [...selected, i]);
    } else {
      setSelected([i]);
    }
  };

  const isCorrect = () => {
    if (isMulti) {
      return JSON.stringify([...selected].sort()) === JSON.stringify([...q.correct].sort());
    }
    return selected[0] === q.correct;
  };

  const check = () => {
    if (isCorrect()) setScore(score + 1);
    setShowAnswer(true);
  };

  const next = () => {
    if (idx < questions.length - 1) {
      setIdx(idx + 1); setSelected([]); setShowAnswer(false);
    } else {
      setIdx(0); setSelected([]); setShowAnswer(false); setScore(0);
    }
  };

  return (
    <div>
      <BackButton onBack={onBack} section="Quiz" />
      <div style={{ maxWidth: 680, margin: '30px auto 0' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
          <span className="chip">{isMulti ? 'Mehrfachauswahl' : 'Einfachauswahl'}</span>
          <span style={{ fontSize: 13, color: 'var(--ink-3)' }}>Frage {idx + 1}/{questions.length} · Score {score}</span>
        </div>

        <h2 className="display" style={{ fontSize: 26, fontWeight: 500, lineHeight: 1.3, marginBottom: 24 }}>
          {q.q}
        </h2>

        <div style={{ display: 'grid', gap: 10 }}>
          {q.options.map((opt, i) => {
            const isSel = selected.includes(i);
            const isRight = isMulti ? q.correct.includes(i) : q.correct === i;
            let bg = 'var(--paper)', border = 'var(--cream-border)', textCol = 'var(--ink)';
            if (showAnswer) {
              if (isRight) { bg = 'rgba(61, 91, 66, 0.1)'; border = 'var(--sage)'; }
              else if (isSel) { bg = 'rgba(196, 82, 62, 0.08)'; border = 'var(--terracotta)'; }
            } else if (isSel) {
              border = 'var(--terracotta)'; bg = 'rgba(196, 82, 62, 0.05)';
            }
            return (
              <button key={i} onClick={() => toggle(i)} style={{
                textAlign: 'left', padding: '14px 18px', borderRadius: 10,
                border: `1.5px solid ${border === 'var(--cream-border)' ? 'var(--cream-border)' : border}`,
                background: bg, color: textCol, cursor: showAnswer ? 'default' : 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                fontSize: 14, transition: 'all 0.15s'
              }}>
                <span>{opt}</span>
                {showAnswer && isRight && <Check size={16} color="var(--sage)" />}
                {showAnswer && isSel && !isRight && <X size={16} color="var(--terracotta)" />}
              </button>
            );
          })}
        </div>

        {showAnswer && (
          <div style={{ marginTop: 20, padding: 18, background: 'var(--ground-2)', borderRadius: 10 }}>
            <div style={{ fontSize: 12, fontWeight: 500, color: isCorrect() ? 'var(--sage)' : 'var(--terracotta)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              {isCorrect() ? 'Richtig' : 'Nicht ganz'}
            </div>
            <p style={{ fontSize: 14, lineHeight: 1.6, color: 'var(--ink)' }}>{q.explain}</p>
          </div>
        )}

        <div style={{ marginTop: 24, display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
          {!showAnswer && <button className="btn-primary" onClick={check} disabled={selected.length === 0}>Prüfen</button>}
          {showAnswer && <button className="btn-primary" onClick={next}>{idx === questions.length - 1 ? 'Neu starten' : 'Weiter'} <ArrowRight size={15} /></button>}
        </div>
      </div>
    </div>
  );
}

/* ---------- AUDIO Q&A ---------- */
function AudioQA({ onBack }) {
  const [playing, setPlaying] = useState(false);
  const speak = () => {
    const u = new SpeechSynthesisUtterance('Frau Meier, 78 Jahre, klagt seit zwei Stunden über starke Brustschmerzen, die in den linken Arm ausstrahlen. Welche drei Maßnahmen ergreifen Sie als Erstes?');
    u.lang = 'de-DE'; u.rate = 0.92;
    u.onstart = () => setPlaying(true);
    u.onend = () => setPlaying(false);
    speechSynthesis.speak(u);
  };

  return (
    <div>
      <BackButton onBack={onBack} section="Audio-Fragen" />
      <div style={{ maxWidth: 640, margin: '30px auto 0' }}>
        <span className="chip"><Headphones size={11} /> Fallsituation · B1</span>
        <h2 className="display" style={{ fontSize: 26, fontWeight: 500, margin: '14px 0 24px', lineHeight: 1.3 }}>
          Höre den Fall an und beantworte die Frage.
        </h2>

        <div className="paper-card" style={{ padding: 32, textAlign: 'center' }}>
          <button onClick={speak} disabled={playing} style={{
            width: 64, height: 64, borderRadius: '50%', border: 'none', cursor: 'pointer',
            background: playing ? 'var(--sage)' : 'var(--terracotta)',
            color: 'var(--paper)', display: 'grid', placeItems: 'center', margin: '0 auto'
          }}>
            <Volume2 size={26} />
          </button>
          <div style={{ marginTop: 16, fontSize: 13, color: 'var(--ink-2)' }}>
            {playing ? 'Fall wird vorgelesen…' : 'Klicken zum Abspielen'}
          </div>
          <div style={{ marginTop: 24, display: 'flex', justifyContent: 'center', gap: 4, height: 24 }}>
            {[...Array(16)].map((_, i) => (
              <div key={i} className={playing ? 'wave-bar' : ''} style={{
                width: 3, background: playing ? 'var(--terracotta)' : 'var(--ground-2)',
                borderRadius: 2, height: playing ? undefined : 6, animationDelay: `${i * 0.07}s`
              }} />
            ))}
          </div>
        </div>

        <div style={{ marginTop: 20 }}>
          <label className="label">Deine Antwort</label>
          <textarea className="input" rows="4" placeholder="Tippe deine drei Sofortmaßnahmen…" style={{ resize: 'vertical' }} />
          <button className="btn-primary" style={{ marginTop: 12 }}>Antwort prüfen <ArrowRight size={15} /></button>
        </div>
      </div>
    </div>
  );
}

/* ---------- AI PROFESSOR (VOICE-TO-VOICE) ---------- */
function AIProfessor({ onBack, user, initialContext, clearContext }) {
  const topics = [
    { icon: Heart, label: 'Vitalzeichen', desc: 'Puls, Blutdruck, Atmung' },
    { icon: Shield, label: 'Hygiene', desc: 'Desinfektion & Schutz' },
    { icon: Pill, label: 'Medikamente', desc: 'Verabreichung & Dosierung' },
    { icon: AlertCircle, label: 'Notfall', desc: 'Reanimation, Erstmaßnahmen' },
    { icon: Users, label: 'Kommunikation', desc: 'Gespräch mit Patient:innen' },
    { icon: Sparkles, label: 'Überraschung', desc: 'Thema der KI' }
  ];

  // If context was passed in (from flashcard or library), start directly
  const contextTopic = initialContext ? {
    icon: initialContext.source === 'flashcard' ? BookOpen : Library,
    label: initialContext.topic,
    desc: initialContext.category || (initialContext.source === 'flashcard' ? 'Aus Karteikarte' : 'Aus Bibliothek'),
    contextContent: initialContext.content,
    suggestedQuestion: initialContext.suggestedQuestion
  } : null;

  const [topic, setTopic] = useState(contextTopic);
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [transcript, setTranscript] = useState([]);
  const [currentUser, setCurrentUser] = useState('');
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState(null);
  const [supported, setSupported] = useState(true);
  const [greeted, setGreeted] = useState(false);
  const recognitionRef = useRef(null);
  const transcriptEndRef = useRef(null);

  useEffect(() => {
    if (transcriptEndRef.current) {
      transcriptEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [transcript, thinking]);

  useEffect(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { setSupported(false); return; }
    const rec = new SR();
    rec.lang = 'de-DE';
    rec.continuous = false;
    rec.interimResults = true;
    rec.onresult = (e) => {
      let interim = '';
      let final = '';
      for (let i = e.resultIndex; i < e.results.length; i++) {
        if (e.results[i].isFinal) final += e.results[i][0].transcript;
        else interim += e.results[i][0].transcript;
      }
      setCurrentUser(final || interim);
      if (final) {
        setListening(false);
        handleUserMessage(final);
      }
    };
    rec.onerror = (e) => { setError('Spracherkennung: ' + e.error); setListening(false); };
    rec.onend = () => setListening(false);
    recognitionRef.current = rec;
  }, []);

  // Auto-greeting when arriving with a context
  useEffect(() => {
    if (topic && topic.contextContent && !greeted && transcript.length === 0) {
      setGreeted(true);
      generateGreeting();
    }
  }, [topic, greeted]);

  const generateGreeting = async () => {
    setThinking(true);
    try {
      const response = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 200,
          system: buildSystemPrompt(),
          messages: [{
            role: 'user',
            content: `[Kontext-Wechsel] Die Schülerin kommt gerade aus: ${topic.contextContent}. Begrüße sie kurz (1–2 Sätze), nimm auf den Inhalt Bezug und stelle eine einzige offene Einstiegsfrage, die ihr Verständnis prüft. Keine Listen, keine Zitate — natürlich und warm.`
          }]
        })
      });
      if (!response.ok) throw new Error('API ' + response.status);
      const data = await response.json();
      const reply = data.content.filter(b => b.type === 'text').map(b => b.text).join(' ').trim();
      setTranscript([{ role: 'assistant', text: reply }]);
      setThinking(false);
      speak(reply);
    } catch (e) {
      setError(e.message);
      setThinking(false);
    }
  };

  const buildSystemPrompt = () => {
    const studentName = user.firstName || 'die Schülerin';
    const country = user.country || 'dem Ausland';
    const nativeLang = user.language || 'ihrer Muttersprache';
    const specialty = user.speciality || 'Pflege';
    const level = user.level || 'B1';

    let contextBlock = '';
    if (topic && topic.contextContent) {
      contextBlock = `\n## Aktueller Lernkontext\nDie Schülerin kommt gerade aus einem anderen Lernmodul: ${topic.contextContent}\nNimm auf diesen Inhalt Bezug, ohne ihn stumpf zu wiederholen. Verknüpfe ihn mit konkreten Pflegesituationen.`;
    } else if (topic) {
      contextBlock = `\n## Aktuelles Thema\n${topic.label}${topic.desc ? ' — ' + topic.desc : ''}`;
    }

    // Adapted from user's Python version, tightened for voice output
    return `Du bist Professorin Dr. Weber, eine einfühlsame, geduldige KI-Nachhilfelehrerin für Pflegewissenschaften an einer deutschen Berufsfachschule.

## Über die Schülerin
- Name: ${studentName}
- Herkunftsland: ${country}
- Muttersprache: ${nativeLang}
- Fachrichtung: ${specialty}
- Aktuelles Sprachniveau (Deutsch): ${level}
${contextBlock}

## Deine Aufgaben
- Pflegewissenschaftliche Konzepte verständlich und praxisnah erklären
- Gezielte Fragen stellen, um den Wissensstand einzuschätzen
- Konstruktives, ermutigendes Feedback geben
- Theorie mit konkreten Pflegesituationen aus dem Alltag verknüpfen

## Sprachliche Anpassung
- Passe Wortwahl und Satzbau an Niveau ${level} an: einfache Grammatik, kurze Sätze, bekannte Wörter.
- Wenn ein deutscher Fachbegriff fällt, erkläre ihn beim ersten Auftreten mit einfachen Worten.
- Bei Grammatikfehlern der Schülerin: sanft korrigieren im Kontext ("Genau — man sagt: ..."), nie wie eine Lehrerin mit Rotstift.
- Falls hilfreich, kannst du ein Wort in ${nativeLang} vergleichen — aber nur, wenn es den Lernfluss wirklich unterstützt.

## Lernfortschritt
- Merke dir, was besprochen wurde, und baue darauf auf.
- Erkenne Wissenslücken und adressiere sie behutsam.
- Steigere den Schwierigkeitsgrad schrittweise.

## Format (ZWINGEND, weil Audio vorgelesen wird)
- IMMER auf Deutsch.
- Antworten SEHR KURZ: 2–3 Sätze, maximal 50 Wörter.
- Nur fließender Text — keine Listen, keine Aufzählungen, kein Markdown, keine Sonderzeichen.
- Sprich natürlich und warm, wie ein echtes Gespräch.
- Ende oft mit einer einzelnen Rückfrage, die das Gespräch offen hält.

## Persönlichkeit
Freundlich, geduldig, nie herablassend. Lobt echte Fortschritte, keine leeren Floskeln.`;
  };

  const start = () => {
    if (!recognitionRef.current || speaking || thinking) return;
    setError(null); setCurrentUser(''); setListening(true);
    try { recognitionRef.current.start(); } catch (e) { /* already started */ }
  };

  const stop = () => {
    if (recognitionRef.current) recognitionRef.current.stop();
    setListening(false);
  };

  const speak = (text) => {
    const u = new SpeechSynthesisUtterance(text);
    u.lang = 'de-DE'; u.rate = 0.96; u.pitch = 1.02;
    const voices = speechSynthesis.getVoices();
    const deVoice = voices.find(v => v.lang.startsWith('de') && v.name.toLowerCase().includes('female'))
                 || voices.find(v => v.lang.startsWith('de'));
    if (deVoice) u.voice = deVoice;
    u.onstart = () => setSpeaking(true);
    u.onend = () => setSpeaking(false);
    speechSynthesis.speak(u);
  };

  const handleUserMessage = async (text) => {
    if (!text.trim()) return;
    const newTranscript = [...transcript, { role: 'user', text }];
    setTranscript(newTranscript);
    setCurrentUser(''); setThinking(true); setError(null);

    try {
      const messages = newTranscript.map(m => ({
        role: m.role === 'user' ? 'user' : 'assistant',
        content: m.text
      }));

      const response = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 300,
          system: buildSystemPrompt(),
          messages
        })
      });

      if (!response.ok) throw new Error('API-Fehler: ' + response.status);
      const data = await response.json();
      const reply = data.content.filter(b => b.type === 'text').map(b => b.text).join(' ').trim();

      setTranscript([...newTranscript, { role: 'assistant', text: reply }]);
      setThinking(false);
      speak(reply);
    } catch (e) {
      setError(e.message);
      setThinking(false);
    }
  };

  const useSuggested = () => {
    if (topic && topic.suggestedQuestion) {
      handleUserMessage(topic.suggestedQuestion);
    }
  };

  const reset = () => {
    setTopic(null); setTranscript([]); setCurrentUser(''); setError(null); setGreeted(false);
    if (clearContext) clearContext();
    speechSynthesis.cancel();
  };

  if (!topic) {
    return (
      <div>
        <BackButton onBack={onBack} section="KI-Professorin" />
        <div style={{ maxWidth: 720, margin: '20px auto 0' }}>
          <div className="section-num">Voice-to-Voice · Beta</div>
          <h1 style={{ fontSize: 36, fontWeight: 500, margin: '10px 0 12px', lineHeight: 1.1 }}>
            Worüber möchtest du <em style={{ color: 'var(--terracotta)' }}>sprechen?</em>
          </h1>
          <p style={{ color: 'var(--ink-2)', fontSize: 15, marginBottom: 32, maxWidth: 520 }}>
            Wähle ein Thema — die Professorin stellt dir Fragen, du antwortest per Stimme. Sie passt sich deinem Niveau {user.level} an.
          </p>

          {!supported && (
            <div className="paper-card" style={{ padding: 16, marginBottom: 20, background: 'rgba(196, 82, 62, 0.08)', borderColor: 'var(--terracotta)' }}>
              <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--terracotta-dark)' }}>
                Hinweis: Dein Browser unterstützt keine Spracherkennung. Chrome oder Safari nutzen.
              </div>
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
            {topics.map(t => {
              const Icon = t.icon;
              return (
                <div key={t.label} className="paper-card card-hover" onClick={() => setTopic(t)}
                  style={{ padding: 20 }}>
                  <Icon size={20} color="var(--terracotta)" style={{ marginBottom: 14 }} />
                  <div className="display" style={{ fontSize: 17, fontWeight: 500, marginBottom: 4 }}>{t.label}</div>
                  <div style={{ fontSize: 12, color: 'var(--ink-3)' }}>{t.desc}</div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <BackButton onBack={onBack} section="KI-Professorin" />

      <div style={{ maxWidth: 780, margin: '20px auto 0' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 18 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{ width: 42, height: 42, borderRadius: '50%', background: 'var(--sage)', color: 'var(--paper)', display: 'grid', placeItems: 'center' }}>
              <Brain size={20} />
            </div>
            <div>
              <div className="display" style={{ fontSize: 16, fontWeight: 500 }}>Prof. Dr. Weber</div>
              <div style={{ fontSize: 12, color: 'var(--ink-3)' }}>Thema: {topic.label}</div>
            </div>
          </div>
          <button className="btn-secondary" onClick={reset} style={{ padding: '8px 14px', fontSize: 13 }}>
            <RotateCw size={13} /> Neues Thema
          </button>
        </div>

        {topic.contextContent && (
          <div style={{
            padding: '12px 16px', marginBottom: 14,
            background: 'rgba(61, 91, 66, 0.08)', borderLeft: '3px solid var(--sage)',
            borderRadius: '0 8px 8px 0', fontSize: 12, color: 'var(--ink-2)', lineHeight: 1.5
          }}>
            <strong style={{ color: 'var(--sage-dark)', fontWeight: 500 }}>Kontext aus {initialContext?.source === 'flashcard' ? 'Karteikarte' : 'Bibliothek'}:</strong>{' '}
            {topic.contextContent.replace(/^[^:]+:\s*/, '')}
          </div>
        )}

        <div className="paper-card" style={{ padding: 24, minHeight: 320, maxHeight: 400, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 14 }}>
          {transcript.length === 0 && !thinking && (
            <div style={{ margin: 'auto', textAlign: 'center', color: 'var(--ink-3)', fontSize: 14, maxWidth: 320 }}>
              <Mic size={24} style={{ margin: '0 auto 12px', display: 'block' }} />
              Drücke das Mikrofon und stelle deine erste Frage — die Professorin hört zu.
            </div>
          )}
          {transcript.map((m, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
              <div style={{
                maxWidth: '78%', padding: '12px 16px', borderRadius: 14,
                background: m.role === 'user' ? 'var(--ink)' : 'var(--ground-2)',
                color: m.role === 'user' ? 'var(--paper)' : 'var(--ink)',
                fontSize: 14, lineHeight: 1.55
              }}>
                {m.text}
              </div>
            </div>
          ))}
          {currentUser && listening && (
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <div style={{ maxWidth: '78%', padding: '12px 16px', borderRadius: 14, background: 'var(--ink)', color: 'var(--paper)', opacity: 0.5, fontSize: 14, fontStyle: 'italic' }}>
                {currentUser}…
              </div>
            </div>
          )}
          {thinking && (
            <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
              <div style={{ padding: '12px 16px', borderRadius: 14, background: 'var(--ground-2)', color: 'var(--ink-3)', fontSize: 13, display: 'flex', gap: 6, alignItems: 'center' }}>
                <span>denkt nach</span>
                <span style={{ display: 'inline-flex', gap: 3 }}>
                  <span style={{ width: 4, height: 4, borderRadius: '50%', background: 'var(--ink-3)', animation: 'pulse-mic 1s infinite' }} />
                  <span style={{ width: 4, height: 4, borderRadius: '50%', background: 'var(--ink-3)', animation: 'pulse-mic 1s infinite', animationDelay: '0.15s' }} />
                  <span style={{ width: 4, height: 4, borderRadius: '50%', background: 'var(--ink-3)', animation: 'pulse-mic 1s infinite', animationDelay: '0.3s' }} />
                </span>
              </div>
            </div>
          )}
          <div ref={transcriptEndRef} />
        </div>

        {error && (
          <div style={{ marginTop: 12, padding: 12, background: 'rgba(196,82,62,0.08)', borderRadius: 8, fontSize: 12, color: 'var(--terracotta-dark)' }}>
            {error}
          </div>
        )}

        {topic.suggestedQuestion && transcript.length <= 1 && !thinking && (
          <button
            onClick={useSuggested}
            style={{
              marginTop: 14, padding: '10px 14px', width: '100%',
              background: 'var(--paper)', color: 'var(--ink-2)',
              border: '1px dashed var(--cream-border)', borderRadius: 8, cursor: 'pointer',
              fontSize: 13, textAlign: 'left'
            }}
          >
            <span style={{ color: 'var(--ink-3)', fontSize: 11, letterSpacing: '0.05em', textTransform: 'uppercase', marginRight: 8 }}>Vorschlag:</span>
            "{topic.suggestedQuestion}"
          </button>
        )}

        <div style={{ marginTop: 24, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
          <button
            onClick={listening ? stop : start}
            disabled={!supported || speaking || thinking}
            className={listening ? 'mic-pulse' : ''}
            style={{
              width: 76, height: 76, borderRadius: '50%', border: 'none', cursor: supported ? 'pointer' : 'not-allowed',
              background: listening ? 'var(--terracotta)' : speaking ? 'var(--sage)' : 'var(--ink)',
              color: 'var(--paper)', display: 'grid', placeItems: 'center',
              opacity: (!supported || thinking) ? 0.5 : 1,
              transition: 'background 0.2s'
            }}
          >
            {listening ? <MicOff size={28} /> : speaking ? <Volume2 size={28} /> : <Mic size={28} />}
          </button>
          <div style={{ fontSize: 12, color: 'var(--ink-3)', height: 16 }}>
            {listening ? 'Höre zu — klicken zum Beenden' :
             speaking ? 'Professorin spricht…' :
             thinking ? 'Antwort wird formuliert…' :
             'Tippen zum Sprechen'}
          </div>
          {listening && (
            <div style={{ display: 'flex', gap: 4, height: 20, marginTop: 4 }}>
              {[...Array(12)].map((_, i) => (
                <div key={i} className="wave-bar" style={{ animationDelay: `${i * 0.06}s` }} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ---------- LIBRARY ---------- */
function LibraryView({ onBack, onAskProfessor }) {
  const [simple, setSimple] = useState(true);
  const topics = [
    { title: 'Blutdruck messen', cat: 'Vitalzeichen',
      simple: 'Blutdruck ist der Druck, mit dem das Blut gegen die Wände der Adern drückt. Wir messen zwei Werte: den hohen Wert (wenn das Herz drückt) und den niedrigen Wert (wenn das Herz ruht). Normal ist etwa 120 zu 80.',
      pro: 'Der arterielle Blutdruck wird als systolischer und diastolischer Wert erfasst. Die Messung erfolgt palpatorisch oder auskultatorisch nach Riva-Rocci, typischerweise an der A. brachialis. Normwerte liegen bei 120/80 mmHg.'
    },
    { title: 'Dekubitus-Prophylaxe', cat: 'Pflegetechnik',
      simple: 'Ein Dekubitus ist eine Wunde, die entsteht, wenn jemand lange auf einer Stelle liegt. Wir können das verhindern: die Person oft drehen, die Haut trocken halten und auf rote Stellen achten.',
      pro: 'Der Dekubitus entsteht durch prolongierten Auflagedruck mit konsekutiver Minderperfusion. Prävention umfasst die Umlagerung nach individuellem Bewegungsplan, Hautinspektion, Mobilisation sowie den Einsatz druckreduzierender Hilfsmittel gemäß Expertenstandard.'
    },
    { title: 'Hygienische Händedesinfektion', cat: 'Hygiene',
      simple: 'Hände werden nicht gewaschen, sondern mit einem speziellen Mittel eingerieben. Etwa drei Milliliter nehmen, 30 Sekunden alle Stellen der Hand reiben, dann trocknen lassen.',
      pro: 'Die hygienische Händedesinfektion nach VAH-Richtlinie: ca. 3 ml alkoholisches Desinfektionsmittel auf trockene Hände, 30 s Einwirkzeit, Berücksichtigung der Sechs-Schritte-Technik nach EN 1500.'
    }
  ];

  const askAboutTopic = (topic) => {
    const text = simple ? topic.simple : topic.pro;
    onAskProfessor({
      source: 'library',
      topic: topic.title,
      category: topic.cat,
      content: `Bibliotheksartikel "${topic.title}" (${topic.cat}) in ${simple ? 'einfacher Sprache' : 'Fachsprache'}: "${text}"`,
      suggestedQuestion: `Ich habe gerade über "${topic.title}" gelesen. Können wir das gemeinsam vertiefen?`
    });
  };

  return (
    <div>
      <BackButton onBack={onBack} section="Bibliothek" />
      <div style={{ maxWidth: 760, margin: '20px auto 0' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 24 }}>
          <div>
            <div className="section-num">03 — Bibliothek</div>
            <h1 style={{ fontSize: 32, fontWeight: 500, margin: '8px 0 0' }}>Themen zum Nachlesen</h1>
          </div>
          <div style={{ padding: 4, background: 'var(--ground-2)', borderRadius: 10, display: 'flex', fontSize: 12, fontWeight: 500 }}>
            <button onClick={() => setSimple(true)} style={{
              padding: '8px 14px', borderRadius: 7, border: 'none', cursor: 'pointer',
              background: simple ? 'var(--ink)' : 'transparent', color: simple ? 'var(--paper)' : 'var(--ink-2)'
            }}>Einfache Sprache</button>
            <button onClick={() => setSimple(false)} style={{
              padding: '8px 14px', borderRadius: 7, border: 'none', cursor: 'pointer',
              background: !simple ? 'var(--ink)' : 'transparent', color: !simple ? 'var(--paper)' : 'var(--ink-2)'
            }}>Fachsprache</button>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {topics.map((t, i) => (
            <div key={i} className="paper-card" style={{ padding: 22 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16 }}>
                <div style={{ flex: 1 }}>
                  <span className="chip">{t.cat}</span>
                  <h3 className="display" style={{ fontSize: 20, fontWeight: 500, margin: '10px 0 8px' }}>{t.title}</h3>
                  <p style={{ fontSize: 14, lineHeight: 1.65, color: 'var(--ink-2)' }}>
                    {simple ? t.simple : t.pro}
                  </p>
                </div>
              </div>
              <button
                onClick={() => askAboutTopic(t)}
                style={{
                  marginTop: 14, padding: '10px 14px',
                  background: 'transparent', color: 'var(--sage-dark)',
                  border: '1px solid var(--sage)', borderRadius: 8, cursor: 'pointer',
                  display: 'inline-flex', alignItems: 'center', gap: 8,
                  fontSize: 13, fontWeight: 500
                }}
              >
                <MessageSquare size={14} /> Mit Professorin vertiefen
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ---------- GAMIFICATION ---------- */
function Gamification({ user }) {
  const leaderboard = [
    { rank: 1, name: 'Mohamed K.', points: 4820, streak: 31 },
    { rank: 2, name: 'Linh N.', points: 4510, streak: 24 },
    { rank: 3, name: 'Patricia S.', points: 4205, streak: 19 },
    { rank: 4, name: 'Ahmed H.', points: 3980, streak: 15 },
    { rank: 5, name: 'Yuki T.', points: 3720, streak: 22 },
    { rank: 14, name: (user.firstName || 'Amara') + ' ' + ((user.lastName || 'O')[0]) + '.', points: 2140, streak: 12, me: true }
  ];

  return (
    <div>
      <div className="section-num">03 — Ranking & Missionen</div>
      <h1 style={{ fontSize: 40, fontWeight: 500, margin: '10px 0 8px', lineHeight: 1.1 }}>
        Jeden Freitag <em style={{ color: 'var(--terracotta)' }}>gewinnen drei</em> einen Kantinengutschein.
      </h1>
      <p style={{ color: 'var(--ink-2)', fontSize: 15, maxWidth: 520, marginBottom: 36 }}>
        Deine Position beeinflusst deine Gewinnchance — aber auch Platz 50 kann ziehen.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 14 }}>
        <div className="paper-card" style={{ padding: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 18 }}>
            <h3 className="display" style={{ fontSize: 18, fontWeight: 500 }}>Wochen-Leaderboard</h3>
            <span className="chip"><Trophy size={11} /> Kalenderwoche 16</span>
          </div>
          <div>
            {leaderboard.map(p => (
              <div key={p.rank} style={{
                display: 'grid', gridTemplateColumns: '40px 1fr auto auto', gap: 14, alignItems: 'center',
                padding: '12px 0', borderBottom: '1px solid var(--cream-border)',
                background: p.me ? 'rgba(196, 82, 62, 0.05)' : 'transparent',
                marginLeft: p.me ? -12 : 0, marginRight: p.me ? -12 : 0,
                paddingLeft: p.me ? 12 : 0, paddingRight: p.me ? 12 : 0,
                borderRadius: p.me ? 8 : 0
              }}>
                <div className="display" style={{ fontSize: p.rank <= 3 ? 22 : 16, fontWeight: 500, color: p.rank === 1 ? 'var(--terracotta)' : p.rank <= 3 ? 'var(--honey)' : 'var(--ink-3)' }}>
                  {p.rank}
                </div>
                <div style={{ fontWeight: p.me ? 500 : 400, fontSize: 14 }}>
                  {p.name} {p.me && <span className="chip" style={{ marginLeft: 6, padding: '2px 8px' }}>Du</span>}
                </div>
                <div style={{ fontSize: 12, color: 'var(--ink-3)', display: 'flex', alignItems: 'center', gap: 4 }}>
                  <Flame size={11} /> {p.streak}
                </div>
                <div className="display" style={{ fontSize: 15, fontWeight: 500 }}>{p.points.toLocaleString('de')}</div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="paper-card" style={{ padding: 22, background: 'var(--ink)', color: 'var(--paper)', borderColor: 'var(--ink)' }}>
            <Ticket size={20} style={{ marginBottom: 12 }} />
            <div style={{ fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase', opacity: 0.6, marginBottom: 6 }}>Lotterie</div>
            <div className="display" style={{ fontSize: 24, fontWeight: 500, lineHeight: 1.2, marginBottom: 8 }}>
              Freitag · 14:00
            </div>
            <div style={{ fontSize: 13, lineHeight: 1.5, opacity: 0.7 }}>
              Drei Schüler:innen gewinnen einen 10 €-Gutschein für die Kantine.
            </div>
          </div>
          <div className="paper-card" style={{ padding: 22 }}>
            <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 12 }}>Heutige Ziele</div>
            {[
              { label: '3 Karteikarten-Runden', done: true },
              { label: '1 Gespräch mit Prof. Weber', done: true },
              { label: '1 Quiz abschließen', done: true },
              { label: 'Streak halten', done: false },
              { label: 'Neue Lektion starten', done: false }
            ].map((g, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '6px 0', fontSize: 13, color: g.done ? 'var(--ink-3)' : 'var(--ink)', textDecoration: g.done ? 'line-through' : 'none' }}>
                <div style={{ width: 16, height: 16, borderRadius: 4, border: '1.5px solid', borderColor: g.done ? 'var(--sage)' : 'var(--cream-border)', background: g.done ? 'var(--sage)' : 'transparent', display: 'grid', placeItems: 'center' }}>
                  {g.done && <Check size={10} color="var(--paper)" />}
                </div>
                {g.label}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------- UPLOAD ---------- */
function UploadView() {
  const files = [
    { name: 'Skript_Vitalzeichen.pdf', size: '2.4 MB', status: 'Verarbeitet', cards: 42 },
    { name: 'Hygiene_Richtlinien_2026.docx', size: '890 KB', status: 'Verarbeitet', cards: 18 },
    { name: 'Pharmakologie_Grundlagen.pdf', size: '5.1 MB', status: 'In Bearbeitung', cards: null }
  ];
  return (
    <div>
      <div className="section-num">04 — Materialien</div>
      <h1 style={{ fontSize: 36, fontWeight: 500, margin: '10px 0 8px', lineHeight: 1.1 }}>
        Eigene Unterlagen <em style={{ color: 'var(--terracotta)' }}>hochladen.</em>
      </h1>
      <p style={{ color: 'var(--ink-2)', fontSize: 15, marginBottom: 32, maxWidth: 520 }}>
        Die KI liest dein Skript und erstellt automatisch Karteikarten, Quiz-Fragen und Fallszenarien.
      </p>

      <div className="paper-card" style={{ padding: 40, textAlign: 'center', borderStyle: 'dashed', marginBottom: 28 }}>
        <Upload size={28} color="var(--terracotta)" style={{ marginBottom: 14 }} />
        <div className="display" style={{ fontSize: 20, fontWeight: 500, marginBottom: 6 }}>Datei hier ablegen</div>
        <div style={{ fontSize: 13, color: 'var(--ink-3)', marginBottom: 18 }}>PDF, DOCX oder TXT · max. 20 MB</div>
        <button className="btn-primary">Datei auswählen</button>
      </div>

      <h3 style={{ fontSize: 14, fontWeight: 500, marginBottom: 12, color: 'var(--ink-2)' }}>Zuletzt hochgeladen</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {files.map((f, i) => (
          <div key={i} className="paper-card" style={{ padding: 18, display: 'flex', alignItems: 'center', gap: 16 }}>
            <div style={{ width: 36, height: 36, borderRadius: 8, background: 'var(--ground-2)', display: 'grid', placeItems: 'center' }}>
              <BookOpen size={16} color="var(--ink-2)" />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 14, fontWeight: 500 }}>{f.name}</div>
              <div style={{ fontSize: 12, color: 'var(--ink-3)' }}>{f.size} · {f.status}{f.cards ? ` · ${f.cards} Karten erstellt` : ''}</div>
            </div>
            <ChevronRight size={16} color="var(--ink-3)" />
          </div>
        ))}
      </div>
    </div>
  );
}

/* ---------- TEACHER DASHBOARD ---------- */
function TeacherDashboard() {
  const classData = [
    { week: 'KW 12', active: 62 },
    { week: 'KW 13', active: 71 },
    { week: 'KW 14', active: 78 },
    { week: 'KW 15', active: 81 },
    { week: 'KW 16', active: 87 }
  ];
  const topics = [
    { topic: 'Vitalzeichen', mastery: 78 },
    { topic: 'Hygiene', mastery: 65 },
    { topic: 'Medikamente', mastery: 42 },
    { topic: 'Kommunikation', mastery: 71 },
    { topic: 'Notfall', mastery: 38 }
  ];
  const max = Math.max(...classData.map(d => d.active));

  return (
    <div>
      <div className="section-num">Schulsicht · Berufsfachschule Hannover</div>
      <h1 style={{ fontSize: 38, fontWeight: 500, margin: '10px 0 8px', lineHeight: 1.1 }}>
        Klasse PA-24: <em style={{ color: 'var(--terracotta)' }}>87 aktive</em> Schüler:innen.
      </h1>
      <p style={{ color: 'var(--ink-2)', fontSize: 15, marginBottom: 32, maxWidth: 540 }}>
        Nutzung, Fortschritt und Schwachstellen der Klasse — damit du deinen Unterricht gezielt ansetzen kannst.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 28 }}>
        <Stat icon={Users} label="Aktiv" value="87" unit="von 92" tone="sage" />
        <Stat icon={Clock} label="Ø Nutzung" value="34" unit="Min/Tag" tone="terracotta" />
        <Stat icon={TrendingUp} label="Fortschritt" value="+18%" unit="vs. KW 12" tone="sage" />
        <Stat icon={AlertCircle} label="Achtung" value="7" unit="Schüler:innen" tone="terracotta" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
        <div className="paper-card" style={{ padding: 24 }}>
          <h3 className="display" style={{ fontSize: 17, fontWeight: 500, marginBottom: 18 }}>Aktive Schüler:innen pro Woche</h3>
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 14, height: 140, padding: '0 10px 20px' }}>
            {classData.map((d, i) => (
              <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
                <div style={{ fontSize: 11, color: 'var(--ink-2)' }}>{d.active}</div>
                <div style={{ width: '100%', background: i === classData.length - 1 ? 'var(--terracotta)' : 'var(--ground-2)', height: `${(d.active / max) * 100}%`, borderRadius: 4, minHeight: 4 }} />
                <div style={{ fontSize: 10, color: 'var(--ink-3)', letterSpacing: '0.05em' }}>{d.week}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="paper-card" style={{ padding: 24 }}>
          <h3 className="display" style={{ fontSize: 17, fontWeight: 500, marginBottom: 18 }}>Themenbeherrschung</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {topics.map((t, i) => (
              <div key={i}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 5 }}>
                  <span>{t.topic}</span>
                  <span style={{ color: t.mastery < 50 ? 'var(--terracotta)' : 'var(--ink-2)', fontWeight: 500 }}>{t.mastery}%</span>
                </div>
                <div style={{ height: 6, background: 'var(--ground-2)', borderRadius: 3 }}>
                  <div style={{ width: `${t.mastery}%`, height: '100%', background: t.mastery < 50 ? 'var(--terracotta)' : 'var(--sage)', borderRadius: 3 }} />
                </div>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 18, padding: 14, background: 'rgba(196,82,62,0.06)', borderRadius: 8, fontSize: 12, color: 'var(--terracotta-dark)', lineHeight: 1.5 }}>
            <strong style={{ fontWeight: 500 }}>Empfehlung:</strong> Medikamentenlehre und Notfall in der nächsten Einheit vertiefen.
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------- UTILS ---------- */
function BackButton({ onBack, section }) {
  return (
    <button onClick={onBack} style={{
      display: 'inline-flex', alignItems: 'center', gap: 6, padding: '6px 0',
      background: 'transparent', border: 'none', cursor: 'pointer',
      color: 'var(--ink-2)', fontSize: 13
    }}>
      <ChevronLeft size={16} /> {section}
    </button>
  );
}
