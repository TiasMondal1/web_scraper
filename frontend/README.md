# Price Tracker Pro - Frontend

Modern React dashboard for Price Tracker Pro SaaS application.

## Tech Stack

- **React 18** - UI library
- **Vite** - Build tool
- **React Router** - Routing
- **Tailwind CSS** - Styling
- **Axios** - API client
- **Recharts** - Data visualization
- **React Hook Form** - Form handling
- **React Hot Toast** - Notifications

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at `http://localhost:3000`

### Build for Production

```bash
# Create production build
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/      # Reusable components
│   │   ├── Layout.jsx   # Main layout
│   │   ├── Navbar.jsx   # Navigation
│   │   └── ...
│   ├── pages/           # Page components
│   │   ├── Landing.jsx  # Landing page
│   │   ├── Dashboard.jsx # User dashboard
│   │   ├── Products.jsx # Product list
│   │   └── ...
│   ├── context/         # React context
│   │   └── AuthContext.jsx # Auth state
│   ├── utils/           # Utilities
│   │   └── api.js       # API client
│   ├── App.jsx          # Main app component
│   ├── main.jsx         # Entry point
│   └── index.css        # Global styles
├── public/              # Static assets
├── index.html           # HTML template
├── vite.config.js       # Vite configuration
├── tailwind.config.js   # Tailwind configuration
└── package.json         # Dependencies

## Key Features

### Authentication
- User registration and login
- JWT token management
- Auto token refresh
- Protected routes

### Dashboard
- Overview statistics
- Product tracking
- Price alerts
- Savings tracking

### Products
- Add products to track
- View price history
- Set target prices
- Enable/disable alerts

### Alerts
- View price drop notifications
- Filter by date
- Export data

## Environment Variables

Create a `.env` file:

```env
VITE_API_URL=http://localhost:8000
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Lint code

## API Integration

The frontend communicates with the backend API using Axios. All API calls go through `src/utils/api.js` which handles:

- Authentication headers
- Token refresh
- Error handling
- Request/response interceptors

## Styling

This project uses Tailwind CSS for styling. Custom utilities are defined in `src/index.css`.

Common classes:
- `.btn-primary` - Primary button
- `.btn-secondary` - Secondary button
- `.input` - Form input
- `.card` - Card container

## Deployment

### Deploy to Vercel

```bash
npm install -g vercel
vercel
```

### Deploy to Netlify

```bash
npm install -g netlify-cli
netlify deploy --prod
```

### Build and Deploy with Docker

```dockerfile
# Dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Contributing

1. Create feature branch
2. Make changes
3. Test thoroughly
4. Submit pull request

## License

MIT
