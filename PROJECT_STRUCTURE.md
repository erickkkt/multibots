# Multibots Project Structure

## Directory Structure

```plaintext
multibots/
├── backend/
│   ├── Multibots.sln
│   ├── Multibots.Api/
│   │   ├── Controllers/
│   │   │   ├── AnalyzeController.cs
│   │   │   └── AssistantController.cs
│   │   ├── Models/
│   │   ├── Services/
│   │   └── Program.cs
│   ├── Multibots.Api.Tests/
│   └── Multibots.Core/
├── python_engine/
│   ├── engine.py
│   ├── vnstock_adapter.py
│   ├── server.py
│   └── test_engine.py
└── frontend/
    ├── angular.json
    ├── package.json
    ├── tsconfig*.json
    └── src/
        ├── app/
        ├── environments/
        └── index.html
```

## Phase 1 Components

- **Python Engine**: Rule-based analysis (MA, RSI, MACD, volume breakout), OHLCV normalization, and `/analyze` HTTP endpoint.
- **C# API Gateway**: `/analyze` endpoint, request validation (max 5 symbols), in-memory caching, and HTTP integration with Python engine.
- **Angular Dashboard**: Symbol input (max 5), parameter controls, realtime signal cards, and price + signal chart overlay.
