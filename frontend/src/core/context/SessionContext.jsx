import React, { createContext, useContext, useState, useEffect } from 'react';

const SessionContext = createContext();

export const SessionProvider = ({ children }) => {
  // Environment detection (Simulation of .env)
  const [appMode, setAppMode] = useState('LAB'); // Could be loaded from import.meta.env.VITE_APP_MODE

  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSession = async () => {
      if (appMode === 'LAB') {
        setSession({
          prefecture: { id: '3128253', name: 'Guaraciama - MG' },
          unit: { id: '10', name: 'UBS SAO JOAO BATISTA PLANTOES' },
          sector: { id: '0', name: 'ATENDIMENTO' },
          user: { id: '1659', name: 'Administrador (Mock)', role: 'Gestor' },
          isValid: true
        });
        setLoading(false);
        return;
      }

      try {
        const response = await fetch('http://localhost:8000/almox/v1/session/current');
        const result = await response.json();
        if (result.data) {
          setSession(result.data);
        }
      } catch (error) {
        console.error("Failed to fetch real session:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchSession();
  }, [appMode]);

  const updateUnit = (newUnit) => {
    setSession(prev => ({
      ...prev,
      unit: newUnit,
      sector: { id: '', name: 'Selecione o Setor' } 
    }));
  };

  const updateSector = (newSector) => {
    setSession(prev => ({ ...prev, sector: newSector }));
  };

  return (
    <SessionContext.Provider value={{ session, loading, appMode, updateUnit, updateSector, setAppMode }}>
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
