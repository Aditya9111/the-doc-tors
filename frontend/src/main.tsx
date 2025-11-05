import React from 'react'
import ReactDOM from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { ChakraProvider } from '@chakra-ui/react'
import { system } from './theme'
import App from './pages/App'
import Upload from './pages/Upload'
import Query from './pages/Query'
import Versions from './pages/Versions'
import Compare from './pages/Compare'
import Docs from './pages/Docs'
import Health from './pages/Health'
import './index.css'

const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { index: true, element: <Upload /> },
      { path: 'upload', element: <Upload /> },
      { path: 'query', element: <Query /> },
      { path: 'versions', element: <Versions /> },
      { path: 'compare', element: <Compare /> },
      { path: 'docs', element: <Docs /> },
      { path: 'health', element: <Health /> }
    ]
  }
])

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ChakraProvider value={system}>
      <RouterProvider router={router} />
    </ChakraProvider>
  </React.StrictMode>
)


