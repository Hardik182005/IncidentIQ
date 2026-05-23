// =============================================
// VOICE-ORB.JSX — The star feature
// =============================================
const { useState, useEffect, useRef } = React;

// Same-origin when served by the FastAPI backend (Cloud Run); falls back to a
// local dev server when the page is opened directly from disk.
const API_BASE = (typeof location !== 'undefined' && location.protocol.startsWith('http'))
  ? '' : 'http://127.0.0.1:8000';

// Fallback replies used only when the /api/chat call fails (offline demo mode).
const RESPONSES = [
  'Root cause confirmed: PostgreSQL connection pool exhaustion on payments-api. The idle_timeout was set to 300s in the last deploy. I recommend draining idle connections and scaling the pool to 200 immediately.',
  'The auth-service JWT latency spike correlates with the cert renewal 11 minutes ago. The JWKS endpoint cache appears stale — force a cache refresh on all auth-service pods.',
  'Three services in degraded state right now: payments-api critical, auth-service high, notification-worker medium. Cascade risk is elevated — recommend activating runbook INC-2847-RB.',
];

const CHIPS = ['What\'s the root cause?', 'How do I fix this?', 'Which service is affected?'];

function VoiceOrb({ externalMessage, onExternalDone, incidentId }) {
  const [state, setState] = useState('idle');
  const [bars, setBars]   = useState([30, 50, 40, 60, 35]);
  const [transcript, setTranscript] = useState('');
  const [response, setResponse]     = useState('');
  const [showChips, setShowChips]   = useState(true);
  const timers  = useRef([]);
  const barLoop = useRef(null);

  function clearAll() {
    timers.current.forEach(clearTimeout);
    timers.current = [];
    clearInterval(barLoop.current);
    barLoop.current = null;
  }

  function typewrite(text, setter) {
    let i = 0;
    function tick() {
      if (i >= text.length) return;
      setter(p => p + text[i++]);
      timers.current.push(setTimeout(tick, 20));
    }
    tick();
  }

  function startBars(color) {
    clearInterval(barLoop.current);
    barLoop.current = setInterval(() => setBars(Array.from({length:5}, () => 15 + Math.random()*70)), 90);
  }

  async function askBackend(question) {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: question, incident_id: incidentId || null }),
    });
    const data = await res.json();
    if (!res.ok || !data) throw new Error(data?.error || `HTTP ${res.status}`);
    // Backend wraps payloads as { success, data: { response }, error }.
    const answer = data.data?.response ?? data.response;
    if (!answer) throw new Error('empty response');
    return answer;
  }

  function activate(query) {
    if (state !== 'idle') return;
    clearAll(); setShowChips(false); setTranscript(''); setResponse('');
    setState('listening');
    startBars();
    const question = query || 'What is the current incident status?';

    const t1 = setTimeout(() => {
      clearInterval(barLoop.current); setState('processing');
      typewrite(question, setTranscript);

      // Real conversational answer from the 3-stage pipeline's OpenAI layer;
      // canned reply only if the backend is unreachable (static demo).
      askBackend(question)
        .catch(() => RESPONSES[Math.floor(Math.random() * RESPONSES.length)])
        .then(answer => {
          setState('speaking');
          startBars();
          setResponse('');
          typewrite(answer, setResponse);

          const hold = Math.min(16000, 4500 + answer.length * 28);
          const t3 = setTimeout(() => {
            clearAll(); setState('idle'); setTranscript(''); setResponse(''); setShowChips(true);
          }, hold);
          timers.current.push(t3);
        });
    }, 2800);
    timers.current.push(t1);
  }

  useEffect(() => {
    if (!externalMessage || state !== 'idle') return;
    clearAll(); setShowChips(false); setTranscript(''); setResponse('');
    setState('speaking'); startBars();
    typewrite(externalMessage, setResponse);
    const t = setTimeout(() => {
      clearAll(); setState('idle'); setResponse(''); setShowChips(true);
      onExternalDone?.();
    }, 5500);
    timers.current.push(t);
  }, [externalMessage]);

  useEffect(() => () => clearAll(), []);

  const sizes = { idle:80, listening:94, processing:84, speaking:92 };
  const speeds = { idle:'4.5s', listening:'0.85s', processing:'0.45s', speaking:'1.3s' };
  const grads = {
    idle:      '#3B82F6,#06B6D4,#8B5CF6,#3B82F6',
    listening: '#06B6D4,#10B981,#3B82F6,#06B6D4',
    processing:'#F59E0B,#EF4444,#F97316,#F59E0B',
    speaking:  '#8B5CF6,#3B82F6,#06B6D4,#8B5CF6',
  };
  const sz = sizes[state];

  return (
    <div style={{
      position: 'fixed', bottom: '28px', right: '28px', zIndex: 1000,
      display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '10px',
    }}>

      {/* Speech / transcript bubble */}
      {(response || transcript) && (
        <div style={{
          background: 'rgba(6,6,18,0.94)', border: '1px solid rgba(255,255,255,0.11)',
          borderRadius: '12px 12px 4px 12px', padding: '12px 15px', maxWidth: '300px',
          backdropFilter: 'blur(24px)', animation: 'float-up 0.3s ease both',
          boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
        }}>
          {transcript && (
            <p style={{
              color: '#06B6D4', fontSize: '11px', fontFamily: "'JetBrains Mono', monospace",
              fontStyle: 'italic', marginBottom: response ? '8px' : 0,
            }}>"{transcript}"</p>
          )}
          {response && (
            <p style={{ color: '#eeeef5', fontSize: '12px', lineHeight: '1.65', fontFamily: "'Space Grotesk', sans-serif" }}>
              {response}
              {state === 'speaking' && (
                <span style={{ display:'inline-block', width:'7px', height:'13px', background:'#8B5CF6', marginLeft:'2px', verticalAlign:'text-bottom', animation:'flicker 0.6s infinite' }} />
              )}
            </p>
          )}
        </div>
      )}

      {/* Suggestion chips */}
      {showChips && state === 'idle' && (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '6px', animation: 'fade-in 0.6s ease' }}>
          {CHIPS.map((chip, i) => (
            <button key={i} onClick={() => activate(chip)} style={{
              background: 'rgba(255,255,255,0.048)', border: '1px solid rgba(255,255,255,0.09)',
              borderRadius: '20px', padding: '6px 14px', color: '#9898b0', fontSize: '11px',
              cursor: 'pointer', transition: 'all 0.2s', fontFamily: "'Space Grotesk', sans-serif",
              backdropFilter: 'blur(10px)', whiteSpace: 'nowrap',
            }}
            onMouseEnter={e => { e.target.style.background='rgba(59,130,246,0.14)'; e.target.style.color='#60A5FA'; e.target.style.borderColor='rgba(59,130,246,0.3)'; }}
            onMouseLeave={e => { e.target.style.background='rgba(255,255,255,0.048)'; e.target.style.color='#9898b0'; e.target.style.borderColor='rgba(255,255,255,0.09)'; }}
            >{chip}</button>
          ))}
        </div>
      )}

      {/* Orb wrapper */}
      <div
        onClick={() => activate(null)}
        style={{
          position: 'relative', cursor: state==='idle' ? 'pointer' : 'default',
          width: sz+6+'px', height: sz+6+'px',
          transition: 'width 0.35s cubic-bezier(0.34,1.3,0.64,1), height 0.35s cubic-bezier(0.34,1.3,0.64,1)',
        }}
      >
        {/* Outer ambient glow */}
        <div style={{
          position: 'absolute', inset: '-18px', borderRadius: '50%',
          background: `radial-gradient(circle, ${state==='processing'?'rgba(245,158,11,0.15)':state==='listening'?'rgba(6,182,212,0.15)':state==='speaking'?'rgba(139,92,246,0.15)':'rgba(59,130,246,0.12)'}, transparent 70%)`,
          animation: 'breathe 2.8s ease-in-out infinite', pointerEvents: 'none',
        }} />

        {/* Spinning conic-gradient ring */}
        <div style={{
          position: 'absolute', inset: 0, borderRadius: '50%',
          background: `conic-gradient(${grads[state]})`,
          animation: `spin ${speeds[state]} linear infinite`,
        }} />

        {/* Inner orb */}
        <div style={{
          position: 'absolute', inset: '3px', borderRadius: '50%',
          background: 'radial-gradient(circle at 38% 32%, rgba(59,130,246,0.14) 0%, #080810 55%)',
          backdropFilter: 'blur(24px)',
          boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.1), inset 0 -1px 0 rgba(0,0,0,0.3)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          animation: state==='idle' ? 'breathe 3s ease-in-out infinite' : 'none',
        }}>
          {/* IDLE: glowing core */}
          {state === 'idle' && (
            <div style={{
              width: '26px', height: '26px', borderRadius: '50%',
              background: 'radial-gradient(circle, rgba(59,130,246,0.65), rgba(6,182,212,0.3))',
              boxShadow: '0 0 18px rgba(59,130,246,0.55)', animation: 'breathe-fast 2.5s ease-in-out infinite',
            }} />
          )}

          {/* LISTENING / SPEAKING: audio bars */}
          {(state==='listening' || state==='speaking') && (
            <div style={{ display:'flex', alignItems:'center', gap:'3px', height:'32px' }}>
              {bars.map((h, i) => (
                <div key={i} style={{
                  width: '4px', minHeight: '3px',
                  height: `${Math.max(3, Math.round(h * 0.32))}px`,
                  background: state==='listening' ? `rgba(6,182,212,${0.6+i*0.07})` : `rgba(139,92,246,${0.6+i*0.07})`,
                  borderRadius: '2px', transition: 'height 0.09s ease',
                  boxShadow: state==='listening' ? '0 0 5px rgba(6,182,212,0.5)' : '0 0 5px rgba(139,92,246,0.5)',
                }} />
              ))}
            </div>
          )}

          {/* PROCESSING: dual spinner */}
          {state === 'processing' && (
            <div style={{ position:'relative', width:'34px', height:'34px' }}>
              <div style={{
                position:'absolute', inset:0, borderRadius:'50%',
                border:'2px solid rgba(245,158,11,0.18)', borderTopColor:'#F59E0B',
                animation:'spin 0.75s linear infinite', boxShadow:'0 0 12px rgba(245,158,11,0.3)',
              }} />
              <div style={{
                position:'absolute', inset:'7px', borderRadius:'50%',
                border:'1.5px solid rgba(245,158,11,0.1)', borderBottomColor:'#F97316',
                animation:'spin-rev 1.1s linear infinite',
              }} />
            </div>
          )}
        </div>
      </div>

      {/* State label */}
      {state !== 'idle' && (
        <div style={{
          color: '#52526a', fontSize: '9px', fontFamily: "'JetBrains Mono', monospace",
          letterSpacing: '0.1em', textAlign: 'right', marginTop: '-6px',
          animation: 'fade-in 0.3s ease',
        }}>
          {{ listening:'LISTENING...', processing:'ANALYZING...', speaking:'SPEAKING...' }[state]}
        </div>
      )}
    </div>
  );
}

Object.assign(window, { VoiceOrb });
