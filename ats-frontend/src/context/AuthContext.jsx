import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authService } from '../services/authService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem('ats_user');
      if (stored) return JSON.parse(stored);
    } catch {
      // ignore
    }
    return null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('ats_token') || null);

  const logout = useCallback(() => {
    localStorage.removeItem('ats_token');
    localStorage.removeItem('ats_user');
    setToken(null);
    setUser(null);
  }, []);

  const updateUser = useCallback((updates) => {
    setUser((current) => (current ? { ...current, ...updates } : current));
  }, []);

  useEffect(() => {
    if (token) {
      localStorage.setItem('ats_token', token);
    } else {
      localStorage.removeItem('ats_token');
    }

    if (user) {
      localStorage.setItem('ats_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('ats_user');
    }
  }, [token, user]);

  const login = async (credentials) => {
    const data = await authService.login(credentials);
    const { access, user: userData } = data;
    localStorage.setItem('ats_token', access);
    localStorage.setItem('ats_user', JSON.stringify(userData));
    setToken(access);
    setUser(userData);
    return userData;
  };

  const register = async (formData) => {
    const data = await authService.register(formData);
    return data;
  };

  const isRole = (role) => user?.role === role;

  return (
    <AuthContext.Provider value={{ user, token, login, logout, register, updateUser, isRole }}>
      {children}
    </AuthContext.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
