import React from 'react';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import './AppShell.css';

const AppShell = ({ children, activeView, onViewChange }) => {
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
