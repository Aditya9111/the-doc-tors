# Frontend Documentation

## Overview

The frontend is a modern, responsive React application built with TypeScript and Chakra UI. It provides an intuitive interface for interacting with the RAG backend, featuring glassmorphism design, smooth animations, and comprehensive functionality for document management, querying, version control, and documentation generation.

## Technology Stack

- **React 18.3** - UI library
- **TypeScript 5.5** - Type-safe JavaScript
- **Vite 5.4** - Build tool and dev server
- **Chakra UI 3.27** - Component library with custom theme
- **React Router 6.26** - Client-side routing
- **React Markdown 8.0** - Markdown rendering
- **Framer Motion 12.23** - Animations (via Chakra UI)
- **React Icons 5.5** - Icon library

## Architecture

### Component Structure

```
src/
├── main.tsx              # Application entry point
├── App.tsx                # Main layout with navigation
├── theme.ts               # Chakra UI theme configuration
├── index.css              # Global styles and animations
└── pages/
    ├── Upload.tsx         # File upload interface
    ├── Query.tsx          # Question-answering interface
    ├── Versions.tsx       # Version management
    ├── Compare.tsx        # Multi-version comparison
    ├── Docs.tsx           # Documentation generation
    └── Health.tsx         # System health monitoring
```

### Routing Structure

```typescript
/                    → Upload (default)
/upload              → Upload page
/query               → Query page
/versions            → Versions page
/compare             → Compare page
/docs                → Documentation page
/health              → Health page
```

### State Management

The application uses React's built-in state management:
- **useState** - Local component state
- **useEffect** - Side effects and API calls
- **useRef** - DOM references and mutable values
- **useDisclosure** - Chakra UI disclosure hooks

No global state management library is used - state is managed at the component level with props for data flow.

## Installation & Setup

### Prerequisites

- Node.js 16.0 or higher
- npm or yarn package manager

### Step-by-Step Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start development server**:
   ```bash
   npm run dev
   ```

   The application will be available at `http://localhost:5173` (or the next available port)

4. **Build for production**:
   ```bash
   npm run build
   ```

   Output will be in the `dist/` directory

5. **Preview production build**:
   ```bash
   npm run preview
   ```

### Configuration

The frontend expects the backend API to be running at:
- Development: `http://localhost:8000`
- Production: Configure via environment variables or proxy settings

## Project Structure

### Directory Layout

```
frontend/
├── src/
│   ├── main.tsx              # React entry point with router
│   ├── App.tsx               # Main app component with navigation
│   ├── theme.ts              # Chakra UI theme configuration
│   ├── index.css             # Global styles
│   └── pages/                # Page components
│       ├── Upload.tsx
│       ├── Query.tsx
│       ├── Versions.tsx
│       ├── Compare.tsx
│       ├── Docs.tsx
│       └── Health.tsx
├── dist/                     # Production build output
├── index.html                # HTML template
├── package.json              # Dependencies and scripts
├── tsconfig.json             # TypeScript configuration
└── vite.config.ts            # Vite configuration
```

### Component Hierarchy

```
App (Layout + Navigation)
├── Upload
├── Query
│   ├── Version Selector
│   ├── Query Input
│   └── Results Display
├── Versions
│   └── Version Cards
├── Compare
│   ├── Version Multi-Select
│   ├── Query Input
│   └── Comparison Results
├── Docs
│   ├── File Upload
│   ├── Progress Tracker
│   └── Results Display
└── Health
    └── Stats Display
```

## Pages & Features

### Upload Page (`/upload`)

**Purpose**: Upload ZIP files as new versions with metadata.

**Features**:
- Drag-and-drop file upload
- Click-to-upload fallback
- File validation (ZIP only, 100MB limit)
- Version metadata form:
  - Version name input
  - Description textarea
  - Tags input (comma-separated)
- Real-time upload progress
- Success/error feedback
- Upload result display with statistics

