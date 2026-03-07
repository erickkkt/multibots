# Multibots Project Structure

## Directory Structure

```plaintext
multibots/
├── backend/
│   ├── Dockerfile
│   ├── multibots.sln
│   ├── Multibots.Api/
│   │   ├── Controllers/
│   │   ├── Models/
│   │   ├── Services/
│   │   ├── Startup.cs
│   │   └── Program.cs
│   └── Multibots.Core/
│       ├── Interfaces/
│       ├── Entities/
│       └── Services/
│
├── frontend/
│   ├── Dockerfile
│   ├── angular.json
│   ├── package.json
│   ├── src/
│   │   ├── app/
│   │   ├── assets/
│   │   ├── environments/
│   │   └── index.html
│   └── tsconfig.json
│
└── docker-compose.yml
```

## Docker Configuration
- Backend Dockerfile: Specify the build instructions for the .NET backend service.
- Frontend Dockerfile: Specify the build instructions for the Angular frontend.
- Docker Compose: To orchestrate the backend and frontend services together.
