// =============================================
// VOICE-ORB.JSX — The SRE AI Chatbot & Voice Orb
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
  const [bars, setBars]   = useState([8, 8, 8, 8, 8]);
  const [transcript, setTranscript] = useState('');
  const [response, setResponse]     = useState('');
  const [showChips, setShowChips]   = useState(true);
  const [inputText, setInputText]   = useState(''); // For textual chat input
  
  const timers  = useRef([]);
  const barLoop = useRef(null);
  
  // Real recording, audio stream, and WS refs
  const mediaRecorderRef = useRef(null);
  const audioStreamRef = useRef(null);
  const wsRef = useRef(null);
  const audioCtxRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);
  
  // Ref to hold the currently playing ElevenLabs Audio element
  const audioElementRef = useRef(null);

  function stopRecording() {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach(track => track.stop());
      audioStreamRef.current = null;
    }
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (audioCtxRef.current && audioCtxRef.current.state !== 'closed') {
      audioCtxRef.current.close().catch(() => {});
      audioCtxRef.current = null;
    }
    analyserRef.current = null;

    // Pause and release any active ElevenLabs TTS playback
    if (audioElementRef.current) {
      try {
        audioElementRef.current.pause();
      } catch (e) {}
      audioElementRef.current = null;
    }
  }

  function clearAll() {
    timers.current.forEach(clearTimeout);
    timers.current = [];
    clearInterval(barLoop.current);
    barLoop.current = null;
    stopRecording();
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

  function startBars() {
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
    const answer = data.data?.response ?? data.response;
    if (!answer) throw new Error('empty response');
    return answer;
  }

  // Synthesize and play audio stream from ElevenLabs TTS
  async function speak(text, onEnded = null) {
    if (audioElementRef.current) {
      try {
        audioElementRef.current.pause();
      } catch (e) {}
      audioElementRef.current = null;
    }

    try {
      const res = await fetch(`${API_BASE}/api/voice/speak`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) throw new Error("TTS request failed");
      const blob = await res.blob();
      const audioUrl = URL.createObjectURL(blob);
      const audio = new Audio(audioUrl);
      audioElementRef.current = audio;
      if (onEnded) {
        audio.onended = onEnded;
      }
      audio.play().catch(err => {
        console.warn("Audio autoplay blocked or failed", err);
        if (onEnded) onEnded();
      });
    } catch (e) {
      console.error("ElevenLabs TTS playback error", e);
      if (onEnded) onEnded();
    }
  }

  // Handle tap-to-start / tap-to-finish click on orb (microphone)
  function handleOrbClick() {
    if (state === 'idle') {
      startListening();
    } else if (state === 'listening') {
      finishListening();
    }
  }

  // Handle suggestion chips or typed text inputs
  function handleChipClick(chipText) {
    if (state !== 'idle') return;
    clearAll(); setShowChips(false); setTranscript(''); setResponse('');
    setState('processing');
    typewrite(chipText, setTranscript);

    askBackend(chipText)
      .catch(() => RESPONSES[Math.floor(Math.random() * RESPONSES.length)])
      .then(answer => {
        setState('speaking');
        startBars();
        setResponse('');
        typewrite(answer, setResponse);
        
        speak(answer, () => {
          clearAll(); setState('idle'); setTranscript(''); setResponse(''); setShowChips(true);
        });
      });
  }

  // Record microphone and stream audio bytes to WebSocket endpoint /api/voice/listen
  async function startListening() {
    clearAll(); setShowChips(false); setTranscript(''); setResponse('');
    
    try {
      // 1. Obtain user microphone stream
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioStreamRef.current = stream;

      // 2. Open live Voice transcribing WebSocket
      let wsUrl = '';
      if (typeof location !== 'undefined' && location.protocol.startsWith('http')) {
        const wsProto = location.protocol === 'https:' ? 'wss:' : 'ws:';
        wsUrl = `${wsProto}//${location.host}/api/voice/listen`;
      } else {
        wsUrl = 'ws://127.0.0.1:8000/api/voice/listen';
      }

      const socket = new WebSocket(wsUrl);
      wsRef.current = socket;
      setState('listening');

      // 3. Audio Context & Analyser Node for REAL-TIME MIC VOLUME GRAPH
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      const audioCtx = new AudioCtx();
      audioCtxRef.current = audioCtx;

      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 32;
      source.connect(analyser);
      analyserRef.current = analyser;

      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      function drawBars() {
        if (!analyserRef.current) return;
        analyserRef.current.getByteFrequencyData(dataArray);
        const heights = Array.from(dataArray).slice(0, 5).map(v => Math.max(8, (v / 255) * 85));
        setBars(heights);
        animationFrameRef.current = requestAnimationFrame(drawBars);
      }
      drawBars();

      socket.onopen = () => {
        console.log("Voice WebSocket connected - streaming microphone stream");
        
        // 4. Stream audio segments via MediaRecorder
        const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        mediaRecorderRef.current = mediaRecorder;

        mediaRecorder.ondataavailable = (e) => {
          if (e.data && e.data.size > 0 && socket.readyState === WebSocket.OPEN) {
            socket.send(e.data);
          }
        };
        mediaRecorder.start(250); // Send slice every 250ms
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.transcript || data.response) {
            stopRecording();
            setState('speaking');
            startBars(); // talking animation

            if (data.transcript) {
              setTranscript(data.transcript);
            }
            if (data.response) {
              setResponse('');
              typewrite(data.response, setResponse);
              speak(data.response, () => {
                clearAll(); setState('idle'); setTranscript(''); setResponse(''); setShowChips(true);
              });
            }
          } else if (data.error) {
            console.error("Transcriber error: ", data.error);
            fallbackSpeech("Analysis could not hear you. Please speak clearly.");
          }
        } catch (e) {
          console.error("Error reading socket payload", e);
        }
      };

      socket.onerror = (err) => {
        console.error("Voice WS error", err);
      };

      socket.onclose = () => {
        console.log("Voice WS closed");
      };

      // Auto-stop after 10s maximum recording
      timers.current.push(setTimeout(() => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          finishListening();
        }
      }, 10000));

    } catch (err) {
      console.error("Could not activate microphone", err);
      fallbackSpeech("Microphone access failed. Please enable permissions.");
    }
  }

  function finishListening() {
    if (state !== 'listening') return;
    setState('processing');

    // Flush recorder
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }

    // Send end of speech
    setTimeout(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: "end_of_speech", incident_id: incidentId || null }));
      } else {
        fallbackSpeech("Connection interrupted.");
      }
    }, 450);
  }

  function fallbackSpeech(msg) {
    stopRecording();
    setState('speaking');
    startBars();
    setResponse('');
    typewrite(msg, setResponse);
    speak(msg, () => {
      clearAll(); setState('idle'); setTranscript(''); setResponse(''); setShowChips(true);
    });
  }

  useEffect(() => {
    if (!externalMessage || state !== 'idle') return;
    clearAll(); setShowChips(false); setTranscript(''); setResponse('');
    setState('speaking'); startBars();
    typewrite(externalMessage, setResponse);
    speak(externalMessage, () => {
      clearAll(); setState('idle'); setResponse(''); setShowChips(true);
      onExternalDone?.();
    });
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
      display: 'flex', alignItems: 'flex-end', gap: '24px',
    }}>

      {/* Left Column: Chat interfaces stacked vertically */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '8px' }}>
        
        {/* Speech / transcript bubble */}
        {(response || transcript) && (
          <div style={{
            background: 'rgba(6,6,18,0.94)', border: '1px solid rgba(255,255,255,0.11)',
            borderRadius: '12px 12px 4px 12px', padding: '12px 15px', maxWidth: '300px',
            backdropFilter: 'blur(24px)', animation: 'float-up 0.3s ease both',
            boxShadow: '0 8px 32px rgba(0,0,0,0.5)', marginRight: '8px',
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

        {/* Suggestion chips (now laid out horizontally side-by-side to save height) */}
        {showChips && state === 'idle' && (
          <div style={{ display: 'flex', gap: '6px', animation: 'fade-in 0.6s ease', marginRight: '8px' }}>
            {CHIPS.map((chip, i) => (
              <button key={i} onClick={() => handleChipClick(chip)} style={{
                background: 'rgba(255,255,255,0.048)', border: '1px solid rgba(255,255,255,0.18)',
                borderRadius: '20px', padding: '6px 14px', color: '#f1f5f9', fontSize: '11px',
                cursor: 'pointer', transition: 'all 0.2s', fontFamily: "'Space Grotesk', sans-serif",
                backdropFilter: 'blur(10px)', whiteSpace: 'nowrap', fontWeight: '600'
              }}
              onMouseEnter={e => { e.target.style.background='rgba(255,255,255,0.12)'; e.target.style.color='#ffffff'; e.target.style.borderColor='rgba(255,255,255,0.35)'; }}
              onMouseLeave={e => { e.target.style.background='rgba(255,255,255,0.048)'; e.target.style.color='#f1f5f9'; e.target.style.borderColor='rgba(255,255,255,0.18)'; }}
              >{chip}</button>
            ))}
          </div>
        )}

        {/* Textual Chat Input (when idle) */}
        {state === 'idle' && (
          <form onSubmit={(e) => { e.preventDefault(); if (inputText.trim()) { handleChipClick(inputText); setInputText(''); } }} style={{
            display: 'flex', gap: '6px', background: 'rgba(6,6,18,0.85)',
            border: '1px solid rgba(255,255,255,0.18)', borderRadius: '20px',
            padding: '4px 6px 4px 12px', width: '250px', backdropFilter: 'blur(16px)',
            boxShadow: '0 8px 24px rgba(0,0,0,0.3)', animation: 'fade-in 0.4s ease',
            marginRight: '8px'
          }}>
            <input
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Ask IQ-Sentry a question..."
              style={{
                flex: 1, background: 'transparent', border: 'none',
                outline: 'none', color: '#ffffff', fontSize: '11px',
                fontFamily: "'Space Grotesk', sans-serif", fontWeight: '600'
              }}
            />
            <button type="submit" style={{
              background: 'rgba(255,255,255,0.14)', border: 'none',
              borderRadius: '50%', width: '22px', height: '22px', display: 'flex',
              alignItems: 'center', justifyContent: 'center', color: '#ffffff',
              fontSize: '9px', cursor: 'pointer', outline: 'none', fontWeight: '700'
            }}>➔</button>
          </form>
        )}
      </div>

      {/* Right Column: Orb wrapper and dynamic state label */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
        
        <div
          onClick={handleOrbClick}
          style={{
            position: 'relative', cursor: state==='idle' || state==='listening' ? 'pointer' : 'default',
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
            letterSpacing: '0.1em', textAlign: 'center',
            animation: 'fade-in 0.3s ease',
          }}>
            {{ listening:'LISTENING...', processing:'ANALYZING...', speaking:'SPEAKING...' }[state]}
          </div>
        )}
      </div>

    </div>
  );
}

Object.assign(window, { VoiceOrb });
