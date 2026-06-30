import React, { createContext, useContext, useState, ReactNode } from 'react';

interface SimulationContextType {
  customImage: string | null;
  setCustomImage: (image: string | null) => void;
}

const SimulationContext = createContext<SimulationContextType | undefined>(undefined);

export const SimulationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [customImage, setCustomImageState] = useState<string | null>(() => {
    return localStorage.getItem('simulation_custom_image') || null;
  });

  const setCustomImage = (image: string | null) => {
    setCustomImageState(image);
    if (image) {
      try {
        localStorage.setItem('simulation_custom_image', image);
      } catch (e) {
        console.warn('Could not persist image in localStorage (likely due to size limits). Image will remain in memory.', e);
      }
    } else {
      localStorage.removeItem('simulation_custom_image');
    }
  };

  return (
    <SimulationContext.Provider value={{ customImage, setCustomImage }}>
      {children}
    </SimulationContext.Provider>
  );
};

export const useSimulation = () => {
  const context = useContext(SimulationContext);
  if (!context) {
    throw new Error('useSimulation must be used within a SimulationProvider');
  }
  return context;
};
