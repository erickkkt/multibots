import { CommonModule, DecimalPipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import {
  PnlByTickerValue,
  PortfolioMode,
  PortfolioSimulationRequest,
  PortfolioSimulationResponse,
  PortfolioSimulationService
} from '../services/portfolio-simulation.service';

interface AllocationRow {
  ticker: string;
  percent: number;
}

interface PnlRow {
  ticker: string;
  absolute: number;
  percent: number | null;
}

interface PortfolioSettings {
  initialCapital: number;
  mode: PortfolioMode;
  lookbackDays: number;
  tickersInput: string;
  allocation: Record<string, number>;
  stopLossPct: number;
  takeProfitPct: number;
  feePctPerSide: number;
}

const STORAGE_KEY = 'portfolio-simulation-settings-v1';

@Component({
  selector: 'app-portfolio-simulation',
  standalone: true,
  imports: [CommonModule, FormsModule, DecimalPipe],
  templateUrl: './portfolio-simulation.component.html',
  styleUrl: './portfolio-simulation.component.css'
})
export class PortfolioSimulationComponent implements OnInit {
  readonly initialCapital = signal(100000000);
  readonly mode = signal<PortfolioMode>('Backtest');
  readonly lookbackDays = signal(180);
  readonly tickersInput = signal('HPG,FPT');
  readonly allocationRows = signal<AllocationRow[]>([]);
  readonly stopLossPct = signal(3);
  readonly takeProfitPct = signal(6);
  readonly feePctPerSide = signal(0.1);

  readonly loading = signal(false);
  readonly error = signal('');
  readonly response = signal<PortfolioSimulationResponse | null>(null);

  readonly tickers = computed(() =>
    Array.from(
      new Set(
        this.tickersInput()
          .split(',')
          .map((x) => x.trim().toUpperCase())
          .filter(Boolean)
      )
    )
  );

  readonly allocationSum = computed(() =>
    this.allocationRows().reduce((sum, row) => sum + (Number.isFinite(row.percent) ? row.percent : 0), 0)
  );

  readonly allocationValid = computed(() => Math.abs(this.allocationSum() - 100) < 0.0001);

  readonly canSubmit = computed(
    () =>
      this.initialCapital() > 0 &&
      this.lookbackDays() > 0 &&
      this.tickers().length > 0 &&
      this.allocationRows().length === this.tickers().length &&
      this.allocationValid()
  );

  readonly pnlRows = computed<PnlRow[]>(() => {
    const result = this.response();
    if (!result?.pnlByTicker) {
      return [];
    }

    return Object.entries(result.pnlByTicker).map(([ticker, value]) => {
      const parsed = this.parsePnlValue(value);
      return {
        ticker,
        absolute: parsed.absolute,
        percent: parsed.percent
      };
    });
  });

  constructor(private readonly portfolioService: PortfolioSimulationService) {}

  ngOnInit(): void {
    this.loadSettings();
    this.syncAllocationRows();
  }

  onTickersInputChange(value: string): void {
    this.tickersInput.set(value);
    this.syncAllocationRows();
    this.persistSettings();
  }

  onAllocationChange(index: number, value: string): void {
    const rows = [...this.allocationRows()];
    rows[index] = {
      ...rows[index],
      percent: Number(value)
    };
    this.allocationRows.set(rows);
    this.persistSettings();
  }

  runSimulation(): void {
    this.error.set('');
    this.response.set(null);

    if (!this.canSubmit()) {
      this.error.set('Vui lòng nhập dữ liệu hợp lệ. Tổng allocation phải bằng 100%.');
      return;
    }

    const request: PortfolioSimulationRequest = {
      mode: this.mode(),
      lookbackDays: this.lookbackDays(),
      tickers: this.tickers(),
      allocation: Object.fromEntries(this.allocationRows().map((row) => [row.ticker, row.percent])),
      stopLossPct: this.stopLossPct(),
      takeProfitPct: this.takeProfitPct(),
      feePctPerSide: this.feePctPerSide(),
      initialCapital: this.initialCapital()
    };

    this.persistSettings();
    this.loading.set(true);
    this.portfolioService.simulate(request).subscribe({
      next: (data) => {
        this.response.set(data);
        this.loading.set(false);
      },
      error: (err: HttpErrorResponse) => {
        this.error.set(this.parseError(err));
        this.loading.set(false);
      }
    });
  }

  equityChartPoints(): string {
    const points = this.response()?.equityCurve ?? [];
    if (!points.length) {
      return '';
    }

    const width = 680;
    const height = 240;
    const values = points.map((x) => x.totalValue);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const span = Math.max(max - min, 0.0001);

    return points
      .map((point, index) => {
        const x = (index / Math.max(points.length - 1, 1)) * width;
        const y = height - ((point.totalValue - min) / span) * height;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(' ');
  }

  private syncAllocationRows(): void {
    const tickerList = this.tickers();
    const current = new Map(this.allocationRows().map((x) => [x.ticker, x.percent]));

    const nextRows = tickerList.map((ticker) => ({
      ticker,
      percent: current.get(ticker) ?? 0
    }));

    this.allocationRows.set(nextRows);
  }

  private parsePnlValue(value: PnlByTickerValue): { absolute: number; percent: number | null } {
    if (typeof value === 'number') {
      return { absolute: value, percent: null };
    }

    return {
      absolute: value.absolute ?? 0,
      percent: value.percent ?? null
    };
  }

  private parseError(error: HttpErrorResponse): string {
    const body = error.error;
    if (body && typeof body === 'object') {
      const typedBody = body as { title?: string; detail?: string; errors?: Record<string, string[]> };
      if (typedBody.errors) {
        return Object.values(typedBody.errors)
          .flat()
          .join(' ');
      }
      if (typedBody.detail) {
        return typedBody.detail;
      }
      if (typedBody.title) {
        return typedBody.title;
      }
    }

    return 'Không thể chạy mô phỏng danh mục ở thời điểm này.';
  }

  private loadSettings(): void {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return;
    }

    try {
      const saved = JSON.parse(raw) as Partial<PortfolioSettings>;
      if (typeof saved.initialCapital === 'number' && saved.initialCapital > 0) {
        this.initialCapital.set(saved.initialCapital);
      }
      if (saved.mode === 'Backtest' || saved.mode === 'Realtime') {
        this.mode.set(saved.mode);
      }
      if (typeof saved.lookbackDays === 'number' && saved.lookbackDays > 0) {
        this.lookbackDays.set(saved.lookbackDays);
      }
      if (typeof saved.tickersInput === 'string') {
        this.tickersInput.set(saved.tickersInput);
      }
      if (typeof saved.stopLossPct === 'number') {
        this.stopLossPct.set(saved.stopLossPct);
      }
      if (typeof saved.takeProfitPct === 'number') {
        this.takeProfitPct.set(saved.takeProfitPct);
      }
      if (typeof saved.feePctPerSide === 'number') {
        this.feePctPerSide.set(saved.feePctPerSide);
      }
      if (saved.allocation) {
        const rows = Object.entries(saved.allocation)
          .filter(([ticker, value]) => typeof ticker === 'string' && typeof value === 'number')
          .map(([ticker, percent]) => ({ ticker, percent }));
        if (rows.length > 0) {
          this.allocationRows.set(rows);
        }
      }
    } catch {
      localStorage.removeItem(STORAGE_KEY);
    }
  }

  persistSettings(): void {
    const payload: PortfolioSettings = {
      initialCapital: this.initialCapital(),
      mode: this.mode(),
      lookbackDays: this.lookbackDays(),
      tickersInput: this.tickersInput(),
      allocation: Object.fromEntries(this.allocationRows().map((row) => [row.ticker, row.percent])),
      stopLossPct: this.stopLossPct(),
      takeProfitPct: this.takeProfitPct(),
      feePctPerSide: this.feePctPerSide()
    };

    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  }
}
