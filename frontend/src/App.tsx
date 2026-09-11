import { BrowserRouter, Routes, Route } from 'react-router';
import { WorksList } from './pages/WorksList';
import { DocumentViewer } from './pages/DocumentViewer';
import { PersonaProvider } from './context/PersonaContext';
import { PersonaSwitcher } from './components/PersonaSwitcher';
import './App.css';

function App() {
  return (
    <PersonaProvider>
      <BrowserRouter>
        {/* App-wide header with persona switcher on the right */}
        <div className="app-header">
          <PersonaSwitcher />
        </div>

        <Routes>
          <Route path="/" element={<WorksList />} />
          <Route path="/works/:id/*" element={<DocumentViewer />} />
        </Routes>
      </BrowserRouter>
    </PersonaProvider>
  );
}

export default App;