**UI Components**:
- Glassmorphic upload area with hover effects
- File preview card
- Form inputs with validation
- Loading states with progress bar
- Success/error notifications

**API Integration**:
- `POST /api/ingest_versioned` - Upload file with metadata

**Example Usage**:
1. Drag and drop ZIP file or click to browse
2. Enter version name (e.g., "v1.0.0")
3. Add description (optional)
4. Add tags (optional, comma-separated)
5. Click "Upload as New Version"
6. View processing results

### Query Page (`/query`)

**Purpose**: Ask questions about uploaded documents using natural language.

**Features**:
- Natural language query input
- Version selection dropdown:
  - Searchable version list
  - Keyboard navigation (arrow keys, enter, escape)
  - "Latest version" option
  - Version metadata display
- Real-time query execution
- Markdown-formatted answer display
- Source attribution:
  - Expandable sources list
  - File paths and chunk types
  - Content previews
  - Source highlighting
- Copy to clipboard functionality
- Version context display

**UI Components**:
- Query input with submit button
- Version selector with autocomplete
- Answer display with markdown rendering
- Collapsible sources section
- Source cards with metadata
- Loading spinners
- Error messages

**API Integration**:
- `GET /api/versions` - Fetch available versions
- `GET /api/query` - Submit query with optional version_id

**Example Usage**:
1. Select version (optional, defaults to latest)
2. Enter question (e.g., "How does authentication work?")
3. Click "Search" or press Enter
4. View answer with source citations
5. Expand sources to see relevant chunks

### Versions Page (`/versions`)

**Purpose**: View and manage all uploaded document versions.

**Features**:
- Version list display:
  - Version cards with metadata
  - File and chunk statistics
  - Status badges (active/archived/deleted)
  - Upload timestamps
  - File type indicators
  - Tags display
- Version filtering:
  - Status filter (active/archived/deleted)
  - Search functionality
- Version actions:
  - View details
  - Delete version (with confirmation)
  - Status updates
- Refresh button
- Empty state handling

**UI Components**:
- Grid layout for version cards
- Status badges
- Statistics display
- Action buttons
- Confirmation dialogs
- Loading states

**API Integration**:
- `GET /api/versions` - List all versions
- `GET /api/versions/{version_id}` - Get version details
- `DELETE /api/versions/{version_id}` - Delete version
- `PUT /api/versions/{version_id}/status` - Update status

**Example Usage**:
1. View all versions in grid layout
2. Filter by status using dropdown
3. Search versions by name or ID
4. Click version card for details
5. Delete version with confirmation

### Compare Page (`/compare`)

**Purpose**: Compare answers across multiple document versions.

**Features**:
- Multi-version selection:
  - Searchable version dropdown
  - Keyboard navigation
  - Selected versions display
  - Remove selected versions
- Query input for comparison
- Side-by-side comparison results:
  - Version-specific answers
  - Source counts
  - Version metadata
- Copy individual answers
- Clear selection option

**UI Components**:
- Version multi-select dropdown
- Selected versions chips
- Query input
- Comparison results grid
- Answer cards with copy buttons
- Loading states

**API Integration**:
- `GET /api/versions` - Fetch versions
- `GET /api/query_compare` - Compare answers

**Example Usage**:
1. Select multiple versions to compare
2. Enter comparison query
3. View side-by-side answers
4. Copy specific answers
5. Analyze differences between versions

### Docs Page (`/docs`)

**Purpose**: Generate documentation for codebases.

**Features**:
- File upload for documentation generation
- Documentation mode selection:
  - Standard documentation
  - RAG-enhanced documentation
- Progress tracking:
  - Real-time progress updates
  - File count tracking
  - Status indicators
- Results display:
  - Documentation download links
  - Individual file downloads
  - Generation statistics
- Background processing support
- Progress polling

**UI Components**:
- File upload area
- Mode selector
- Progress bar with percentage
- Results display
- Download buttons
- Loading states

