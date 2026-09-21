import React, { createContext, useContext, useState, useEffect } from 'react';
import { loginUser as apiLogin, registerUser as apiRegister } from '../api/auth';
import { listProjects } from '../api/projects';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(() => localStorage.getItem('bhuvistaar_token') || null);
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('bhuvistaar_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [selectedProjectId, setSelectedProjectId] = useState(() => {
    const saved = localStorage.getItem('bhuvistaar_project_id');
    return saved ? parseInt(saved, 10) : null;
  });
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (token) {
      fetchProjects();
    } else {
      setProjects([]);
      setSelectedProjectId(null);
    }
  }, [token]);

  const fetchProjects = async () => {
    try {
      const data = await listProjects();
      setProjects(data);
      if (data.length > 0 && !selectedProjectId) {
        changeSelectedProject(data[0].id);
      }
    } catch (err) {
      console.error('Failed to load user projects:', err);
    }
  };

  const changeSelectedProject = (projectId) => {
    const id = parseInt(projectId, 10);
    setSelectedProjectId(id);
    localStorage.setItem('bhuvistaar_project_id', id.toString());
  };

  const login = async (email, password) => {
    setLoading(true);
    try {
      const res = await apiLogin(email, password);
      const accessToken = res.access_token;
      setToken(accessToken);
      localStorage.setItem('bhuvistaar_token', accessToken);

      const userInfo = { email, id: res.user_id || 1 };
      setUser(userInfo);
      localStorage.setItem('bhuvistaar_user', JSON.stringify(userInfo));

      await fetchProjects();
      return { success: true };
    } catch (err) {
      return { success: false, error: err.friendlyMessage || 'Login failed' };
    } finally {
      setLoading(false);
    }
  };

  const register = async (name, email, password) => {
    setLoading(true);
    try {
      const res = await apiRegister(name, email, password);
      // Auto login after registration
      return await login(email, password);
    } catch (err) {
      setLoading(false);
      return { success: false, error: err.friendlyMessage || 'Registration failed' };
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    setSelectedProjectId(null);
    setProjects([]);
    localStorage.removeItem('bhuvistaar_token');
    localStorage.removeItem('bhuvistaar_user');
    localStorage.removeItem('bhuvistaar_project_id');
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        isAuthenticated: !!token,
        selectedProjectId,
        changeSelectedProject,
        projects,
        refreshProjects: fetchProjects,
        login,
        register,
        logout,
        loading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
