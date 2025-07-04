import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useParams, useNavigate } from 'react-router-dom';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginForm />} />
        <Route path="/register" element={<RegistrationForm />} />
        <Route path="/dashboard" element={<DashboardWrapper />} />
        <Route path="/register-member/:gymId" element={<MemberRegistrationForm />} />
        <Route path="/verify-cash-payment/:gymId" element={<CashPaymentVerification />} />
      </Routes>
    </Router>
  );
}

// Dashboard Wrapper Component
function DashboardWrapper() {
  const [gymOwner, setGymOwner] = useState(null);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Check if gym owner data exists in localStorage
    const storedGymOwner = localStorage.getItem('gymOwner');
    if (storedGymOwner) {
      setGymOwner(JSON.parse(storedGymOwner));
    } else {
      navigate('/');
    }
  }, [navigate]);

  if (!gymOwner) {
    return <div>Loading...</div>;
  }

  return (
    <Dashboard 
      gymOwner={gymOwner} 
      setGymOwner={setGymOwner}
      members={members}
      setMembers={setMembers}
      loading={loading}
      setLoading={setLoading}
    />
  );
}

// Home/Landing Page Component
const HomePage = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">G</span>
              </div>
              <h1 className="text-xl font-bold text-gray-900">GymSaaS</h1>
            </div>
            <nav className="hidden md:flex space-x-8">
              <a href="#features" className="text-gray-600 hover:text-indigo-600">Features</a>
              <a href="#pricing" className="text-gray-600 hover:text-indigo-600">Pricing</a>
              <a href="#contact" className="text-gray-600 hover:text-indigo-600">Contact</a>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
              Gym Management
              <span className="block text-indigo-600">Made Simple</span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
              Automate membership fees, manage members, and send WhatsApp reminders. 
              Complete gym management solution for modern fitness centers.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button 
                onClick={() => navigate('/login')}
                className="bg-indigo-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-indigo-700 transition-colors"
              >
                Login
              </button>
              <button 
                onClick={() => navigate('/register')}
                className="border border-indigo-600 text-indigo-600 px-8 py-3 rounded-lg font-semibold hover:bg-indigo-50 transition-colors"
              >
                Start Free Trial
              </button>
              <button className="border border-gray-300 text-gray-700 px-8 py-3 rounded-lg font-semibold hover:bg-gray-50 transition-colors">
                Watch Demo
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Everything You Need</h2>
            <p className="text-lg text-gray-600">Powerful features to manage your gym efficiently</p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"></path>
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Member Management</h3>
              <p className="text-gray-600">Easy QR-based registration and complete member database</p>
            </div>
            
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"></path>
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Smart Payments</h3>
              <p className="text-gray-600">Online and cash payment tracking with automated verification</p>
            </div>
            
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">WhatsApp Automation</h3>
              <p className="text-gray-600">Automated monthly fee reminders via WhatsApp</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

