// ========================================
// Sidebar Navigation Component
// Responsive admin navigation
// ========================================

import type { ReactNode } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { ThemeToggle } from "./ThemeToggle";
import {
  ActiveOrdersIcon,
  OrderHistoryIcon,
  MenuManagementIcon,
  WaiterViewIcon,
  LogoutIcon,
} from "./icons/NavigationIcons";
import { Package, CurrencyInr } from "@phosphor-icons/react";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const navigate = useNavigate();
  const { logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  // Always use cream logo
  const logoSrc = '/logos/logo_cream.png';

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
          ${isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
        `}
      >
        {/* Logo Section */}
        <div className="h-24 flex items-center justify-between border-b border-coffee-light px-6">
          <div className="flex items-center gap-3">
            <img
              src={logoSrc}
              alt="Lily Cafe Logo"
              className="w-11 h-11 object-contain shrink-0 transition-opacity duration-300"
            />
            <div className="flex-1 text-left">
              <span className="block font-heading text-xl tracking-[0.18em] leading-tight">
                Lily Cafe
              </span>
              <span className="block text-[0.65rem] uppercase tracking-[0.3em] text-cream/70 mt-1">
                Admin Portal
              </span>
            </div>
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
            icon={<ActiveOrdersIcon />}
            label="Active Orders"
            onClick={onClose}
          />
          <NavItem
            to="/admin/order-history"
            icon={<OrderHistoryIcon />}
            label="Order History"
            onClick={onClose}
          />
          <NavItem
            to="/admin/cash-counter"
            icon={<CurrencyInr size={24} />}
            label="Cash Counter"
            onClick={onClose}
          />
          <NavItem
            to="/admin/inventory"
            icon={<Package size={24} />}
            label="Inventory"
            onClick={onClose}
          />
          <NavItem
            to="/admin/menu"
            icon={<MenuManagementIcon />}
            label="Menu Management"
            onClick={onClose}
          />

          {/* Divider */}
          <div className="border-t border-coffee-light my-4"></div>

          <NavItem
            to="/tables"
            icon={<WaiterViewIcon />}
            label="Waiter View"
            onClick={onClose}
          />
        </nav>

        {/* Theme Toggle & Logout Section */}
        <div className="p-4 border-t border-coffee-light space-y-3">
          {/* Theme Toggle */}
          <div className="flex items-center justify-center">
            <ThemeToggle />
          </div>

          {/* Logout Button */}
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg
                     text-cream hover:bg-coffee-brown transition-colors"
          >
            <span className="text-lg">
              <LogoutIcon size={22} />
            </span>
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
  icon: ReactNode;
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
            ? "bg-coffee-brown text-cream font-semibold"
            : "text-cream hover:bg-coffee-light"
        }`
      }
    >
      <span className="text-xl text-cream/80">{icon}</span>
      <span>{label}</span>
    </NavLink>
  );
}
