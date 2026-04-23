import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { environment } from '../../environments/environment';

interface ForeignTradePoint {
  date: string;
  buyVol: number;
  sellVol: number;
  buyVal: number;
  sellVal: number;
}

interface AnalyzeResult {
  symbol: string;
  action: 'buy' | 'sell' | 'hold';
  confidence: number;
  currentPrice: number;
  reasons: string[];
  prices: { date: string; close: number }[];
  foreignTrade: ForeignTradePoint[];
}

@Component({
  selector: 'app-analyze-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './analyze-dashboard.component.html',
  styleUrl: './analyze-dashboard.component.css'
})
export class AnalyzeDashboardComponent {
  private readonly http = inject(HttpClient);
  private readonly apiBaseUrl = environment.apiBaseUrl.replace(/\/+$/, '');

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

    this.http.post<{ results: AnalyzeResult[] }>(`${this.apiBaseUrl}/analyze`, body).subscribe({
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
    if (!prices.length) return '';
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

  foreignNetBars(foreignTrade: ForeignTradePoint[]): { x: number; y: number; w: number; h: number; positive: boolean }[] {
    if (!foreignTrade?.length) return [];
    const width = 240;
    const halfH = 40;
    const n = foreignTrade.length;
    const nets = foreignTrade.map((f) => f.buyVol - f.sellVol);
    const maxAbs = Math.max(...nets.map(Math.abs), 1);
    const barW = Math.max(1, width / n - 1);
    return nets.map((net, i) => {
      const barH = (Math.abs(net) / maxAbs) * halfH;
      const positive = net >= 0;
      return {
        x: i * (width / n),
        y: positive ? halfH - barH : halfH,
        w: barW,
        h: barH,
        positive
      };
    });
  }

  foreignRatio(foreignTrade: ForeignTradePoint[]): { buyPct: number; sellPct: number } {
    if (!foreignTrade?.length) return { buyPct: 50, sellPct: 50 };
    const totalBuy = foreignTrade.reduce((s, f) => s + f.buyVol, 0);
    const totalSell = foreignTrade.reduce((s, f) => s + f.sellVol, 0);
    const total = totalBuy + totalSell || 1;
    return {
      buyPct: Math.round((totalBuy / total) * 100),
      sellPct: Math.round((totalSell / total) * 100)
    };
  }

  totalForeignBuy(foreignTrade: ForeignTradePoint[]): number {
    return foreignTrade?.reduce((s, f) => s + f.buyVol, 0) ?? 0;
  }

  totalForeignSell(foreignTrade: ForeignTradePoint[]): number {
    return foreignTrade?.reduce((s, f) => s + f.sellVol, 0) ?? 0;
  }

  formatPrice(price: number): string {
    return price.toLocaleString('vi-VN');
  }

  formatVol(vol: number): string {
    if (vol >= 1_000_000) return (vol / 1_000_000).toFixed(1) + 'M';
    if (vol >= 1_000) return (vol / 1_000).toFixed(0) + 'K';
    return vol.toString();
  }
}
