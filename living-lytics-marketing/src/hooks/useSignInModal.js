import { create } from 'zustand';

// Simple global state for sign-in modal
// If zustand is not installed, we'll use a React context approach instead
// For simplicity, using a basic event-driven approach

let listeners = [];
let isOpen = false;

export function useSignInModal() {
  const [open, setOpen] = React.useState(isOpen);

  React.useEffect(() => {
    const listener = (value) => setOpen(value);
    listeners.push(listener);
    return () => {
      listeners = listeners.filter(l => l !== listener);
    };
  }, []);

  const openModal = () => {
    isOpen = true;
    listeners.forEach(l => l(true));
  };

  const closeModal = () => {
    isOpen = false;
    listeners.forEach(l => l(false));
  };

  return { isOpen: open, openModal, closeModal };
}

// Export standalone functions for easy use
export function openSignInModal() {
  isOpen = true;
  listeners.forEach(l => l(true));
}

export function closeSignInModal() {
  isOpen = false;
  listeners.forEach(l => l(false));
}

// Simpler implementation without external dependency
import React from 'react';
