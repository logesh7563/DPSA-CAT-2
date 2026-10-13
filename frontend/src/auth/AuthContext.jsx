import React, { createContext, useContext, useState, useEffect } from 'react';
import { authApi } from '../api/endpoints.js';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = sessionStorage.getItem('fed_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [loading, setLoading] = useState(false);

  const login = async (username, password) => {
    setLoading(true);
    try {
      const data = await authApi.login(username, password);
      const userInfo = {
        username: data.username,
        role: data.role,
        client_id: data.client_id,
        token: data.access_token,
      };
      sessionStorage.setItem('fed_token', data.access_token);
      sessionStorage.setItem('fed_user', JSON.stringify(userInfo));
      setUser(userInfo);
      return userInfo;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    sessionStorage.removeItem('fed_token');
    sessionStorage.removeItem('fed_user');
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        logout,
        loading,
        isAdmin: user?.role === 'admin',
        isClient: user?.role === 'client',
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
