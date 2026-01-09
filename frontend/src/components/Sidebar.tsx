import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { ThemeToggle } from "./ThemeToggle";
import { useSidebar } from "../context/SidebarContext";
import {
  ActiveOrdersIcon,
  OrderHistoryIcon,
  MenuManagementIcon,
  WaiterViewIcon,
  LogoutIcon,
} from "./icons/NavigationIcons";
import { Package, CurrencyInr, ChartLine, CaretLeft, CaretRight } from "@phosphor-icons/react";
import type { ReactNode } from "react";

export default function Sidebar() {
  const navigate = useNavigate();
  const { logout, role } = useAuth();
  const { isCollapsed, toggleCollapse, isMobileOpen, setMobileOpen } = useSidebar();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  const handleCloseMobile = () => setMobileOpen(false);

  // Always use cream logo
  const logoSrc = '/logos/logo_cream.png';

  return (
    <>
      {/* Backdrop for mobile */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={handleCloseMobile}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <div
        className={`
          bg-coffee-dark text-cream h-screen fixed left-0 top-0 flex flex-col shadow-lg z-50
          transition-all duration-300 ease-in-out
          ${isMobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
          ${isCollapsed ? "lg:w-20" : "lg:w-60"}
          w-60
        `}
      >
        {/* Logo Section */}
        <div className={`h-24 flex items-center ${isCollapsed ? 'justify-center' : 'justify-between px-6'} border-b border-coffee-light relative`}>
           <div className={`flex items-center gap-3 ${isCollapsed ? 'justify-center w-full' : ''}`}>
             <img
               src={logoSrc}
               alt="Lily Cafe Logo"
               className={`object-contain shrink-0 transition-all duration-300 ${isCollapsed ? 'w-10 h-10' : 'w-11 h-11'}`}
             />
             {!isCollapsed && (
               <div className="flex-1 text-left min-w-0">
                 <span className="block font-heading text-xl tracking-[0.18em] leading-tight truncate">
                   Lily Cafe
                 </span>
                 <span className="block text-[0.65rem] uppercase tracking-[0.3em] text-cream/70 mt-1 truncate">
                   Admin Portal
                 </span>
               </div>
             )}
           </div>
           
           {/* Collapse Toggle Button (Desktop) */}
           <button
             onClick={toggleCollapse}
             className="hidden lg:flex absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 bg-coffee-brown border border-coffee-light rounded-full items-center justify-center text-cream hover:bg-coffee-light transition-colors z-50 shadow-md"
             title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
           >
             {isCollapsed ? <CaretRight size={14} weight="bold" /> : <CaretLeft size={14} weight="bold" />}
           </button>

          {/* Close button for mobile */}
          <button
            onClick={handleCloseMobile}
            className="lg:hidden w-8 h-8 flex items-center justify-center rounded-full hover:bg-coffee-light transition-colors absolute right-4 top-1/2 -translate-y-1/2"
            aria-label="Close menu"
          >
            <span className="text-xl">&times;</span>
          </button>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto overflow-x-hidden">
          <NavItem
            to="/admin/active-orders"
            icon={<ActiveOrdersIcon />}
            label="Active Orders"
            onClick={handleCloseMobile}
            isCollapsed={isCollapsed}
          />
          <NavItem
            to="/admin/order-history"
            icon={<OrderHistoryIcon />}
            label="Order History"
            onClick={handleCloseMobile}
            isCollapsed={isCollapsed}
          />
          {role === 'owner' && (
            <NavItem
              to="/admin/analytics"
              icon={<ChartLine size={24} weight="duotone" />}
              label="Analytics"
              onClick={handleCloseMobile}
              isCollapsed={isCollapsed}
            />
          )}
          <NavItem
            to="/admin/cash-counter"
            icon={<CurrencyInr size={24} />}
            label="Cash Counter"
            onClick={handleCloseMobile}
            isCollapsed={isCollapsed}
          />
          <NavItem
            to="/admin/inventory"
            icon={<Package size={24} />}
            label="Inventory"
            onClick={handleCloseMobile}
            isCollapsed={isCollapsed}
          />
          <NavItem
            to="/admin/menu"
            icon={<MenuManagementIcon />}
            label="Menu Management"
            onClick={handleCloseMobile}
            isCollapsed={isCollapsed}
          />

          {/* Divider */}
          <div className="border-t border-coffee-light my-4"></div>

          <NavItem
            to="/tables"
            icon={<WaiterViewIcon />}
            label="Waiter View"
            onClick={handleCloseMobile}
            isCollapsed={isCollapsed}
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
            className={`w-full flex items-center ${isCollapsed ? 'justify-center' : 'gap-3'} px-4 py-3 rounded-lg
                     text-cream hover:bg-coffee-brown transition-colors group relative`}
            title={isCollapsed ? "Logout" : ""}
          >
            <span className="text-lg shrink-0">
              <LogoutIcon size={22} />
            </span>
            {!isCollapsed && <span className="font-medium whitespace-nowrap">Logout</span>}
            
            {/* Tooltip for collapsed state */}
            {isCollapsed && (
              <div className="absolute left-full ml-4 px-2 py-1 bg-coffee-dark text-cream text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50 pointer-events-none">
                Logout
              </div>
            )}
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
  isCollapsed: boolean;
}

function NavItem({ to, icon, label, onClick, isCollapsed }: NavItemProps) {
  return (
    <NavLink
      to={to}
      onClick={onClick}
      className={({ isActive }) =>
        `flex items-center ${isCollapsed ? 'justify-center px-2' : 'gap-3 px-4'} py-3 rounded-lg transition-colors group relative ${
          isActive
            ? "bg-coffee-brown text-cream font-semibold"
            : "text-cream hover:bg-coffee-light"
        }`
      }
      title={isCollapsed ? label : ""}
    >
      <span className="text-xl text-cream/80 shrink-0">{icon}</span>
      {!isCollapsed && <span className="whitespace-nowrap overflow-hidden">{label}</span>}

      {/* Tooltip for collapsed state */}
      {isCollapsed && (
        <div className="absolute left-full ml-4 px-2 py-1 bg-coffee-dark text-cream text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50 pointer-events-none">
          {label}
        </div>
      )}
    </NavLink>
  );
}

