/**
 * MaintenanceView — machine health detail (temp/vibration values),
 * maintenance history / overdue status, technical recommended actions.
 */

import { useState, useEffect } from 'react';
import AlertList from './AlertList';
import { api } from '../api';

export default function MaintenanceView({ alerts, machines, onStatusChange, loading }) {
  const [selectedMachineId, setSelectedMachineId] = useState('M103');
  const [readings, setReadings] = useState([]);
  const [readingsLoading, setReadingsLoading] = useState(false);

  // Selected machine object
  const selectedMachine = machines.find((m) => m.machine_id === selectedMachineId) || machines[0];

  useEffect(() => {
    if (selectedMachineId) {
      setReadingsLoading(true);
      api
        .getMachineReadings(selectedMachineId)
        .then((data) => setReadings(data))
        .catch((err) => console.error('Failed to fetch readings:', err))
        .finally(() => setReadingsLoading(false));
    }
  }, [selectedMachineId]);

  // Alert for the selected machine if any
  const machineAlerts = alerts.filter((a) => a.machine_id === selectedMachineId);

  // Calculate days overdue
  const getOverdueDays = (dueDateStr) => {
    if (!dueDateStr) return 0;
    const due = new Date(dueDateStr);
    const today = new Date();
    const diffTime = today - due;
    return Math.floor(diffTime / (1000 * 60 * 60 * 24));
  };

  const latestReading = readings[readings.length - 1];

  return (
    <div className="fade-in">
      <div className="role-section">
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)', marginBottom: 'var(--space-lg)' }}>
          <div className="role-section-title" style={{ margin: 0 }}>
            <span className="icon">🔧</span> Machine Telemetry & Maintenance
          </div>
          <select
            value={selectedMachineId}
            onChange={(e) => setSelectedMachineId(e.target.value)}
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
            {machines.map((m) => (
              <option key={m.machine_id} value={m.machine_id}>
                {m.machine_id} — {m.machine_name} ({m.line_id})
              </option>
            ))}
          </select>
        </div>

        {/* Machine Status Summary */}
        {selectedMachine && (
          <div className="machine-detail">
            <div className="machine-detail-header">
              <div>
                <h3 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 700 }}>
                  {selectedMachine.machine_name} ({selectedMachine.machine_id})
                </h3>
                <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)' }}>
                  Type: {selectedMachine.machine_type} | Line: {selectedMachine.line_id}
                </div>
              </div>
              <div>
                {getOverdueDays(selectedMachine.maintenance_due_date) > 0 ? (
                  <span className="severity-badge critical">
                    ⚠ Maintenance {getOverdueDays(selectedMachine.maintenance_due_date)} Days Overdue
                  </span>
                ) : (
                  <span className="severity-badge low">Maintenance Up to Date</span>
                )}
              </div>
            </div>

            {/* Sensor Readings Gauges / Cards */}
            {readingsLoading ? (
              <div className="loading" style={{ padding: 'var(--space-md)' }}>
                <div className="loading-spinner" />
              </div>
            ) : latestReading ? (
              <div className="sensor-readings">
                {/* Temperature Sensor */}
                <div className="sensor-item">
                  <div className="sensor-label">Temperature</div>
                  <div
                    className="sensor-value"
                    style={{
                      color:
                        latestReading.temperature > latestReading.normal_temperature * 1.2
                          ? 'var(--severity-critical)'
                          : latestReading.temperature > latestReading.normal_temperature * 1.1
                          ? 'var(--severity-high)'
                          : 'var(--accent-success)',
                    }}
                  >
                    {latestReading.temperature}°C
                  </div>
                  <div className="sensor-normal">Normal Baseline: {latestReading.normal_temperature}°C</div>
                  <div className="sensor-bar">
                    <div
                      className="sensor-bar-fill"
                      style={{
                        width: `${Math.min(100, (latestReading.temperature / 100) * 100)}%`,
                        background:
                          latestReading.temperature > latestReading.normal_temperature * 1.2
                            ? 'var(--severity-critical)'
                            : latestReading.temperature > latestReading.normal_temperature * 1.1
                            ? 'var(--severity-high)'
                            : 'var(--accent-success)',
                      }}
                    />
                  </div>
                </div>

                {/* Vibration Sensor */}
                <div className="sensor-item">
                  <div className="sensor-label">Vibration</div>
                  <div
                    className="sensor-value"
                    style={{
                      color:
                        latestReading.vibration > latestReading.normal_vibration * 1.5
                          ? 'var(--severity-critical)'
                          : latestReading.vibration > latestReading.normal_vibration * 1.2
                          ? 'var(--severity-high)'
                          : 'var(--accent-success)',
                    }}
                  >
                    {latestReading.vibration} mm/s
                  </div>
                  <div className="sensor-normal">Normal Baseline: {latestReading.normal_vibration} mm/s</div>
                  <div className="sensor-bar">
                    <div
                      className="sensor-bar-fill"
                      style={{
                        width: `${Math.min(100, (latestReading.vibration / 6.0) * 100)}%`,
                        background:
                          latestReading.vibration > latestReading.normal_vibration * 1.5
                            ? 'var(--severity-critical)'
                            : latestReading.vibration > latestReading.normal_vibration * 1.2
                            ? 'var(--severity-high)'
                            : 'var(--accent-success)',
                      }}
                    />
                  </div>
                </div>

                {/* Maintenance Log */}
                <div className="sensor-item">
                  <div className="sensor-label">Maintenance Info</div>
                  <div style={{ fontSize: 'var(--font-size-sm)', marginTop: '4px' }}>
                    <strong>Last Service:</strong> {selectedMachine.last_maintenance_date || 'N/A'}
                  </div>
                  <div style={{ fontSize: 'var(--font-size-sm)', marginTop: '4px' }}>
                    <strong>Due Date:</strong> {selectedMachine.maintenance_due_date || 'N/A'}
                  </div>
                </div>
              </div>
            ) : (
              <div style={{ color: 'var(--text-muted)' }}>No telemetry available for this machine.</div>
            )}
          </div>
        )}
      </div>

      {/* Sensor Trend Table */}
      {readings.length > 0 && (
        <div className="role-section">
          <div className="role-section-title">
            <span className="icon">📈</span> Telemetry History ({selectedMachineId})
          </div>
          <div className="machine-detail" style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Temperature (°C)</th>
                  <th>Temp Normal</th>
                  <th>Vibration (mm/s)</th>
                  <th>Vib Normal</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {[...readings].reverse().map((r) => {
                  const isTempHigh = r.temperature > r.normal_temperature * 1.1;
                  const isVibHigh = r.vibration > r.normal_vibration * 1.2;
                  return (
                    <tr key={r.id}>
                      <td>{new Date(r.timestamp).toLocaleTimeString()}</td>
                      <td style={{ fontWeight: isTempHigh ? 700 : 400, color: isTempHigh ? 'var(--severity-critical)' : 'inherit' }}>
                        {r.temperature}°C
                      </td>
                      <td>{r.normal_temperature}°C</td>
                      <td style={{ fontWeight: isVibHigh ? 700 : 400, color: isVibHigh ? 'var(--severity-critical)' : 'inherit' }}>
                        {r.vibration} mm/s
                      </td>
                      <td>{r.normal_vibration} mm/s</td>
                      <td>
                        {isTempHigh || isVibHigh ? (
                          <span className="severity-badge critical">Anomaly</span>
                        ) : (
                          <span className="severity-badge low">Normal</span>
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

      {/* Technical Actions & Alerts for this machine */}
      <div className="role-section">
        <AlertList
          alerts={machineAlerts}
          onStatusChange={onStatusChange}
          loading={loading}
          title={`🛠 Technical Actions & Alerts (${selectedMachineId})`}
        />
      </div>
    </div>
  );
}
