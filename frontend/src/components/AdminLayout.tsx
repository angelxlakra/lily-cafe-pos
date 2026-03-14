import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import LinenTexture from "./LinenTexture";
import { useSidebar } from "../context/SidebarContext";

export default function AdminLayout() {
  const { isCollapsed } = useSidebar();

  return (
    <div className="flex min-h-screen bg-off-white relative">
      <LinenTexture />
      <Sidebar />
      <main
        className={`
          flex-1 transition-all duration-300 ease-in-out relative z-10
          ${isCollapsed ? "lg:ml-20" : "lg:ml-60"}
        `}
      >
        <Outlet />
      </main>
    </div>
  );
}
