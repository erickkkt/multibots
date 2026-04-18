import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export type PortfolioMode = 'Backtest' | 'Realtime';

export interface PortfolioSimulationRequest {
  mode: PortfolioMode;
  lookbackDays: number;
  tickers: string[];
  allocation: Record<string, number>;
  stopLossPct: number;
  takeProfitPct: number;
  feePctPerSide: number;
  initialCapital: number;
}

export interface EquityPoint {
  timestamp: string;
  totalValue: number;
}

export interface PortfolioTrade {
  symbol: string;
  entryDate: string;
  exitDate: string;
  entryPrice: number;
  exitPrice: number;
  quantity: number;
  grossPnl: number;
  netPnl: number;
  exitReason: string;
}

export interface PortfolioPnlItem {
  absolute?: number;
  percent?: number;
}

export type PnlByTickerValue = number | PortfolioPnlItem;

export interface PortfolioSimulationResponse {
  generatedAtUtc: string;
  mode: PortfolioMode;
  equityCurve: EquityPoint[];
  pnlByTicker: Record<string, PnlByTickerValue>;
  trades?: PortfolioTrade[];
}

@Injectable({
  providedIn: 'root'
})
export class PortfolioSimulationService {
  private readonly http = inject(HttpClient);
  private readonly apiBaseUrl = environment.apiBaseUrl.replace(/\/+$/, '');

  simulate(request: PortfolioSimulationRequest): Observable<PortfolioSimulationResponse> {
    return this.http.post<PortfolioSimulationResponse>(`${this.apiBaseUrl}/api/portfolio/simulate`, request);
  }
}
