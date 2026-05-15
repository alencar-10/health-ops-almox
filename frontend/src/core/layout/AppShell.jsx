import { useSession } from '../context/SessionContext';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import './AppShell.css';

const AppShell = ({ children, activeView, onViewChange }) => {
  const { loading } = useSession();

  if (loading) {
    return (
      <div className="app-shell-loading">
        <div className="loader"></div>
        <p>Sincronizando Contexto Real com Vivver ERP...</p>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <Sidebar activeView={activeView} onViewChange={onViewChange} />
      <TopBar />
      <main className="main-content">
        {children}
      </main>
    </div>
  );
};

export default AppShell;
