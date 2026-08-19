/**
 * PlantManagerView — factory-wide risk overview, financial impact, prioritized top risks.
 */

import AlertList from './AlertList';

export default function PlantManagerView({ alerts, summary, orders, onStatusChange, loading }) {
  // Calculate totals
  const totalCostAtRisk = alerts.reduce(
    (sum, a) => sum + (a.business_impact?.estimated_cost || 0), 0
  );
  const totalUnitsAtRisk = alerts.reduce(
    (sum, a) => sum + (a.business_impact?.units_at_risk || 0), 0
  );
  const criticalAlerts = alerts.filter(a => a.risk_level === 'Critical').length;
  const highAlerts = alerts.filter(a => a.risk_level === 'High').length;
  const customersAffected = [
    ...new Set(alerts.map(a => a.business_impact?.affected_customer).filter(Boolean))
  ];

  return (
    <div className="fade-in">
      <div className="role-section">
        <div className="role-section-title">
          <span className="icon">📊</span> Executive Summary
        </div>
        <div className="metrics-row">
          <div className="metric-card">
            <div className="metric-card-label">Total Financial Exposure</div>
            <div className="metric-card-value" style={{ color: 'var(--severity-critical)' }}>
              ${totalCostAtRisk.toLocaleString()}
            </div>
            <div className="metric-card-subtitle">Across all active alerts</div>
          </div>
          <div className="metric-card">
            <div className="metric-card-label">Units at Risk</div>
            <div className="metric-card-value" style={{ color: 'var(--severity-high)' }}>
              {totalUnitsAtRisk.toLocaleString()}
            </div>
            <div className="metric-card-subtitle">Production output threatened</div>
          </div>
          <div className="metric-card">
            <div className="metric-card-label">Critical / High Alerts</div>
            <div className="metric-card-value" style={{ color: 'var(--severity-critical)' }}>
              {criticalAlerts} / {highAlerts}
            </div>
            <div className="metric-card-subtitle">Requiring immediate attention</div>
          </div>
          <div className="metric-card">
            <div className="metric-card-label">Customers Affected</div>
            <div className="metric-card-value" style={{ color: 'var(--accent-secondary)' }}>
              {customersAffected.length}
            </div>
            <div className="metric-card-subtitle">
              {customersAffected.join(', ') || 'None'}
            </div>
          </div>
        </div>
      </div>

      {/* Orders at risk */}
      {orders && orders.length > 0 && (
        <div className="role-section">
          <div className="role-section-title">
            <span className="icon">📦</span> Orders Status
          </div>
          <div className="machine-detail">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Order</th>
                  <th>Customer</th>
                  <th>Due Date</th>
                  <th>Priority</th>
                  <th>Progress</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((order) => {
                  const pct = ((order.units_completed / order.units_target) * 100).toFixed(0);
                  const daysUntil = Math.ceil(
                    (new Date(order.due_date) - new Date()) / (1000 * 60 * 60 * 24)
                  );
                  const isAtRisk = pct < 80 && daysUntil <= 2;
                  return (
                    <tr key={order.order_id}>
                      <td>{order.order_id}</td>
                      <td style={{ fontWeight: 600 }}>{order.customer}</td>
                      <td>
                        {order.due_date}
                        <span style={{
                          color: daysUntil <= 1 ? 'var(--severity-critical)' : 'var(--text-muted)',
                          fontSize: 'var(--font-size-xs)',
                          marginLeft: '6px'
                        }}>
                          ({daysUntil <= 0 ? 'TODAY' : `${daysUntil}d`})
                        </span>
                      </td>
                      <td>
                        <span className={`severity-badge ${order.priority === 'High' ? 'high' : 'low'}`}>
                          {order.priority}
                        </span>
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <div className="progress-bar" style={{ flex: 1 }}>
                            <div
                              className="progress-bar-fill"
                              style={{
                                width: `${pct}%`,
                                background: isAtRisk ? 'var(--severity-critical)' : 'var(--accent-success)',
                              }}
                            />
                          </div>
                          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', minWidth: '36px' }}>
                            {pct}%
                          </span>
                        </div>
                      </td>
                      <td>
                        {isAtRisk ? (
                          <span style={{ color: 'var(--severity-critical)', fontWeight: 600, fontSize: 'var(--font-size-xs)' }}>
                            ⚠ AT RISK
                          </span>
                        ) : (
                          <span style={{ color: 'var(--accent-success)', fontSize: 'var(--font-size-xs)' }}>
                            On Track
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Prioritized alerts */}
      <div className="role-section">
        <AlertList
          alerts={alerts}
          onStatusChange={onStatusChange}
          loading={loading}
          title="📋 Prioritized Risk Queue"
        />
      </div>
    </div>
  );
}
