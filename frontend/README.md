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

```
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

