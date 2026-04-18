import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

interface AnalyzeResult {
  symbol: string;
  action: 'buy' | 'sell' | 'hold';
  confidence: number;
  reasons: string[];
  prices: { date: string; close: number }[];
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  private readonly http = inject(HttpClient);

  readonly symbolsInput = signal('HPG,FPT,VCB');
  readonly shortMa = signal(9);
  readonly longMa = signal(21);
  readonly rsi = signal(14);
  readonly loading = signal(false);
  readonly results = signal<AnalyzeResult[]>([]);
  readonly error = signal('');

  readonly symbols = computed(() =>
    this.symbolsInput()
      .split(',')
      .map((x) => x.trim().toUpperCase())
      .filter(Boolean)
      .slice(0, 5)
  );

  analyze(): void {
    this.loading.set(true);
    this.error.set('');

    const body = {
      symbols: this.symbols(),
      parameters: {
        shortMaPeriod: this.shortMa(),
        longMaPeriod: this.longMa(),
        rsiPeriod: this.rsi(),
        volumeLookback: 20,
        candles: 120
      }
    };

    this.http.post<{ results: AnalyzeResult[] }>('http://localhost:5238/analyze', body).subscribe({
      next: (response) => {
        this.results.set(response.results ?? []);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Không lấy được dữ liệu realtime từ backend');
        this.loading.set(false);
      }
    });
  }

  chartPoints(prices: { close: number }[]): string {
    if (!prices.length) {
      return '';
    }

    const width = 240;
    const height = 80;
    const min = Math.min(...prices.map((x) => x.close));
    const max = Math.max(...prices.map((x) => x.close));
    const span = Math.max(max - min, 0.0001);

    return prices
      .map((point, index) => {
        const x = (index / Math.max(prices.length - 1, 1)) * width;
        const y = height - ((point.close - min) / span) * height;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(' ');
  }
}
