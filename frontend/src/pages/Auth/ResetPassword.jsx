import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, ShieldCheck, Key } from 'lucide-react';
import api from '../../api/api';

const ResetPassword = () => {
  const [step, setStep] = useState(1); // 1 = request, 2 = confirm
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleRequest = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);

    try {
      const res = await api.post('auth/password-reset/', { email });
      setMessage(res.data.message);
      setStep(2);
    } catch (err) {
      setError(err.response?.data?.error || 'Password reset request failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);

    try {
      const res = await api.post('auth/password-reset/confirm/', {
        email,
        code,
        password
      });
      setMessage(res.data.message);
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to reset password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center bg-transparent px-4 py-12 sm:px-6 lg:px-8 relative">
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 h-80 w-80 rounded-full bg-cyanAccent/5 blur-[100px]"></div>

      <div className="w-full max-w-md space-y-8 glass-panel p-8 rounded-xl z-10 border border-slate-205 dark:border-gray-800 shadow-2xl">
        <div className="text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-cyanAccent/10 text-cyanAccent mb-4">
            {step === 1 ? <Mail size={24} /> : <Key size={24} />}
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            {step === 1 ? 'Reset your password' : 'Enter reset code'}
          </h2>
          <p className="mt-2 text-xs text-gray-400">
            {step === 1
              ? 'Enter your email address and we will send you a reset code.'
              : 'Enter the 6-digit code sent to your email and your new password.'}
          </p>
        </div>

        {error && (
          <div className="rounded-md bg-red-900/30 border border-red-500/50 p-4 text-xs text-red-200">
            {error}
          </div>
        )}

        {message && (
          <div className="rounded-md bg-emerald-950/30 border border-emerald-500/50 p-4 text-xs text-emerald-200">
            {message}
          </div>
        )}

        {step === 1 ? (
          <form className="mt-8 space-y-6" onSubmit={handleRequest}>
            <div>
              <label htmlFor="email" className="text-xs font-semibold text-gray-400 block mb-1">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded p-3 text-xs glass-input"
                placeholder="john@example.com"
              />
            </div>
            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-md bg-gradient-to-r from-cyanAccent to-emeraldAccent py-3 text-xs font-bold text-black hover:opacity-90 transition shadow shadow-cyanAccent/15 disabled:opacity-50"
              >
                {loading ? 'Sending code...' : 'Send Reset Code'}
              </button>
            </div>
          </form>
        ) : (
          <form className="mt-8 space-y-6" onSubmit={handleConfirm}>
            <div className="space-y-4">
              <div>
                <label htmlFor="code" className="text-xs font-semibold text-gray-400 block mb-1">
                  6-Digit Verification Code
                </label>
                <input
                  id="code"
                  type="text"
                  required
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  className="w-full text-center tracking-widest rounded p-3 text-sm font-bold glass-input"
                  placeholder="000000"
                  maxLength={6}
                />
              </div>
              <div>
                <label htmlFor="password" className="text-xs font-semibold text-gray-400 block mb-1">
                  New Password
                </label>
                <input
                  id="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded p-3 text-xs glass-input"
                  placeholder="••••••••"
                />
              </div>
            </div>
            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-md bg-gradient-to-r from-cyanAccent to-emeraldAccent py-3 text-xs font-bold text-black hover:opacity-90 transition shadow shadow-cyanAccent/15 disabled:opacity-50"
              >
                {loading ? 'Resetting password...' : 'Confirm Reset'}
              </button>
            </div>
          </form>
        )}

        <div className="text-center pt-2">
          <Link to="/login" className="text-xs text-gray-400 hover:text-white transition">
            Back to login
          </Link>
        </div>
      </div>
    </div>
  );
};

export default ResetPassword;
