import { Routes, Route } from 'react-router-dom'
import Layout from './components/common/Layout'
import LibraryPage from './pages/LibraryPage'
import SearchPage from './pages/SearchPage'
import UploadPage from './pages/UploadPage'
import VideoPage from './pages/VideoPage'
import WorkspacePage from './pages/WorkspacePage'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<LibraryPage />} />
        <Route path="/library" element={<LibraryPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/videos/:id" element={<VideoPage />} />
        <Route path="/workspace" element={<WorkspacePage />} />
      </Routes>
    </Layout>
  )
}

export default App
