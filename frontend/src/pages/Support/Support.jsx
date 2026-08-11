import React, { useState, useEffect, useRef } from 'react';
import api from '../../api/api';
import { LifeBuoy, Plus, Send, Clock, AlertCircle, MessageSquare, Check, User, ShieldAlert, Image as ImageIcon, X, Maximize2 } from 'lucide-react';

const ALLOWED_EXTENSIONS = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

const Support = () => {
  const [tickets, setTickets] = useState([]);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [ticketDetails, setTicketDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Form states for creating ticket
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');
  const [priority, setPriority] = useState('MEDIUM');
  const [createFile, setCreateFile] = useState(null);
  const [createFilePreview, setCreateFilePreview] = useState(null);
  const [creating, setCreating] = useState(false);

  // Form states for chat reply
  const [replyMessage, setReplyMessage] = useState('');
  const [replyFile, setReplyFile] = useState(null);
  const [replyFilePreview, setReplyFilePreview] = useState(null);
  const [replying, setReplying] = useState(false);

  // Lightbox state
  const [lightboxImage, setLightboxImage] = useState(null);

  const chatEndRef = useRef(null);
  const replyFileInputRef = useRef(null);
  const createFileInputRef = useRef(null);

  useEffect(() => {
    fetchTickets();
  }, []);

  useEffect(() => {
    if (selectedTicket) {
      fetchTicketDetails(selectedTicket.id);
      const interval = setInterval(() => {
        fetchTicketDetails(selectedTicket.id, true);
      }, 5000); // Polling for new admin messages every 5s
      return () => clearInterval(interval);
    }
  }, [selectedTicket]);

  useEffect(() => {
    scrollToBottom();
  }, [ticketDetails]);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchTickets = async () => {
    try {
      const res = await api.get('support/tickets/');
      setTickets(res.data);
      if (res.data.length > 0 && !selectedTicket) {
        setSelectedTicket(res.data[0]);
      }
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch support tickets.');
      setLoading(false);
    }
  };

  const fetchTicketDetails = async (id, isSilent = false) => {
    try {
      const res = await api.get(`support/tickets/${id}/`);
      setTicketDetails(res.data);
    } catch (err) {
      if (!isSilent) {
        setError('Failed to fetch conversation history.');
      }
    }
  };

  const handleSelectCreateFile = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!ALLOWED_EXTENSIONS.includes(file.type)) {
      setError('Invalid file format. Please attach a JPG, PNG, WEBP, or GIF image.');
      return;
    }
    if (file.size > MAX_FILE_SIZE) {
      setError('Image file is too large. Maximum allowed size is 10 MB.');
      return;
    }

    setError('');
    setCreateFile(file);
    setCreateFilePreview(URL.createObjectURL(file));
  };

  const handleRemoveCreateFile = () => {
    setCreateFile(null);
    if (createFilePreview) {
      URL.revokeObjectURL(createFilePreview);
      setCreateFilePreview(null);
    }
    if (createFileInputRef.current) {
      createFileInputRef.current.value = '';
    }
  };

  const handleSelectReplyFile = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!ALLOWED_EXTENSIONS.includes(file.type)) {
      setError('Invalid file format. Please attach a JPG, PNG, WEBP, or GIF image.');
      return;
    }
    if (file.size > MAX_FILE_SIZE) {
      setError('Image file is too large. Maximum allowed size is 10 MB.');
      return;
    }

    setError('');
    setReplyFile(file);
    setReplyFilePreview(URL.createObjectURL(file));
  };

  const handleRemoveReplyFile = () => {
    setReplyFile(null);
    if (replyFilePreview) {
      URL.revokeObjectURL(replyFilePreview);
      setReplyFilePreview(null);
    }
    if (replyFileInputRef.current) {
      replyFileInputRef.current.value = '';
    }
  };

  const handleCreateTicket = async (e) => {
    e.preventDefault();
    if (!subject.trim() || (!message.trim() && !createFile)) {
      setError('Please provide a subject and a message or image attachment.');
      return;
    }

    setCreating(true);
    setError('');
    setSuccess('');

    try {
      const formData = new FormData();
      formData.append('subject', subject.trim());
      formData.append('message', message.trim());
      formData.append('priority', priority);
      if (createFile) {
        formData.append('initial_attachment', createFile);
      }

      const res = await api.post('support/tickets/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setSuccess('Support ticket created successfully.');
      setSubject('');
      setMessage('');
      setPriority('MEDIUM');
      handleRemoveCreateFile();
      setShowCreateModal(false);
      
      const updatedRes = await api.get('support/tickets/');
      setTickets(updatedRes.data);
      const newTicket = updatedRes.data.find(t => t.id === res.data.id) || res.data;
      setSelectedTicket(newTicket);
    } catch (err) {
      setError(err.response?.data?.detail || err.response?.data?.initial_attachment?.[0] || 'Failed to open a support ticket.');
    } finally {
      setCreating(false);
    }
  };

  const handleSendReply = async (e) => {
    e.preventDefault();
    if (!replyMessage.trim() && !replyFile) return;

    setReplying(true);
    setError('');

    try {
      const formData = new FormData();
      if (replyMessage.trim()) {
        formData.append('message', replyMessage.trim());
      }
      if (replyFile) {
        formData.append('attachment', replyFile);
      }

      const res = await api.post(`support/tickets/${selectedTicket.id}/messages/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      if (ticketDetails) {
        setTicketDetails({
          ...ticketDetails,
          messages: [...(ticketDetails.messages || []), res.data]
        });
      }
      setReplyMessage('');
      handleRemoveReplyFile();
      
      fetchTickets();
    } catch (err) {
      setError(err.response?.data?.detail || err.response?.data?.attachment?.[0] || 'Failed to deliver message.');
    } finally {
      setReplying(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center bg-transparent">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-cyanAccent border-t-transparent"></div>
      </div>
    );
  }

  const getPriorityStyle = (p) => {
    switch (p) {
      case 'CRITICAL': return 'bg-red-500/15 text-red-400 border border-red-500/30';
      case 'HIGH': return 'bg-orange-500/15 text-orange-400 border border-orange-500/30';
      case 'MEDIUM': return 'bg-yellow-500/15 text-yellow-400 border border-yellow-500/30';
      default: return 'bg-blue-500/15 text-blue-400 border border-blue-500/30';
    }
  };

  const getStatusStyle = (s) => {
    switch (s) {
      case 'RESOLVED': return 'bg-emeraldAccent/15 text-emeraldAccent';
      case 'CLOSED': return 'bg-gray-800 text-gray-500';
      case 'IN_PROGRESS': return 'bg-cyanAccent/15 text-cyanAccent';
      default: return 'bg-yellow-500/15 text-yellow-500';
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 min-h-[calc(100vh-4rem)] flex flex-col text-left font-sans">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-black text-slate-900 dark:text-white flex items-center gap-2">
            <LifeBuoy className="text-cyanAccent animate-pulse" /> Support Operations Center
          </h1>
          <p className="text-xs text-gray-400">Initiate tickets and chat directly with our financial support specialists.</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 bg-gradient-to-r from-cyanAccent to-emeraldAccent text-black px-4 py-2 rounded text-xs font-bold hover:opacity-90 transition cursor-pointer"
        >
          <Plus size={16} /> New Support Ticket
        </button>
      </div>

      {error && (
        <div className="rounded-md bg-red-950/40 border border-red-500/50 p-4 text-xs text-red-200 mb-6 flex justify-between items-center">
          <span>⚠ {error}</span>
          <button onClick={() => setError('')} className="text-red-300 hover:text-white"><X size={14} /></button>
        </div>
      )}

      {success && (
        <div className="rounded-md bg-emerald-950/40 border border-emerald-500/50 p-4 text-xs text-emerald-200 mb-6 flex justify-between items-center">
          <span>✓ {success}</span>
          <button onClick={() => setSuccess('')} className="text-emerald-300 hover:text-white"><X size={14} /></button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 flex-1 min-h-[500px]">
        {/* Ticket List column */}
        <div className="glass-panel rounded-xl overflow-hidden flex flex-col max-h-[650px] border border-slate-200 dark:border-gray-800">
          <div className="p-4 border-b border-slate-200 dark:border-gray-850 bg-slate-100/40 dark:bg-gray-950/30 flex items-center justify-between">
            <span className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">Your Support Tickets</span>
            <span className="bg-slate-200 dark:bg-gray-800 text-[10px] text-slate-500 dark:text-gray-400 px-2 py-0.5 rounded-full font-bold">{tickets.length}</span>
          </div>

          <div className="overflow-y-auto divide-y divide-slate-150 dark:divide-gray-850 flex-1">
            {tickets.length === 0 ? (
              <div className="text-center py-12 text-xs text-gray-500 px-4">
                <MessageSquare size={32} className="mx-auto text-slate-450 dark:text-gray-650 mb-2" />
                No tickets filed. Click 'New Support Ticket' to start a session.
              </div>
            ) : (
              tickets.map((t) => (
                <div
                  key={t.id}
                  onClick={() => setSelectedTicket(t)}
                  className={`p-4 cursor-pointer text-left transition ${
                    selectedTicket?.id === t.id ? 'bg-slate-100/60 dark:bg-[#1f2937]/35 border-l-2 border-cyanAccent' : 'hover:bg-slate-100/20 dark:hover:bg-gray-900/30'
                  }`}
                >
                  <div className="flex justify-between items-start gap-2 mb-1.5">
                    <span className="text-xs font-bold text-slate-900 dark:text-white truncate max-w-[150px]">{t.subject}</span>
                    <span className={`text-[8px] font-black uppercase px-2 py-0.5 rounded ${getStatusStyle(t.status)}`}>
                      {t.status}
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-500 dark:text-gray-400 line-clamp-1 mb-2">{t.message}</p>
                  <div className="flex items-center justify-between text-[9px] text-gray-500">
                    <span className={`px-1.5 py-0.5 rounded text-[8px] font-bold ${getPriorityStyle(t.priority)}`}>
                      {t.priority}
                    </span>
                    <span>{new Date(t.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Conversation details column */}
        <div className="lg:col-span-2 glass-panel rounded-xl overflow-hidden flex flex-col max-h-[650px] border border-slate-200 dark:border-gray-800">
          {selectedTicket ? (
            <>
              {/* Ticket header status banner */}
              <div className="p-4 border-b border-slate-200 dark:border-gray-850 bg-slate-100/30 dark:bg-gray-950/20 flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2">
                <div>
                  <h3 className="text-xs font-bold text-slate-900 dark:text-white mb-1">Ticket #{selectedTicket.id}: {selectedTicket.subject}</h3>
                  <p className="text-[9px] text-gray-400">Created: {new Date(selectedTicket.created_at).toLocaleString()}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase ${getPriorityStyle(selectedTicket.priority)}`}>
                    {selectedTicket.priority} Priority
                  </span>
                  <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase ${getStatusStyle(selectedTicket.status)}`}>
                    {selectedTicket.status}
                  </span>
                </div>
              </div>

              {/* Scrollable messages area */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/20 dark:bg-gray-950/5">
                {/* Messages List */}
                {ticketDetails?.messages?.map((msg) => {
                  const isAgent = msg.is_admin;
                  return (
                    <div key={msg.id} className={`flex ${isAgent ? 'justify-start' : 'justify-end'}`}>
                      <div className={`max-w-[85%] sm:max-w-[75%] rounded-xl p-3.5 text-left ${
                        isAgent 
                          ? 'bg-white dark:bg-[#111827] border border-cyanAccent/40 shadow-md' 
                          : 'bg-slate-200/80 dark:bg-gray-800/90 border border-slate-300 dark:border-gray-700'
                      }`}>
                        <div className="flex items-center justify-between gap-4 text-[9px] font-semibold mb-1.5 border-b border-slate-200 dark:border-gray-700/50 pb-1">
                          <div className="flex items-center gap-1.5">
                            {isAgent ? (
                              <>
                                <ShieldAlert size={12} className="text-emeraldAccent" />
                                <span className="text-emeraldAccent font-bold">Support Specialist</span>
                              </>
                            ) : (
                              <>
                                <User size={12} className="text-cyanAccent" />
                                <span className="text-cyanAccent font-bold">{msg.sender_name || msg.sender_username || 'You'}</span>
                              </>
                            )}
                          </div>
                          <span className="text-[8px] text-gray-400 font-normal">
                            {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>

                        {msg.message && (
                          <p className="text-xs text-slate-800 dark:text-gray-100 whitespace-pre-wrap leading-relaxed mb-2">{msg.message}</p>
                        )}

                        {/* Message Image Attachment */}
                        {msg.attachment && (
                          <div className="mt-2 pt-2 border-t border-slate-200 dark:border-gray-750">
                            <div className="relative group inline-block overflow-hidden rounded-lg border border-cyanAccent/30 bg-black/40">
                              <img
                                src={msg.attachment}
                                alt="Attachment"
                                className="max-h-48 max-w-full object-cover cursor-pointer transition transform group-hover:scale-105"
                                onClick={() => setLightboxImage(msg.attachment)}
                              />
                              <button
                                onClick={() => setLightboxImage(msg.attachment)}
                                className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center text-white transition text-xs font-semibold gap-1"
                              >
                                <Maximize2 size={16} /> View Full
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
                <div ref={chatEndRef} />
              </div>

              {/* Chat Input panel */}
              <div className="p-4 border-t border-slate-200 dark:border-gray-850 bg-slate-100/40 dark:bg-gray-950/40 space-y-3">
                {selectedTicket.status === 'CLOSED' && (
                  <p className="text-[10px] text-yellow-500">⚠ This ticket is closed. Typing a reply will automatically reopen this support thread.</p>
                )}

                {/* Reply File Preview Bar */}
                {replyFilePreview && (
                  <div className="flex items-center gap-3 p-2 rounded bg-slate-200 dark:bg-gray-900 border border-cyanAccent/40">
                    <img src={replyFilePreview} alt="Preview" className="h-10 w-10 object-cover rounded border border-gray-700" />
                    <div className="flex-1 min-w-0 text-[10px]">
                      <p className="font-semibold text-slate-900 dark:text-white truncate">{replyFile?.name}</p>
                      <p className="text-gray-400">{(replyFile?.size / 1024).toFixed(1)} KB</p>
                    </div>
                    <button
                      type="button"
                      onClick={handleRemoveReplyFile}
                      className="p-1 text-gray-400 hover:text-red-400 transition"
                    >
                      <X size={16} />
                    </button>
                  </div>
                )}

                <form onSubmit={handleSendReply} className="flex items-center gap-2">
                  <input
                    type="file"
                    ref={replyFileInputRef}
                    onChange={handleSelectReplyFile}
                    accept="image/jpeg,image/png,image/webp,image/gif"
                    className="hidden"
                  />
                  <button
                    type="button"
                    onClick={() => replyFileInputRef.current?.click()}
                    className={`p-2.5 rounded border transition flex items-center justify-center ${
                      replyFile 
                        ? 'bg-cyanAccent/20 border-cyanAccent text-cyanAccent' 
                        : 'border-slate-300 dark:border-gray-700 text-gray-400 hover:text-white hover:bg-slate-200 dark:hover:bg-gray-800'
                    }`}
                    title="Attach Image (JPG, PNG, WEBP, GIF, max 10MB)"
                  >
                    <ImageIcon size={18} />
                  </button>

                  <input
                    type="text"
                    placeholder="Write a message..."
                    className="flex-1 p-2.5 rounded glass-input text-xs"
                    value={replyMessage}
                    onChange={(e) => setReplyMessage(e.target.value)}
                  />

                  <button
                    type="submit"
                    disabled={replying || (!replyMessage.trim() && !replyFile)}
                    className="bg-gradient-to-r from-cyanAccent to-emeraldAccent text-black px-4 py-2.5 rounded font-bold text-xs hover:opacity-90 disabled:opacity-40 transition flex items-center justify-center cursor-pointer gap-1"
                  >
                    <Send size={16} /> Send
                  </button>
                </form>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-xs text-gray-500 py-12 px-4">
              <LifeBuoy size={48} className="text-slate-400 dark:text-gray-650 mb-3" />
              <p className="font-semibold text-slate-900 dark:text-white">No Ticket Selected</p>
              <p className="text-[10px] text-gray-400 mt-1">Select a ticket from the left panel or start a new support thread.</p>
            </div>
          )}
        </div>
      </div>

      {/* CREATE TICKET DIALOG MODAL */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-lg bg-white dark:bg-[#111827] border border-slate-200 dark:border-gray-850 rounded-xl shadow-2xl p-6 text-left space-y-4">
            <div className="flex justify-between items-center border-b border-slate-200 dark:border-gray-800 pb-3">
              <h3 className="text-sm font-bold text-slate-950 dark:text-white">File Support Request Ticket</h3>
              <button onClick={() => setShowCreateModal(false)} className="text-gray-400 hover:text-white"><X size={18} /></button>
            </div>

            <form onSubmit={handleCreateTicket} className="space-y-4">
              <div>
                <label className="block text-[10px] text-gray-400 uppercase font-semibold mb-1">Subject / Core Issue</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Deposit proof upload failed"
                  className="w-full p-2.5 rounded glass-input text-xs"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-[10px] text-gray-400 uppercase font-semibold mb-1">Priority Level</label>
                <select
                  className="w-full p-2.5 rounded glass-input text-xs"
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                >
                  <option value="LOW">Low - General Question</option>
                  <option value="MEDIUM">Medium - Technical Problem</option>
                  <option value="HIGH">High - Transaction Hold</option>
                  <option value="CRITICAL">Critical - Compromised Account</option>
                </select>
              </div>

              <div>
                <label className="block text-[10px] text-gray-400 uppercase font-semibold mb-1">Detailed Description</label>
                <textarea
                  rows={4}
                  placeholder="Please state transaction hashes or steps where possible..."
                  className="w-full p-2.5 rounded glass-input text-xs"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                />
              </div>

              {/* File Attachment Upload & Preview */}
              <div>
                <label className="block text-[10px] text-gray-400 uppercase font-semibold mb-1">Attach Image (Optional)</label>
                <input
                  type="file"
                  ref={createFileInputRef}
                  onChange={handleSelectCreateFile}
                  accept="image/jpeg,image/png,image/webp,image/gif"
                  className="hidden"
                />
                
                {createFilePreview ? (
                  <div className="flex items-center gap-3 p-2 rounded bg-slate-100 dark:bg-gray-900 border border-cyanAccent/40">
                    <img src={createFilePreview} alt="Preview" className="h-12 w-12 object-cover rounded border border-gray-700" />
                    <div className="flex-1 min-w-0 text-[10px]">
                      <p className="font-semibold text-slate-900 dark:text-white truncate">{createFile?.name}</p>
                      <p className="text-gray-400">{(createFile?.size / 1024).toFixed(1)} KB</p>
                    </div>
                    <button
                      type="button"
                      onClick={handleRemoveCreateFile}
                      className="p-1 text-gray-400 hover:text-red-400 transition"
                    >
                      <X size={16} />
                    </button>
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={() => createFileInputRef.current?.click()}
                    className="w-full p-3 rounded border border-dashed border-slate-300 dark:border-gray-700 text-xs text-gray-400 hover:text-white hover:border-cyanAccent transition flex items-center justify-center gap-2"
                  >
                    <ImageIcon size={18} className="text-cyanAccent" /> Select Image Attachment (JPG, PNG, WEBP, GIF max 10MB)
                  </button>
                )}
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border border-slate-250 dark:border-gray-850 text-slate-700 dark:text-white rounded text-xs hover:bg-slate-100 dark:hover:bg-gray-850 transition cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-2 bg-gradient-to-r from-cyanAccent to-emeraldAccent text-black rounded text-xs font-bold hover:opacity-90 transition cursor-pointer"
                >
                  {creating ? 'Opening Session...' : 'Submit Support Ticket'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* LIGHTBOX IMAGE MODAL */}
      {lightboxImage && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90 backdrop-blur-md animate-fade-in">
          <div className="relative max-w-4xl max-h-[90vh] flex flex-col items-center">
            <button
              onClick={() => setLightboxImage(null)}
              className="absolute -top-10 right-0 text-white hover:text-cyanAccent p-2 transition"
            >
              <X size={24} />
            </button>
            <img
              src={lightboxImage}
              alt="Full Size View"
              className="max-h-[85vh] max-w-full object-contain rounded-lg border border-slate-800 shadow-2xl"
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default Support;
