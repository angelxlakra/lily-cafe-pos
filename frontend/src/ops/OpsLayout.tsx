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
        <NavLink to="/admin/ops/inventory" className={link}>Inventory</NavLink>
        <NavLink to="/admin/ops/sheet" className={link}>Daily sheet</NavLink>
        {isOwner && <NavLink to="/admin/ops/recipes" className={link}>Recipes</NavLink>}
        <span className="spacer" />
        <button type="button" onClick={toggleTheme}>{theme === 'dark' ? 'Light mode' : 'Dark mode'}</button>
        <NavLink to="/admin/active-orders">Back to admin</NavLink>
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