// Registration Form Component
const RegistrationForm = () => {
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    gym_name: '',
    address: '',
    monthly_fee: ''
  });
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/gym-owner/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...formData,
          monthly_fee: parseFloat(formData.monthly_fee)
        }),
      });

      if (response.ok) {
        const ownerData = await response.json();
        // Store gym owner data in localStorage
        localStorage.setItem('gymOwner', JSON.stringify(ownerData));
        navigate('/dashboard');
      } else {
        const errorData = await response.json();
        alert(`Registration failed: ${errorData.detail}`);
      }
    } catch (error) {
      alert('Registration failed. Please try again.');
      console.error('Registration error:', error);
    }
    
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 bg-indigo-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-xl">G</span>
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Register Your Gym
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Start managing your gym members today
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Your Name</label>
              <input
                type="text"
                name="name"
                required
                value={formData.name}
                onChange={handleInputChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Phone Number</label>
              <input
                type="tel"
                name="phone"
                required
                value={formData.phone}
                onChange={handleInputChange}
                placeholder="10-digit mobile number"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Gym Name</label>
              <input
                type="text"
                name="gym_name"
                required
                value={formData.gym_name}
                onChange={handleInputChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Address</label>
              <textarea
                name="address"
                required
                value={formData.address}
                onChange={handleInputChange}
                rows="3"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Monthly Fee (₹)</label>
              <input
                type="number"
                name="monthly_fee"
                required
                value={formData.monthly_fee}
                onChange={handleInputChange}
                placeholder="e.g., 1500"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {loading ? 'Registering...' : 'Register Gym'}
            </button>
          </div>
          
          <div className="text-center">
            <button
              type="button"
              onClick={() => navigate('/')}
              className="text-indigo-600 hover:text-indigo-500 text-sm"
            >
              ← Back to Home
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Member Registration Form (accessed via QR code)
const MemberRegistrationForm = () => {
  const { gymId } = useParams();
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    gym_id: gymId
  });
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [gymInfo, setGymInfo] = useState(null);

  useEffect(() => {
    // Load gym information
    const loadGymInfo = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/gym-owner/${gymId}`);
        if (response.ok) {
          const data = await response.json();
          setGymInfo(data);
        }
      } catch (error) {
        console.error('Error loading gym info:', error);
      }
    };

    if (gymId) {
      loadGymInfo();
    }
  }, [gymId]);

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/member/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        setSubmitted(true);
      } else {
        const errorData = await response.json();
        alert(`Registration failed: ${errorData.detail}`);
      }
    } catch (error) {
      alert('Registration failed. Please try again.');
      console.error('Member registration error:', error);
    }
    
    setLoading(false);
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-green-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full text-center">
          <div className="mx-auto h-12 w-12 bg-green-600 rounded-full flex items-center justify-center">
            <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
            </svg>
          </div>
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">Registration Successful!</h2>
          <p className="mt-2 text-gray-600">Welcome to {gymInfo?.gym_name}! Your membership is now active.</p>
          <div className="mt-6 bg-white p-4 rounded-lg shadow">
            <p className="text-sm text-gray-600">Monthly Fee: <span className="font-semibold">₹{gymInfo?.monthly_fee}</span></p>
            <p className="text-sm text-gray-600 mt-2">Payment due at the beginning of each month.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Join {gymInfo?.gym_name || 'Our Gym'}
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Fill in your details to complete registration
          </p>
          {gymInfo && (
            <div className="mt-4 bg-indigo-50 p-4 rounded-lg">
              <p className="text-sm text-indigo-800">
                <span className="font-semibold">Monthly Fee:</span> ₹{gymInfo.monthly_fee}
              </p>
              <p className="text-sm text-indigo-600 mt-1">
                {gymInfo.address}
              </p>
            </div>
          )}
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Full Name</label>
              <input
                type="text"
                name="name"
                required
                value={formData.name}
                onChange={handleInputChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Phone Number</label>
              <input
                type="tel"
                name="phone"
                required
                value={formData.phone}
                onChange={handleInputChange}
                placeholder="10-digit mobile number"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            {loading ? 'Registering...' : 'Register'}
          </button>
        </form>
      </div>
    </div>
  );
};

// Cash Payment Verification Component
const CashPaymentVerification = () => {
  const { gymId } = useParams();
  const [formData, setFormData] = useState({
    phone: '',
    name: ''
  });
  const [loading, setLoading] = useState(false);
  const [verified, setVerified] = useState(false);
  const [gymInfo, setGymInfo] = useState(null);

  useEffect(() => {
    // Load gym information
    const loadGymInfo = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/gym-owner/${gymId}`);
        if (response.ok) {
          const data = await response.json();
          setGymInfo(data);
        }
      } catch (error) {
        console.error('Error loading gym info:', error);
      }
    };

    if (gymId) {
      loadGymInfo();
    }
  }, [gymId]);

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/verify-cash-payment/${gymId}?phone=${formData.phone}&name=${formData.name}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        setVerified(true);
      } else {
        const errorData = await response.json();
        alert(`Verification failed: ${errorData.detail}`);
      }
    } catch (error) {
      alert('Verification failed. Please try again.');
      console.error('Cash payment verification error:', error);
    }
    
    setLoading(false);
  };

  if (verified) {
    return (
      <div className="min-h-screen bg-green-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full text-center">
          <div className="mx-auto h-12 w-12 bg-green-600 rounded-full flex items-center justify-center">
            <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
            </svg>
          </div>
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">Payment Verified!</h2>
          <p className="mt-2 text-gray-600">Your cash payment has been successfully verified and recorded.</p>
          <div className="mt-6 bg-white p-4 rounded-lg shadow">
            <p className="text-sm text-gray-600">Payment Status: <span className="text-green-600 font-semibold">Paid</span></p>
            <p className="text-sm text-gray-600 mt-2">Thank you for your payment!</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Verify Cash Payment
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Enter your details to verify your cash payment
          </p>
          {gymInfo && (
            <div className="mt-4 bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-blue-800 font-semibold text-center">
                {gymInfo.gym_name}
              </p>
              <p className="text-sm text-blue-600 text-center">
                {gymInfo.address}
              </p>
            </div>
          )}
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Registered Phone Number</label>
              <input
                type="tel"
                name="phone"
                required
                value={formData.phone}
                onChange={handleInputChange}
                placeholder="Enter your registered phone number"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Full Name</label>
              <input
                type="text"
                name="name"
                required
                value={formData.name}
                onChange={handleInputChange}
                placeholder="Enter your full name"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-yellow-700">
                  Please ensure you have already made the cash payment to the gym owner before verifying.
                </p>
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            {loading ? 'Verifying...' : 'Verify Payment'}
          </button>
        </form>
      </div>
    </div>
  );
};

