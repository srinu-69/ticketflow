// Centralized API Configuration
// This file contains all API-related configuration for the frontend

const API_CONFIG = {
  // Backend API base URL
  BASE_URL: process.env.REACT_APP_API_URL || "http://localhost:8000",
  
  // API endpoints
  ENDPOINTS: {
    // Authentication
    AUTH: {
      LOGIN: "/auth/login",
      REGISTER: "/auth/register",
    },
    
    // Users
    USERS: {
      BASE: "/users",
      BY_ID: (id) => `/users/${id}`,
    },
    
    // User Profiles
    USER_PROFILES: {
      BASE: "/user-profiles",
      BY_EMAIL: (email) => `/user-profiles/email/${encodeURIComponent(email)}`,
      BY_ID: (id) => `/user-profiles/${id}`,
    },
    
    // User Management
    USERS_MANAGEMENT: {
      BASE: "/users-management",
      BY_EMAIL: (email) => `/users-management/email/${encodeURIComponent(email)}`,
    },
    
    // Assets
    ASSETS: {
      BASE: "/assets",
      BY_ID: (id) => `/assets/${id}`,
    },
    
    // Timeline
    TIMELINE: {
      PROJECTS: {
        BASE: "/timeline/projects",
        BY_ID: (id) => `/timeline/projects/${id}`,
        TASKS: (id) => `/timeline/projects/${id}/tasks`,
      },
      TASKS: {
        BASE: "/timeline/tasks",
        BY_ID: (id) => `/timeline/tasks/${id}`,
      },
    },
    
    // Projects
    PROJECTS: {
      BASE: "/projects",
    },
    
    // Tickets
    TICKETS: {
      BASE: "/tickets",
      BY_ID: (id) => `/tickets/${id}`,
    },
    
    // Epics
    EPICS: {
      BASE: "/epics",
      BY_ID: (id) => `/epics/${id}`,
    },
  },
  
  // Request timeout (in milliseconds)
  TIMEOUT: 30000, // 30 seconds
  
  // Default headers
  DEFAULT_HEADERS: {
    "Content-Type": "application/json",
  },
};

// Helper function to build full URL
export const buildUrl = (endpoint) => {
  if (endpoint.startsWith("http")) {
    return endpoint; // Already a full URL
  }
  return `${API_CONFIG.BASE_URL}${endpoint}`;
};

// Helper function to make API requests with error handling
export const apiRequest = async (url, options = {}) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT);
  
  try {
    const response = await fetch(buildUrl(url), {
      ...options,
      headers: {
        ...API_CONFIG.DEFAULT_HEADERS,
        ...options.headers,
      },
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch (e) {
        errorData = { detail: `HTTP ${response.status}: ${response.statusText}` };
      }
      throw new Error(errorData.detail || "Request failed");
    }
    
    // Handle empty responses (204 No Content)
    if (response.status === 204) {
      return null;
    }
    
    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    
    if (error.name === "AbortError") {
      throw new Error("Request timed out. Please check your connection and try again.");
    } else if (error.message.includes("Failed to fetch") || error.message.includes("NetworkError")) {
      throw new Error("Cannot connect to server. Please make sure the backend is running.");
    }
    throw error;
  }
};

export default API_CONFIG;

