/**
 * FactoryHealthBar — top summary bar with key metrics.
 */

export default function FactoryHealthBar({ summary, loading }) {
  if (loading) {
    return (
      <div className="health-bar">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="health-metric" style={{ opacity: 0.5 }}>
            <div className="health-metric-label">Loading...</div>
            <div className="health-metric-value" style={{ color: 'var(--text-muted)' }}>—</div>
          </div>
        ))}
      </div>
    );
  }

  if (!summary) return null;

  const riskColor =
    summary.overall_risk_pct > 70
      ? 'var(--severity-critical)'
      : summary.overall_risk_pct > 40
        ? 'var(--severity-high)'
        : summary.overall_risk_pct > 20
          ? 'var(--severity-medium)'
          : 'var(--severity-low)';

  const prodColor =
    summary.production_health_pct >= 95
      ? 'var(--accent-success)'
      : summary.production_health_pct >= 85
        ? 'var(--severity-medium)'
        : 'var(--severity-critical)';

  return (
    <div className="health-bar fade-in">
      <div className="health-metric">
        <div className="health-metric-label">Overall Risk Level</div>
        <div className="health-metric-value" style={{ color: riskColor }}>
          {summary.overall_risk_pct.toFixed(0)}%
        </div>
        <div className="health-metric-subtitle">
          Factory-wide avg risk score
        </div>
      </div>

      <div className="health-metric">
        <div className="health-metric-label">Production Health</div>
        <div className="health-metric-value" style={{ color: prodColor }}>
          {summary.production_health_pct.toFixed(1)}%
        </div>
        <div className="health-metric-subtitle">
          Actual vs target output
        </div>
      </div>

      <div className="health-metric">
        <div className="health-metric-label">Active Alerts</div>
        <div className="health-metric-value metric-alerts">
          {summary.active_alerts}
        </div>
        <div className="health-metric-subtitle">
          Require attention
        </div>
      </div>

      <div className="health-metric">
        <div className="health-metric-label">Lines at Risk</div>
        <div className="health-metric-value metric-lines">
          {summary.lines_at_risk} / {summary.total_lines}
        </div>
        <div className="health-metric-subtitle">
          Production lines affected
        </div>
      </div>
    </div>
  );
}
