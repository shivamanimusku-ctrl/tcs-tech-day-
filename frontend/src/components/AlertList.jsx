/**
 * AlertList — ranked list of alert cards.
 */

import AlertCard from './AlertCard';

export default function AlertList({ alerts, onStatusChange, loading, title = 'Active Alerts' }) {
  if (loading) {
    return (
      <div className="alert-list">
        <div className="alert-list-header">
          <h2>{title}</h2>
        </div>
        <div className="loading">
          <div className="loading-spinner" />
          <span>Loading active alerts...</span>
        </div>
      </div>
    );
  }

  if (!alerts || alerts.length === 0) {
    return (
      <div className="alert-list">
        <div className="alert-list-header">
          <h2>{title}</h2>
        </div>
        <div className="empty-state">
          <div className="empty-state-icon">✅</div>
          <p>No active alerts — all manufacturing lines running normally</p>
        </div>
      </div>
    );
  }

  return (
    <div className="alert-list">
      <div className="alert-list-header">
        <h2>{title}</h2>
        <span className="alert-count-badge">{alerts.length} active alert{alerts.length !== 1 ? 's' : ''}</span>
      </div>
      {alerts.map((alert) => (
        <AlertCard
          key={alert.alert_id}
          alert={alert}
          onStatusChange={onStatusChange}
        />
      ))}
    </div>
  );
}