**API Integration**:
- `POST /api/generate_documentation` - Generate standard docs
- `GET /api/documentation_progress/{job_id}` - Poll progress
- `POST /api/generate_documentation_rag` - Generate RAG docs
- `GET /api/download_documentation/{doc_id}` - Download ZIP
- `GET /api/download_documentation_file/{doc_id}/{filename}` - Download file

**Example Usage**:
1. Upload ZIP file
2. Select documentation mode
3. Click "Generate Documentation"
4. Monitor progress (for standard docs)
5. Download generated documentation

### Health Page (`/health`)

**Purpose**: Monitor system health and statistics.

**Features**:
- Health status display
- System statistics:
  - Vectorstore status
  - Document counts
  - File type breakdown
  - Storage information
- Refresh functionality
- JSON data display

**UI Components**:
- Status indicators
- Statistics cards
- JSON viewer
- Refresh button

**API Integration**:
- `GET /api/health` - Health check
- `GET /api/stats` - System statistics

**Example Usage**:
1. View system health status
2. Check document statistics
3. Monitor vectorstore health
4. Refresh data

## UI/UX Features

### Glassmorphism Design

The application uses a modern glassmorphism design system:

**Glass Effects**:
- `glass` - Standard glass effect with blur
- `glass-strong` - Stronger glass effect with more blur
- `glass-card` - Card-style glass container

**Properties**:
- Backdrop blur (10-20px)
- Semi-transparent backgrounds
- Subtle borders
- Soft shadows
- Light/dark mode support

**Implementation**:
- CSS classes in `index.css`
- Chakra UI theme extensions in `theme.ts`
- Responsive to light/dark themes

### Responsive Design

**Breakpoints**:
- Mobile: < 768px
- Tablet: 768px - 1024px
- Desktop: > 1024px

**Responsive Features**:
- Navigation labels hidden on mobile (icons only)
- Grid layouts adapt to screen size
- Touch-friendly button sizes
- Scrollable content areas

### Animations & Transitions

**CSS Animations** (in `index.css`):
- `animate-fade-in` - Fade in on mount
- `animate-slide-up` - Slide up animation
- `animate-gradient` - Animated gradient background
- `animate-float` - Floating element animation
- `animate-pulse` - Pulsing effect

**Component Transitions**:
- Hover lift effects (`hover-lift` class)
- Smooth color transitions
- Button hover states
- Loading state transitions

**Framer Motion**:
- Used via Chakra UI components
- Smooth page transitions
- Component animations

### Dark/Light Theme Support

**Theme Configuration**:
- Chakra UI system theme
- Light mode by default
- Dark mode support via Chakra UI
- Glass effects adapt to theme

**Theme Colors**:
- Primary: Blue shades
- Success: Green shades
- Error: Red shades
- Glass: White/black overlays

### Accessibility Features

**Keyboard Navigation**:
- Tab navigation
- Enter to submit
- Escape to close
- Arrow keys for dropdowns

**ARIA Labels**:
- Icon buttons have labels
- Form inputs properly labeled
- Status messages announced

**Color Contrast**:
- High contrast text
- Accessible color combinations
- Focus indicators

## Styling & Theming

### Chakra UI Configuration

**Theme File** (`theme.ts`):
- Custom color palette
- Glass effect variants
- Component base styles
- Button variants
- Box variants

**Custom Colors**:
```typescript
glass: {
  50-900: rgba(255, 255, 255, 0.1-0.95)
}
glass-dark: {
  50-900: rgba(0, 0, 0, 0.1-0.95)
}
gradient: {
  primary, success, error, background
}
```

### CSS Animations

**Global Styles** (`index.css`):
- Keyframe animations
- Utility classes
- Glass effect styles
- Animation delays

**Key Animations**:
- Fade in
- Slide up
- Gradient animation
- Floating elements
- Pulse effects

### Component Styling Patterns