// Dashboard Component (continuing from the original)
const Dashboard = ({ gymOwner, setGymOwner, members, setMembers, loading, setLoading }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const navigate = useNavigate();

  useEffect(() => {
    if (gymOwner) {
      loadMembers();
    }
  }, [gymOwner]);

  const loadMembers = async () => {
    if (!gymOwner) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/gym/${gymOwner.id}/members`);
      if (response.ok) {
        const membersData = await response.json();
        setMembers(membersData);
      }
    } catch (error) {
      console.error('Error loading members:', error);
    }
    setLoading(false);
  };

  const markAsPaid = async (memberId, paymentMethod) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/member/${gymOwner.id}/${memberId}/payment`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ payment_method: paymentMethod }),
      });

      if (response.ok) {
        loadMembers(); // Refresh members list
      } else {
        alert('Failed to update payment status');
      }
    } catch (error) {
      alert('Error updating payment status');
      console.error('Payment update error:', error);
    }
  };

  const toggleMemberStatus = async (memberId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/member/${gymOwner.id}/${memberId}/toggle-active`, {
        method: 'PATCH',
      });

      if (response.ok) {
        loadMembers(); // Refresh members list
      } else {
        alert('Failed to update member status');
      }
    } catch (error) {
      alert('Error updating member status');
      console.error('Member status error:', error);
    }
  };

  const totalMembers = members.length;
  const paidMembers = members.filter(m => m.fee_status === 'paid').length;
  const unpaidMembers = members.filter(m => m.fee_status === 'unpaid').length;
  const totalRevenue = members.filter(m => m.fee_status === 'paid').reduce((sum, m) => sum + m.current_month_fee, 0);

  // Update QR code URLs to use the current domain
  const currentDomain = window.location.origin;
  const memberRegistrationUrl = `${currentDomain}/register-member/${gymOwner.id}`;
  const cashVerificationUrl = `${currentDomain}/verify-cash-payment/${gymOwner.id}`;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{gymOwner?.gym_name}</h1>
              <p className="text-gray-600">Owner: {gymOwner?.name}</p>
            </div>
            <button
              onClick={() => {
                localStorage.removeItem('gymOwner');
                setGymOwner(null);
                navigate('/');
              }}
              className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {['overview', 'members', 'qr-codes', 'payments'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-4 px-1 border-b-2 font-medium text-sm capitalize ${
                  activeTab === tab
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.replace('-', ' ')}
              </button>
            ))}
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                      <span className="text-white text-sm font-bold">{totalMembers}</span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Total Members</p>
                    <p className="text-2xl font-bold text-gray-900">{totalMembers}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                      <span className="text-white text-sm font-bold">{paidMembers}</span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Paid This Month</p>
                    <p className="text-2xl font-bold text-gray-900">{paidMembers}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-red-500 rounded-full flex items-center justify-center">
                      <span className="text-white text-sm font-bold">{unpaidMembers}</span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Pending Payment</p>
                    <p className="text-2xl font-bold text-gray-900">{unpaidMembers}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-yellow-500 rounded-full flex items-center justify-center">
                      <span className="text-white text-sm font-bold">₹</span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Revenue This Month</p>
                    <p className="text-2xl font-bold text-gray-900">₹{totalRevenue.toFixed(2)}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Members */}
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Recent Members</h3>
              </div>
              <div className="px-6 py-4">
                {members.slice(0, 5).map((member) => (
                  <div key={member.id} className="flex items-center justify-between py-3 border-b border-gray-200 last:border-b-0">
                    <div>
                      <p className="font-medium text-gray-900">{member.name}</p>
                      <p className="text-sm text-gray-600">{member.phone}</p>
                    </div>
                    <div className="text-right">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        member.fee_status === 'paid' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {member.fee_status}
                      </span>
                      <p className="text-sm text-gray-600 mt-1">₹{member.current_month_fee}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Members Tab */}
        {activeTab === 'members' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">All Members</h2>
              <button
                onClick={loadMembers}
                className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700"
              >
                Refresh
              </button>
            </div>

            <div className="bg-white shadow overflow-hidden sm:rounded-lg">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Member
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Joining Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Fee
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {members.map((member) => (
                    <tr key={member.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{member.name}</div>
                          <div className="text-sm text-gray-500">{member.phone}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(member.joining_date).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        ₹{member.current_month_fee}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          member.fee_status === 'paid' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {member.fee_status}
                        </span>
                        {member.payment_method && (
                          <span className="ml-2 text-xs text-gray-500">({member.payment_method})</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                        {member.fee_status === 'unpaid' && (
                          <>
                            <button
                              onClick={() => markAsPaid(member.id, 'cash')}
                              className="bg-green-600 text-white px-3 py-1 rounded text-xs hover:bg-green-700"
                            >
                              Mark Cash Paid
                            </button>
                            <button
                              onClick={() => markAsPaid(member.id, 'online')}
                              className="bg-blue-600 text-white px-3 py-1 rounded text-xs hover:bg-blue-700"
                            >
                              Mark Online Paid
                            </button>
                          </>
                        )}
                        <button
                          onClick={() => toggleMemberStatus(member.id)}
                          className={`px-3 py-1 rounded text-xs ${
                            member.is_active
                              ? 'bg-yellow-600 text-white hover:bg-yellow-700'
                              : 'bg-green-600 text-white hover:bg-green-700'
                          }`}
                        >
                          {member.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* QR Codes Tab */}
        {activeTab === 'qr-codes' && gymOwner && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900">QR Codes</h2>
            
            <div className="grid md:grid-cols-2 gap-8">
              {/* Member Registration QR */}
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Member Registration QR</h3>
                <p className="text-gray-600 mb-4">Members scan this QR to register for your gym</p>
                <div className="flex justify-center mb-4">
                  <img 
                    src={`data:image/png;base64,${gymOwner.qr_code}`} 
                    alt="Member Registration QR" 
                    className="w-48 h-48 border border-gray-300 rounded"
                  />
                </div>
                <div className="text-center">
                  <p className="text-sm text-gray-500 break-all">{memberRegistrationUrl}</p>
                  <button
                    onClick={() => navigator.clipboard.writeText(memberRegistrationUrl)}
                    className="mt-2 text-indigo-600 hover:text-indigo-500 text-sm"
                  >
                    Copy URL
                  </button>
                </div>
              </div>

              {/* Cash Payment Verification QR */}
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Cash Payment Verification QR</h3>
                <p className="text-gray-600 mb-4">Show this QR after receiving cash payment from members</p>
                <div className="flex justify-center mb-4">
                  <img 
                    src={`data:image/png;base64,${gymOwner.cash_verification_qr}`} 
                    alt="Cash Payment QR" 
                    className="w-48 h-48 border border-gray-300 rounded"
                  />
                </div>
                <div className="text-center">
                  <p className="text-sm text-gray-500">Members use this to verify cash payments</p>
                  <p className="text-sm text-gray-500 break-all mt-2">{cashVerificationUrl}</p>
                  <button
                    onClick={() => navigator.clipboard.writeText(cashVerificationUrl)}
                    className="mt-2 text-indigo-600 hover:text-indigo-500 text-sm"
                  >
                    Copy URL
                  </button>
                </div>
              </div>
            </div>

            {/* WhatsApp Integration Status */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-yellow-800">WhatsApp Integration Ready</h3>
                  <div className="mt-2 text-sm text-yellow-700">
                    <p>Automated monthly fee reminders will be enabled once WhatsApp is configured.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Payments Tab */}
        {activeTab === 'payments' && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900">Payment Integration</h2>
            
            {/* Razorpay Integration Status */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4z" />
                    <path fillRule="evenodd" d="M18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-blue-800">Razorpay Integration Ready</h3>
                  <div className="mt-2 text-sm text-blue-700">
                    <p>Add your Razorpay API keys to enable online payment collection and automatic verification.</p>
                    <p className="mt-1">Required: RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Payment Statistics */}
            <div className="grid md:grid-cols-3 gap-6">
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Cash Payments</h3>
                <p className="text-3xl font-bold text-green-600">
                  {members.filter(m => m.payment_method === 'cash').length}
                </p>
                <p className="text-sm text-gray-600">Total members paid via cash</p>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Online Payments</h3>
                <p className="text-3xl font-bold text-blue-600">
                  {members.filter(m => m.payment_method === 'online').length}
                </p>
                <p className="text-sm text-gray-600">Total members paid online</p>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Pending Payments</h3>
                <p className="text-3xl font-bold text-red-600">{unpaidMembers}</p>
                <p className="text-sm text-gray-600">Members with pending payments</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default App;