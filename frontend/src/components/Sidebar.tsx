// ========================================
// Sidebar Navigation Component
// Responsive admin navigation
// ========================================

import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const navigate = useNavigate();
  const { logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  return (
    <>
      {/* Backdrop for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <div
        className={`
          w-60 bg-coffee-dark text-cream h-screen fixed left-0 top-0 flex flex-col shadow-lg z-50
          transition-transform duration-300 ease-in-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        {/* Logo Section */}
        <div className="h-20 flex items-center justify-between border-b border-coffee-light px-6">
          <div className="text-center flex-1">
            <h1 className="text-lg font-bold">Lily Cafe</h1>
            <p className="text-xs text-cream/70">Admin Portal</p>
          </div>
          {/* Close button for mobile */}
          <button
            onClick={onClose}
            className="lg:hidden w-8 h-8 flex items-center justify-center rounded-full hover:bg-coffee-light transition-colors"
            aria-label="Close menu"
          >
            <span className="text-xl">&times;</span>
          </button>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
          <NavItem
            to="/admin/active-orders"
            icon="📊"
            label="Active Orders"
            onClick={onClose}
          />
          <NavItem
            to="/admin/order-history"
            icon="📜"
            label="Order History"
            onClick={onClose}
          />
          <NavItem
            to="/admin/menu"
            icon="📋"
            label="Menu Management"
            onClick={onClose}
          />

          {/* Divider */}
          <div className="border-t border-coffee-light my-4"></div>

          <NavItem
            to="/tables"
            icon="🏠"
            label="Waiter View"
            onClick={onClose}
          />
        </nav>

        {/* Logout Section */}
        <div className="p-4 border-t border-coffee-light">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg
                     text-cream hover:bg-coffee-brown transition-colors"
          >
            <span className="text-lg">🚪</span>
            <span className="font-medium">Logout</span>
          </button>
        </div>
      </div>
    </>
  );
}

// Navigation Item Component
interface NavItemProps {
  to: string;
  icon: string;
  label: string;
  onClick: () => void;
}

function NavItem({ to, icon, label, onClick }: NavItemProps) {
  return (
    <NavLink
      to={to}
      onClick={onClick}
      className={({ isActive }) =>
        `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
          isActive
            ? 'bg-coffee-brown text-cream font-semibold'
            : 'text-cream hover:bg-coffee-light'
        }`
      }
    >
      <span className="text-lg">{icon}</span>
      <span>{label}</span>
    </NavLink>
  );
}
