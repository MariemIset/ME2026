import { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';

export type Role = 'CEO' | 'Marketing' | 'Process' | 'Client' | null;

interface AuthContextType {
  role: Role;
  login: (email: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [role, setRole] = useState<Role>(null);

  const login = (email: string) => {
    const emailLower = email.toLowerCase();
    if (emailLower.includes('ceo')) setRole('CEO');
    else if (emailLower.includes('marketing')) setRole('Marketing');
    else if (emailLower.includes('process')) setRole('Process');
    else setRole('Client');
  };

  const logout = () => setRole(null);

  return (
    <AuthContext.Provider value={{ role, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
};
