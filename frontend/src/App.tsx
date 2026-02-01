import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import CreateUnit from './pages/CreateUnit';
import CreateRota from './pages/CreateRota';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="create-unit" element={<CreateUnit />} />
          <Route path="create-rota" element={<CreateRota />} />
          <Route path="edit-rota/:id" element={<CreateRota />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
