#!/usr/bin/env node
/**
 * Quick Auth Test Script
 * 
 * Tests authentication endpoints via the Vite dev proxy
 * Usage: node scripts/testAuth.mjs --email user@example.com --password MyPassword123
 */

import { request } from 'undici';

const BASE_URL = 'http://localhost:5000';
const API_PREFIX = '/api';

// Parse args
const args = process.argv.slice(2);
const email = args[args.indexOf('--email') + 1];
const password = args[args.indexOf('--password') + 1];

if (!email || !password) {
  console.error('❌ Missing required arguments');
  console.log('Usage: node scripts/testAuth.mjs --email <email> --password <password>');
  process.exit(1);
}

// Simple cookie jar
let cookies = [];

function parseCookies(setCookieHeaders) {
  if (!setCookieHeaders) return [];
  const headers = Array.isArray(setCookieHeaders) ? setCookieHeaders : [setCookieHeaders];
  return headers.map(h => h.split(';')[0]);
}

function getCookieHeader() {
  return cookies.length > 0 ? cookies.join('; ') : undefined;
}

async function testHealth() {
  try {
    const { statusCode } = await request(`${BASE_URL}${API_PREFIX}/v1/health/liveness`);
    console.log(`✓ Health: ${statusCode}`);
    return statusCode === 200;
  } catch (err) {
    console.error(`✗ Health failed: ${err.message}`);
    return false;
  }
}

async function testLogin() {
  try {
    const { statusCode, headers, body } = await request(`${BASE_URL}${API_PREFIX}/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    // Store cookies
    if (headers['set-cookie']) {
      cookies = parseCookies(headers['set-cookie']);
    }

    const data = await body.json().catch(() => ({}));
    
    console.log(`${statusCode === 200 ? '✓' : '✗'} Login: ${statusCode}`);
    if (statusCode !== 200) {
      console.log(`  Message: ${data.detail || data.message || 'Unknown error'}`);
    }
    
    return statusCode === 200;
  } catch (err) {
    console.error(`✗ Login failed: ${err.message}`);
    return false;
  }
}

async function testStatus() {
  try {
    const headers = {};
    const cookieHeader = getCookieHeader();
    if (cookieHeader) {
      headers['cookie'] = cookieHeader;
    }

    const { statusCode, body } = await request(`${BASE_URL}${API_PREFIX}/v1/auth/status`, {
      headers,
    });

    const data = await body.json().catch(() => ({}));
    
    // Truncate to relevant fields
    const truncated = {
      authenticated: data.authenticated,
      email: data.email,
      google: !!data.google,
      instagram: !!data.instagram,
    };
    
    console.log(`${statusCode === 200 ? '✓' : '✗'} Status: ${statusCode}`);
    console.log(`  ${JSON.stringify(truncated, null, 2)}`);
    
    return statusCode === 200 || statusCode === 403; // 403 means not authed, but endpoint works
  } catch (err) {
    console.error(`✗ Status failed: ${err.message}`);
    return false;
  }
}

async function runTests() {
  console.log('\n🧪 Testing Authentication Flow\n');
  console.log(`Email: ${email}`);
  console.log(`Base URL: ${BASE_URL}${API_PREFIX}\n`);

  const healthOk = await testHealth();
  if (!healthOk) {
    console.error('\n❌ Health check failed. Is the dev server running?');
    process.exit(1);
  }

  const loginOk = await testLogin();
  if (!loginOk) {
    console.error('\n❌ Login failed. Check credentials or backend.');
    process.exit(1);
  }

  const statusOk = await testStatus();
  if (!statusOk) {
    console.error('\n❌ Status check failed.');
    process.exit(1);
  }

  console.log('\n✅ All tests passed\n');
  process.exit(0);
}

runTests();
