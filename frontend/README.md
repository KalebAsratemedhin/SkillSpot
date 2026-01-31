# SkillSpot Frontend

Vue 3 + TypeScript frontend for SkillSpot marketplace application with shadcn-vue components and Zod validation.

## Tech Stack

- **Vue 3** - Progressive JavaScript framework
- **TypeScript** - Type-safe JavaScript
- **Pinia** - State management
- **Vue Router** - Client-side routing
- **Axios** - HTTP client
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn-vue** - High-quality Vue components
- **Zod** - Schema validation
- **Vite** - Build tool and dev server

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create a `.env` file (optional):
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

3. Start development server:
```bash
npm run dev
```

4. Build for production:
```bash
npm run build
```

## Features

- **Authentication**: Login, register, and JWT token management with Zod validation
- **Job Management**: Browse, create, and manage jobs
- **Profile Management**: User and service provider profiles
- **Messaging**: Real-time messaging between users
- **Contracts**: Contract creation and signing
- **Responsive Design**: Mobile-first responsive UI
- **Dark Mode**: Full dark mode support
- **Type Safety**: Full TypeScript coverage
- **Form Validation**: Zod schemas for all forms

## Components

The project uses shadcn-vue components located in `src/components/ui/`:
- `Button` - Styled button component with variants
- `Input` - Form input with validation support
- `FormField` - Form field wrapper with error display

## Validation

Zod schemas are defined in `src/lib/validations/`:
- `auth.ts` - Login and registration schemas

## API Integration

The frontend communicates with the Django REST API backend. All API calls are handled through service modules in `src/services/` with proper TypeScript typing.

## State Management

State is managed using Pinia stores:
- `auth` - Authentication and user state
- `jobs` - Job listings and details
- `profiles` - User profiles
- `messaging` - Conversations and messages

## Routing

Protected routes require authentication. Guest routes (login/register) redirect authenticated users to the dashboard.
