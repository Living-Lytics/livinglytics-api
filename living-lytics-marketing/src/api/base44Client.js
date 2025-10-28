import { createClient } from '@base44/sdk';
// import { getAccessToken } from '@base44/sdk/utils/auth-utils';

// Create a client with authentication required
export const base44 = createClient({
  appId: "68f0782e51aee78aca360200", 
  requiresAuth: true // Ensure authentication is required for all operations
});
