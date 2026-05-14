import React, { useState } from 'react';
import { SessionProvider } from './core/context/SessionContext';
import AppShell from './core/layout/AppShell';
import Reconciliation from './pages/Inbound/Reconciliation';
import DirectInbound from './pages/Inbound/DirectInbound';
import PrinciplesList from './pages/Catalog/PrinciplesList';
import ProductsList from './pages/Catalog/ProductsList';
import './App.css';

function App() {
  const [currentView, setCurrentView] = useState('direct_inbound');

  const renderView = () => {
    switch (currentView) {
      case 'principles': return <PrinciplesList />;
      case 'products': return <ProductsList />;
      case 'reconciliation': return <Reconciliation />;
      case 'direct_inbound': return <DirectInbound />;
      default: return <Reconciliation />;
    }
  };

  return (
    <SessionProvider>
      <AppShell activeView={currentView} onViewChange={setCurrentView}>
        {renderView()}
      </AppShell>
    </SessionProvider>
  );
}

export default App;
