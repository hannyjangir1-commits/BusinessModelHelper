import React, { useState } from 'react';
import { Check, KeyRound, ShieldAlert, User, UserX } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { Button } from '../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { Textarea } from '../components/ui/Textarea';
import { Select } from '../components/ui/Select';
import { Modal } from '../components/ui/Modal';
import { Alert } from '../components/ui/Alert';

interface ProfilePageProps {
  onNavigate: (path: string) => void;
}

export const ProfilePage: React.FC<ProfilePageProps> = ({ onNavigate }) => {
  const { user, updateUser, logout } = useAuth();

  // Profile Edit State
  const [displayName, setDisplayName] = useState(user?.display_name || '');
  const [bio, setBio] = useState(user?.bio || '');
  const [country, setCountry] = useState(user?.country || '');
  const [preferredCurrency, setPreferredCurrency] = useState(user?.preferred_currency || 'USD');
  const [isUpdatingProfile, setIsUpdatingProfile] = useState(false);

  // Password Change State
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  // Account Deletion State
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deletePassword, setDeletePassword] = useState('');
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  const [isDeletingAccount, setIsDeletingAccount] = useState(false);

  // Status Alerts
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);
    setIsUpdatingProfile(true);
    try {
      const updated = await api.profile.update({
        display_name: displayName.trim(),
        bio: bio.trim() || null,
        country: country.trim() || null,
        preferred_currency: preferredCurrency,
      });
      updateUser(updated);
      setSuccessMsg('Profile updated successfully.');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to update profile.');
    } finally {
      setIsUpdatingProfile(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);

    if (newPassword !== confirmNewPassword) {
      setErrorMsg('New passwords do not match.');
      return;
    }

    setIsChangingPassword(true);
    try {
      await api.auth.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
        confirm_new_password: confirmNewPassword,
      });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmNewPassword('');
      setSuccessMsg('Password changed successfully.');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to change password.');
    } finally {
      setIsChangingPassword(false);
    }
  };

  const handleDeleteAccount = async () => {
    setErrorMsg(null);
    if (deleteConfirmText !== 'DELETE') {
      setErrorMsg('Please type DELETE in capital letters to confirm.');
      return;
    }

    setIsDeletingAccount(true);
    try {
      await api.profile.deleteAccount({
        password: deletePassword,
        confirmation_text: deleteConfirmText,
      });
      await logout();
      onNavigate('/');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to delete account. Please verify password.');
      setIsDeletingAccount(false);
    }
  };

  if (!user) return null;

  return (
    <div className="max-w-4xl mx-auto px-4 py-10 space-y-8">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">Account & Profile Settings</h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">Manage your identity, security credentials, and preferences.</p>
      </div>

      {errorMsg && <Alert type="error" message={errorMsg} onClose={() => setErrorMsg(null)} />}
      {successMsg && <Alert type="success" message={successMsg} onClose={() => setSuccessMsg(null)} />}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Profile Card */}
        <div className="md:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Profile Details</CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <form onSubmit={handleUpdateProfile} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
                      Username (Immutable)
                    </label>
                    <div className="px-3 py-2 bg-slate-100 rounded-lg text-xs font-mono text-slate-700">
                      {user.username}
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
                      Email Address
                    </label>
                    <div className="px-3 py-2 bg-slate-100 rounded-lg text-xs font-mono text-slate-700 truncate">
                      {user.email}
                    </div>
                  </div>
                </div>

                <Input
                  label="Display Name"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  required
                />

                <Textarea
                  label="Professional Bio"
                  placeholder="e.g. Founder building SaaS solutions in clean tech..."
                  value={bio}
                  onChange={(e) => setBio(e.target.value)}
                  rows={3}
                />

                <div className="grid grid-cols-2 gap-4">
                  <Input
                    label="Country / Primary Market"
                    placeholder="e.g. United States, Germany, India"
                    value={country}
                    onChange={(e) => setCountry(e.target.value)}
                  />

                  <Select
                    label="Preferred Currency"
                    value={preferredCurrency}
                    onChange={(e) => setPreferredCurrency(e.target.value)}
                    options={[
                      { value: 'USD', label: 'USD ($)' },
                      { value: 'EUR', label: 'EUR (€)' },
                      { value: 'GBP', label: 'GBP (£)' },
                      { value: 'INR', label: 'INR (₹)' },
                      { value: 'CAD', label: 'CAD ($)' },
                      { value: 'AUD', label: 'AUD ($)' },
                    ]}
                  />
                </div>

                <div className="pt-2 flex justify-end">
                  <Button type="submit" variant="primary" isLoading={isUpdatingProfile} leftIcon={<Check className="w-4 h-4" />}>
                    Save Profile Changes
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          {/* Password Change Card */}
          <Card>
            <CardHeader>
              <CardTitle>Change Security Password</CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <form onSubmit={handleChangePassword} className="space-y-4">
                <Input
                  label="Current Password"
                  type="password"
                  placeholder="Enter current password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  required
                />

                <div className="grid grid-cols-2 gap-4">
                  <Input
                    label="New Password"
                    type="password"
                    placeholder="At least 8 chars"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                  />

                  <Input
                    label="Confirm New Password"
                    type="password"
                    placeholder="Re-type new password"
                    value={confirmNewPassword}
                    onChange={(e) => setConfirmNewPassword(e.target.value)}
                    required
                  />
                </div>

                <div className="pt-2 flex justify-end">
                  <Button type="submit" variant="outline" isLoading={isChangingPassword} leftIcon={<KeyRound className="w-4 h-4" />}>
                    Update Password
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar: Account Metadata & Danger Zone */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Account Information</CardTitle>
            </CardHeader>
            <CardContent className="p-6 space-y-3 text-xs text-slate-600">
              <div>
                <span className="font-semibold text-slate-800 block">Member Since</span>
                <span>{new Date(user.created_at).toLocaleDateString()}</span>
              </div>
              <div>
                <span className="font-semibold text-slate-800 block">Last Active</span>
                <span>{user.last_login_at ? new Date(user.last_login_at).toLocaleString() : 'First session'}</span>
              </div>
              <div className="pt-3 border-t border-slate-100">
                <span className="font-semibold text-slate-800 block mb-1">Legal Agreements</span>
                <button
                  onClick={() => onNavigate('/terms')}
                  className="text-indigo-600 hover:underline block"
                >
                  Terms & Conditions (v2026-v1.0)
                </button>
                <button
                  onClick={() => onNavigate('/privacy')}
                  className="text-indigo-600 hover:underline block mt-0.5"
                >
                  Privacy Policy (v2026-v1.0)
                </button>
              </div>
            </CardContent>
          </Card>

          {/* Danger Zone */}
          <Card className="border-rose-200">
            <CardHeader className="bg-rose-50/50">
              <CardTitle className="text-rose-900 flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-rose-600" />
                Danger Zone
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 space-y-3">
              <p className="text-xs text-slate-600 leading-relaxed">
                Permanently delete your user account and purge all business projects, blueprints, and history logs.
              </p>
              <Button
                variant="destructive"
                size="sm"
                className="w-full justify-center"
                onClick={() => setDeleteModalOpen(true)}
                leftIcon={<UserX className="w-4 h-4" />}
              >
                Delete Account
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Account Deletion Confirmation Modal */}
      <Modal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        title="Permanently Delete Account?"
        description="This action is irreversible and purges all projects and blueprints immediately."
        maxWidth="md"
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-600 leading-relaxed">
            Please enter your current account password and type <strong>DELETE</strong> in all-caps to confirm.
          </p>

          <Input
            label="Current Password"
            type="password"
            placeholder="Confirm your password"
            value={deletePassword}
            onChange={(e) => setDeletePassword(e.target.value)}
            required
          />

          <Input
            label="Type 'DELETE' to confirm"
            placeholder="DELETE"
            value={deleteConfirmText}
            onChange={(e) => setDeleteConfirmText(e.target.value)}
            required
          />

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <Button variant="outline" onClick={() => setDeleteModalOpen(false)} disabled={isDeletingAccount}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteAccount}
              isLoading={isDeletingAccount}
              disabled={deleteConfirmText !== 'DELETE' || !deletePassword}
            >
              Permanently Delete Account
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
