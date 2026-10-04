# AI Dynamic Production Scheduling POC - Frontend

This is the frontend dashboard for the AI Dynamic Production Scheduling Proof of Concept. It provides a visual interface to interact with the backend scheduling engine, allowing you to generate schedules, simulate machine breakdowns, and trigger AI rescheduling.

## Tech Stack

- React 18
- TypeScript
- Vite
- Tailwind CSS v4
- Lucide React (Icons)
- date-fns (Date Formatting)
- Axios (API Client)
- React Router (Routing)

## Prerequisites

- Node.js (v18+)
- The backend FastAPI server must be running (default `http://127.0.0.1:8000`).

## Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Environment Variables:**
   Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```
   Ensure `VITE_API_BASE_URL` points to the running backend.

3. **Start Development Server:**
   ```bash
   npm run dev
   ```
   
4. **Build for Production:**
   ```bash
   npm run build
   ```

## Recommended Demo Flow

1. **Start Backend**: Ensure the FastAPI backend is running and `POST /admin/reset` has been called if you want a clean state.
2. **Dashboard**: Observe KPI cards and current machine status.
3. **Schedule**: Click "Generate Initial Schedule". This will trigger the backend solver and display the Gantt chart.
4. **Breakdown Simulation**: Go to "Breakdown Simulation", select a machine (e.g., CNC-02), pick a time during a scheduled job, and simulate a breakdown.
5. **Rescheduling**: Go to "Rescheduling", trigger the AI to re-optimize, and view the comparison and AI decisions.
6. **History**: View the audit log of scheduling events in "History".

## API Integration

This frontend strictly acts as a presentation layer. It does not implement any scheduling or constraint-solving logic. All complex logic is handled by the backend.

The API client is located in `src/api/client.ts` and exports are found in `src/api/index.ts`. All schemas used match the backend responses directly (see `src/types/schemas.ts`).
