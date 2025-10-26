# FlightVault Frontend

Modern Next.js 15 frontend for FlightVault - Visual Disaster Recovery Tool.

## Features

- **Timeline Slider** - Navigate through 24 hours of database history
- **Real-time Data Display** - View records at any timestamp
- **AI-Powered Restore** - Smart restore point suggestions
- **Responsive Design** - Works on desktop and mobile
- **TypeScript** - Full type safety
- **Tailwind CSS** - Modern, clean UI

## Getting Started

1. **Install dependencies:**
```bash
cd frontend
npm install
```

2. **Start development server:**
```bash
npm run dev
```

3. **Open browser:**
```
http://localhost:3000
```

## Prerequisites

- Node.js 18+ 
- FlightVault API running on http://localhost:8000

## Architecture

```
frontend/
├── app/                 # Next.js 15 app directory
├── components/          # React components
│   ├── Header.tsx       # Status header
│   ├── TimelineSlider.tsx # Main timeline feature
│   ├── DataDisplay.tsx  # Data table with pagination
│   └── RestorePanel.tsx # AI restore suggestions
├── lib/                 # Utilities
│   ├── api.ts          # API client
│   └── utils.ts        # Helper functions
└── types/              # TypeScript definitions
```

## Key Components

### TimelineSlider
- Horizontal slider for time navigation
- Visual markers for change events
- Debounced API calls for smooth performance
- Historical vs current state indicators

### DataDisplay  
- Paginated data table
- Export functionality
- Real-time updates as timeline changes
- Responsive design

### RestorePanel
- AI-powered restore suggestions
- Confidence scoring
- Preview and execute restore
- Confirmation dialogs

## API Integration

The frontend communicates with the FlightVault API through:
- `/api/timeline` - Timeline data
- `/api/state` - Historical data snapshots  
- `/api/suggest-restore` - AI restore suggestions
- `/api/restore` - Execute recovery operations

## Styling

- **Tailwind CSS** for utility-first styling
- **Custom components** for consistent design
- **Responsive breakpoints** for mobile support
- **Dark mode ready** (can be enabled)

## Performance

- **Debounced API calls** prevent excessive requests
- **Pagination** handles large datasets
- **Loading states** provide user feedback
- **Error boundaries** handle failures gracefully