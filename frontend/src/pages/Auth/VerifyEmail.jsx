import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import api from '../../api/api';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';

const VerifyEmail = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [status, setStatus] = useState('verifying'); // verifying, success, error
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    const token = new URLSearchParams(location.search).get('token');
    if (!token) {
      setStatus('error');
      setErrorMessage('Verification token is missing.');
      return;
    }

    const verifyToken = async () => {
      try {
        await api.post('auth/verify-email/', { token });
        setStatus('success');
        setTimeout(() => {
          navigate('/login?verify_success=true');
        }, 3000);
      } catch (err) {
        setStatus('error');
        setErrorMessage(
          err.response?.data?.error || 'Invalid or expired email verification link.'
        );
      }
    };

    verifyToken();
  }, [location, navigate]);

  return (
    <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center bg-transparent px-4 py-12 sm:px-6 lg:px-8 relative">
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 h-80 w-80 rounded-full bg-cyanAccent/5 blur-[100px]"></div>

      <div className="w-full max-w-md space-y-8 glass-panel p-8 rounded-xl z-10 border border-slate-205 dark:border-gray-800 shadow-2xl text-center">
        {status === 'verifying' && (
          <div className="flex flex-col items-center justify-center py-12 space-y-4">
            <Loader2 className="h-16 w-16 animate-spin text-cyanAccent" />
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">Verifying your email</h2>
            <p className="text-xs text-gray-400">Please wait while we confirm your email address...</p>
          </div>
        )}

        {status === 'success' && (
          <div className="flex flex-col items-center justify-center py-8 space-y-4">
            <CheckCircle className="h-16 w-16 text-emeraldAccent" />
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">Email Verified!</h2>
            <p className="text-xs text-gray-400">
              Your email has been verified successfully. Redirecting you to the login page...
            </p>
            <button
              onClick={() => navigate('/login?verify_success=true')}
              className="mt-4 px-6 py-2.5 rounded bg-gradient-to-r from-cyanAccent to-emeraldAccent text-black text-xs font-bold shadow shadow-cyanAccent/15 hover:opacity-90 transition"
            >
              Go to Login
            </button>
          </div>
        )}

        {status === 'error' && (
          <div className="flex flex-col items-center justify-center py-8 space-y-4">
            <XCircle className="h-16 w-16 text-red-500" />
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">Verification Failed</h2>
            <p className="text-xs text-red-400 font-semibold">{errorMessage}</p>
            <p className="text-xs text-gray-450">
              The link might be invalid, expired, or already used.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 mt-4 w-full justify-center">
              <Link
                to="/login"
                className="px-6 py-2.5 border border-slate-300 dark:border-gray-700 text-slate-700 dark:text-white text-xs font-bold rounded hover:bg-slate-100 dark:hover:bg-gray-800 transition"
              >
                Back to Login
              </Link>
              <Link
                to="/register"
                className="px-6 py-2.5 bg-cyanAccent text-black text-xs font-bold rounded shadow hover:opacity-90 transition"
              >
                Register Again
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VerifyEmail;
