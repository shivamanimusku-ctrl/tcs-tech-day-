/**
 * SupervisorView — line-level performance, active alerts, and operational actions.
 */

import { useState } from 'react';
import AlertList from './AlertList';

export default function SupervisorView({ alerts, production, quality, orders, notes, onStatusChange, loading }) {
  const [selectedLine, setSelectedLine] = useState('Line-3');

  // Get unique lines from alerts
  const lines = [...new Set([
    ...alerts.map(a => a.line_id),
    ...production.map(p => p.line_id),
  ])].sort();

  // Filter data by selected line
  const lineAlerts = alerts.filter(a => a.line_id === selectedLine);
  const lineProduction = production.filter(p => p.line_id === selectedLine);
  const lineQuality = quality.filter(q => q.line_id === selectedLine);
  const lineOrders = orders.filter(o => o.line_id === selectedLine);
  const lineNotes = notes.filter(n => n.line_id === selectedLine);

  // Latest production stats
  const latestProd = lineProduction[0];
  const prodPct = latestProd
    ? ((latestProd.actual_production / latestProd.production_target) * 100).toFixed(1)
    : 100;
  const latestQuality = lineQuality[0];
  const defectPct = latestQuality ? (latestQuality.defect_rate * 100).toFixed(1) : '0.0';

  return (
    <div className="fade-in">
      {/* Line selector */}
      <div className="role-section">
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)', marginBottom: 'var(--space-lg)' }}>
          <div className="role-section-title" style={{ margin: 0 }}>
            <span className="icon">👷</span> Line Performance
          </div>
          <select
            value={selectedLine}
            onChange={(e) => setSelectedLine(e.target.value)}
            style={{
              appearance: 'none',
              background: 'var(--bg-elevated)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-default)',
              padding: '6px 28px 6px 12px',
              borderRadius: 'var(--radius-md)',
              fontFamily: 'var(--font-family)',
              fontSize: 'var(--font-size-sm)',
              fontWeight: 600,
              cursor: 'pointer',
              backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%239498b0' d='M6 8L1 3h10z'/%3E%3C/svg%3E")`,
              backgroundRepeat: 'no-repeat',
              backgroundPosition: 'right 8px center',
            }}
          >
            {lines.map(line => (
              <option key={line} value={line}>{line}</option>
            ))}
          </select>
        </div>

        {/* Line metrics */}
        <div className="metrics-row">
          <div className="metric-card">
            <div className="metric-card-label">Production Rate</div>
            <div className="metric-card-value" style={{
              color: prodPct >= 95 ? 'var(--accent-success)' :
                prodPct >= 85 ? 'var(--severity-medium)' : 'var(--severity-critical)'
            }}>
              {prodPct}%
            </div>
            <div className="metric-card-subtitle">
              {latestProd ? `${latestProd.actual_production} / ${latestProd.production_target} units` : 'No data'}
            </div>
            {latestProd && (
              <div className="progress-bar" style={{ marginTop: '8px' }}>
                <div
                  className="progress-bar-fill"
                  style={{
                    width: `${Math.min(100, prodPct)}%`,
                    background: prodPct >= 95 ? 'var(--accent-success)' :
                      prodPct >= 85 ? 'var(--severity-medium)' : 'var(--severity-critical)'
                  }}
                />
              </div>
            )}
          </div>
          <div className="metric-card">
            <div className="metric-card-label">Defect Rate</div>
            <div className="metric-card-value" style={{
              color: defectPct <= 2 ? 'var(--accent-success)' :
                defectPct <= 5 ? 'var(--severity-medium)' : 'var(--severity-critical)'
            }}>
              {defectPct}%
            </div>
            <div className="metric-card-subtitle">
              {latestQuality ? `${latestQuality.defect_count} defects / ${latestQuality.total_inspected} inspected` : 'No data'}
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-card-label">Downtime Today</div>
            <div className="metric-card-value" style={{
              color: latestProd && latestProd.downtime_minutes > 15
                ? 'var(--severity-high)' : 'var(--accent-success)'
            }}>
              {latestProd ? `${latestProd.downtime_minutes}m` : '0m'}
            </div>
            <div className="metric-card-subtitle">Minutes of unplanned downtime</div>
          </div>
          <div className="metric-card">
            <div className="metric-card-label">Active Alerts</div>
            <div className="metric-card-value" style={{
              color: lineAlerts.length > 0 ? 'var(--severity-high)' : 'var(--accent-success)'
            }}>
              {lineAlerts.length}
            </div>
            <div className="metric-card-subtitle">On {selectedLine}</div>
          </div>
        </div>
      </div>

      {/* Orders for this line */}
      {lineOrders.length > 0 && (
        <div className="role-section">
          <div className="role-section-title">
            <span className="icon">📦</span> Active Orders — {selectedLine}
          </div>
          {lineOrders.map(order => {
            const pct = ((order.units_completed / order.units_target) * 100).toFixed(0);
            const remaining = order.units_target - order.units_completed;
            const daysUntil = Math.ceil(
              (new Date(order.due_date) - new Date()) / (1000 * 60 * 60 * 24)
            );
            return (
              <div key={order.order_id} className="machine-detail">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontWeight: 700, marginBottom: '4px' }}>
                      {order.order_id} — {order.customer}
                    </div>
                    <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)' }}>
                      Due: {order.due_date} ({daysUntil <= 0 ? 'TODAY' : `${daysUntil} day${daysUntil !== 1 ? 's' : ''}`}) · 
                      {remaining.toLocaleString()} units remaining
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 800, color: pct >= 80 ? 'var(--accent-success)' : 'var(--severity-critical)' }}>
                      {pct}%
                    </div>
                  </div>
                </div>
                <div className="progress-bar" style={{ marginTop: '12px' }}>
                  <div className="progress-bar-fill" style={{
                    width: `${pct}%`,
                    background: pct >= 80 ? 'var(--accent-success)' : 'var(--severity-critical)'
                  }} />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Operator notes */}
      {lineNotes.length > 0 && (
        <div className="role-section">
          <div className="role-section-title">
            <span className="icon">📝</span> Recent Notes
          </div>
          {lineNotes.map(note => (
            <div key={note.note_id} className="note-item">
              <div className="note-meta">
                {note.author_role} — {new Date(note.timestamp).toLocaleString()}
              </div>
              <div className="note-text">"{note.text}"</div>
            </div>
          ))}
        </div>
      )}

      {/* Line alerts */}
      <div className="role-section">
        <AlertList
          alerts={lineAlerts}
          onStatusChange={onStatusChange}
          loading={loading}
          title={`⚠ Alerts — ${selectedLine}`}
        />
      </div>
    </div>
  );
}
