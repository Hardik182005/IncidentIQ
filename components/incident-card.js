// AUTO-GENERATED from incident-card.jsx by tools/build-dashboard.mjs — do not edit.
(function () {
// =============================================
// INCIDENT-CARD.JSX
// =============================================
const {
  useState,
  useEffect
} = React;
function ConfidenceRing({
  value,
  color,
  size = 48
}) {
  const r = size / 2 - 5;
  const circ = 2 * Math.PI * r;
  const dash = Math.max(0, value / 100) * circ;
  const c = size / 2;
  return /*#__PURE__*/React.createElement("svg", {
    width: size,
    height: size,
    style: {
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement("circle", {
    cx: c,
    cy: c,
    r: r,
    fill: "none",
    stroke: "rgba(255,255,255,0.07)",
    strokeWidth: "2.5"
  }), /*#__PURE__*/React.createElement("circle", {
    cx: c,
    cy: c,
    r: r,
    fill: "none",
    stroke: color,
    strokeWidth: "2.5",
    strokeDasharray: `${dash} ${circ}`,
    strokeLinecap: "round",
    transform: `rotate(-90 ${c} ${c})`,
    style: {
      filter: `drop-shadow(0 0 4px ${color})`,
      transition: 'stroke-dasharray 1s cubic-bezier(0.34,1.3,0.64,1)'
    }
  }), /*#__PURE__*/React.createElement("text", {
    x: c,
    y: c + 4,
    textAnchor: "middle",
    fill: "#eeeef5",
    fontSize: "11",
    fontFamily: "'JetBrains Mono', monospace",
    fontWeight: "500"
  }, value, "%"));
}
function IncidentCard({
  incident,
  onAnalyze,
  isNew
}) {
  const cfg = SEVERITY_CONFIG[incident.severity];
  const [elapsed, setElapsed] = useState(incident.elapsed);
  const [hov, setHov] = useState(false);
  useEffect(() => {
    const t = setInterval(() => setElapsed(e => e + 1), 1000);
    return () => clearInterval(t);
  }, []);
  const statusColor = {
    ACTIVE: '#EF4444',
    ANALYZING: '#3B82F6',
    MITIGATING: '#F59E0B',
    RESOLVED: '#10B981'
  }[incident.status] || '#9898b0';
  const isCrit = incident.severity === 'CRITICAL';
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: hov ? 'rgba(255,255,255,0.058)' : 'rgba(255,255,255,0.036)',
      border: `1px solid ${isCrit ? 'rgba(239,68,68,0.26)' : 'rgba(255,255,255,0.07)'}`,
      borderRadius: '10px',
      padding: '14px 16px',
      marginBottom: '10px',
      backdropFilter: 'blur(16px)',
      cursor: 'pointer',
      transition: 'transform 0.22s ease, background 0.22s, box-shadow 0.3s',
      transform: hov ? 'translateY(-2px)' : 'none',
      boxShadow: isCrit ? hov ? '0 8px 32px rgba(239,68,68,0.22), 0 0 0 1px rgba(239,68,68,0.12)' : '0 4px 18px rgba(239,68,68,0.1)' : hov ? '0 8px 24px rgba(0,0,0,0.28)' : 'none',
      animation: isNew ? 'slide-down 0.5s cubic-bezier(0.34,1.3,0.64,1) both' : 'none',
      position: 'relative',
      overflow: 'hidden'
    },
    onMouseEnter: () => setHov(true),
    onMouseLeave: () => setHov(false),
    onClick: () => onAnalyze(incident)
  }, isCrit && /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      height: '1px',
      background: 'linear-gradient(90deg, transparent, rgba(239,68,68,0.7), transparent)'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      marginBottom: '8px'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      background: cfg.bg,
      color: cfg.color,
      border: `1px solid ${cfg.color}35`,
      borderRadius: '4px',
      padding: '1px 8px',
      fontSize: '10px',
      fontFamily: "'JetBrains Mono', monospace",
      fontWeight: '600',
      letterSpacing: '0.1em',
      boxShadow: isCrit ? `0 0 10px ${cfg.glow}` : 'none'
    }
  }, isCrit && /*#__PURE__*/React.createElement("span", {
    style: {
      marginRight: '4px',
      animation: 'flicker 2s infinite'
    }
  }, "\u25CF"), incident.severity), /*#__PURE__*/React.createElement("span", {
    style: {
      color: statusColor,
      fontSize: '10px',
      fontFamily: "'JetBrains Mono', monospace",
      letterSpacing: '0.06em'
    }
  }, incident.status), /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 'auto',
      color: '#52526a',
      fontSize: '11px',
      fontFamily: "'JetBrains Mono', monospace"
    }
  }, formatElapsed(elapsed))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'baseline',
      gap: '8px',
      marginBottom: '5px'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: '#52526a',
      fontSize: '11px',
      fontFamily: "'JetBrains Mono', monospace"
    }
  }, incident.id), /*#__PURE__*/React.createElement("span", {
    style: {
      color: '#eeeef5',
      fontSize: '15px',
      fontWeight: '600',
      letterSpacing: '-0.02em'
    }
  }, incident.service), /*#__PURE__*/React.createElement("span", {
    style: {
      color: '#52526a',
      fontSize: '11px'
    }
  }, incident.region)), /*#__PURE__*/React.createElement("p", {
    style: {
      color: '#9898b0',
      fontSize: '12px',
      lineHeight: '1.55',
      marginBottom: '12px',
      fontFamily: "'JetBrains Mono', monospace",
      fontWeight: '300'
    }
  }, incident.rootCause), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: '10px'
    }
  }, /*#__PURE__*/React.createElement(ConfidenceRing, {
    value: incident.confidence,
    color: cfg.color
  }), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      color: '#52526a',
      fontSize: '9px',
      letterSpacing: '0.1em',
      marginBottom: '2px'
    }
  }, "AI CONFIDENCE"), /*#__PURE__*/React.createElement("div", {
    style: {
      color: '#eeeef5',
      fontSize: '13px',
      fontWeight: '600'
    }
  }, incident.confidence, "% match"))), /*#__PURE__*/React.createElement("button", {
    onClick: e => {
      e.stopPropagation();
      onAnalyze(incident);
    },
    style: {
      background: 'linear-gradient(135deg, rgba(59,130,246,0.16), rgba(6,182,212,0.13))',
      border: '1px solid rgba(59,130,246,0.32)',
      color: '#60A5FA',
      borderRadius: '8px',
      padding: '7px 16px',
      fontSize: '12px',
      fontWeight: '600',
      cursor: 'pointer',
      letterSpacing: '0.04em',
      transition: 'all 0.2s',
      fontFamily: "'Space Grotesk', sans-serif"
    },
    onMouseEnter: e => {
      e.target.style.background = 'linear-gradient(135deg, rgba(59,130,246,0.28), rgba(6,182,212,0.26))';
      e.target.style.boxShadow = '0 0 16px rgba(59,130,246,0.38)';
    },
    onMouseLeave: e => {
      e.target.style.background = 'linear-gradient(135deg, rgba(59,130,246,0.16), rgba(6,182,212,0.13))';
      e.target.style.boxShadow = 'none';
    }
  }, "Analyze \u2192")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: '5px',
      marginTop: '10px',
      flexWrap: 'wrap'
    }
  }, incident.tags.map(tag => /*#__PURE__*/React.createElement("span", {
    key: tag,
    style: {
      background: 'rgba(255,255,255,0.048)',
      border: '1px solid rgba(255,255,255,0.07)',
      borderRadius: '3px',
      padding: '1px 7px',
      fontSize: '10px',
      color: '#52526a',
      fontFamily: "'JetBrains Mono', monospace"
    }
  }, "#", tag))));
}
Object.assign(window, {
  IncidentCard,
  ConfidenceRing
});
})();
