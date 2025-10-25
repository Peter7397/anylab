# OnLab Frontend

A modern React-based web interface for the OnLab lab IT operations and troubleshooting platform.

## Features

- **Dashboard**: System overview with quick stats and recent activity
- **AI Assistant**: Knowledge library management and conversational AI chat
- **Navigation**: Collapsible sidebar with organized sections
- **Responsive Design**: Modern UI built with Tailwind CSS
- **TypeScript**: Full type safety throughout the application

## Technology Stack

- **React 18** with TypeScript
- **React Router** for navigation
- **Tailwind CSS** for styling
- **Lucide React** for icons
- **Framer Motion** for animations (ready for future use)

## Getting Started

### Prerequisites

- Node.js 16+ 
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

3. Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

### Available Scripts

- `npm start` - Runs the app in development mode
- `npm test` - Launches the test runner
- `npm run build` - Builds the app for production
- `npm run eject` - Ejects from Create React App (not recommended)

## Project Structure

```
src/
├── components/
│   ├── Layout/           # Main layout components
│   │   ├── Layout.tsx    # Main layout wrapper
│   │   ├── Sidebar.tsx   # Navigation sidebar
│   │   └── TopBar.tsx    # Top action bar
│   ├── Dashboard/        # Dashboard components
│   │   └── Dashboard.tsx # Main dashboard
│   └── AI/              # AI Assistant components
│       ├── KnowledgeLibrary.tsx
│       └── ChatAssistant.tsx
├── types/               # TypeScript type definitions
│   └── index.ts
├── App.tsx             # Main app component with routing
└── index.css           # Global styles with Tailwind
```

## UI Components

### Layout Components
- **Sidebar**: Collapsible navigation with grouped sections
- **TopBar**: Quick actions, AI mode toggle, user menu
- **Breadcrumbs**: Dynamic navigation path display

### Dashboard
- **Stats Cards**: System overview metrics
- **System Overview**: Real-time system status
- **Recent Activity**: Latest system events
- **Quick Actions**: Direct access to key features

### AI Assistant
- **Knowledge Library**: PDF upload and URL management
- **Chat Interface**: Conversational AI with source citations
- **Document Filtering**: Select knowledge sources for AI responses

## Design System

### Colors
- **Primary**: Blue shades for main actions
- **Success**: Green for positive states
- **Warning**: Yellow for caution states  
- **Danger**: Red for error states

### Components
- **Buttons**: Primary, secondary, and danger variants
- **Cards**: Consistent card styling with shadows
- **Tables**: Responsive table layouts
- **Status Badges**: Color-coded status indicators

## Development

### Adding New Pages

1. Create a new component in the appropriate directory
2. Add the route to `App.tsx`
3. Update the sidebar navigation if needed

### Styling

- Use Tailwind CSS classes for styling
- Custom components are defined in `src/index.css`
- Follow the established design patterns

### State Management

Currently using React's built-in state management. For complex state, consider:
- React Context for global state
- Zustand for lightweight state management
- Redux Toolkit for complex applications

## Future Enhancements

- [ ] Dark mode support
- [ ] Real-time notifications
- [ ] Advanced filtering and search
- [ ] Data visualization charts
- [ ] Export functionality
- [ ] Mobile responsive improvements

## Contributing

1. Follow the existing code style and patterns
2. Use TypeScript for all new components
3. Add proper type definitions
4. Test your changes thoroughly

## License

This project is part of the OnLab platform.
