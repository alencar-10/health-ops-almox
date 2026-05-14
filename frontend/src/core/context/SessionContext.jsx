import React, { createContext, useContext, useState, useEffect } from 'react';

const SessionContext = createContext();

export const SessionProvider = ({ children }) => {
  // Environment detection (Simulation of .env)
  const [appMode, setAppMode] = useState('LAB'); // Could be loaded from import.meta.env.VITE_APP_MODE

  const [session, setSession] = useState({
    prefecture: {
      id: '3128253',
      name: 'Guaraciama - MG'
    },
    unit: {
      id: '10',
      name: 'UBS SAO JOAO BATISTA PLANTOES'
    },
    sector: {
      id: '0',
      name: 'ATENDIMENTO'
    },
    user: {
      id: '1659',
      name: 'Administrador',
      role: 'Gestor'
    },
    isValid: true
  });

  const updateUnit = (newUnit) => {
    setSession(prev => ({
      ...prev,
      unit: newUnit,
      sector: { id: '', name: 'Selecione o Setor' } // Reset sector on unit change
    }));
  };

  const updateSector = (newSector) => {
    setSession(prev => ({ ...prev, sector: newSector }));
  };

  return (
    <SessionContext.Provider value={{ session, appMode, updateUnit, updateSector }}>
      {children}
    </SessionContext.Provider>
  );
};

export const useSession = () => {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
};