**Consistent Patterns**:
- Glass containers for cards
- Hover lift on buttons
- Smooth transitions
- Consistent spacing (gap, padding)
- Border radius (12px, 16px)

**Color Usage**:
- Primary: Blue for actions
- Success: Green for success states
- Error: Red for errors
- Gray: Text and backgrounds

## API Integration

### Endpoint Usage

All API calls use the `/api` prefix:

**Base URL**: `http://localhost:8000/api`

**Fetch Patterns**:
```typescript
// GET request
const res = await fetch('/api/versions')
const json = await res.json()

// POST request with FormData
const form = new FormData()
form.append('file', file)
form.append('version_name', name)
const res = await fetch('/api/ingest_versioned', {
  method: 'POST',
  body: form
})

// GET with query parameters
const res = await fetch(`/api/query?q=${encodeURIComponent(query)}&version_id=${versionId}`)
```

### Error Handling

**Error Patterns**:
```typescript
try {
  const res = await fetch('/api/endpoint')
  const json = await res.json()
  if (!res.ok) {
    throw new Error(json.detail || res.statusText)
  }
  // Handle success
} catch (e: any) {
  // Handle error
  setError(e.message)
}
```

**Error Display**:
- Red notification boxes
- Error icons
- User-friendly messages
- Console logging for debugging

### Loading States

**Loading Patterns**:
```typescript
const [loading, setLoading] = useState(false)

// Start loading
setLoading(true)
try {
  // API call
} finally {
  setLoading(false)
}
```

**Loading UI**:
- Spinner components
- Disabled buttons
- Progress bars
- Loading text

### Progress Tracking

**Progress Polling** (for async operations):
```typescript
const pollProgress = async (jobId: string) => {
  const interval = setInterval(async () => {
    const res = await fetch(`/api/documentation_progress/${jobId}`)
    const progress = await res.json()
    
    setUploadProgress({
      total: progress.total_files,
      completed: progress.completed_files,
      status: progress.status
    })
    
    if (progress.status === 'completed') {
      clearInterval(interval)
      // Handle completion
    }
  }, 1000) // Poll every second
}
```

## Development

### Development Workflow

1. **Start Development Server**:
   ```bash
   npm run dev
   ```

2. **Make Changes**:
   - Edit files in `src/`
   - Hot Module Replacement (HMR) updates automatically

3. **Test Changes**:
   - Check browser console for errors
   - Test functionality
   - Verify responsive design

4. **Build for Production**:
   ```bash
   npm run build
   ```

### Adding New Pages

1. **Create Page Component**:
   ```typescript
   // src/pages/NewPage.tsx
   export default function NewPage() {
     return (
       <VStack gap={8} align="stretch">
         <Heading>New Page</Heading>
         {/* Content */}
       </VStack>
     )
   }
   ```

2. **Add Route**:
   ```typescript
   // src/main.tsx
   import NewPage from './pages/NewPage'
   
   const router = createBrowserRouter([
     {
       path: '/',
       element: <App />,
       children: [
         { path: 'newpage', element: <NewPage /> }
       ]
     }
   ])
   ```

3. **Add Navigation Link**:
   ```typescript
   // src/pages/App.tsx
   const navItems = [
     // ... existing items
     { path: '/newpage', label: 'New Page', icon: FiIcon }
   ]
   ```

### Styling Guidelines

**Use Chakra UI Components**:
- Prefer Chakra components over custom HTML
- Use theme colors and spacing
- Follow Chakra UI patterns

**Glass Effects**:
- Use `className="glass"` for standard glass
- Use `className="glass-strong"` for emphasis
- Use `className="glass-card"` for cards

**Spacing**:
- Use `gap` prop for consistent spacing
- Use `p` (padding) and `m` (margin) props
- Follow 4px/8px spacing scale

**Colors**:
- Use theme colors: `blue.400`, `gray.800`, etc.
- Use semantic colors: `success`, `error`
- Maintain contrast for readability

### TypeScript Usage

