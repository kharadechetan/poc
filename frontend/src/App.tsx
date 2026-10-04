import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { Machines } from './pages/Machines';
import { WorkOrders } from './pages/WorkOrders';
import { Schedule } from './pages/Schedule';
import { Breakdown } from './pages/Breakdown';
import { Rescheduling } from './pages/Rescheduling';
import { History } from './pages/History';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="machines" element={<Machines />} />
          <Route path="work-orders" element={<WorkOrders />} />
          <Route path="schedule" element={<Schedule />} />
          <Route path="breakdown" element={<Breakdown />} />
          <Route path="rescheduling" element={<Rescheduling />} />
          <Route path="history" element={<History />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
