import React, { useState } from 'react';
import { useAuth } from './auth/AuthContext.jsx';
import { Login } from './routes/Login.jsx';
import { Learn } from './routes/Learn.jsx';

// Admin Views
import { AdminLayout } from './components/layout/AdminLayout.jsx';
import { AdminDashboard } from './routes/admin/AdminDashboard.jsx';
import { AdminClients } from './routes/admin/AdminClients.jsx';
import { AdminRounds } from './routes/admin/AdminRounds.jsx';
import { AdminModels } from './routes/admin/AdminModels.jsx';
import { AdminPrivacy } from './routes/admin/AdminPrivacy.jsx';
import { AdminCommunication } from './routes/admin/AdminCommunication.jsx';
import { AdminAudit } from './routes/admin/AdminAudit.jsx';

// Client Views
import { ClientLayout } from './components/layout/ClientLayout.jsx';
import { ClientHome } from './routes/client/ClientHome.jsx';
import { ClientData } from './routes/client/ClientData.jsx';
import { ClientTraining } from './routes/client/ClientTraining.jsx';
import { ClientModel } from './routes/client/ClientModel.jsx';
import { ClientPredict } from './routes/client/ClientPredict.jsx';

export function App() {
  const { user } = useAuth();
  const [adminTab, setAdminTab] = useState('dashboard');
  const [clientTab, setClientTab] = useState('home');

  if (!user) {
    return <Login />;
  }

  if (user.role === 'admin') {
    return (
      <AdminLayout activeTab={adminTab} onSelectTab={setAdminTab}>
        {adminTab === 'dashboard' && <AdminDashboard onNavigate={setAdminTab} />}
        {adminTab === 'clients' && <AdminClients />}
        {adminTab === 'rounds' && <AdminRounds />}
        {adminTab === 'models' && <AdminModels />}
        {adminTab === 'privacy' && <AdminPrivacy />}
        {adminTab === 'communication' && <AdminCommunication />}
        {adminTab === 'audit' && <AdminAudit />}
        {adminTab === 'learn' && <Learn />}
      </AdminLayout>
    );
  }

  // Client Portal
  return (
    <ClientLayout activeTab={clientTab} onSelectTab={setClientTab}>
      {clientTab === 'home' && <ClientHome onNavigate={setClientTab} />}
      {clientTab === 'data' && <ClientData />}
      {clientTab === 'training' && <ClientTraining />}
      {clientTab === 'model' && <ClientModel />}
      {clientTab === 'predict' && <ClientPredict />}
      {clientTab === 'learn' && <Learn />}
    </ClientLayout>
  );
}

export default App;