**Type Definitions**:
```typescript
// Define interfaces for API responses
interface Version {
  version_id: string
  version_name: string
  description: string
  // ... other fields
}

// Use types in state
const [versions, setVersions] = useState<Version[]>([])
```

**Type Safety**:
- Use TypeScript for all components
- Define prop types
- Type API responses
- Avoid `any` when possible

### Component Patterns

**State Management**:
```typescript
const [state, setState] = useState<Type>(initialValue)
const [loading, setLoading] = useState(false)
const [error, setError] = useState<string | null>(null)
```

**API Calls**:
```typescript
const fetchData = async () => {
  setLoading(true)
  setError(null)
  try {
    const res = await fetch('/api/endpoint')
    const json = await res.json()
    if (!res.ok) throw new Error(json.detail)
    setState(json.data)
  } catch (e: any) {
    setError(e.message)
  } finally {
    setLoading(false)
  }
}
```

**Effects**:
```typescript
useEffect(() => {
  fetchData()
}, []) // Run once on mount

useEffect(() => {
  // Effect with dependencies
}, [dependency])
```

## Troubleshooting

### Common Issues

**1. API Connection Errors**
- **Error**: `Failed to fetch`
- **Solution**: Ensure backend is running on port 8000
- **Check**: Verify CORS settings in backend

**2. Build Errors**
- **Error**: TypeScript compilation errors
- **Solution**: Check type definitions, fix type errors
- **Check**: Ensure all imports are correct

**3. Hot Reload Not Working**
- **Error**: Changes not reflected
- **Solution**: Restart dev server
- **Check**: Browser cache, clear and reload

**4. Styling Issues**
- **Error**: Styles not applying
- **Solution**: Check class names, verify CSS imports
- **Check**: Chakra UI theme configuration

**5. Routing Issues**
- **Error**: 404 on navigation
- **Solution**: Verify route definitions in `main.tsx`
- **Check**: Browser console for errors

### Debugging Tips

1. **Browser DevTools**:
   - Check Console for errors
   - Inspect Network tab for API calls
   - Use React DevTools for component inspection

2. **Console Logging**:
   ```typescript
   console.log('Debug:', data)
   console.error('Error:', error)
   ```

3. **TypeScript Errors**:
   - Check terminal for compilation errors
   - Fix type mismatches
   - Ensure proper type definitions

4. **API Testing**:
   - Use browser Network tab
   - Check request/response payloads
   - Verify endpoint URLs

### Performance Optimization

1. **Code Splitting**:
   - Already implemented via React Router
   - Lazy load components if needed

2. **Image Optimization**:
   - Use appropriate image formats
   - Implement lazy loading for images

3. **Bundle Size**:
   - Check bundle size with `npm run build`
   - Remove unused dependencies
   - Use tree-shaking

## Build & Deployment

### Production Build

```bash
npm run build
```

**Output**:
- `dist/` directory with optimized files
- Minified JavaScript
- Optimized CSS
- Asset optimization

### Preview Production Build

```bash
npm run preview
```

### Deployment Options

**Static Hosting**:
- Deploy `dist/` to static hosting
- Configure API proxy if needed
- Set environment variables

**Vercel/Netlify**:
- Connect repository
- Configure build command: `npm run build`
- Set output directory: `dist`
- Configure API proxy

**Custom Server**:
- Serve `dist/` directory
- Configure reverse proxy for API
- Set up HTTPS

### Environment Configuration

**Development**:
- API URL: `http://localhost:8000`
- Dev server: `http://localhost:5173`

**Production**:
- Configure API URL via environment variables
- Use production API endpoint
- Set up CORS properly

## Additional Resources

- [React Documentation](https://react.dev/)
- [TypeScript Documentation](https://www.typescriptlang.org/)
- [Chakra UI Documentation](https://chakra-ui.com/)
- [Vite Documentation](https://vitejs.dev/)
- [React Router Documentation](https://reactrouter.com/)

