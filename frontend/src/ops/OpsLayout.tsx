import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useTheme } from '../contexts/ThemeContext';
import './ops.css';

/** The ops pages' own chrome: a thin top bar, no POS sidebar. */
export default function OpsLayout() {
  const { isOwner } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const link = ({ isActive }: { isActive: boolean }) => (isActive ? 'active' : undefined);
  return (
    <div className="ops">
      <nav className="ops-bar" aria-label="Ops">
        <div className="ops-links">
          <NavLink to="/admin/ops/inventory" className={link}>Inventory</NavLink>
          <NavLink to="/admin/ops/count" className={link}>Count</NavLink>
          <NavLink to="/admin/ops/sheet" className={link}>Daily sheet</NavLink>
          <NavLink to="/admin/ops/order" className={link}>Order</NavLink>
          <NavLink to="/admin/ops/log" className={link}>Stock log</NavLink>
          {isOwner && <NavLink to="/admin/ops/setup" className={link}>Setup</NavLink>}
          {isOwner && <NavLink to="/admin/ops/recipes" className={link}>Recipes</NavLink>}
        </div>
        <button type="button" onClick={toggleTheme}>
          <span className="long">{theme === 'dark' ? 'Light mode' : 'Dark mode'}</span>
          <span className="short">{theme === 'dark' ? 'Light' : 'Dark'}</span>
        </button>
        <NavLink to="/admin/active-orders">
          <span className="long">Back to admin</span>
          <span className="short">Admin</span>
        </NavLink>
      </nav>
      <main className="ops-main">
        <Outlet />
      </main>
    </div>
  );
}
