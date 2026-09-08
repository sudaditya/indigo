import { BrowserRouter, Routes, Route } from 'react-router';
import { WorksList } from './pages/WorksList';
import { DocumentViewer } from './pages/DocumentViewer';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<WorksList />} />
        <Route path="/works/:id" element={<DocumentViewer />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;