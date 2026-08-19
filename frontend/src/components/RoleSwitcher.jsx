/**
 * RoleSwitcher — High-visibility Tab Buttons for Plant Manager, Supervisor, and Maintenance views.
 */

export default function RoleSwitcher({ currentRole, onRoleChange }) {
  const roles = [
    { id: 'Plant Manager', label: '📊 Plant Manager', subtitle: 'Executive View' },
    { id: 'Supervisor', label: '👷 Supervisor', subtitle: 'Operations View' },
    { id: 'Maintenance Team', label: '🔧 Maintenance', subtitle: 'Technical View' },
  ];

  return (
    <div className="role-switcher-tabs" aria-label="Role View Selection">
      {roles.map((role) => (
        <button
          key={role.id}
          className={`role-tab-btn ${currentRole === role.id ? 'active' : ''}`}
          onClick={() => onRoleChange(role.id)}
          type="button"
        >
          {role.label}
        </button>
      ))}
    </div>
  );
}
