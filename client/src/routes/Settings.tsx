import { useState } from 'react';
import { Page } from '../components/Page';
import { useToast } from '../components/Toast';
import { disconnectAll } from '../lib/api';

export const Settings = () => {
  const { toast } = useToast();
  const [showConfirm, setShowConfirm] = useState(false);
  const [orgName, setOrgName] = useState(localStorage.getItem('orgName') || '');

  const handleSaveOrgName = () => {
    localStorage.setItem('orgName', orgName);
    toast('Organization name saved', 'success');
  };

  const handleDisconnect = async () => {
    try {
      await disconnectAll();
      toast('Disconnected successfully. Your data will be removed.', 'success');
      setShowConfirm(false);
      window.location.href = '/';
    } catch (error) {
      toast(error instanceof Error ? error.message : 'Failed to disconnect', 'error');
    }
  };

  return (
    <Page title="Settings">
      <div className="max-w-2xl">
        {/* Organization Name */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Organization</h3>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Organization Name
          </label>
          <div className="flex gap-3">
            <input
              type="text"
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter organization name"
            />
            <button
              onClick={handleSaveOrgName}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors"
            >
              Save
            </button>
          </div>
        </div>

        {/* Disconnect */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Disconnect & Delete Data</h3>
          <p className="text-gray-600 text-sm mb-4">
            This will disconnect all connected accounts and remove your data from our servers.
          </p>
          <button
            onClick={() => setShowConfirm(true)}
            className="bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-lg font-medium transition-colors"
          >
            Disconnect All Accounts
          </button>
        </div>
      </div>

      {/* Confirmation Modal */}
      {showConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md mx-4">
            <h3 className="text-xl font-bold text-gray-900 mb-2">Confirm Disconnection</h3>
            <p className="text-gray-600 mb-6">
              Are you sure you want to disconnect all accounts and delete your data? This action cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowConfirm(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleDisconnect}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Yes, Disconnect
              </button>
            </div>
          </div>
        </div>
      )}
    </Page>
  );
};
