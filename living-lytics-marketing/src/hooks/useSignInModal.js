import React from 'react';

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

export function openSignInModal() {
  isOpen = true;
  listeners.forEach(l => l(true));
}

export function closeSignInModal() {
  isOpen = false;
  listeners.forEach(l => l(false));
}
