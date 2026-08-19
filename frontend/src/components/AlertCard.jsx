/**
 * AlertCard — Light Mode fully exposed card with high contrast,
 * severity coding, AI explanation, business impact, recommendations, and action buttons.
 */

import { useState } from 'react';

export default function AlertCard({ alert, onStatusChange }) {
  const [updating, setUpdating] = useState(false);

  const severityClass = alert.risk_level.toLowerCase();
  const statusClass = alert.status.toLowerCase().replace(/\s/g, '-');

  const handleStatusChange = async (newStatus) => {
    setUpdating(true);
    try {
      await onStatusChange(alert.alert_id, newStatus);
    } finally {
      setUpdating(false);
    }
  };

  const impact = alert.business_impact || {};

  // Format cost
  const formatCost = (cost) => {
    if (!cost) return '$0';
    return `$${cost.toLocaleString()}`;
  };

  // Status flow buttons
  const getNextActions = () => {
    switch (alert.status) {
      case 'New':
        return [
          { label: 'Acknowledge Alert', status: 'Acknowledged', className: 'btn-primary' },
          { label: '⚡ Escalate Issue', status: 'Escalated', className: 'btn-danger' },
        ];
      case 'Acknowledged':
        return [
          { label: 'Start Work', status: 'In Progress', className: 'btn-primary' },
          { label: '⚡ Escalate Issue', status: 'Escalated', className: 'btn-danger' },
        ];
      case 'In Progress':
        return [
          { label: '✓ Resolve Issue', status: 'Resolved', className: 'btn-success' },
          { label: '⚡ Escalate Issue', status: 'Escalated', className: 'btn-danger' },
        ];
      case 'Resolved':
        return [{ label: '↺ Reopen Alert', status: 'New', className: '' }];
      case 'Escalated':
        return [
          { label: 'Start Work', status: 'In Progress', className: 'btn-primary' },
          { label: '✓ Resolve Issue', status: 'Resolved', className: 'btn-success' },
        ];
      default:
        return [];
    }
  };

  return (
    <div className={`alert-card severity-${severityClass} fade-in`}>
      {/* Header */}
      <div className="alert-card-header">
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
          {alert.priority_rank && (
            <div className={`priority-rank rank-${Math.min(alert.priority_rank, 3)}`}>
              #{alert.priority_rank}
            </div>
          )}
          <div className="alert-card-title-group">
            <div className="alert-card-title">
              {alert.machine_id ? `${alert.machine_id} (${alert.line_id})` : alert.line_id}
            </div>
            <div className="alert-card-subtitle">
              Created: {new Date(alert.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} · Alert ID: {alert.alert_id}
            </div>
          </div>
        </div>

        <div className="alert-badges">
          <span className={`severity-badge ${severityClass}`}>
            {alert.risk_level} SEVERITY
          </span>
          <span className="risk-score">Score: {alert.risk_score.toFixed(0)}/100</span>
          <span className={`status-badge ${statusClass}`}>{alert.status}</span>
        </div>
      </div>

      {/* Priority rationale for #1 */}
      {alert.priority_rank === 1 && alert.priority_rationale && (
        <div className="priority-rationale">
          ⚠ <strong>TOP PRIORITY ACTION:</strong> {alert.priority_rationale}
        </div>
      )}

      {/* Contributing Factors */}
      {alert.contributing_factors && alert.contributing_factors.length > 0 && (
        <div className="alert-section">
          <div className="alert-section-label">⚡ Contributing Risk Factors</div>
          <div className="factors-grid">
            {alert.contributing_factors
              .filter(f => f.factor !== 'Operator Note')
              .map((factor, i) => (
                <span key={i} className="factor-chip">
                  <span className={`factor-dot ${(factor.severity || 'info').toLowerCase()}`} />
                  {factor.factor}
                  {factor.deviation_pct ? ` (${factor.deviation_pct}%)` : ''}
                  {factor.value && !factor.deviation_pct ? `: ${factor.value}` : ''}
                </span>
              ))}
          </div>
        </div>
      )}

      {/* AI Explanation — Fully Visible */}
      {alert.ai_explanation && (
        <div className="alert-section">
          <div className="alert-section-label">🤖 AI Risk Explanation</div>
          <div className="alert-explanation">{alert.ai_explanation}</div>
        </div>
      )}

      {/* Business Impact — Fully Visible */}
      {impact && (impact.units_at_risk > 0 || impact.estimated_cost > 0) && (
        <div className="alert-section">
          <div className="alert-section-label">📈 Estimated Business Impact</div>
          <div className="impact-grid">
            {impact.units_at_risk > 0 && (
              <div className="impact-item">
                <div className="impact-item-label">Units Delayed</div>
                <div className="impact-item-value">{impact.units_at_risk.toLocaleString()} units</div>
              </div>
            )}
            {impact.estimated_cost > 0 && (
              <div className="impact-item">
                <div className="impact-item-label">Financial Cost Impact</div>
                <div className="impact-item-value cost">{formatCost(impact.estimated_cost)}</div>
              </div>
            )}
            {impact.affected_customer && (
              <div className="impact-item">
                <div className="impact-item-label">Affected Customer</div>
                <div className="impact-item-value">{impact.affected_customer}</div>
              </div>
            )}
            {impact.order_due_date && (
              <div className="impact-item">
                <div className="impact-item-label">Order Deadline</div>
                <div className="impact-item-value">{impact.order_due_date}</div>
              </div>
            )}
            {impact.expected_downtime_hours > 0 && (
              <div className="impact-item">
                <div className="impact-item-label">Expected Downtime</div>
                <div className="impact-item-value">{impact.expected_downtime_hours} Hours</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* AI Recommendations — Fully Visible */}
      {alert.ai_recommendation && (
        <div className="alert-section">
          <div className="alert-section-label">📋 AI Recommended Action Plan</div>
          <div className="alert-recommendations">{alert.ai_recommendation}</div>
        </div>
      )}

      {/* Operator Notes — Fully Visible */}
      {alert.contributing_factors && alert.contributing_factors
        .filter(f => f.factor === 'Operator Note')
        .length > 0 && (
          <div className="alert-section">
            <div className="alert-section-label">📝 Operator Field Notes</div>
            {alert.contributing_factors
              .filter(f => f.factor === 'Operator Note')
              .map((note, i) => (
                <div key={i} className="note-item">
                  <div className="note-meta">{note.author} — {new Date(note.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                  <div className="note-text">"{note.text}"</div>
                </div>
              ))}
          </div>
        )}

      {/* Action Buttons */}
      <div className="alert-actions">
        {getNextActions().map((action) => (
          <button
            key={action.status}
            className={`btn ${action.className}`}
            onClick={() => handleStatusChange(action.status)}
            disabled={updating}
            type="button"
          >
            {updating ? 'Updating...' : action.label}
          </button>
        ))}
      </div>
    </div>
  );
}
