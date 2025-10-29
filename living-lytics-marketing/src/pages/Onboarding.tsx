import React from 'react';
import { saveOnboarding } from '../lib/api';
import { rememberOnboardingDone } from '../lib/auth';
import { useNavigate } from 'react-router-dom';

const INDUSTRIES = ['Retail', 'Real Estate', 'Services', 'Education', 'E-commerce', 'Other'];
const ROLES = ['Owner', 'Marketer', 'Analyst', 'Consultant', 'Other'];
const PURPOSES = ['Track results', 'Compare channels', 'Get AI insights', 'Client reporting'];

export default function Onboarding() {
  const nav = useNavigate();
  const [industry, setIndustry] = React.useState('');
  const [role, setRole] = React.useState('');
  const [purpose, setPurpose] = React.useState('');
  const [loading, setLoading] = React.useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    await saveOnboarding({ industry, role, purpose });
    rememberOnboardingDone();
    setLoading(false);
    nav('/connect');
  }

  return (
    <div className="min-h-[70vh] py-12 px-4">
      <div className="mx-auto max-w-2xl">
        <h1 className="text-2xl font-semibold mb-2">Let's tailor your experience</h1>
        <p className="text-slate-600 dark:text-slate-400 mb-6">Answer a few quick questions so we can personalize insights.</p>
        <form onSubmit={onSubmit} className="space-y-5">
          <Select label="Industry" value={industry} setValue={setIndustry} options={INDUSTRIES} />
          <Select label="Your role" value={role} setValue={setRole} options={ROLES} />
          <Select label="What's your goal?" value={purpose} setValue={setPurpose} options={PURPOSES} />
          <button disabled={loading || !industry || !role || !purpose}
            className="w-full rounded-lg bg-gradient-to-r from-indigo-600 to-teal-400 py-2.5 font-semibold text-white disabled:opacity-60">
            {loading ? 'Saving…' : 'Continue'}
          </button>
        </form>
      </div>
    </div>
  );
}

function Select({ label, value, setValue, options }:{label:string; value:string; setValue:(v:string)=>void; options:string[]}) {
  return (
    <label className="block">
      <span className="text-sm text-slate-700 dark:text-slate-300">{label}</span>
      <select className="mt-1 w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 p-2"
        value={value} onChange={e=>setValue(e.target.value)} required>
        <option value="" disabled>Select…</option>
        {options.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
    </label>
  );
}
