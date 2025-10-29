import Layout from "./Layout.jsx";

import Home from "./Home";

import Features from "./Features";

import Integrations from "./Integrations";

import Pricing from "./Pricing";

import HowItWorks from "./HowItWorks";

import CaseStudies from "./CaseStudies";

import Resources from "./Resources";

import Security from "./Security";

import About from "./About";

import Contact from "./Contact";

import Connect from "./Connect";

import ConnectCallback from "./ConnectCallback";

import SignIn from "./SignIn";

import Dashboard from "./Dashboard";

import Onboarding from "./Onboarding";

import Settings from "./Settings";

import Insights from "./Insights";

import { BrowserRouter as Router, Route, Routes, useLocation } from 'react-router-dom';

import { ThemeProvider } from '../state/theme';

import AuthGuard from '../components/layout/AuthGuard';

const PAGES = {
    
    Home: Home,
    
    Features: Features,
    
    Integrations: Integrations,
    
    Pricing: Pricing,
    
    HowItWorks: HowItWorks,
    
    CaseStudies: CaseStudies,
    
    Resources: Resources,
    
    Security: Security,
    
    About: About,
    
    Contact: Contact,
    
    Connect: Connect,
    
    SignIn: SignIn,
    
    Dashboard: Dashboard,
    
    Onboarding: Onboarding,
    
    Settings: Settings,
    
    Insights: Insights,
    
}

function _getCurrentPage(url) {
    if (url.endsWith('/')) {
        url = url.slice(0, -1);
    }
    let urlLastPart = url.split('/').pop();
    if (urlLastPart.includes('?')) {
        urlLastPart = urlLastPart.split('?')[0];
    }

    const pageName = Object.keys(PAGES).find(page => page.toLowerCase() === urlLastPart.toLowerCase());
    return pageName || Object.keys(PAGES)[0];
}

// Create a wrapper component that uses useLocation inside the Router context
function PagesContent() {
    const location = useLocation();
    const currentPage = _getCurrentPage(location.pathname);
    
    return (
        <Layout currentPageName={currentPage}>
            <Routes>            
                
                    <Route path="/" element={<Home />} />
                
                
                <Route path="/Home" element={<Home />} />
                
                <Route path="/Features" element={<Features />} />
                
                <Route path="/Integrations" element={<Integrations />} />
                
                <Route path="/Pricing" element={<Pricing />} />
                
                <Route path="/HowItWorks" element={<HowItWorks />} />
                
                <Route path="/CaseStudies" element={<CaseStudies />} />
                
                <Route path="/Resources" element={<Resources />} />
                
                <Route path="/Security" element={<Security />} />
                
                <Route path="/About" element={<About />} />
                
                <Route path="/Contact" element={<Contact />} />
                
                <Route path="/Connect" element={<Connect />} />
                
                <Route path="/connect/callback" element={<ConnectCallback />} />
                
                <Route path="/signin" element={<SignIn />} />
                
                <Route path="/onboarding" element={<Onboarding />} />
                
                <Route path="/dashboard" element={<Dashboard />} />
                
                <Route path="/settings" element={<Settings />} />
                
                <Route path="/insights" element={<Insights />} />
                
            </Routes>
        </Layout>
    );
}

export default function Pages() {
    return (
        <ThemeProvider>
            <Router>
                <AuthGuard>
                    <PagesContent />
                </AuthGuard>
            </Router>
        </ThemeProvider>
    );
}