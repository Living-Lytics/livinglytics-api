import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { useEffect } from 'react';
import { ToastProvider } from './components/Toast';
import { Dashboard } from './routes/Dashboard';
import { Connections } from './routes/Connections';
import { Settings } from './routes/Settings';
import { CallbackGoogle } from './routes/CallbackGoogle';
import { CallbackInstagram } from './routes/CallbackInstagram';
import { useStore } from './lib/useStore';

const Navigation = () => {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  const navItemClass = (path: string) =>
    `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
      isActive(path)
        ? 'bg-blue-600 text-white'
        : 'text-gray-700 hover:bg-gray-100'
    }`;

  return (
    <aside className="w-64 bg-white border-r border-gray-200 min-h-screen p-6">
      {/* Logo */}
      <div className="mb-8">
        <div className="flex items-center gap-2">
          <div className="bg-blue-600 text-white w-10 h-10 rounded-lg flex items-center justify-center font-bold text-lg">
            LL
          </div>
          <div>
            <h1 className="font-bold text-gray-900">Living Lytics</h1>
            <p className="text-xs text-gray-500">Where data comes alive</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="space-y-2">
        <Link to="/" className={navItemClass('/')}>
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
          Dashboard
        </Link>

        <Link to="/connections" className={navItemClass('/connections')}>
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          Connections
        </Link>

        <Link to="/settings" className={navItemClass('/settings')}>
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          Settings
        </Link>
      </nav>
    </aside>
  );
};

const NotFound = () => (
  <div className="flex items-center justify-center h-screen">
    <div className="text-center">
      <h1 className="text-6xl font-bold text-gray-300 mb-4">404</h1>
      <p className="text-gray-600 mb-4">Page not found</p>
      <Link to="/" className="text-blue-600 hover:text-blue-700">
        Go to Dashboard
      </Link>
    </div>
  </div>
);

const Layout = () => {
  const { refreshConnections } = useStore();

  useEffect(() => {
    refreshConnections();
  }, [refreshConnections]);

  return (
    <div className="flex">
      <Navigation />
      <main className="flex-1 bg-gray-50 min-h-screen">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/connections" element={<Connections />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
    </div>
  );
};

function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <Routes>
          <Route path="/oauth/callback/google" element={<CallbackGoogle />} />
          <Route path="/oauth/callback/instagram" element={<CallbackInstagram />} />
          <Route path="/*" element={<Layout />} />
        </Routes>
      </ToastProvider>
    </BrowserRouter>
  );
}

export default App;
