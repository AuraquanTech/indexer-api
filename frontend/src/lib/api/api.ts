import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

export const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
    (config) => {
        // We'll read from localStorage for simplicity in this phase, 
        // but cookies are better for production. 
        // AuthProvider will handle setting this.
        const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;

        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor for global error handling
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Handle unauthorized access (e.g., redirect to login)
            // We can dispatch an event or use a callback here if needed
            if (typeof window !== 'undefined') {
                // window.location.href = '/login'; // Optional: auto-redirect
            }
        }
        return Promise.reject(error);
    }
);
