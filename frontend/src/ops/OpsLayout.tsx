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
          <NavLink to="/admin/ops/sheet" className={link}>Daily sheet</NavLink>
          {isOwner && <NavLink to="/admin/ops/recipes" className={link}>Recipes</NavLink>}
        </div>
        <button type="button" onClick={toggleTheme} aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}>
          {theme === 'dark' ? 'Light' : 'Dark'}
        </button>
        <NavLink to="/admin/active-orders" aria-label="Back to admin">Admin</NavLink>
      </nav>
      <main className="ops-main">
        <Outlet />
      </main>
    </div>
  );
}

/** Stands in for a page a later step builds. */
export function OpsPlaceholder({ title }: { title: string }) {
  return (
    <>
      <h1>{title}</h1>
      <p className="muted">Coming in the next step.</p>
    </>
  );
}
