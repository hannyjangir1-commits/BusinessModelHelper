import React, { createContext, useContext, useEffect, useState } from 'react';
import { LoginPayload, RegisterPayload, User } from '../types';
import { api } from '../services/api';
import { clearLegacyProjectDraft, clearProjectDraft } from '../utils/projectDraft';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (data: LoginPayload) => Promise<User>;
  register: (data: RegisterPayload) => Promise<User>;
  logout: (optionsOrSkipServer?: boolean | { skipServerRequest?: boolean }) => Promise<void>;
  refreshUser: () => Promise<void>;
  updateUser: (updated: User) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const refreshUser = async () => {
    try {
      const u = await api.auth.me();
      setUser(u);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshUser();
  }, []);

  const login = async (data: LoginPayload): Promise<User> => {
    clearLegacyProjectDraft();
    const res = await api.auth.login(data);
    setUser(res.user);
    return res.user;
  };

  const register = async (data: RegisterPayload): Promise<User> => {
    clearLegacyProjectDraft();
    const res = await api.auth.register(data);
    setUser(res.user);
    return res.user;
  };

  const logout = async (optionsOrSkipServer?: boolean | { skipServerRequest?: boolean }) => {
    const skipServerRequest =
      typeof optionsOrSkipServer === 'boolean'
        ? optionsOrSkipServer
        : Boolean(optionsOrSkipServer?.skipServerRequest);

    try {
      if (user?.id) {
        clearProjectDraft(user.id);
      }
      clearLegacyProjectDraft();
      if (!skipServerRequest) {
        try {
          await api.auth.logout();
        } catch {
          // If server logout fails (e.g. session already expired or cleared by server),
          // local cleanup must still succeed deterministically.
        }
      }
    } finally {
      setUser(null);
    }
  };

  const updateUser = (updated: User) => {
    setUser(updated);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
