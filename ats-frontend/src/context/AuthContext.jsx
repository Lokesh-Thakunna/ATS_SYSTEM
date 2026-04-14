import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authService } from '../services/authService';
import { normalizeRole, resolveUserRole } from '../utils/roles';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  // Bootstrap the stored session once so route guards do not flash incorrectly.
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem('ats_user');
      if (stored) {
        const parsedUser = JSON.parse(stored);
        return { ...parsedUser, role: resolveUserRole(parsedUser) };
      }
    } catch {
      // ignore
    }
    return null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('ats_token') || null);
  const [loading] = useState(false);

  // Shared logout keeps browser storage and in-memory auth state aligned.
  const logout = useCallback(() => {
    localStorage.removeItem('ats_token');
    localStorage.removeItem('ats_user');
    setToken(null);
    setUser(null);
  }, []);

  // User updates always pass through the same role normalization step.
  const updateUser = useCallback((updates) => {
    setUser((current) => (
      current
        ? {
            ...current,
            ...updates,
            role: resolveUserRole({ ...current, ...updates }),
          }
        : current
    ));
  }, []);

  // Persist the auth session after login, logout, or profile updates.
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
    const normalizedUser = { ...userData, role: resolveUserRole(userData) };
    localStorage.setItem('ats_token', access);
    localStorage.setItem('ats_user', JSON.stringify(normalizedUser));
    setToken(access);
    setUser(normalizedUser);
    return normalizedUser;
  };

  const register = async (formData) => {
    const data = await authService.register(formData);
    return data;
  };

  const isRole = (role) => resolveUserRole(user) === normalizeRole(role);

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, register, updateUser, isRole }}>
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
