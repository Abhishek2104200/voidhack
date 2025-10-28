import { Outlet, Link, useNavigate } from 'react-router-dom';
import { FileText, LayoutDashboard, LogOut } from 'lucide-react';

const MainLayout = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    navigate('/login');
  };

  return (
    <div className="min-h-screen animated-gradient-bg">
      <div className="flex min-h-screen">
        <aside className="w-64 glass-sidebar flex flex-col">
          <div className="p-6">
            <h1 className="text-2xl font-bold text-white mb-2">Voidhack</h1>
            <p className="text-sm text-gray-400">Grading System</p>
          </div>

          <nav className="flex-1 px-4 space-y-2">
            <Link
              to="/"
              className="flex items-center space-x-3 px-4 py-3 text-gray-300 hover:text-white hover:bg-white/10 rounded-lg transition-all duration-200"
            >
              <FileText className="w-5 h-5" />
              <span>New Evaluation</span>
            </Link>

            <Link
              to="/admin"
              className="flex items-center space-x-3 px-4 py-3 text-gray-300 hover:text-white hover:bg-white/10 rounded-lg transition-all duration-200"
            >
              <LayoutDashboard className="w-5 h-5" />
              <span>Admin Dashboard</span>
            </Link>
          </nav>

          <div className="p-4">
            <button
              onClick={handleLogout}
              className="flex items-center space-x-3 w-full px-4 py-3 text-gray-300 hover:text-white hover:bg-red-500/20 rounded-lg transition-all duration-200"
            >
              <LogOut className="w-5 h-5" />
              <span>Logout</span>
            </button>
          </div>
        </aside>

        <main className="flex-1 p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default MainLayout;
