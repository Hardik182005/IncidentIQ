// AUTO-GENERATED from charts.jsx by tools/build-dashboard.mjs — do not edit.
(function () {
// =============================================
// CHARTS.JSX — Canvas charts, topology, timeline
// =============================================
const {
  useRef,
  useEffect,
  useState
} = React;
function MetricChart({
  title,
  color,
  baseVal,
  variance,
  spikeIdx,
  unit,
  height = 85
}) {
  const canvasRef = useRef(null);
  const dataRef = useRef(generateSeries(60, baseVal, variance, spikeIdx));
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    let animId, W, H;
    const dpr = window.devicePixelRatio || 1;
    function resize() {
      W = canvas.offsetWidth;
      H = canvas.offsetHeight;
      canvas.width = W * dpr;
      canvas.height = H * dpr;
      canvas.style.width = W + 'px';
      canvas.style.height = H + 'px';
    }
    const interval = setInterval(() => {
      const last = dataRef.current[dataRef.current.length - 1];
      const next = Math.max(0, last + (Math.random() - 0.5) * variance * 0.55);
      dataRef.current = [...dataRef.current.slice(1), next];
    }, 2000);
    function draw() {
      if (!canvas.parentElement) return;
      const ctx = canvas.getContext('2d');
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, W, H);
      const data = dataRef.current;
      const min = Math.min(...data) * 0.92;
      const max = Math.max(...data) * 1.08;
      const rng = max - min || 1;
      const toX = i => i / (data.length - 1) * W;
      const toY = v => H - 4 - (v - min) / rng * (H - 8);

      // Grid lines
      ctx.strokeStyle = 'rgba(255,255,255,0.04)';
      ctx.lineWidth = 1;
      for (let i = 1; i < 4; i++) {
        const y = H / 4 * i;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(W, y);
        ctx.stroke();
      }

      // Spike marker
      if (spikeIdx != null) {
        const sx = toX(spikeIdx);
        ctx.strokeStyle = 'rgba(239,68,68,0.32)';
        ctx.lineWidth = 1;
        ctx.setLineDash([3, 4]);
        ctx.beginPath();
        ctx.moveTo(sx, 0);
        ctx.lineTo(sx, H);
        ctx.stroke();
        ctx.setLineDash([]);
      }

      // Gradient fill
      const grad = ctx.createLinearGradient(0, 0, 0, H);
      grad.addColorStop(0, color + '26');
      grad.addColorStop(1, color + '00');
      ctx.beginPath();
      ctx.moveTo(toX(0), toY(data[0]));
      for (let i = 1; i < data.length; i++) {
        const x0 = toX(i - 1),
          y0 = toY(data[i - 1]),
          x1 = toX(i),
          y1 = toY(data[i]);
        ctx.bezierCurveTo((x0 + x1) / 2, y0, (x0 + x1) / 2, y1, x1, y1);
      }
      ctx.lineTo(W, H);
      ctx.lineTo(0, H);
      ctx.closePath();
      ctx.fillStyle = grad;
      ctx.fill();

      // Line
      ctx.beginPath();
      ctx.moveTo(toX(0), toY(data[0]));
      for (let i = 1; i < data.length; i++) {
        const x0 = toX(i - 1),
          y0 = toY(data[i - 1]),
          x1 = toX(i),
          y1 = toY(data[i]);
        ctx.bezierCurveTo((x0 + x1) / 2, y0, (x0 + x1) / 2, y1, x1, y1);
      }
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.5;
      ctx.shadowColor = color;
      ctx.shadowBlur = 7;
      ctx.stroke();
      ctx.shadowBlur = 0;

      // Live dot
      const lx = toX(data.length - 1),
        ly = toY(data[data.length - 1]);
      ctx.beginPath();
      ctx.arc(lx, ly, 3.5, 0, 6.28);
      ctx.fillStyle = color;
      ctx.shadowColor = color;
      ctx.shadowBlur = 12;
      ctx.fill();
      ctx.shadowBlur = 0;
      animId = requestAnimationFrame(draw);
    }
    requestAnimationFrame(() => {
      resize();
      draw();
    });
    return () => {
      cancelAnimationFrame(animId);
      clearInterval(interval);
    };
  }, []);
  const cur = dataRef.current[dataRef.current.length - 1];
  const disp = unit === 'ms' ? Math.round(cur) : unit === '%' ? cur.toFixed(1) : Math.round(cur);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: '14px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'baseline',
      marginBottom: '6px'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: '#52526a',
      fontSize: '10px',
      letterSpacing: '0.1em',
      textTransform: 'uppercase'
    }
  }, title), /*#__PURE__*/React.createElement("span", {
    style: {
      color,
      fontSize: '16px',
      fontWeight: '700',
      fontFamily: "'JetBrains Mono', monospace",
      textShadow: `0 0 10px ${color}80`
    }
  }, disp, unit)), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      height: `${height}px`
    }
  }, /*#__PURE__*/React.createElement("canvas", {
    ref: canvasRef,
    style: {
      width: '100%',
      height: '100%',
      display: 'block'
    }
  })));
}
function ServiceTopology() {
  const canvasRef = useRef(null);
  const tickRef = useRef(0);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dpr = window.devicePixelRatio || 1;
    let W, H, animId;
    function setup() {
      W = canvas.offsetWidth;
      H = 175;
      canvas.width = W * dpr;
      canvas.height = H * dpr;
      canvas.style.width = W + 'px';
      canvas.style.height = H + 'px';
    }
    const statusColor = {
      healthy: '#10B981',
      degraded: '#F59E0B',
      critical: '#EF4444'
    };
    function draw() {
      tickRef.current++;
      const t = tickRef.current;
      const ctx = canvas.getContext('2d');
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, W, H);
      const pos = n => ({
        x: n.x * W,
        y: n.y * H
      });

      // Edges
      for (const [aId, bId] of TOPOLOGY_EDGES) {
        const a = TOPOLOGY_NODES.find(n => n.id === aId);
        const b = TOPOLOGY_NODES.find(n => n.id === bId);
        const pa = pos(a),
          pb = pos(b);
        const isCritEdge = a.status === 'critical' || b.status === 'critical';
        const mx = (pa.x + pb.x) / 2,
          my = (pa.y + pb.y) / 2 - 18;
        ctx.beginPath();
        ctx.moveTo(pa.x, pa.y);
        ctx.quadraticCurveTo(mx, my, pb.x, pb.y);
        ctx.strokeStyle = isCritEdge ? 'rgba(239,68,68,0.22)' : 'rgba(255,255,255,0.07)';
        ctx.lineWidth = isCritEdge ? 1.5 : 1;
        ctx.stroke();

        // Animated packet on critical edges
        if (isCritEdge) {
          const pct = t * 0.009 % 1;
          const tp = 1 - pct;
          const px = tp * tp * pa.x + 2 * tp * pct * mx + pct * pct * pb.x;
          const py = tp * tp * pa.y + 2 * tp * pct * my + pct * pct * pb.y;
          ctx.beginPath();
          ctx.arc(px, py, 2.5, 0, Math.PI * 2);
          ctx.fillStyle = 'rgba(239,68,68,0.85)';
          ctx.shadowColor = '#EF4444';
          ctx.shadowBlur = 7;
          ctx.fill();
          ctx.shadowBlur = 0;
        }
      }

      // Nodes
      for (const node of TOPOLOGY_NODES) {
        const {
          x,
          y
        } = pos(node);
        const col = statusColor[node.status];
        const r = 13;
        if (node.status === 'critical') {
          const pulse = 0.5 + 0.5 * Math.sin(t * 0.09);
          ctx.beginPath();
          ctx.arc(x, y, r + 7 + pulse * 5, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(239,68,68,${0.05 + pulse * 0.06})`;
          ctx.fill();
        } else if (node.status === 'degraded') {
          const pulse = 0.5 + 0.5 * Math.sin(t * 0.06 + 1);
          ctx.beginPath();
          ctx.arc(x, y, r + 5 + pulse * 3, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(245,158,11,${0.04 + pulse * 0.04})`;
          ctx.fill();
        }
        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI * 2);
        ctx.fillStyle = `${col}1e`;
        ctx.fill();
        ctx.strokeStyle = col;
        ctx.lineWidth = node.status === 'healthy' ? 1.5 : 2;
        ctx.shadowColor = col;
        ctx.shadowBlur = node.status === 'healthy' ? 5 : 14;
        ctx.stroke();
        ctx.shadowBlur = 0;
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fillStyle = col;
        ctx.fill();
        ctx.fillStyle = '#9898b0';
        ctx.font = `9px 'JetBrains Mono', monospace`;
        ctx.textAlign = 'center';
        ctx.fillText(node.label, x, y + r + 13);
      }
      animId = requestAnimationFrame(draw);
    }
    requestAnimationFrame(() => {
      setup();
      draw();
    });
    return () => cancelAnimationFrame(animId);
  }, []);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: '14px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: '8px'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: '#52526a',
      fontSize: '10px',
      letterSpacing: '0.1em',
      textTransform: 'uppercase'
    }
  }, "Service Topology"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: '10px'
    }
  }, [['healthy', '#10B981'], ['degraded', '#F59E0B'], ['critical', '#EF4444']].map(([s, c]) => /*#__PURE__*/React.createElement("span", {
    key: s,
    style: {
      color: '#52526a',
      fontSize: '9px',
      display: 'flex',
      alignItems: 'center',
      gap: '4px'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: '6px',
      height: '6px',
      borderRadius: '50%',
      background: c,
      display: 'inline-block',
      boxShadow: `0 0 5px ${c}`
    }
  }), s)))), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      height: '175px'
    }
  }, /*#__PURE__*/React.createElement("canvas", {
    ref: canvasRef,
    style: {
      width: '100%',
      height: '100%',
      display: 'block'
    }
  })));
}
function HorizontalTimeline() {
  const typeColor = {
    deploy: '#3B82F6',
    spike: '#EF4444',
    alert: '#F59E0B',
    analysis: '#8B5CF6',
    action: '#06B6D4',
    recovery: '#10B981'
  };
  const MIN = -55,
    MAX = 5;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '12px 16px',
      background: 'rgba(255,255,255,0.028)',
      border: '1px solid rgba(255,255,255,0.065)',
      borderRadius: '10px',
      overflowX: 'auto'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      color: '#52526a',
      fontSize: '10px',
      letterSpacing: '0.1em',
      marginBottom: '12px',
      textTransform: 'uppercase'
    }
  }, "Incident Timeline"), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      height: '52px',
      minWidth: '500px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 0,
      right: 0,
      top: '20px',
      height: '1px',
      background: 'rgba(255,255,255,0.07)'
    }
  }), TIMELINE_EVENTS.map((ev, i) => {
    const pct = (ev.time - MIN) / (MAX - MIN) * 100;
    const col = typeColor[ev.type] || '#9898b0';
    return /*#__PURE__*/React.createElement("div", {
      key: i,
      title: ev.detail,
      style: {
        position: 'absolute',
        left: `${pct}%`,
        top: 0,
        transform: 'translateX(-50%)',
        cursor: 'default'
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        width: '10px',
        height: '10px',
        borderRadius: '50%',
        background: col,
        border: '2px solid rgba(0,0,0,0.6)',
        margin: '15px auto 0',
        boxShadow: `0 0 8px ${col}90`,
        position: 'relative'
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        position: 'absolute',
        top: '14px',
        left: '50%',
        transform: 'translateX(-50%)',
        whiteSpace: 'nowrap',
        fontSize: '9px',
        color: '#52526a',
        fontFamily: "'JetBrains Mono', monospace"
      }
    }, ev.label)));
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: `${(0 - MIN) / (MAX - MIN) * 100}%`,
      top: 0,
      height: '52px',
      width: '1px',
      background: 'rgba(6,182,212,0.6)',
      boxShadow: '0 0 6px rgba(6,182,212,0.5)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      top: '-2px',
      left: '50%',
      transform: 'translateX(-50%)',
      fontSize: '8px',
      color: '#06B6D4',
      whiteSpace: 'nowrap',
      letterSpacing: '0.08em'
    }
  }, "NOW"))));
}
Object.assign(window, {
  MetricChart,
  ServiceTopology,
  HorizontalTimeline
});
})();
