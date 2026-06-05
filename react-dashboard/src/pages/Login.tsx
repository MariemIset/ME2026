import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    login(email);
    navigate('/');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white dark:bg-gray-800 p-10 rounded-2xl shadow-xl border border-gray-100 dark:border-gray-700">
        <div className="flex flex-col items-center">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 124.4 64" className="w-16 h-10">
            <path fill="#d81e05" fill-rule="evenodd" clip-rule="evenodd" d="M13.6,53c16.5-13.3,28.2-24.8,31.7-31c1.5-2.4,2-4.7,1.1-6.5c-1.5-3.5-7-4.5-13.6-3.2C62.7,5.5,93.2,1.4,123.8,0c0.3,0,0.6,0.2,0.6,0.5c0,0.2-0.1,0.5-0.4,0.5c-38.8,12.6-74.1,33-104,59.4c0,0-0.1,0.1-0.1,0.1L0.3,64c-0.3,0-0.4-0.3-0.2-0.5C4.7,60.1,9.2,56.6,13.6,53"/>
            <path fill="#93282c" fill-rule="evenodd" clip-rule="evenodd" d="M11,17.4c-0.4,0.1-0.9,0.2-1.3,0.4c-0.3,0.1-0.2,0.4,0,0.5l7.4,1.1L30,21.2c0.1,0,0.1,0,0.1,0c9.1-4.3,15.1-6,16.5-4.1c0.4,0.6,0.3,1.5-0.1,2.6c-0.2,0.4-0.4,0.8-0.6,1.3c1.4-2.3,1.9-4.4,1.1-6.2c-1.5-3.3-6.6-4.3-13.1-3C26.2,13.5,18.6,15.4,11,17.4"/>
          </svg>
          <h2 className="mt-4 text-center text-3xl font-extrabold text-gray-900 dark:text-white">
            ALI — Airline Loyalty Intelligence
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
            Sign in to access your dashboard
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 placeholder-gray-500 dark:placeholder-gray-400 text-gray-900 dark:text-white dark:bg-gray-700 rounded-t-md focus:outline-none focus:ring-rose-500 focus:border-rose-500 focus:z-10 sm:text-sm"
                placeholder="Email address (ceo@, marketing@, process@, or any for client)"
              />
            </div>
            <div>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 placeholder-gray-500 dark:placeholder-gray-400 text-gray-900 dark:text-white dark:bg-gray-700 rounded-b-md focus:outline-none focus:ring-rose-500 focus:border-rose-500 focus:z-10 sm:text-sm"
                placeholder="Password (any)"
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-rose-600 hover:bg-rose-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-rose-500 transition-colors"
            >
              Sign In
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;
