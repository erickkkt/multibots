import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    redirectTo: 'analyze'
  },
  {
    path: 'analyze',
    loadComponent: () => import('./pages/analyze-dashboard.component').then((m) => m.AnalyzeDashboardComponent)
  },
  {
    path: 'portfolio-simulation',
    loadComponent: () =>
      import('./pages/portfolio-simulation.component').then((m) => m.PortfolioSimulationComponent)
  },
  {
    path: '**',
    redirectTo: 'analyze'
  }
];
